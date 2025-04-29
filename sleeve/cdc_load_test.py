import argparse
import datetime
import logging
import os
import random
import string
import sys
import threading
import time
# Removed queue import: from queue import Queue, Empty

import yaml
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# --- Configuration ---
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(threadName)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
LOAD_TEST_LABEL_KEY = "load-test" # Label key used to identify resources created by this script
LOAD_TEST_LABEL_VALUE = "true"

# --- Global Stop Signal ---
stop_event = threading.Event()

def generate_random_suffix(length=6):
    """Generates a random alphanumeric suffix."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def load_cdc_template(template_path):
    """Loads the CassandraDatacenter YAML template."""
    try:
        with open(template_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load template file {template_path}: {e}")
        sys.exit(1)

# Removed created_names_queue argument
def worker_lifecycle(worker_id, args, cdc_template, custom_objects_api):
    """
    Represents the lifecycle of operations performed by a single worker thread.
    Creates a CDC, waits, then deletes it. Repeats until stop_event is set.
    """
    thread_name = threading.current_thread().name
    logging.info("Worker started")
    sequence = 0

    while not stop_event.is_set():
        resource_suffix = f"w{worker_id}-s{sequence}-{generate_random_suffix()}"
        cdc_name = f"loadtest-cdc-{resource_suffix}"
        cdc_body = cdc_template.copy() # Start with a fresh copy
        # Ensure metadata exists
        if 'metadata' not in cdc_body:
            cdc_body['metadata'] = {}
        cdc_body['metadata']['name'] = cdc_name
        cdc_body['metadata']['namespace'] = args.namespace
        # Ensure labels exist and add the load test label
        if 'labels' not in cdc_body['metadata']:
             cdc_body['metadata']['labels'] = {}
        # Add/overwrite the specific label for cleanup
        cdc_body['metadata']['labels'][LOAD_TEST_LABEL_KEY] = LOAD_TEST_LABEL_VALUE
        # Optional: Keep worker/sequence labels for debugging if needed
        # cdc_body['metadata']['labels']['load-test-worker'] = str(worker_id)
        # cdc_body['metadata']['labels']['load-test-sequence'] = str(sequence)


        created_successfully = False
        try:
            logging.info(f"Attempting to CREATE CassandraDatacenter: {cdc_name}")
            custom_objects_api.create_namespaced_custom_object(
                group=args.crd_group,
                version=args.crd_version,
                namespace=args.namespace,
                plural=args.crd_plural,
                body=cdc_body,
            )
            created_successfully = True
            # Removed queue.put
            logging.info(f"Successfully CREATED CassandraDatacenter: {cdc_name}")

            # --- Wait Phase ---
            # Wait for a short, slightly random duration before deleting
            wait_time = args.wait_min + random.random() * (args.wait_max - args.wait_min)
            logging.debug(f"Waiting for {wait_time:.2f}s before deleting {cdc_name}")
            time.sleep(wait_time) # Simulate resource being active

        except ApiException as e:
            logging.error(f"API Error creating {cdc_name}: {e.status} - {e.reason} - {e.body}")
            created_successfully = False
        except Exception as e:
            logging.error(f"Non-API Error creating {cdc_name}: {e}")
            created_successfully = False
        finally:
            # --- Delete Phase ---
            # Delete is still attempted by the worker for immediate cleanup,
            # but the final cleanup function provides the safety net.
            if created_successfully and not stop_event.is_set(): # Only delete if created and not stopping
                try:
                    logging.info(f"Attempting to DELETE CassandraDatacenter: {cdc_name}")
                    custom_objects_api.delete_namespaced_custom_object(
                        group=args.crd_group,
                        version=args.crd_version,
                        namespace=args.namespace,
                        plural=args.crd_plural,
                        name=cdc_name,
                        body=client.V1DeleteOptions(propagation_policy='Background'), # Or 'Foreground' if needed
                    )
                    logging.info(f"Successfully initiated DELETE for CassandraDatacenter: {cdc_name}")
                except ApiException as e:
                    if e.status == 404:
                         logging.warning(f"CassandraDatacenter {cdc_name} already deleted.")
                    else:
                         logging.error(f"API Error deleting {cdc_name}: {e.status} - {e.reason} - {e.body}")
                except Exception as e:
                    logging.error(f"Non-API Error deleting {cdc_name}: {e}")
            elif created_successfully and stop_event.is_set():
                 logging.warning(f"Stop signal received, skipping delete for {cdc_name}. It will be cleaned up by final LIST.")


        sequence += 1
        # Optional: Add a small delay between cycles for this worker
        if not stop_event.is_set():
             time.sleep(args.cycle_delay)

    logging.info("Worker finished")

# Removed created_names_queue argument
def cleanup_resources(custom_objects_api, args):
    """Lists and deletes resources matching the load test label."""
    logging.info(f"Starting final cleanup by LISTING resources with label '{LOAD_TEST_LABEL_KEY}={LOAD_TEST_LABEL_VALUE}'...")
    deleted_count = 0
    label_selector = f"{LOAD_TEST_LABEL_KEY}={LOAD_TEST_LABEL_VALUE}"

    try:
        # List all CDCs in the namespace with the specific label
        res = custom_objects_api.list_namespaced_custom_object(
            group=args.crd_group,
            version=args.crd_version,
            namespace=args.namespace,
            plural=args.crd_plural,
            label_selector=label_selector,
        )

        items = res.get('items', [])
        logging.info(f"Found {len(items)} resource(s) matching label selector for cleanup.")

        for item in items:
            cdc_name = item.get('metadata', {}).get('name')
            if not cdc_name:
                logging.warning("Found item in list without a name, skipping.")
                continue

            try:
                logging.info(f"Cleanup: Attempting to DELETE CassandraDatacenter: {cdc_name}")
                custom_objects_api.delete_namespaced_custom_object(
                    group=args.crd_group,
                    version=args.crd_version,
                    namespace=args.namespace,
                    plural=args.crd_plural,
                    name=cdc_name,
                    body=client.V1DeleteOptions(propagation_policy='Background'),
                )
                deleted_count += 1
                logging.info(f"Cleanup: Successfully initiated DELETE for CassandraDatacenter: {cdc_name}")
                # Add a small delay between deletes if the API server gets overloaded
                time.sleep(0.1)
            except ApiException as e:
                if e.status == 404:
                    logging.warning(f"Cleanup: CassandraDatacenter {cdc_name} already deleted (concurrently?).")
                else:
                    logging.error(f"Cleanup: API Error deleting {cdc_name}: {e.status} - {e.reason}")
            except Exception as e:
                logging.error(f"Cleanup: Non-API Error deleting {cdc_name}: {e}")

    except ApiException as e:
        logging.error(f"Cleanup: API Error LISTING resources: {e.status} - {e.reason}")
    except Exception as e:
        logging.error(f"Cleanup: Non-API Error LISTING resources: {e}")

    logging.info(f"Final cleanup finished. Initiated delete for {deleted_count} resources found via LIST.")


def main():
    parser = argparse.ArgumentParser(description="Generate load on CassandraDatacenter operator.")
    parser.add_argument("-d", "--duration", type=int, required=True, help="Duration of the workload in seconds.")
    parser.add_argument("-w", "--workers", type=int, default=5, help="Number of concurrent workers.")
    parser.add_argument("-n", "--namespace", default="default", help="Namespace to create resources in.")
    parser.add_argument("-t", "--template", required=True, help="Path to the CassandraDatacenter YAML template file.")
    parser.add_argument("--crd-group", required=True, help="API group of the CassandraDatacenter CRD (e.g., k8ssandra.io).")
    parser.add_argument("--crd-version", required=True, help="API version of the CassandraDatacenter CRD (e.g., v1alpha1).")
    parser.add_argument("--crd-plural", required=True, help="Plural name of the CassandraDatacenter CRD (e.g., cassandradatacenters).")
    parser.add_argument("--wait-min", type=float, default=10.0, help="Minimum time (seconds) a resource exists before deletion.")
    parser.add_argument("--wait-max", type=float, default=30.0, help="Maximum time (seconds) a resource exists before deletion.")
    parser.add_argument("--cycle-delay", type=float, default=1.0, help="Delay (seconds) between create/delete cycles for a single worker.")
    parser.add_argument("--kubeconfig", help="Path to kubeconfig file (optional, uses default if not specified).")

    args = parser.parse_args()

    if args.wait_min >= args.wait_max:
        logging.error("wait-min must be less than wait-max.")
        sys.exit(1)

    # --- Load Kubeconfig ---
    try:
        if args.kubeconfig:
            logging.info(f"Loading kubeconfig from: {args.kubeconfig}")
            config.load_kube_config(config_file=args.kubeconfig)
        else:
            logging.info("Loading default kubeconfig")
            config.load_kube_config()
    except Exception as e:
        logging.error(f"Failed to load kubeconfig: {e}")
        sys.exit(1)

    # --- Create API Client ---
    api_client = client.ApiClient()
    custom_objects_api = client.CustomObjectsApi(api_client)

    # --- Load Template ---
    cdc_template = load_cdc_template(args.template)
    # Basic validation of template structure
    if not isinstance(cdc_template, dict) or 'apiVersion' not in cdc_template or 'kind' not in cdc_template or 'metadata' not in cdc_template or 'spec' not in cdc_template:
         logging.error("Invalid template structure. Must be a dictionary with apiVersion, kind, metadata, and spec.")
         sys.exit(1)
    logging.info(f"Loaded template for Kind: {cdc_template.get('kind', 'N/A')}, APIVersion: {cdc_template.get('apiVersion', 'N/A')}")


    # --- Start Workload ---
    threads = []
    # Removed created_names_queue

    logging.info(f"Starting workload generation: {args.workers} workers for {args.duration} seconds.")
    t_start_iso = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    logging.info(f"T_START: {t_start_iso}")

    start_time = time.monotonic()

    for i in range(args.workers):
        thread = threading.Thread(
            target=worker_lifecycle,
            # Removed created_names_queue from args
            args=(i, args, cdc_template, custom_objects_api),
            name=f"Worker-{i}",
            daemon=True # Allow main thread to exit even if workers are stuck (though we try to join)
        )
        threads.append(thread)
        thread.start()

    # --- Wait for Duration ---
    while True:
        elapsed = time.monotonic() - start_time
        if elapsed >= args.duration:
            logging.info(f"Duration ({args.duration}s) reached. Signaling workers to stop.")
            stop_event.set()
            break
        # Check if all workers died unexpectedly
        if not any(t.is_alive() for t in threads):
             logging.warning("All worker threads seem to have terminated early.")
             stop_event.set() # Ensure stop is signaled
             break
        time.sleep(0.5) # Check duration periodically

    # --- Stop Workload ---
    t_end_iso = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    logging.info(f"T_END: {t_end_iso}")

    logging.info("Waiting for worker threads to finish current cycle...")
    # Give workers a chance to finish their current operation and notice the stop signal
    # Adjust timeout as needed, depends on typical operation duration + wait time
    join_timeout = args.wait_max + 10 # Generous timeout
    for thread in threads:
        thread.join(timeout=join_timeout)
        if thread.is_alive():
            logging.warning(f"Thread {thread.name} did not finish within timeout.")

    logging.info("All worker threads signaled.")

    # --- Final Cleanup ---
    # Call cleanup without the queue
    cleanup_resources(custom_objects_api, args)

    logging.info("Workload generation script finished.")
    print(f"T_START={t_start_iso}")
    print(f"T_END={t_end_iso}")


if __name__ == "__main__":
    main()
