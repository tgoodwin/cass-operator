import time
import yaml
import threading
import concurrent.futures
import argparse
import sys
import os
import json
import logging
import random
import datetime
from collections import deque # Used to track active resources efficiently

# --- Plotting Imports ---
# Removed plotting imports

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from copy import deepcopy

# --- Configuration ---
DEFAULT_NAMESPACE = "default"
DEFAULT_BASE_NAME = "loadtest-cdc" # Base name for created resources
DEFAULT_RATES_GEOM = [2**i for i in range(8)] # 1, 2, ..., 128
DEFAULT_MEASUREMENT_DURATION_S = 300 # 5 minutes
DEFAULT_WARMUP_DURATION_S = 60 # 1 minute
DEFAULT_COOLDOWN_S = 30 # 30 seconds
DEFAULT_YAML_PATH = "cdc_template.yaml"
DEFAULT_WORKERS = 50 # Default worker threads for creates/deletes
DEFAULT_MAX_CONCURRENT_CDCS = 100 # Max target number of CDCs existing at once per step
DEFAULT_OUTPUT_JSON = "load_results.json"
LOAD_TEST_LABEL_KEY = "cdc-load-test"
LOAD_TEST_LABEL_VALUE = "true"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- K8s API Interaction Functions ---

def load_yaml_template(path):
    """Loads the base CassandraDatacenter YAML template."""
    try:
        with open(path, 'r') as stream:
            template = yaml.safe_load(stream)
            # No need to enforce size here, create will use template's spec
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

def create_k8s_api_client(num_workers):
    """Initializes K8s clients, configuring the global connection pool size."""
    try:
        try: config.load_kube_config()
        except config.ConfigException:
            try: config.load_incluster_config()
            except config.ConfigException:
                logging.error("Could not load any Kubernetes configuration.")
                return None, None

        default_config = client.Configuration.get_default()
        if not default_config:
             logging.error("Failed to get default Kubernetes configuration after loading.")
             return None, None

        pool_size = num_workers + 10
        default_config.pool_connections = pool_size
        default_config.pool_maxsize = pool_size
        logging.info(f"Set global default Kubernetes client connection pool size to: {pool_size}")
        logging.info(f"Attempting to connect to K8s API server at: {default_config.host}")

        v1_api = client.CoreV1Api()
        custom_api = client.CustomObjectsApi()

        try: # Test connection
             v1_api.list_namespace(limit=1)
             logging.debug("Initial connection test successful.")
        except Exception as test_e:
             logging.error(f"Initial connection test failed: {test_e}", exc_info=True)
             # return None, None # Optional: exit early

        return v1_api, custom_api
    except Exception as e:
        logging.error(f"Error initializing Kubernetes client: {e}", exc_info=True)
        return None, None

def create_cdc_worker(custom_api, namespace, cr_name, template_body, api_info):
    """Worker function to create a CassandraDatacenter CR with the load test label."""
    body = deepcopy(template_body)
    if 'metadata' not in body: body['metadata'] = {}
    body['metadata']['name'] = cr_name
    body['metadata']['namespace'] = namespace
    if 'labels' not in body['metadata']: body['metadata']['labels'] = {}
    body['metadata']['labels'][LOAD_TEST_LABEL_KEY] = LOAD_TEST_LABEL_VALUE # Add the label

    try:
        custom_api.create_namespaced_custom_object(
            group=api_info['group'], version=api_info['version'],
            namespace=namespace, plural=api_info['plural'], body=body
        )
        return True
    except ApiException as e:
        if e.status == 409: # Already exists (e.g., from failed cleanup)
            logging.warning(f"CR {cr_name} already exists (409). Treating as successful dispatch.")
            return True # Still count as work dispatched
        else:
            logging.error(f"Failed to create CR {cr_name}. Status: {e.status}, Reason: {e.reason}, Body: {getattr(e, 'body', 'N/A')}")
            return False
    except Exception as e:
        logging.error(f"Unexpected error creating CR {cr_name}: {e}", exc_info=True)
        return False

def delete_cdc_worker(custom_api, namespace, name, api_info):
    """Worker function to delete a CassandraDatacenter CR."""
    try:
        custom_api.delete_namespaced_custom_object(
            group=api_info['group'], version=api_info['version'], namespace=namespace,
            plural=api_info['plural'], name=name, body=client.V1DeleteOptions(propagation_policy='Background')
        )
        logging.debug(f"Submitted async delete for {name}")
    except ApiException as e:
        if e.status != 404: # Ignore not found errors during cleanup
            logging.warning(f"API Error submitting async delete for {name}: {e.status} - {e.reason}")
    except Exception as e:
        logging.warning(f"Non-API Error submitting async delete for {name}: {e}")


def delete_cdc_by_label(custom_api, namespace, label_key, label_value, api_info, num_workers=20):
    """Deletes resources matching a label selector in parallel (Final Cleanup)."""
    cleanup_start_time = time.time()
    label_selector = f"{label_key}={label_value}"
    logging.info(f"--- Starting final cleanup by LISTING resources with label '{label_selector}' ---")
    names_to_delete = []
    try:
        res = custom_api.list_namespaced_custom_object(
            group=api_info['group'], version=api_info['version'], namespace=namespace,
            plural=api_info['plural'], label_selector=label_selector,
        )
        items = res.get('items', [])
        names_to_delete = [item.get('metadata', {}).get('name') for item in items if item.get('metadata', {}).get('name')]
        logging.info(f"Found {len(names_to_delete)} resource(s) matching label selector for cleanup.")
    except ApiException as e:
        logging.error(f"Cleanup: API Error LISTING resources: {e.status} - {e.reason}")
        return
    except Exception as e:
        logging.error(f"Cleanup: Non-API Error LISTING resources: {e}", exc_info=True)
        return

    if not names_to_delete:
        logging.info("--- Cleanup finished (no matching resources found) ---")
        return

    # Use a separate small pool for cleanup deletes
    cleanup_workers = min(num_workers, 20) # Don't use too many workers for cleanup
    with concurrent.futures.ThreadPoolExecutor(max_workers=cleanup_workers, thread_name_prefix='final_cleanup') as executor:
        # Submit all delete tasks
        futures = [executor.submit(delete_cdc_worker, custom_api, namespace, name, api_info) for name in names_to_delete]
        concurrent.futures.wait(futures) # Wait for submissions, not necessarily completion

    logging.info(f"--- Final cleanup finished submitting deletes in {time.time() - cleanup_start_time:.2f}s ---")

# --- Load Generation Functions ---

# Removed precreate_pool function

def run_load_phase(custom_api, rate, duration_s, namespace, base_name, template_body, api_info, num_workers, step_index, max_concurrent_cdcs, phase_name="measurement"):
    """
    Runs a load generation phase (warm-up or measurement).
    Creates new resources at the target rate.
    If max_concurrent_cdcs is reached, deletes the oldest resource before creating a new one.

    Args:
        custom_api (client.CustomObjectsApi): Initialized K8s client.
        rate (float): The target request dispatch rate (creates per second).
        duration_s (int): Duration for this phase (seconds).
        namespace (str): Target Kubernetes namespace.
        base_name (str): Base name for generated CRs.
        template_body (dict): Loaded YAML template for the CR.
        api_info (dict): Contains 'group', 'version', 'plural'.
        num_workers (int): Maximum number of worker threads in the pool.
        step_index (int): Index of the current rate step for unique naming.
        max_concurrent_cdcs (int): Target maximum number of active CDCs for this step.
        phase_name (str): Identifier for logging ("Warmup" or "Measurement").

    Returns:
        tuple: (requests_submitted_count, active_cdc_queue)
               Returns the total count of create requests submitted and the queue
               containing the names of currently active CDCs created in this phase.
    """
    step_start_time = time.time()
    step_end_time = step_start_time + duration_s
    logging.info(f"    Starting {phase_name} Phase: Rate={rate:.2f} req/s, Duration={duration_s}s, Max Concurrent={max_concurrent_cdcs}")

    request_count = 0
    # Use a deque to efficiently track active CDC names (add to right, remove from left)
    active_cdc_queue = deque(maxlen=max_concurrent_cdcs if max_concurrent_cdcs > 0 else None)
    # Use a separate small pool for delete operations so they don't block create workers
    delete_workers = min(num_workers // 4, 10) + 1 # Small pool for deletes
    delete_executor = concurrent.futures.ThreadPoolExecutor(max_workers=delete_workers, thread_name_prefix=f'{phase_name}_del')

    if rate <= 0 or duration_s <= 0:
        logging.info(f"    Skipping {phase_name} phase (rate or duration is zero/negative).")
        delete_executor.shutdown(wait=False) # Shutdown delete pool
        return 0, active_cdc_queue

    inter_request_delay = 1.0 / rate

    # Main executor for CREATE operations
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers, thread_name_prefix=f'{phase_name}{step_index}_r{rate:.1f}') as create_executor:
        next_req_target_time = step_start_time

        while True:
            current_time = time.time()
            if current_time >= step_end_time: break

            sleep_duration = max(0, next_req_target_time - current_time)
            time.sleep(sleep_duration)

            current_time_after_sleep = time.time()
            if current_time_after_sleep >= step_end_time: break

            # --- Bounded Resource Logic ---
            if max_concurrent_cdcs > 0 and len(active_cdc_queue) >= max_concurrent_cdcs:
                # Limit reached, delete the oldest CDC before creating a new one
                try:
                    name_to_delete = active_cdc_queue.popleft() # Remove oldest from the left
                    # Submit delete asynchronously using the separate delete pool
                    delete_executor.submit(delete_cdc_worker, custom_api, namespace, name_to_delete, api_info)
                except IndexError:
                    pass # Should not happen if len check is correct, but handle defensively

            # --- Dispatch Create Request ---
            # Generate a unique name for the new CR
            cr_name = f"{base_name}-{phase_name}-{step_index}-{rate:.1f}-{request_count}"

            # Submit the CREATE task to the main worker pool
            create_executor.submit(create_cdc_worker, custom_api, namespace, cr_name, template_body, api_info)
            active_cdc_queue.append(cr_name) # Add new name to the right of the queue

            request_count += 1
            next_req_target_time += inter_request_delay
            # --- End Dispatch ---

    actual_step_end_time = time.time()
    logging.info(f"    Finished {phase_name} Phase. Submitted {request_count} create requests in {actual_step_end_time - step_start_time:.2f}s.")
    logging.info(f"    Approx {len(active_cdc_queue)} active CDCs at end of phase.")

    # Shutdown the delete executor, allow pending deletes to complete if possible
    delete_executor.shutdown(wait=True) # Wait for submitted delete tasks

    return request_count, active_cdc_queue


def main():
    """
    Main function to parse arguments, set up clients, run load generation
    (bounded create/delete), and save results.
    """
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Kubernetes CassandraDatacenter Load Generator (Bounded Create/Delete)")
    # Load Gen Args
    parser.add_argument("-n", "--namespace", default=DEFAULT_NAMESPACE, help="Namespace for resources")
    parser.add_argument("-b", "--base-name", default=DEFAULT_BASE_NAME, help="Base name prefix for created resources")
    parser.add_argument("-r", "--rates", nargs='+', type=float, default=DEFAULT_RATES_GEOM, help=f"List of target create rates (req/s). Default: {DEFAULT_RATES_GEOM}")
    parser.add_argument("--measurement-duration", type=int, default=DEFAULT_MEASUREMENT_DURATION_S, help=f"Measurement duration per step (s). Default: {DEFAULT_MEASUREMENT_DURATION_S}")
    parser.add_argument("--warmup-duration", type=int, default=DEFAULT_WARMUP_DURATION_S, help=f"Warm-up duration per step (s). Default: {DEFAULT_WARMUP_DURATION_S}")
    parser.add_argument("-c", "--cooldown", type=int, default=DEFAULT_COOLDOWN_S, help=f"Cooldown period between steps (s). Default: {DEFAULT_COOLDOWN_S}")
    parser.add_argument("-y", "--yaml-path", default=DEFAULT_YAML_PATH, help=f"Path to the CDC YAML template. Default: {DEFAULT_YAML_PATH}")
    parser.add_argument("--max-concurrent-cdcs", type=int, default=DEFAULT_MAX_CONCURRENT_CDCS, help=f"Target max number of simultaneously existing CDCs per step. Default: {DEFAULT_MAX_CONCURRENT_CDCS}")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help=f"Number of worker threads for K8s API calls. Default: {DEFAULT_WORKERS}")
    parser.add_argument("-o", "--output-json", default=DEFAULT_OUTPUT_JSON, help=f"Path to save the results JSON file. Default: {DEFAULT_OUTPUT_JSON}")
    # Removed Plotting Args

    args = parser.parse_args()

    # --- Input Validation ---
    if args.measurement_duration <= 0 or args.warmup_duration < 0 or args.cooldown < 0 or args.workers <= 0 or args.max_concurrent_cdcs <= 0:
        logging.error("Durations, workers, and max-concurrent-cdcs must be positive/non-negative.")
        sys.exit(1)

    # --- Initialization ---
    template_body = load_yaml_template(args.yaml_path)
    if not template_body: sys.exit(1)

    v1_api, custom_api = create_k8s_api_client(num_workers=args.workers)
    if not custom_api: sys.exit(1)

    try:
        api_info = {'group': template_body['apiVersion'].split('/')[0], 'version': template_body['apiVersion'].split('/')[1], 'plural': "cassandradatacenters"}
    except Exception as e:
         logging.error(f"Could not parse apiVersion from template: {e}")
         sys.exit(1)

    try: v1_api.read_namespace(name=args.namespace)
    except ApiException as e:
        if e.status == 404: logging.error(f"Namespace '{args.namespace}' not found.")
        else: logging.error(f"Error checking namespace '{args.namespace}': {e.reason}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Failed initial namespace check - possible connection issue: {e}", exc_info=True)
        sys.exit(1)


    target_rates = sorted(list(set(r for r in args.rates if r > 0)))
    if not target_rates:
         logging.error("No valid positive measurement rates specified.")
         sys.exit(1)

    logging.info(f"--- Load Generation Configuration ---")
    logging.info(f"Target Create Rates (req/s): {target_rates}")
    logging.info(f"Max Concurrent CDCs per Step: {args.max_concurrent_cdcs}")
    logging.info(f"Measurement duration: {args.measurement_duration}s | Warm-up duration: {args.warmup_duration}s | Cooldown: {args.cooldown}s")
    logging.info(f"Workers: {args.workers} | Template: {args.yaml_path} | Namespace: {args.namespace}")
    logging.info(f"Output JSON: {args.output_json}")
    # Removed logging for plotting config

    all_results_data = {}
    # Removed pool_names initialization

    try:
        # --- Removed Pre-create Resource Pool ---

        # --- Main Load Generation Loop ---
        active_cdcs_at_end_of_step = deque() # Track resources across steps for final cleanup robustness
        for i, measurement_rate in enumerate(target_rates):
            logging.info(f"\n===== Starting Experiment Step {i+1}/{len(target_rates)} for Rate: {measurement_rate:.2f} creates/s =====")

            # --- Warm-up Phase ---
            warmup_reqs, active_cdcs_warmup = run_load_phase(
                custom_api, measurement_rate, args.warmup_duration, args.namespace,
                args.base_name, template_body, api_info, args.workers, i,
                args.max_concurrent_cdcs, "Warmup"
            )

            # --- Measurement Phase ---
            measurement_t_start = time.time()
            logging.info(f"  Measurement Window T_START (Epoch): {measurement_t_start:.0f}")
            measurement_reqs, active_cdcs_measure = run_load_phase(
                custom_api, measurement_rate, args.measurement_duration, args.namespace,
                args.base_name, template_body, api_info, args.workers, i,
                args.max_concurrent_cdcs, "Measurement"
            )
            measurement_t_end = measurement_t_start + args.measurement_duration
            logging.info(f"  Measurement Window T_END (Epoch): {measurement_t_end:.0f}")

            # Store results
            all_results_data[str(measurement_rate)] = {
                "T_START": measurement_t_start, "T_END": measurement_t_end,
                "warmup_requests_submitted": warmup_reqs,
                "measurement_requests_submitted": measurement_reqs,
                "target_max_concurrent": args.max_concurrent_cdcs
            }
            expected_reqs = measurement_rate * args.measurement_duration
            logging.info(f"  Target measurement requests: {expected_reqs:.0f}, Actual submitted: {measurement_reqs}")

            # Track all potentially active CDCs for final cleanup
            # Note: This list might grow large if cleanup within step fails often
            active_cdcs_at_end_of_step.extend(active_cdcs_warmup)
            active_cdcs_at_end_of_step.extend(active_cdcs_measure)


            # --- Cooldown Phase ---
            if i < len(target_rates) - 1:
                 logging.info(f"--- Cooling down for {args.cooldown}s ---")
                 time.sleep(args.cooldown)

    except KeyboardInterrupt:
        logging.warning("\n--- Load generation interrupted by user! ---")
    except Exception as e:
        logging.exception(f"An unexpected error occurred during load generation: {e}")
    finally:
        # --- Save Results ---
        if all_results_data:
            try:
                with open(args.output_json, 'w') as f: json.dump(all_results_data, f, indent=4)
                logging.info(f"Successfully saved results to {args.output_json}")
            except Exception as e: logging.error(f"Failed to write results to {args.output_json}: {e}")

        # --- Removed Plotting Call ---

        # --- Final Cleanup ---
        # Use label selector for robustness, as the active queue might be incomplete if errors occurred
        logging.info("Initiating final cleanup using label selector...")
        if 'custom_api' in locals() and custom_api:
             delete_cdc_by_label(custom_api, args.namespace, LOAD_TEST_LABEL_KEY, LOAD_TEST_LABEL_VALUE, api_info, args.workers)
        else:
             logging.error("Cannot perform final cleanup: Kubernetes API client likely failed initialization.")

        # --- Final Summary Output ---
        print("\n" + "="*30 + "\n--- Load Generation Summary ---\n" + "="*30)
        if not all_results_data: print("  No load steps were completed.")
        else:
            print(f"\nResults saved to: {args.output_json}")
            print("\nMeasurement Windows & Request Counts:")
            hdr_fmt = f"{'Rate (req/s)':<15} | {'T_START':<18} | {'T_END':<18} | {'Warmup Reqs':<12} | {'Measure Reqs':<12} | {'Max Concurrent':<15}"
            sep_len = len(hdr_fmt)
            print("-" * sep_len + f"\n{hdr_fmt}\n" + "-" * sep_len)
            for rate_str in sorted(all_results_data.keys(), key=float):
                r = all_results_data[rate_str]
                print(f"{float(rate_str):<15.2f} | {r['T_START']:<18.0f} | {r['T_END']:<18.0f} | {r['warmup_requests_submitted']:<12} | {r['measurement_requests_submitted']:<12} | {r['target_max_concurrent']:<15}")
            print("-" * sep_len)
            # Removed plotting info from summary
        print("="*30)

if __name__ == "__main__":
    main()
