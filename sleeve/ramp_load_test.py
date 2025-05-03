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
DEFAULT_MAX_CONCURRENT_CDCS = 100 # Target number of CDCs existing at once
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

# --- Reverted K8s Client Initialization ---
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
        if e.status == 409: # Already exists
            logging.warning(f"CR {cr_name} already exists (409) during create attempt.")
            return False # Indicate it wasn't newly created
        elif e.status == 422: # Unprocessable Entity (likely validation error)
             logging.error(f"Failed to create CR {cr_name}. Status: {e.status}, Reason: {e.reason}, Body: {getattr(e, 'body', 'N/A')}")
             # Log the invalid name specifically if possible
             try:
                 error_details = json.loads(e.body)
                 if error_details.get("reason") == "Invalid" and error_details.get("details", {}).get("field") == "metadata.name":
                      logging.error(f"Invalid name generated: {cr_name}")
             except: pass # Ignore parsing errors
             return False
        else:
            logging.error(f"Failed to create CR {cr_name}. Status: {e.status}, Reason: {e.reason}, Body: {getattr(e, 'body', 'N/A')}")
            return False
    except Exception as e:
        logging.error(f"Unexpected error creating CR {cr_name}: {e}", exc_info=True)
        return False

def delete_cdc_worker(custom_api, namespace, name, api_info):
    """Worker function to delete a CassandraDatacenter CR."""
    if not name: return # Safety check
    try:
        custom_api.delete_namespaced_custom_object(
            group=api_info['group'], version=api_info['version'], namespace=namespace,
            plural=api_info['plural'], name=name, body=client.V1DeleteOptions(propagation_policy='Background')
        )
        logging.debug(f"Submitted async delete for {name}")
    except ApiException as e:
        if e.status != 404: # Ignore not found errors
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

    cleanup_workers = min(num_workers, 20)
    with concurrent.futures.ThreadPoolExecutor(max_workers=cleanup_workers, thread_name_prefix='final_cleanup') as executor:
        futures = [executor.submit(delete_cdc_worker, custom_api, namespace, name, api_info) for name in names_to_delete]
        concurrent.futures.wait(futures)
    logging.info(f"--- Final cleanup finished submitting deletes in {time.time() - cleanup_start_time:.2f}s ---")

# --- Load Generation Functions ---

def prefill_pool(custom_api, target_pool_size, namespace, base_name, template_body, api_info, num_workers=20):
    """Creates exactly target_pool_size resources to pre-fill the pool."""
    logging.info(f"--- Pre-filling resource pool to target size: {target_pool_size} ---")
    pool_names_deque = deque(maxlen=target_pool_size)
    created_count = 0
    attempted_names = set()
    sequence = 0
    start_time = time.time()

    # Check existing resources first
    label_selector = f"{LOAD_TEST_LABEL_KEY}={LOAD_TEST_LABEL_VALUE}"
    try:
        res = custom_api.list_namespaced_custom_object(
            group=api_info['group'], version=api_info['version'], namespace=namespace,
            plural=api_info['plural'], label_selector=label_selector,
        )
        items = res.get('items', [])
        existing_names = {item.get('metadata', {}).get('name') for item in items if item.get('metadata', {}).get('name')}
        logging.info(f"Found {len(existing_names)} existing resources with label.")
        for name in existing_names:
             if created_count < target_pool_size:
                 pool_names_deque.append(name)
                 attempted_names.add(name)
                 created_count += 1
             else:
                 logging.warning(f"Found more existing resources than pool size. Deleting excess: {name}")
                 delete_cdc_worker(custom_api, namespace, name, api_info)
    except Exception as e:
        logging.error(f"Prefill: Error LISTING existing resources: {e}. Proceeding without check.", exc_info=True)

    # Create remaining resources needed
    needed = target_pool_size - created_count
    if needed > 0:
        logging.info(f"Need to create {needed} more resources for the pool.")
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers, thread_name_prefix='pool_fill') as executor:
            futures = {}
            while created_count < target_pool_size:
                # Simplified naming for pool items
                cr_name = f"{base_name}-pool-{sequence}"
                sequence += 1
                if cr_name in attempted_names: continue
                attempted_names.add(cr_name)
                future = executor.submit(create_cdc_worker, custom_api, namespace, cr_name, template_body, api_info)
                futures[future] = cr_name
                done, _ = concurrent.futures.wait(futures.keys(), timeout=0.1, return_when=concurrent.futures.FIRST_COMPLETED)
                for f in done:
                    name = futures.pop(f)
                    try:
                        if f.result() is True:
                            pool_names_deque.append(name)
                            created_count += 1
                            if created_count >= target_pool_size: break
                        else: logging.warning(f"Creation failed or CR already existed for {name}")
                    except Exception as exc: logging.error(f'Prefill task for {name} generated an exception: {exc}')
                if created_count >= target_pool_size: break
            for f in concurrent.futures.as_completed(futures.keys()):
                 name = futures[f]
                 try:
                     if f.result() is True and created_count < target_pool_size:
                         pool_names_deque.append(name)
                         created_count += 1
                 except Exception as exc: logging.error(f'Prefill task for {name} generated an exception after loop: {exc}')

    logging.info(f"--- Pool pre-fill finished in {time.time() - start_time:.2f}s. Pool size: {len(pool_names_deque)}/{target_pool_size}. ---")
    if len(pool_names_deque) < target_pool_size:
        logging.error(f"Failed to pre-fill pool to target size {target_pool_size}. Only created {len(pool_names_deque)}. Exiting.")
        sys.exit(1)
    return pool_names_deque


def run_load_phase(custom_api, rate, duration_s, namespace, base_name, template_body, api_info, num_workers, step_index, active_cdc_queue, phase_name="measurement"):
    """
    Runs a load generation phase (warm-up or measurement) using the pre-filled pool.
    Alternates submitting DELETE and CREATE operations to achieve the target total rate R.

    Args:
        custom_api (client.CustomObjectsApi): Initialized K8s client.
        rate (float): The target total operation rate (creates + deletes per second).
        duration_s (int): Duration for this phase (seconds).
        namespace (str): Target Kubernetes namespace.
        base_name (str): Base name for newly generated CRs.
        template_body (dict): Loaded YAML template for the CR.
        api_info (dict): Contains 'group', 'version', 'plural'.
        num_workers (int): Maximum number of worker threads in the pool for creates/deletes.
        step_index (int): Index of the current rate step for unique naming.
        active_cdc_queue (deque): Deque tracking the names of active CDCs (should be pre-filled).
        phase_name (str): Identifier for logging ("Warmup" or "Measurement").

    Returns:
        tuple: (create_count, delete_count) submitted during this phase.
    """
    step_start_time = time.time()
    step_end_time = step_start_time + duration_s
    logging.info(f"    Starting {phase_name} Phase: Target Rate={rate:.2f} ops/s (Alternate Create/Delete), Duration={duration_s}s")

    create_submitted_count = 0
    delete_submitted_count = 0
    operation_counter = 0 # Used to alternate operations and for unique naming

    initial_pool_size = len(active_cdc_queue)
    if initial_pool_size == 0:
         logging.error(f"Cannot run {phase_name} phase with an empty active CDC queue.")
         return 0, 0

    if rate <= 0 or duration_s <= 0:
        logging.info(f"    Skipping {phase_name} phase (rate or duration is zero/negative).")
        return 0, 0

    inter_request_delay = 1.0 / rate # Delay between *any* operation (delete or create)

    # Use a single executor pool for both creates and deletes now
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers, thread_name_prefix=f'{phase_name}{step_index}_r{int(rate)}') as executor: # Use int(rate) in name
        next_op_target_time = step_start_time

        while True:
            current_time = time.time()
            if current_time >= step_end_time: break

            sleep_duration = max(0, next_op_target_time - current_time)
            time.sleep(sleep_duration)

            current_time_after_sleep = time.time()
            if current_time_after_sleep >= step_end_time: break

            # --- Alternate Operation ---
            if operation_counter % 2 == 0:
                # --- Dispatch Delete ---
                name_to_delete = None
                try:
                    name_to_delete = active_cdc_queue.popleft()
                    executor.submit(delete_cdc_worker, custom_api, namespace, name_to_delete, api_info)
                    delete_submitted_count += 1
                except IndexError:
                    logging.error(f"Active CDC queue became empty during {phase_name} phase when trying to delete!")
                except Exception as e:
                    logging.error(f"Error submitting delete for {name_to_delete}: {e}")
            else:
                # --- Dispatch Create ---
                # Simplified, RFC 1123 compliant naming scheme
                # Uses base name, phase (lower), step index, and an operation counter
                cr_name = f"{base_name}-{phase_name.lower()}-{step_index}-{operation_counter}"
                # Submit CREATE task
                future = executor.submit(create_cdc_worker, custom_api, namespace, cr_name, template_body, api_info)
                active_cdc_queue.append(cr_name) # Add name to queue *before* checking result
                create_submitted_count += 1

            operation_counter += 1
            next_op_target_time += inter_request_delay
            # --- End Alternate Operation ---

    actual_step_end_time = time.time()
    logging.info(f"    Finished {phase_name} Phase in {actual_step_end_time - step_start_time:.2f}s.")
    logging.info(f"    Submitted: Creates={create_submitted_count}, Deletes={delete_submitted_count}, Total Ops={operation_counter}")
    logging.info(f"    Ending pool size: {len(active_cdc_queue)}")

    return create_submitted_count, delete_submitted_count


def main():
    """
    Main function: Parses args, pre-fills pool, runs load steps (alternate strategy), saves results.
    """
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Kubernetes CassandraDatacenter Load Generator (Prefill & Alternate Create/Delete)")
    # Load Gen Args
    parser.add_argument("-n", "--namespace", default=DEFAULT_NAMESPACE, help="Namespace for resources")
    parser.add_argument("-b", "--base-name", default=DEFAULT_BASE_NAME, help="Base name prefix for created resources")
    parser.add_argument("-r", "--rates", nargs='+', type=float, default=DEFAULT_RATES_GEOM, help=f"List of target total operation rates (creates+deletes)/s. Default: {DEFAULT_RATES_GEOM}")
    parser.add_argument("--measurement-duration", type=int, default=DEFAULT_MEASUREMENT_DURATION_S, help=f"Measurement duration per step (s). Default: {DEFAULT_MEASUREMENT_DURATION_S}")
    parser.add_argument("--warmup-duration", type=int, default=DEFAULT_WARMUP_DURATION_S, help=f"Warm-up duration per step (s). Default: {DEFAULT_WARMUP_DURATION_S}")
    parser.add_argument("-c", "--cooldown", type=int, default=DEFAULT_COOLDOWN_S, help=f"Cooldown period between steps (s). Default: {DEFAULT_COOLDOWN_S}")
    parser.add_argument("-y", "--yaml-path", default=DEFAULT_YAML_PATH, help=f"Path to the CDC YAML template. Default: {DEFAULT_YAML_PATH}")
    parser.add_argument("--pool-size", type=int, default=DEFAULT_MAX_CONCURRENT_CDCS, help=f"Target number of simultaneously existing CDCs (pool size). Default: {DEFAULT_MAX_CONCURRENT_CDCS}")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help=f"Number of worker threads for K8s API calls. Default: {DEFAULT_WORKERS}")
    parser.add_argument("-o", "--output-json", default=DEFAULT_OUTPUT_JSON, help=f"Path to save the results JSON file. Default: {DEFAULT_OUTPUT_JSON}")
    # Removed Plotting Args

    args = parser.parse_args()

    # --- Input Validation ---
    if args.measurement_duration <= 0 or args.warmup_duration < 0 or args.cooldown < 0 or args.workers <= 0 or args.pool_size <= 0:
        logging.error("Durations, workers, and pool-size must be positive/non-negative.")
        sys.exit(1)

    # --- Initialization ---
    template_body = load_yaml_template(args.yaml_path)
    if not template_body: sys.exit(1)

    # Use the simpler client creation function
    v1_api, custom_api = create_k8s_api_client()
    if not custom_api: sys.exit(1) # Check if client creation failed

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
    logging.info(f"Target Operation Rates (ops/s): {target_rates}") # Updated log message
    logging.info(f"Target Pool Size (Max Concurrent CDCs): {args.pool_size}")
    logging.info(f"Measurement duration: {args.measurement_duration}s | Warm-up duration: {args.warmup_duration}s | Cooldown: {args.cooldown}s")
    logging.info(f"Workers: {args.workers} | Template: {args.yaml_path} | Namespace: {args.namespace}")
    logging.info(f"Output JSON: {args.output_json}")

    all_results_data = {}
    active_cdc_queue = deque() # Initialize empty deque

    try:
        # --- Pre-fill Resource Pool ---
        active_cdc_queue = prefill_pool(custom_api, args.pool_size, args.namespace, args.base_name, template_body, api_info, args.workers)

        logging.info("Pausing briefly after pool pre-fill...")
        time.sleep(10)

        # --- Main Load Generation Loop ---
        for i, measurement_rate in enumerate(target_rates):
            logging.info(f"\n===== Starting Experiment Step {i+1}/{len(target_rates)} for Rate: {measurement_rate:.2f} ops/s =====")

            # --- Warm-up Phase ---
            warmup_creates, warmup_deletes = run_load_phase(
                custom_api, measurement_rate, args.warmup_duration, args.namespace,
                args.base_name, template_body, api_info, args.workers, i,
                active_cdc_queue, "Warmup" # Pass the deque
            )

            # --- Measurement Phase ---
            measurement_t_start = time.time()
            logging.info(f"  Measurement Window T_START (Epoch): {measurement_t_start:.0f}")
            measurement_creates, measurement_deletes = run_load_phase(
                custom_api, measurement_rate, args.measurement_duration, args.namespace,
                args.base_name, template_body, api_info, args.workers, i,
                active_cdc_queue, "Measurement" # Pass the deque
            )
            measurement_t_end = measurement_t_start + args.measurement_duration
            logging.info(f"  Measurement Window T_END (Epoch): {measurement_t_end:.0f}")

            # Store results with separate counts
            all_results_data[str(measurement_rate)] = {
                "T_START": measurement_t_start, "T_END": measurement_t_end,
                "warmup_creates_submitted": warmup_creates,
                "warmup_deletes_submitted": warmup_deletes,
                "measurement_creates_submitted": measurement_creates,
                "measurement_deletes_submitted": measurement_deletes,
                "target_pool_size": args.pool_size
            }
            expected_ops = measurement_rate * args.measurement_duration
            total_measure_ops = measurement_creates + measurement_deletes
            logging.info(f"  Target measurement operations: {expected_ops:.0f}, Actual submitted: {total_measure_ops} (Creates: {measurement_creates}, Deletes: {measurement_deletes})")

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
            print("\nMeasurement Windows & Operation Counts:")
            hdr_fmt = f"{'Rate (ops/s)':<15} | {'T_START':<18} | {'T_END':<18} | {'Warmup C/D':<12} | {'Measure C/D':<12} | {'Pool Size':<10}"
            sep_len = len(hdr_fmt)
            print("-" * sep_len + f"\n{hdr_fmt}\n" + "-" * sep_len)
            for rate_str in sorted(all_results_data.keys(), key=float):
                r = all_results_data[rate_str]
                warmup_cd = f"{r['warmup_creates_submitted']}/{r['warmup_deletes_submitted']}"
                measure_cd = f"{r['measurement_creates_submitted']}/{r['measurement_deletes_submitted']}"
                print(f"{float(rate_str):<15.2f} | {r['T_START']:<18.0f} | {r['T_END']:<18.0f} | {warmup_cd:<12} | {measure_cd:<12} | {r['target_pool_size']:<10}")
            print("-" * sep_len)
        print("="*30)

if __name__ == "__main__":
    main()
