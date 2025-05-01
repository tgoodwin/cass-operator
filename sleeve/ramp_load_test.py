import time
import yaml
import threading
import concurrent.futures
import argparse
import sys
import os
import json
import logging
import random # For selecting resource to update
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from copy import deepcopy

# --- Configuration ---
DEFAULT_NAMESPACE = "default"
# Adjusted base name prefix to be closer to previous script's pattern
DEFAULT_BASE_NAME = "loadtest-cdc" # Base name for the pre-created pool
# Geometric sequence: 1, 2, 4, 8, 16, 32, 64, 128
DEFAULT_RATES_GEOM = [2**i for i in range(8)]
# --- Durations ---
DEFAULT_MEASUREMENT_DURATION_S = 300 # 5 minutes (300 seconds) for the actual measurement window
DEFAULT_WARMUP_DURATION_S = 60 # 1 minute (60 seconds) for warm-up (using the measurement rate)
DEFAULT_COOLDOWN_S = 30 # Pause between rates (30 seconds)
DEFAULT_YAML_PATH = "cdc_template.yaml" # Default path for the CR template
DEFAULT_WORKERS = 50 # Max concurrent K8s API calls via workers
DEFAULT_POOL_SIZE = 50 # Number of CDC resources to pre-create and update
DEFAULT_OUTPUT_JSON = "load_results.json" # Default output file name
LOAD_TEST_LABEL_KEY = "cdc-load-test" # Specific label key for this test
LOAD_TEST_LABEL_VALUE = "true" # Label value

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- K8s API Interaction Functions ---

def load_yaml_template(path):
    """Loads the base CassandraDatacenter YAML template."""
    try:
        with open(path, 'r') as stream:
            # Ensure size is present and set to 1 initially in the template
            template = yaml.safe_load(stream)
            if 'spec' not in template:
                template['spec'] = {}
            if 'size' not in template['spec']:
                logging.warning(f"Template {path} missing spec.size, defaulting to 1.")
                template['spec']['size'] = 1
            elif template['spec']['size'] != 1:
                 logging.warning(f"Template {path} spec.size is not 1. Setting to 1 for initial state.")
                 template['spec']['size'] = 1
            return template
    except FileNotFoundError:
        logging.error(f"YAML template file not found: {path}")
        return None
    except yaml.YAMLError as exc:
        logging.error(f"Error parsing YAML file {path}: {exc}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error loading YAML {path}: {e}")
        return None

def create_k8s_api_client():
    """Initializes and returns Kubernetes API clients."""
    try:
        try:
            config.load_kube_config()
            logging.info("Loaded Kubernetes configuration from kubeconfig.")
        except config.ConfigException:
            try:
                config.load_incluster_config()
                logging.info("Loaded Kubernetes configuration from in-cluster service account.")
            except config.ConfigException:
                logging.error("Could not load any Kubernetes configuration.")
                return None, None

        v1_api = client.CoreV1Api()
        custom_api = client.CustomObjectsApi()
        return v1_api, custom_api
    except Exception as e:
        logging.error(f"Error initializing Kubernetes client: {e}")
        return None, None

def create_or_update_labeled_cdc(custom_api, namespace, cr_name, template_body):
    """
    Creates a CassandraDatacenter if it doesn't exist, or updates its labels
    if it does. Ensures the load test label is present. Used for pool creation.

    Returns:
        bool: True if the resource exists or was created successfully, False otherwise.
    """
    body = deepcopy(template_body)
    if 'metadata' not in body: body['metadata'] = {}
    body['metadata']['name'] = cr_name
    body['metadata']['namespace'] = namespace
    if 'labels' not in body['metadata']: body['metadata']['labels'] = {}
    body['metadata']['labels'][LOAD_TEST_LABEL_KEY] = LOAD_TEST_LABEL_VALUE
    # Ensure size is 1 for initial pool creation
    if 'spec' not in body: body['spec'] = {}
    body['spec']['size'] = 1

    group = body['apiVersion'].split('/')[0]
    version = body['apiVersion'].split('/')[1]
    plural = "cassandradatacenters"

    try:
        # Try to get the resource first
        custom_api.get_namespaced_custom_object(group, version, namespace, plural, cr_name)
        # If it exists, patch the labels to ensure ours is present
        logging.debug(f"Resource {cr_name} already exists. Ensuring label is present.")
        # Use JSON Merge Patch for potentially simpler label updates if the key might not exist
        patch = {"metadata": {"labels": {LOAD_TEST_LABEL_KEY: LOAD_TEST_LABEL_VALUE}}}
        # Rely on client library to set Content-Type for merge patch
        custom_api.patch_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=cr_name,
            body=patch
        )
        return True
    except ApiException as e:
        if e.status == 404:
            # Not found, create it
            try:
                logging.debug(f"Creating resource {cr_name} for the pool.")
                custom_api.create_namespaced_custom_object(group, version, namespace, plural, body)
                return True
            except ApiException as create_e:
                logging.error(f"Failed to create pool resource {cr_name}. Status: {create_e.status}, Reason: {create_e.reason}")
                return False
            except Exception as create_e:
                 logging.error(f"Unexpected error creating pool resource {cr_name}: {create_e}")
                 return False
        else:
            # Log other errors during GET or PATCH
            logging.error(f"Error checking/patching pool resource {cr_name}. Status: {e.status}, Reason: {e.reason}")
            return False
    except Exception as e:
         logging.error(f"Unexpected error checking/creating pool resource {cr_name}: {e}")
         return False


def update_cdc_worker(custom_api, namespace, cr_name, target_size, api_info):
    """
    Worker function to patch the spec.size of a CassandraDatacenter CR using JSON Merge Patch.

    Args:
        custom_api (client.CustomObjectsApi): Initialized K8s client.
        namespace (str): Namespace of the CR.
        cr_name (str): Name of the CR to patch.
        target_size (int): The desired size (e.g., 1 or 2).
        api_info (dict): Contains 'group', 'version', 'plural'.

    Returns:
        bool: True if patch was successful, False otherwise.
    """
    # --- Use JSON Merge Patch format ---
    # This sends only the fields that need to be changed/added within their structure.
    patch = {
        "spec": {
            "size": target_size
        }
    }

    try:
        # Rely on client library to set Content-Type for merge patch (usually application/merge-patch+json)
        custom_api.patch_namespaced_custom_object(
            group=api_info['group'],
            version=api_info['version'],
            namespace=namespace,
            plural=api_info['plural'],
            name=cr_name,
            body=patch # Send the merge patch object
        )
        # logging.debug(f"Successfully submitted merge patch for {cr_name} to size {target_size}")
        return True
    except ApiException as e:
        if e.status == 404:
            logging.warning(f"Cannot patch {cr_name}: Not Found (404). May have been deleted.")
        else:
            # Log the body of the error for more details if available
            error_body = e.body
            try:
                # Try to parse if it's JSON
                error_details = json.loads(error_body)
            except json.JSONDecodeError:
                error_details = error_body # Keep as string if not JSON
            logging.error(f"Failed to merge patch CR {cr_name}. Status: {e.status}, Reason: {e.reason}, Body: {error_details}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error merge patching CR {cr_name}: {e}")
        return False


def delete_cdc_by_label(custom_api, namespace, label_key, label_value, api_info, num_workers=20):
    """Deletes resources matching a label selector in parallel."""
    cleanup_start_time = time.time()
    label_selector = f"{label_key}={label_value}"
    logging.info(f"--- Starting final cleanup by LISTING resources with label '{label_selector}' ---")
    names_to_delete = []

    try:
        res = custom_api.list_namespaced_custom_object(
            group=api_info['group'],
            version=api_info['version'],
            namespace=namespace,
            plural=api_info['plural'],
            label_selector=label_selector,
        )
        items = res.get('items', [])
        names_to_delete = [item.get('metadata', {}).get('name') for item in items if item.get('metadata', {}).get('name')]
        logging.info(f"Found {len(names_to_delete)} resource(s) matching label selector for cleanup.")

    except ApiException as e:
        logging.error(f"Cleanup: API Error LISTING resources: {e.status} - {e.reason}")
        return # Cannot proceed with deletion if list failed
    except Exception as e:
        logging.error(f"Cleanup: Non-API Error LISTING resources: {e}")
        return

    if not names_to_delete:
        logging.info("--- Cleanup finished (no matching resources found) ---")
        return

    # Use ThreadPoolExecutor for parallel deletion
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers, thread_name_prefix='cleanup') as executor:
        # Need a simple delete function for the executor
        def delete_worker(name):
            try:
                custom_api.delete_namespaced_custom_object(
                    group=api_info['group'],
                    version=api_info['version'],
                    namespace=namespace,
                    plural=api_info['plural'],
                    name=name,
                    body=client.V1DeleteOptions(propagation_policy='Background'),
                )
                # logging.info(f"Cleanup: Submitted DELETE for {name}")
            except ApiException as e:
                if e.status == 404:
                    logging.warning(f"Cleanup: {name} already deleted (404).")
                else:
                    logging.error(f"Cleanup: API Error deleting {name}: {e.status} - {e.reason}")
            except Exception as e:
                logging.error(f"Cleanup: Non-API Error deleting {name}: {e}")

        # Submit all delete tasks
        futures = [executor.submit(delete_worker, name) for name in names_to_delete]
        concurrent.futures.wait(futures)

    logging.info(f"--- Final cleanup finished in {time.time() - cleanup_start_time:.2f}s ---")


# --- Load Generation Functions ---

def precreate_pool(custom_api, pool_size, namespace, base_name, template_body, num_workers=20):
    """Creates the initial pool of resources."""
    logging.info(f"--- Pre-creating resource pool (size: {pool_size}) ---")
    # Use the updated base_name for pool resource names
    pool_names = [f"{base_name}-{i}" for i in range(pool_size)]
    created_count = 0
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers, thread_name_prefix='pool_create') as executor:
        futures = [executor.submit(create_or_update_labeled_cdc, custom_api, namespace, name, template_body) for name in pool_names]
        # Wait for all futures to complete and collect results
        results = []
        for future in concurrent.futures.as_completed(futures):
             try:
                 results.append(future.result())
             except Exception as exc:
                 logging.error(f'Pool creation task generated an exception: {exc}')
                 results.append(False) # Treat exception as failure

        created_count = sum(1 for r in results if r is True)

    logging.info(f"--- Pool creation finished in {time.time() - start_time:.2f}s. {created_count}/{pool_size} resources ensured. ---")
    if created_count < pool_size:
         logging.warning("Some pool resources might not have been created/ensured successfully. Check logs.")

    # Return the list of intended names; update worker handles potential 404s if creation failed silently.
    return pool_names


def run_load_phase(custom_api, rate, duration_s, namespace, pool_names, api_info, num_workers, step_index, phase_name="measurement"):
    """
    Runs a load generation phase (warm-up or measurement), dispatching update tasks.

    Args:
        custom_api (client.CustomObjectsApi): Initialized K8s client.
        rate (float): The target request dispatch rate (updates per second).
        duration_s (int): Duration for this phase (seconds).
        namespace (str): Target Kubernetes namespace.
        pool_names (list): List of names of the pre-created resources.
        api_info (dict): Contains 'group', 'version', 'plural'.
        num_workers (int): Maximum number of worker threads in the pool.
        step_index (int): Index of the current rate step.
        phase_name (str): Identifier for logging ("warmup" or "measurement").

    Returns:
        int: The total number of requests submitted during this phase.
    """
    step_start_time = time.time()
    step_end_time = step_start_time + duration_s
    logging.info(f"    Starting {phase_name} Phase: Rate={rate:.2f} req/s, Duration={duration_s}s")

    request_count = 0
    pool_size = len(pool_names)

    if rate <= 0 or duration_s <= 0 or pool_size == 0:
        logging.info(f"    Skipping {phase_name} phase (rate/duration is zero/negative or pool is empty).")
        return 0 # Return 0 requests submitted

    inter_request_delay = 1.0 / rate

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers, thread_name_prefix=f'{phase_name}{step_index}_r{rate:.1f}') as executor:
        next_req_target_time = step_start_time

        while True:
            current_time = time.time()
            if current_time >= step_end_time:
                break

            sleep_duration = max(0, next_req_target_time - current_time)
            time.sleep(sleep_duration)

            current_time_after_sleep = time.time()
            if current_time_after_sleep >= step_end_time:
                break

            # Select resource from pool (round-robin)
            resource_index = request_count % pool_size
            cr_name_to_update = pool_names[resource_index]

            # Determine target size (alternate between 1 and 2)
            target_size = 2 if (request_count % 2 == 0) else 1

            # Dispatch the update task
            executor.submit(update_cdc_worker, custom_api, namespace, cr_name_to_update, target_size, api_info)

            request_count += 1
            next_req_target_time += inter_request_delay

    actual_step_end_time = time.time()
    # Log the actual count at the end of the phase
    logging.info(f"    Finished {phase_name} Phase. Submitted {request_count} update requests in {actual_step_end_time - step_start_time:.2f}s.")
    # Return the count
    return request_count


def main():
    """
    Main function to parse arguments, set up clients, pre-create resources,
    run the load generation loop (updates), and clean up.
    """
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Kubernetes CassandraDatacenter Load Generator (Update Strategy)")
    parser.add_argument("-n", "--namespace", default=DEFAULT_NAMESPACE, help="Namespace for resources")
    # Use the updated default base name
    parser.add_argument("-b", "--base-name", default=DEFAULT_BASE_NAME, help="Base name prefix for the resource pool")
    parser.add_argument("-r", "--rates", nargs='+', type=float, default=DEFAULT_RATES_GEOM,
                        help=f"List of target update rates (req/s) for each step. Default: {DEFAULT_RATES_GEOM}")
    parser.add_argument("--measurement-duration", type=int, default=DEFAULT_MEASUREMENT_DURATION_S,
                        help=f"Duration for the measurement window per step (seconds). Default: {DEFAULT_MEASUREMENT_DURATION_S}")
    parser.add_argument("--warmup-duration", type=int, default=DEFAULT_WARMUP_DURATION_S,
                        help=f"Duration for warm-up using updates before measurement (seconds). Default: {DEFAULT_WARMUP_DURATION_S}")
    parser.add_argument("-c", "--cooldown", type=int, default=DEFAULT_COOLDOWN_S,
                        help=f"Cooldown period between rate steps (seconds). Default: {DEFAULT_COOLDOWN_S}")
    parser.add_argument("-y", "--yaml-path", default=DEFAULT_YAML_PATH,
                        help=f"Path to the CassandraDatacenter YAML template. Default: {DEFAULT_YAML_PATH}")
    parser.add_argument("--pool-size", type=int, default=DEFAULT_POOL_SIZE,
                        help=f"Number of CDC resources to pre-create in the pool. Default: {DEFAULT_POOL_SIZE}")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help=f"Number of worker threads for K8s API calls. Default: {DEFAULT_WORKERS}")
    parser.add_argument("-o", "--output-json", default=DEFAULT_OUTPUT_JSON,
                        help=f"Path to save the results JSON file. Default: {DEFAULT_OUTPUT_JSON}")

    args = parser.parse_args()

    # --- Input Validation ---
    if args.measurement_duration <= 0 or args.warmup_duration < 0 or args.cooldown < 0 or args.workers <= 0 or args.pool_size <= 0:
        logging.error("Durations (measurement, warmup, cooldown), workers, and pool-size must be positive/non-negative.")
        sys.exit(1)

    # --- Initialization ---
    template_body = load_yaml_template(args.yaml_path)
    if not template_body:
        sys.exit(1)

    v1_api, custom_api = create_k8s_api_client()
    if not custom_api:
        sys.exit(1)

    # Extract API info from template once
    try:
        api_info = {
            'group': template_body['apiVersion'].split('/')[0],
            'version': template_body['apiVersion'].split('/')[1],
            'plural': "cassandradatacenters" # Assuming plural
        }
    except (KeyError, IndexError, AttributeError) as e:
         logging.error(f"Could not parse apiVersion '{template_body.get('apiVersion', 'N/A')}' from template: {e}")
         sys.exit(1)

    # Check namespace
    try:
         v1_api.read_namespace(name=args.namespace)
         logging.info(f"Target namespace '{args.namespace}' found.")
    except ApiException as e:
        if e.status == 404:
            logging.error(f"Namespace '{args.namespace}' not found.")
        else:
            logging.error(f"Error checking namespace '{args.namespace}': {e.reason}")
        sys.exit(1)

    target_rates = sorted(list(set(r for r in args.rates if r > 0)))
    if not target_rates:
         logging.error("No valid positive measurement rates specified.")
         sys.exit(1)

    logging.info(f"Target Update Rates (req/s): {target_rates}")
    logging.info(f"Resource Pool Size: {args.pool_size}")
    logging.info(f"Measurement duration per step: {args.measurement_duration}s")
    logging.info(f"Warm-up duration per step: {args.warmup_duration}s (at the same rate)")
    logging.info(f"Cooldown between steps: {args.cooldown}s")
    logging.info(f"Worker threads: {args.workers}")
    logging.info(f"Using template: {args.yaml_path}")
    logging.info(f"Target namespace: {args.namespace}")
    logging.info(f"Output JSON file: {args.output_json}")

    all_results_data = {}
    pool_names = [] # Initialize empty list

    try:
        # --- Pre-create Resource Pool ---
        pool_names = precreate_pool(custom_api, args.pool_size, args.namespace, args.base_name, template_body, args.workers)
        if not pool_names or len(pool_names) < args.pool_size:
             logging.warning("Resource pool creation might be incomplete.")
             if not pool_names:
                  logging.error("No pool resources available. Exiting.")
                  sys.exit(1)

        logging.info("Pausing briefly after pool creation...")
        time.sleep(10)


        # --- Main Load Generation Loop ---
        for i, measurement_rate in enumerate(target_rates):
            logging.info(f"\n===== Starting Experiment Step {i+1}/{len(target_rates)} for Rate: {measurement_rate:.2f} updates/s =====")

            # --- Warm-up Phase (using updates) ---
            warmup_requests_submitted = run_load_phase(
                custom_api=custom_api,
                rate=measurement_rate, # Use the step's rate for warm-up
                duration_s=args.warmup_duration,
                namespace=args.namespace,
                pool_names=pool_names,
                api_info=api_info,
                num_workers=args.workers,
                step_index=i,
                phase_name="Warmup" # Pass phase name
            )

            # --- Measurement Phase ---
            measurement_t_start = time.time() # T_START is *after* warm-up
            logging.info(f"  Measurement Window T_START (Epoch): {measurement_t_start:.0f}")

            measurement_requests_submitted = run_load_phase(
                custom_api=custom_api,
                rate=measurement_rate,
                duration_s=args.measurement_duration,
                namespace=args.namespace,
                pool_names=pool_names,
                api_info=api_info,
                num_workers=args.workers,
                step_index=i,
                phase_name="Measurement" # Pass phase name
            )

            # Calculate T_END based on the scheduled duration
            measurement_t_end = measurement_t_start + args.measurement_duration
            logging.info(f"  Measurement Window T_END (Epoch): {measurement_t_end:.0f}")

            # Store the result for this rate step, including counts
            all_results_data[str(measurement_rate)] = {
                "T_START": measurement_t_start,
                "T_END": measurement_t_end,
                "warmup_requests_submitted": warmup_requests_submitted,
                "measurement_requests_submitted": measurement_requests_submitted
            }
            # Log the total expected vs actual for the measurement period
            expected_measurement_reqs = measurement_rate * args.measurement_duration
            logging.info(f"  Target measurement requests: {expected_measurement_reqs:.0f}, Actual submitted: {measurement_requests_submitted}")


            # --- Cooldown Phase ---
            if i < len(target_rates) - 1:
                 logging.info(f"--- Cooling down for {args.cooldown}s ---")
                 time.sleep(args.cooldown)

    except KeyboardInterrupt:
        logging.warning("\n--- Load generation interrupted by user (KeyboardInterrupt)! ---")
    except Exception as e:
        logging.exception(f"An unexpected error occurred during the main loop: {e}")
    finally:
        # --- Save Results to JSON ---
        if all_results_data:
            try:
                with open(args.output_json, 'w') as f:
                    json.dump(all_results_data, f, indent=4)
                logging.info(f"Successfully saved results to {args.output_json}")
            except IOError as e:
                logging.error(f"Failed to write results to {args.output_json}: {e}")
            except TypeError as e:
                logging.error(f"Error serializing results to JSON: {e}")

        # --- Final Cleanup ---
        logging.info("Initiating final cleanup of resource pool...")
        if 'custom_api' in locals() and custom_api:
             delete_cdc_by_label(custom_api, args.namespace, LOAD_TEST_LABEL_KEY, LOAD_TEST_LABEL_VALUE, api_info, args.workers)
        else:
             logging.error("Cannot perform final cleanup: Kubernetes API client not initialized.")


        # --- Final Summary Output ---
        print("\n" + "="*30)
        print("--- Load Generation Summary ---")
        print("="*30)
        if not all_results_data:
             print("  No load steps were completed or results recorded.")
        else:
            print(f"\nResults saved to: {args.output_json}")
            print("\nMeasurement Windows & Request Counts:")
            # Adjust formatting for new columns
            hdr_fmt = f"{'Rate (req/s)':<15} | {'T_START':<18} | {'T_END':<18} | {'Warmup Reqs':<12} | {'Measure Reqs':<12}"
            sep_len = len(hdr_fmt)
            print("-" * sep_len)
            print(hdr_fmt)
            print("-" * sep_len)
            # Sort by rate for display
            for rate_str in sorted(all_results_data.keys(), key=float):
                result = all_results_data[rate_str]
                print(f"{float(rate_str):<15.2f} | {result['T_START']:<18.0f} | {result['T_END']:<18.0f} | {result['warmup_requests_submitted']:<12} | {result['measurement_requests_submitted']:<12}")
            print("-" * sep_len)
            print("\nUse T_START and T_END with Prometheus range queries.")
        print("="*30)


if __name__ == "__main__":
    main()
