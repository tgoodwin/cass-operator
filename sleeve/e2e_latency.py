import asyncio
import csv # For CSV output
import datetime
import logging
import sys
import uuid
from copy import deepcopy
import json # For JSON summary output
import yaml
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
import argparse
import time # For polling sleep

# --- Logging Setup ---
# Set to INFO for cleaner output, DEBUG for verbose troubleshooting
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)

# --- Global Dictionaries for Watcher Communication ---
pending_creations = {}
pending_updates = {} # Added for watcher-based update
pending_deletions = {}
WATCHER_REGISTRY_LOCK = asyncio.Lock()

# --- Kubernetes API Client Setup ---
def load_k8s_clients():
    """Initializes and returns Kubernetes API clients."""
    try:
        config.load_kube_config()
        logging.info("Loaded Kubernetes configuration from kubeconfig.")
    except config.ConfigException:
        try:
            config.load_incluster_config()
            logging.info("Loaded Kubernetes configuration from in-cluster service account.")
        except config.ConfigException:
            logging.error("Could not load any Kubernetes configuration. Exiting.")
            sys.exit(1)
    v1_api = client.CoreV1Api()
    custom_api = client.CustomObjectsApi()
    return v1_api, custom_api

def load_yaml_template(path: str) -> dict:
    """Loads the base CassandraDatacenter YAML template."""
    try:
        with open(path, "r") as stream:
            template = yaml.safe_load(stream)
            if not isinstance(template, dict):
                logging.error(f"YAML template file {path} does not parse into a dictionary.")
                sys.exit(1)
            if 'spec' not in template or 'size' not in template['spec']:
                 logging.warning(f"Template {path} missing 'spec.size'. Defaulting size to 1 for initial creation.")
                 if 'spec' not in template: template['spec'] = {}
                 template['spec']['size'] = 1
            return template
    except FileNotFoundError:
        logging.error(f"YAML template file not found: {path}")
        sys.exit(1)
    except yaml.YAMLError as exc:
        logging.error(f"Error parsing YAML file {path}: {exc}")
        sys.exit(1)
    return None

async def _process_pod_event(event_type: str, pod_object: client.V1Pod, cdc_pod_label_key: str):
    """Processes a single pod event from the watcher in the main asyncio loop."""
    pod_name = pod_object.metadata.name
    pod_labels = pod_object.metadata.labels or {}
    logging.debug(f"Watcher (event processor): Processing event: {event_type} for pod {pod_name}.")

    async with WATCHER_REGISTRY_LOCK:
        if event_type == "ADDED":
            cdc_name_from_label = pod_labels.get(cdc_pod_label_key)
            logging.debug(f"Watcher (event processor): For ADDED pod {pod_name}, looking for label key '{cdc_pod_label_key}'. Found value: '{cdc_name_from_label}'.")

            # --- Check for Creation Phase ---
            logging.debug(f"Watcher (event processor): Current pending_creations keys: {list(pending_creations.keys())}")
            if cdc_name_from_label and cdc_name_from_label in pending_creations:
                creation_info = pending_creations[cdc_name_from_label]
                if not creation_info["event"].is_set():
                    # Store pod name for result reporting, but don't use its timestamp directly
                    creation_info["pod_name_ref"].clear()
                    creation_info["pod_name_ref"].append(pod_name)
                    creation_info["event"].set() # Signal completion
                    logging.info(f"Watcher (event processor): Notified ADDED for pod {pod_name} (CREATE for CDC {cdc_name_from_label}) - Event Set.")
                else:
                    logging.debug(f"Watcher (event processor): Event for CREATE CDC {cdc_name_from_label} already set, ignoring duplicate ADDED for pod {pod_name}.")

            # --- Check for Update Phase ---
            logging.debug(f"Watcher (event processor): Current pending_updates keys: {list(pending_updates.keys())}")
            if cdc_name_from_label and cdc_name_from_label in pending_updates:
                update_info = pending_updates[cdc_name_from_label]
                # Check if it's a genuinely new pod for this update phase
                if pod_name not in update_info['initial_pods'] and pod_name not in update_info['new_pods_seen']:
                    update_info['new_pods_seen'].add(pod_name)
                    logging.debug(f"Watcher (event processor): New pod {pod_name} seen for UPDATE CDC {cdc_name_from_label}. Seen: {len(update_info['new_pods_seen'])}/{update_info['pods_needed']}.")
                    # Check if we've seen enough new pods
                    if len(update_info['new_pods_seen']) >= update_info['pods_needed']:
                        if not update_info["event"].is_set():
                            update_info["event"].set() # Signal completion
                            logging.info(f"Watcher (event processor): Reached target pod count for UPDATE CDC {cdc_name_from_label} - Event Set.")
                        else:
                             logging.debug(f"Watcher (event processor): Event for UPDATE CDC {cdc_name_from_label} already set, ignoring further ADDED pod {pod_name}.")
                else:
                     logging.debug(f"Watcher (event processor): Pod {pod_name} is either initial or already seen for UPDATE CDC {cdc_name_from_label}.")


        elif event_type == "DELETED":
            # Check across all pending deletions if this pod was being tracked
            for cdc_name_key, deletion_info in list(pending_deletions.items()):
                if pod_name in deletion_info["pods_to_delete"]:
                    pod_event = deletion_info["deleted_pods_events"].get(pod_name)
                    if pod_event and not pod_event.is_set():
                        pod_event.set()
                        logging.debug(f"Watcher (event processor): Notified DELETED for pod {pod_name} (CDC {cdc_name_key})")

                    # Check if all pods for this specific CDC deletion task are now deleted
                    if all(e.is_set() for e in deletion_info["deleted_pods_events"].values()):
                        if not deletion_info["all_deleted_event"].is_set():
                            deletion_info["all_deleted_event"].set()
                            logging.info(f"Watcher (event processor): All tracked pods for CDC {cdc_name_key} are deleted.")

def _schedule_coro_on_loop(loop: asyncio.AbstractEventLoop, coro):
    """Helper function to schedule a coroutine as a task on the given loop."""
    if loop and coro:
        loop.create_task(coro)
    elif not loop:
        logging.error("_schedule_coro_on_loop: loop is None")
    elif not coro:
        logging.error("_schedule_coro_on_loop: coro is None")


def _blocking_watch_loop(
    v1_api: client.CoreV1Api,
    namespace: str,
    cdc_pod_label_key: str,
    stop_event: asyncio.Event,
    async_loop: asyncio.AbstractEventLoop
):
    """This function runs in a separate thread and performs the blocking watch."""
    w = watch.Watch()
    current_resource_version = ""
    logging.info(f"Blocking Watch Loop Thread: Started for namespace '{namespace}'.")

    while not stop_event.is_set():
        try:
            logging.debug(f"Blocking Watch Loop Thread: Starting new watch stream from rv='{current_resource_version or 'HEAD'}'...")
            stream_generator = w.stream(
                v1_api.list_namespaced_pod,
                namespace=namespace,
                resource_version=current_resource_version if current_resource_version else None,
                timeout_seconds=15
            )
            logging.debug("Blocking Watch Loop Thread: w.stream() called, iterating events...")
            for event_data in stream_generator:
                if stop_event.is_set():
                    logging.debug("Blocking Watch Loop Thread: Stop event set during event iteration.")
                    break

                event_type = event_data["type"]
                # Handle cases where object might be missing (e.g., on ERROR events)
                pod_object = event_data.get("object")
                if not pod_object:
                     logging.warning(f"Blocking Watch Loop Thread: Received event type {event_type} without an object: {event_data}")
                     continue

                # Ensure pod_object is the correct type if needed, though client usually handles this
                if not isinstance(pod_object, client.V1Pod):
                     try:
                         # Attempt conversion if it looks like a dict
                         if isinstance(pod_object, dict):
                              pod_object = client.V1Pod(**pod_object)
                         else:
                              raise TypeError("Object is not a dict")
                     except Exception as conv_err:
                          logging.error(f"Blocking Watch Loop Thread: Could not process event object - not a V1Pod or dict: {type(pod_object)}. Error: {conv_err}")
                          continue # Skip this event

                logging.debug(f"Blocking Watch Loop Thread: Received event: {event_type} for pod {pod_object.metadata.name} (rv: {pod_object.metadata.resource_version})")

                coro_to_schedule = _process_pod_event(event_type, pod_object, cdc_pod_label_key)
                async_loop.call_soon_threadsafe(_schedule_coro_on_loop, async_loop, coro_to_schedule)

                current_resource_version = pod_object.metadata.resource_version

            if stop_event.is_set():
                 logging.debug("Blocking Watch Loop Thread: Stream iteration stopped by stop_event.")
                 break
            logging.debug("Blocking Watch Loop Thread: Stream ended gracefully (or timed out). Will restart if not stopped.")

        except ApiException as e:
            if e.status == 410:
                logging.warning("Blocking Watch Loop Thread: Watch 'Gone' (410), resetting resource_version to re-list.")
                current_resource_version = ""
            else:
                logging.error(f"Blocking Watch Loop Thread: ApiException: {type(e).__name__} - {e}. Retrying in 1s.")
                if stop_event.wait(timeout=1): break
        except Exception as e:
            logging.error(f"Blocking Watch Loop Thread: Unexpected error: {type(e).__name__} - {e}. Retrying in 1s.")
            logging.debug("Blocking Watch Loop Thread error details:", exc_info=True)
            if stop_event.wait(timeout=1): break

        if stop_event.is_set():
            logging.debug("Blocking Watch Loop Thread: Stop event checked at end of while loop, exiting.")
            break
    w.stop()
    logging.info("Blocking Watch Loop Thread: Stopped.")


async def pod_event_watcher(
    v1_api: client.CoreV1Api,
    namespace: str,
    cdc_pod_label_key: str,
    stop_event: asyncio.Event,
):
    """Manages the blocking watch loop in a separate thread."""
    logging.info(f"Async Pod Event Watcher Task: Starting for namespace '{namespace}'.")
    async_loop = asyncio.get_running_loop()

    try:
        await asyncio.to_thread(
            _blocking_watch_loop,
            v1_api,
            namespace,
            cdc_pod_label_key,
            stop_event,
            async_loop
        )
    except Exception as e:
        logging.error(f"Async Pod Event Watcher Task: Error running/managing blocking watch loop: {e}", exc_info=True)

    logging.info(f"Async Pod Event Watcher Task: Exiting for namespace '{namespace}'.")


async def measure_one_cdc_creation(
    custom_api: client.CustomObjectsApi,
    namespace: str,
    cdc_name: str,
    cdc_template: dict,
    api_info: dict,
    test_run_id: str,
    cdc_pod_label_key: str,
    timeout: int,
):
    """Measures E2E creation latency for a single CDC."""
    logging.debug(f"Task started for CDC creation: {cdc_name}")
    result = {
        "run_id": test_run_id,
        "cdc_name": cdc_name,
        "operation_type": "CREATE",
        "api_request_utc": None,
        "resource_event_utc": None, # Time event observed by script
        "e2e_latency_seconds": None,
        "primary_pod_name": None,
        "initial_pod_count": None,
        "final_pod_count": None,
        "target_pod_count": None,
        "status": "PENDING",
        "error_details": "",
    }

    manifest = deepcopy(cdc_template)
    manifest['spec']['size'] = 1
    manifest["metadata"]["name"] = cdc_name
    manifest["metadata"]["namespace"] = namespace
    if "labels" not in manifest["metadata"]:
        manifest["metadata"]["labels"] = {}
    manifest["metadata"]["labels"]["e2e-latency-test-run-id"] = test_run_id

    creation_event = asyncio.Event()
    pod_name_ref = [] # Use list to pass mutable reference

    logging.debug(f"CDC {cdc_name}: Attempting to acquire WATCHER_REGISTRY_LOCK for pending_creations.")
    async with WATCHER_REGISTRY_LOCK:
        # Store pod_name_ref list instead of pod_info_ref
        pending_creations[cdc_name] = {"event": creation_event, "pod_name_ref": pod_name_ref}
        logging.debug(f"CDC {cdc_name}: Acquired lock, registered in pending_creations.")

    api_req_dt = None
    res_event_dt = None # This will be datetime.now()

    try:
        logging.info(f"Creating CDC CR object: {cdc_name} (size=1)")
        api_req_dt = datetime.datetime.now(datetime.timezone.utc)
        result["api_request_utc"] = api_req_dt
        await asyncio.to_thread(
            custom_api.create_namespaced_custom_object,
            group=api_info["group"],
            version=api_info["version"],
            namespace=namespace,
            plural=api_info["plural"],
            body=manifest,
        )
        logging.info(f"CDC {cdc_name} CR creation request sent. Waiting for pod (label key: {cdc_pod_label_key}, expected value: {cdc_name})...")

        await asyncio.wait_for(creation_event.wait(), timeout=timeout)

        # --- MODIFIED: Capture current time when event is received ---
        res_event_dt = datetime.datetime.now(datetime.timezone.utc)
        result["resource_event_utc"] = res_event_dt
        # -----------------------------------------------------------

        if pod_name_ref: # Check if watcher stored the pod name
            pod_name = pod_name_ref[0]
            result["primary_pod_name"] = pod_name
            latency = result["resource_event_utc"] - result["api_request_utc"]
            result["e2e_latency_seconds"] = latency.total_seconds()
            result["status"] = "SUCCESS"
            result["final_pod_count"] = 1 # Assume 1 pod signifies creation success
            logging.info(f"CDC {cdc_name}: Pod {pod_name} ADDED event processed. Latency: {result['e2e_latency_seconds']:.2f}s")
        else:
            result["status"] = "ERROR"
            result["error_details"] = "Watcher event set for CDC creation, but no pod name was captured."
            logging.error(f"CDC {cdc_name}: {result['error_details']}")

    except ApiException as e:
        result["status"] = "ERROR"
        result["error_details"] = f"API Error creating CDC CR: {e.reason} (Status: {e.status})"
        logging.error(f"CDC {cdc_name}: {result['error_details']}")
    except asyncio.TimeoutError:
        result["status"] = "TIMEOUT"
        result["error_details"] = f"Timeout waiting for pod creation event for CDC {cdc_name} after {timeout}s."
        logging.warning(result["error_details"])
    except Exception as e:
        result["status"] = "ERROR"
        result["error_details"] = f"Unexpected error during CDC {cdc_name} creation: {str(e)}"
        logging.exception(f"CDC {cdc_name}: Unexpected error.")
    finally:
        logging.debug(f"CDC {cdc_name}: Attempting to acquire WATCHER_REGISTRY_LOCK for cleanup in pending_creations.")
        async with WATCHER_REGISTRY_LOCK:
            if cdc_name in pending_creations:
                del pending_creations[cdc_name]
                logging.debug(f"CDC {cdc_name}: Cleaned up from pending_creations.")

        result["api_request_utc"] = api_req_dt.isoformat() if isinstance(api_req_dt, datetime.datetime) else None
        result["resource_event_utc"] = res_event_dt.isoformat() if isinstance(res_event_dt, datetime.datetime) else None
        result["_api_request_dt"] = api_req_dt
        result["_resource_event_dt"] = res_event_dt
    return result


# --- MODIFIED: Update Phase uses Watcher ---
async def measure_one_cdc_update(
    v1_api: client.CoreV1Api, # Still needed for initial list
    custom_api: client.CustomObjectsApi,
    namespace: str,
    cdc_name: str,
    api_info: dict,
    test_run_id: str,
    cdc_pod_label_key: str,
    target_pod_count: int,
    timeout: int,
    # poll_interval: float = 5.0 # No longer needed
):
    """Measures E2E update latency for a single CDC using watcher."""
    logging.debug(f"Task started for CDC update: {cdc_name} to size {target_pod_count}")
    result = {
        "run_id": test_run_id,
        "cdc_name": cdc_name,
        "operation_type": "UPDATE",
        "api_request_utc": None,
        "resource_event_utc": None, # Time Nth new pod ADDED event observed by script
        "e2e_latency_seconds": None,
        "primary_pod_name": None, # Less relevant, maybe store list of new pods?
        "initial_pod_count": None,
        "final_pod_count": None, # Pod count when Nth new pod seen
        "target_pod_count": target_pod_count,
        "status": "PENDING",
        "error_details": "",
    }

    patch_body = {"spec": {"size": target_pod_count}}
    label_selector = f"{cdc_pod_label_key}={cdc_name}"
    api_req_dt = None
    res_event_dt = None # This will be datetime.now() when event is set

    try:
        # 1. Get initial pods
        initial_pod_names = set()
        try:
            initial_pod_list = await asyncio.to_thread(
                v1_api.list_namespaced_pod,
                namespace=namespace,
                label_selector=label_selector,
            )
            for pod in initial_pod_list.items:
                 initial_pod_names.add(pod.metadata.name)
            result["initial_pod_count"] = len(initial_pod_names)
            logging.info(f"CDC {cdc_name}: Initial pod count before update: {result['initial_pod_count']}. Pods: {initial_pod_names or 'None'}")
        except ApiException as e:
             logging.warning(f"CDC {cdc_name}: API Error listing initial pods before update: {e.reason}. Proceeding.")
             result["initial_pod_count"] = -1 # Indicate error

        # 2. Calculate pods needed and check if already met/exceeded
        pods_needed = target_pod_count - result["initial_pod_count"]
        if pods_needed <= 0:
             logging.warning(f"CDC {cdc_name}: Target pod count {target_pod_count} already met or exceeded by initial count {result['initial_pod_count']}. Skipping update measurement, attempting patch anyway.")
             result["status"] = "SKIPPED_ALREADY_MET"
             result["final_pod_count"] = result["initial_pod_count"]
             # Still attempt patch for consistency? Or just return? Let's patch.
             api_req_dt = datetime.datetime.now(datetime.timezone.utc)
             result["api_request_utc"] = api_req_dt
             await asyncio.to_thread(
                 custom_api.patch_namespaced_custom_object,
                 group=api_info["group"], version=api_info["version"], namespace=namespace,
                 plural=api_info["plural"], name=cdc_name, body=patch_body,
             )
             result["api_request_utc"] = api_req_dt.isoformat() if api_req_dt else None
             return result # Exit early

        # 3. Register with watcher
        update_event = asyncio.Event()
        new_pods_seen_set = set()
        logging.debug(f"CDC {cdc_name}: Attempting to acquire WATCHER_REGISTRY_LOCK for pending_updates.")
        async with WATCHER_REGISTRY_LOCK:
            pending_updates[cdc_name] = {
                "event": update_event,
                "initial_pods": initial_pod_names,
                "pods_needed": pods_needed,
                "new_pods_seen": new_pods_seen_set # Store the set here
            }
            logging.debug(f"CDC {cdc_name}: Acquired lock, registered in pending_updates. Need {pods_needed} new pods.")

        # 4. Send the patch request
        logging.info(f"Updating CDC CR object: {cdc_name} to size {target_pod_count}")
        api_req_dt = datetime.datetime.now(datetime.timezone.utc)
        result["api_request_utc"] = api_req_dt
        await asyncio.to_thread(
            custom_api.patch_namespaced_custom_object,
            group=api_info["group"],
            version=api_info["version"],
            namespace=namespace,
            plural=api_info["plural"],
            name=cdc_name,
            body=patch_body,
        )
        logging.info(f"CDC {cdc_name} CR update request sent. Waiting for {pods_needed} new pod(s) to appear...")

        # 5. Wait for the watcher to signal completion
        await asyncio.wait_for(update_event.wait(), timeout=timeout)

        # --- MODIFIED: Capture current time when event is received ---
        res_event_dt = datetime.datetime.now(datetime.timezone.utc)
        result["resource_event_utc"] = res_event_dt
        # -----------------------------------------------------------

        # Record final state
        result["final_pod_count"] = result["initial_pod_count"] + len(new_pods_seen_set)
        result["status"] = "SUCCESS"
        latency = result["resource_event_utc"] - result["api_request_utc"]
        result["e2e_latency_seconds"] = latency.total_seconds()
        logging.info(f"CDC {cdc_name}: Update target reached ({len(new_pods_seen_set)} new pods observed). Latency: {result['e2e_latency_seconds']:.2f}s")
        # Could store list(new_pods_seen_set) in primary_pod_name if needed

    except ApiException as e:
        result["status"] = "ERROR"
        result["error_details"] = f"API Error during update process: {e.reason} (Status: {e.status})"
        logging.error(f"CDC {cdc_name}: {result['error_details']}")
    except asyncio.TimeoutError:
        result["status"] = "TIMEOUT"
        result["error_details"] = f"Timeout waiting for {pods_needed} new pods for CDC {cdc_name} after {timeout}s."
        logging.warning(result["error_details"])
        # Record final count on timeout
        try:
            final_check_list = await asyncio.to_thread(
                v1_api.list_namespaced_pod, namespace=namespace, label_selector=label_selector)
            result["final_pod_count"] = len(final_check_list.items)
        except Exception:
            result["final_pod_count"] = -1 # Error getting count
    except Exception as e:
        result["status"] = "ERROR"
        result["error_details"] = f"Unexpected error during CDC {cdc_name} update: {str(e)}"
        logging.exception(f"CDC {cdc_name}: Unexpected error.")
    finally:
        logging.debug(f"CDC {cdc_name}: Attempting to acquire WATCHER_REGISTRY_LOCK for cleanup in pending_updates.")
        async with WATCHER_REGISTRY_LOCK:
            if cdc_name in pending_updates:
                del pending_updates[cdc_name]
                logging.debug(f"CDC {cdc_name}: Cleaned up from pending_updates.")

        result["api_request_utc"] = api_req_dt.isoformat() if isinstance(api_req_dt, datetime.datetime) else None
        result["resource_event_utc"] = res_event_dt.isoformat() if isinstance(res_event_dt, datetime.datetime) else None
        result["_api_request_dt"] = api_req_dt
        result["_resource_event_dt"] = res_event_dt
    return result


async def measure_one_cdc_deletion(
    v1_api: client.CoreV1Api,
    custom_api: client.CustomObjectsApi,
    namespace: str,
    cdc_name: str,
    api_info: dict,
    test_run_id: str,
    cdc_pod_label_key: str,
    timeout: int,
):
    """Measures E2E deletion latency for a single CDC (time until its pods are gone)."""
    logging.debug(f"Task started for CDC deletion: {cdc_name}")
    result = {
        "run_id": test_run_id,
        "cdc_name": cdc_name,
        "operation_type": "DELETE",
        "api_request_utc": None,
        "resource_event_utc": None, # Time event observed by script
        "e2e_latency_seconds": None,
        "primary_pod_name": None,
        "initial_pod_count": 0,
        "final_pod_count": 0,
        "target_pod_count": 0,
        "status": "PENDING",
        "error_details": "",
    }

    initial_pods_to_track = set()
    try:
        logging.debug(f"CDC {cdc_name}: Listing initial pods for deletion using label '{cdc_pod_label_key}={cdc_name}'.")
        pod_list = await asyncio.to_thread(
            v1_api.list_namespaced_pod,
            namespace=namespace,
            label_selector=f"{cdc_pod_label_key}={cdc_name}",
        )
        for pod in pod_list.items:
            initial_pods_to_track.add(pod.metadata.name)
        result["initial_pod_count"] = len(initial_pods_to_track)
        logging.info(f"CDC {cdc_name}: Found {result['initial_pod_count']} initial pods to track for deletion: {initial_pods_to_track or 'None'}")
    except ApiException as e:
        result["status"] = "ERROR"
        result["error_details"] = f"API Error listing initial pods for CDC {cdc_name}: {e.reason}"
        logging.error(result["error_details"])
        result["api_request_utc"] = result["api_request_utc"].isoformat() if result["api_request_utc"] else None
        result["resource_event_utc"] = result["resource_event_utc"].isoformat() if result["resource_event_utc"] else None
        return result

    all_pods_deleted_event = asyncio.Event()
    deleted_pods_events_map = {name: asyncio.Event() for name in initial_pods_to_track}

    if initial_pods_to_track:
        logging.debug(f"CDC {cdc_name}: Attempting to acquire WATCHER_REGISTRY_LOCK for pending_deletions.")
        async with WATCHER_REGISTRY_LOCK:
            pending_deletions[cdc_name] = {
                "pods_to_delete": initial_pods_to_track.copy(),
                "deleted_pods_events": deleted_pods_events_map,
                "all_deleted_event": all_pods_deleted_event,
            }
            logging.debug(f"CDC {cdc_name}: Acquired lock, registered in pending_deletions.")
    else:
        logging.info(f"CDC {cdc_name}: No initial pods found. Deletion latency for pods will be near zero.")

    api_req_dt = None
    res_event_dt = None

    try:
        logging.info(f"Deleting CDC CR object: {cdc_name}")
        api_req_dt = datetime.datetime.now(datetime.timezone.utc)
        result["api_request_utc"] = api_req_dt
        await asyncio.to_thread(
            custom_api.delete_namespaced_custom_object,
            group=api_info["group"],
            version=api_info["version"],
            namespace=namespace,
            plural=api_info["plural"],
            name=cdc_name,
            body=client.V1DeleteOptions(),
        )
        logging.info(f"CDC {cdc_name} CR deletion request sent. Waiting for {result['initial_pod_count']} pods to be deleted...")

        if not initial_pods_to_track:
            all_pods_deleted_event.set()
            res_event_dt = api_req_dt
            result["resource_event_utc"] = res_event_dt

        await asyncio.wait_for(all_pods_deleted_event.wait(), timeout=timeout)

        # --- MODIFIED: Capture current time when event is received ---
        if result["resource_event_utc"] is None : # Only set if not set by the no-initial-pods case
            res_event_dt = datetime.datetime.now(datetime.timezone.utc)
            result["resource_event_utc"] = res_event_dt
        # -----------------------------------------------------------

        # Final check remains useful for verification
        current_pod_list_after_watch = await asyncio.to_thread(
            v1_api.list_namespaced_pod,
            namespace=namespace,
            label_selector=f"{cdc_pod_label_key}={cdc_name}",
        )
        remaining_from_initial_set = {
            p.metadata.name for p in current_pod_list_after_watch.items
            if p.metadata.name in initial_pods_to_track
        }
        result["final_pod_count"] = len(remaining_from_initial_set)

        if result["final_pod_count"] == 0:
            result["status"] = "SUCCESS"
            if isinstance(result["resource_event_utc"], datetime.datetime) and isinstance(result["api_request_utc"], datetime.datetime):
                latency = result["resource_event_utc"] - result["api_request_utc"]
                result["e2e_latency_seconds"] = latency.total_seconds()
                logging.info(f"CDC {cdc_name}: All {result['initial_pod_count']} initial pods confirmed deleted. Latency: {result['e2e_latency_seconds']:.2f}s")
            else:
                result["status"] = "ERROR"
                result["error_details"] = "Could not calculate latency due to missing timestamps."
                logging.error(f"CDC {cdc_name}: {result['error_details']}")
        else:
            result["status"] = "ERROR"
            result["error_details"] = f"Watcher indicated all pods deleted, but {result['final_pod_count']} of initial pods still found for CDC {cdc_name}. Remaining: {remaining_from_initial_set}"
            logging.error(result["error_details"])

    except ApiException as e:
        result["status"] = "ERROR"
        result["error_details"] = f"API Error deleting CDC CR: {e.reason} (Status: {e.status})"
        logging.error(f"CDC {cdc_name}: {result['error_details']}")
    except asyncio.TimeoutError:
        result["status"] = "TIMEOUT"
        result["error_details"] = f"Timeout waiting for pod deletion for CDC {cdc_name} after {timeout}s."
        logging.warning(result["error_details"])
        try:
            current_pod_list_timeout = await asyncio.to_thread(
                v1_api.list_namespaced_pod,
                namespace=namespace,
                label_selector=f"{cdc_pod_label_key}={cdc_name}",
            )
            result["final_pod_count"] = len([p for p in current_pod_list_timeout.items if p.metadata.name in initial_pods_to_track])
            logging.info(f"CDC {cdc_name} (TIMEOUT): {result['final_pod_count']} of initial pods remain.")
        except Exception:
            logging.exception(f"Could not count remaining pods for {cdc_name} on timeout.")
            result["final_pod_count"] = -1
    except Exception as e:
        result["status"] = "ERROR"
        result["error_details"] = f"Unexpected error during CDC {cdc_name} deletion: {str(e)}"
        logging.exception(f"CDC {cdc_name}: Unexpected error.")
    finally:
        logging.debug(f"CDC {cdc_name}: Attempting to acquire WATCHER_REGISTRY_LOCK for cleanup in pending_deletions.")
        async with WATCHER_REGISTRY_LOCK:
            if cdc_name in pending_deletions:
                del pending_deletions[cdc_name]
                logging.debug(f"CDC {cdc_name}: Cleaned up from pending_deletions.")

        result["api_request_utc"] = api_req_dt.isoformat() if isinstance(api_req_dt, datetime.datetime) else None
        result["resource_event_utc"] = res_event_dt.isoformat() if isinstance(res_event_dt, datetime.datetime) else None
        result["_api_request_dt"] = api_req_dt
        result["_resource_event_dt"] = res_event_dt
    return result

async def cleanup_cdcs(custom_api: client.CustomObjectsApi, namespace: str, test_run_id: str, api_info: dict):
    """Deletes all CDCs associated with the given test_run_id."""
    logging.info(f"Starting cleanup for test run ID: {test_run_id}")
    label_selector = f"e2e-latency-test-run-id={test_run_id}"
    try:
        cdcs_to_delete = await asyncio.to_thread(
            custom_api.list_namespaced_custom_object,
            group=api_info["group"],
            version=api_info["version"],
            namespace=namespace,
            plural=api_info["plural"],
            label_selector=label_selector,
        )

        delete_options = client.V1DeleteOptions(propagation_policy="Background")
        delete_tasks = []

        for cdc in cdcs_to_delete.get("items", []):
            cdc_name = cdc["metadata"]["name"]
            logging.info(f"Scheduling cleanup delete for CDC: {cdc_name}")
            task = asyncio.to_thread(
                custom_api.delete_namespaced_custom_object,
                group=api_info["group"],
                version=api_info["version"],
                namespace=namespace,
                plural=api_info["plural"],
                name=cdc_name,
                body=delete_options,
            )
            delete_tasks.append(task)

        if delete_tasks:
            cleanup_results = await asyncio.gather(*delete_tasks, return_exceptions=True)
            success_count = 0
            error_count = 0
            for i, res in enumerate(cleanup_results):
                if isinstance(res, Exception):
                    logging.error(f"Cleanup: Error deleting CDC (task index {i}): {res}")
                    error_count +=1
                else:
                    success_count +=1
            logging.info(f"Cleanup delete requests submitted for {success_count} CDCs. Errors for {error_count} CDCs.")
        else:
            logging.info("No CDCs found for cleanup with the current test run ID.")

    except ApiException as e:
        logging.error(f"Cleanup: API error listing CDCs with label {label_selector}: {e.reason} (Status: {e.status})")
    except Exception as e:
        logging.error(f"Cleanup: Unexpected error: {e}")

# --- REMOVED Plotting Functions ---

async def main(args):
    """Main orchestrator for the E2E latency test."""
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.getLogger().setLevel(log_level)

    v1_api, custom_api = load_k8s_clients()
    cdc_template = load_yaml_template(args.cdc_template_yaml)
    if not cdc_template:
        return

    try:
        api_version_str = cdc_template.get("apiVersion", "")
        if '/' not in api_version_str:
            raise ValueError(f"apiVersion '{api_version_str}' in template is not in 'group/version' format.")
        api_group, api_version = api_version_str.split("/", 1)
        api_info = {
            "group": api_group,
            "version": api_version,
            "plural": "cassandradatacenters",
        }
        if not api_info["group"] or not api_info["version"]:
            raise ValueError("Could not parse group or version from apiVersion.")
    except Exception as e:
        logging.error(f"Error parsing apiVersion from template '{args.cdc_template_yaml}': {e}")
        sys.exit(1)

    test_run_id = str(uuid.uuid4())
    logging.info(f"Starting E2E Latency Test. Run ID: {test_run_id}, N = {args.n_cdcs}, Delay = {args.inter_creation_delay}s")

    phase_timestamps = {
        "run_id": test_run_id,
        "creation_phase_start_utc": None,
        "creation_phase_end_utc": None,
        "update_phase_start_utc": None,
        "update_phase_end_utc": None,
        "deletion_phase_start_utc": None,
        "deletion_phase_end_utc": None,
    }

    all_operation_results = []
    attempted_creation_cdcs = []
    successfully_created_cdcs = []
    # Store CDCs that successfully completed the update phase for deletion later
    successfully_updated_cdcs = []

    watcher_stop_event = asyncio.Event()
    watcher_task = asyncio.create_task(
        pod_event_watcher(v1_api, args.namespace, args.cdc_pod_label_key, watcher_stop_event)
    )
    await asyncio.sleep(0.5)
    logging.debug("Watcher task created and yielded control briefly.")


    # --- Creation Phase ---
    logging.info(f"--- Starting Creation Phase for {args.n_cdcs} CDCs ---")
    phase_timestamps["creation_phase_start_utc"] = datetime.datetime.now(datetime.timezone.utc)
    logging.info(f"Creation Phase START: {phase_timestamps['creation_phase_start_utc'].isoformat()}")

    creation_task_futures = []
    for i in range(args.n_cdcs):
        cdc_name = f"e2e-{test_run_id[:8]}-{i}"
        logging.debug(f"Main: Preparing creation task for CDC {cdc_name} (iteration {i+1}/{args.n_cdcs})")
        coro = measure_one_cdc_creation(
            custom_api, args.namespace, cdc_name, cdc_template, api_info,
            test_run_id, args.cdc_pod_label_key, args.timeout_creation
        )
        task = asyncio.create_task(coro)
        creation_task_futures.append(task)

        if args.inter_creation_delay > 0 and i < args.n_cdcs - 1:
            logging.debug(f"Sleeping for {args.inter_creation_delay}s before next creation task.")
            await asyncio.sleep(args.inter_creation_delay)

    logging.info(f"Launched {len(creation_task_futures)} creation tasks. Waiting for completion...")

    creation_completed_count = 0
    for future in asyncio.as_completed(creation_task_futures):
        res = await future
        creation_completed_count += 1
        cdc_name_res = "Unknown"
        status_res = "EXCEPTION"
        if isinstance(res, dict):
            cdc_name_res = res.get('cdc_name', 'Unknown')
            status_res = res.get('status', 'COMPLETED_NO_STATUS')
            all_operation_results.append(res)
            if res.get("api_request_utc"):
                attempted_creation_cdcs.append({"name": res["cdc_name"]})
            if res.get("status") == "SUCCESS":
                successfully_created_cdcs.append({"name": res["cdc_name"]})
        elif isinstance(res, Exception):
            logging.error(f"Unhandled exception in creation task {creation_completed_count}: {res}", exc_info=True)
        else:
             logging.error(f"Unexpected result type from creation task {creation_completed_count}: {type(res)}")

        logging.info(f"Creation task {creation_completed_count}/{args.n_cdcs} for CDC '{cdc_name_res}' completed with status: {status_res}")

    phase_timestamps["creation_phase_end_utc"] = datetime.datetime.now(datetime.timezone.utc)
    logging.info(f"Creation Phase END: {phase_timestamps['creation_phase_end_utc'].isoformat()}")
    logging.info(f"===== All {args.n_cdcs} Creation Measurements Attempted. {len(successfully_created_cdcs)} successful. =====")

    # --- Pause Before Update ---
    logging.info(f"Pausing for {args.pause_between_phases} seconds before Update phase...")
    await asyncio.sleep(args.pause_between_phases)

    # --- Update Phase ---
    if not args.skip_update_phase:
        if successfully_created_cdcs:
            logging.info(f"--- Starting Update Phase for {len(successfully_created_cdcs)} successfully created CDCs ---")
            phase_timestamps["update_phase_start_utc"] = datetime.datetime.now(datetime.timezone.utc)
            logging.info(f"Update Phase START: {phase_timestamps['update_phase_start_utc'].isoformat()}")

            update_tasks = []
            for cdc_detail in successfully_created_cdcs:
                 cdc_name = cdc_detail["name"]
                 logging.debug(f"Main: Preparing update task for CDC {cdc_name}")
                 coro = measure_one_cdc_update(
                     v1_api, custom_api, args.namespace, cdc_name, api_info,
                     test_run_id, args.cdc_pod_label_key, args.target_pod_count_update, args.timeout_update
                 )
                 task = asyncio.create_task(coro)
                 update_tasks.append(task)
                 # Optional: Add inter-update delay here if needed
                 # await asyncio.sleep(args.inter_update_delay)

            logging.info(f"Launched {len(update_tasks)} update tasks. Waiting for completion...")
            update_completed_count = 0
            for future in asyncio.as_completed(update_tasks):
                 res = await future
                 update_completed_count += 1
                 cdc_name_res = "Unknown"
                 status_res = "EXCEPTION"
                 if isinstance(res, dict):
                     cdc_name_res = res.get('cdc_name', 'Unknown')
                     status_res = res.get('status', 'COMPLETED_NO_STATUS')
                     all_operation_results.append(res)
                     # Track successfully updated ones if needed for later phases, though deletion uses attempted_creation_cdcs
                     if res.get("status") == "SUCCESS":
                          successfully_updated_cdcs.append({"name": res["cdc_name"]})
                 elif isinstance(res, Exception):
                     logging.error(f"Unhandled exception in update task {update_completed_count}: {res}", exc_info=True)
                 else:
                     logging.error(f"Unexpected result type from update task {update_completed_count}: {type(res)}")
                 logging.info(f"Update task {update_completed_count}/{len(successfully_created_cdcs)} for CDC '{cdc_name_res}' completed with status: {status_res}")

            phase_timestamps["update_phase_end_utc"] = datetime.datetime.now(datetime.timezone.utc)
            logging.info(f"Update Phase END: {phase_timestamps['update_phase_end_utc'].isoformat()}")
        else:
             logging.info("--- No successfully created CDCs to update. Skipping Update Phase. ---")
             phase_timestamps["update_phase_start_utc"] = None
             phase_timestamps["update_phase_end_utc"] = None
    else:
        logging.info("--- Skipping Update Phase as requested by --skip-update-phase ---")
        phase_timestamps["update_phase_start_utc"] = None
        phase_timestamps["update_phase_end_utc"] = None

    # --- Pause Before Deletion ---
    logging.info(f"Pausing for {args.pause_between_phases} seconds before Deletion phase...")
    await asyncio.sleep(args.pause_between_phases)

    # --- Deletion Phase ---
    # Delete all CDCs for which creation was attempted, regardless of update success/failure
    cdcs_to_delete = attempted_creation_cdcs
    if cdcs_to_delete:
        logging.info(f"--- Starting Deletion Phase for {len(cdcs_to_delete)} CDCs ---")
        phase_timestamps["deletion_phase_start_utc"] = datetime.datetime.now(datetime.timezone.utc)
        logging.info(f"Deletion Phase START: {phase_timestamps['deletion_phase_start_utc'].isoformat()}")

        deletion_tasks = []
        for cdc_detail in cdcs_to_delete:
            cdc_name = cdc_detail["name"]
            logging.debug(f"Main: Preparing deletion task for CDC {cdc_name}")
            coro = measure_one_cdc_deletion(
                v1_api, custom_api, args.namespace, cdc_name, api_info,
                test_run_id, args.cdc_pod_label_key, args.timeout_deletion
            )
            task = asyncio.create_task(coro)
            deletion_tasks.append(task)

        logging.info(f"Launched {len(deletion_tasks)} deletion tasks. Waiting for completion...")

        deletion_completed_count = 0
        for future in asyncio.as_completed(deletion_tasks):
            res = await future
            deletion_completed_count += 1
            cdc_name_res = "Unknown"
            status_res = "EXCEPTION"
            if isinstance(res, dict):
                cdc_name_res = res.get('cdc_name', 'Unknown')
                status_res = res.get('status', 'COMPLETED_NO_STATUS')
                all_operation_results.append(res)
            elif isinstance(res, Exception):
                 logging.error(f"Unhandled exception in deletion task {deletion_completed_count}: {res}", exc_info=True)
            else:
                 logging.error(f"Unexpected result type from deletion task {deletion_completed_count}: {type(res)}")

            logging.info(f"Deletion task {deletion_completed_count}/{len(cdcs_to_delete)} for CDC '{cdc_name_res}' completed with status: {status_res}")

        phase_timestamps["deletion_phase_end_utc"] = datetime.datetime.now(datetime.timezone.utc)
        logging.info(f"Deletion Phase END: {phase_timestamps['deletion_phase_end_utc'].isoformat()}")

    else:
        logging.info("--- No CDCs from creation phase to delete. Skipping Deletion Phase. ---")
        phase_timestamps["deletion_phase_start_utc"] = None
        phase_timestamps["deletion_phase_end_utc"] = None

    logging.info("--- Measurement Phases Complete ---")

    logging.info("Stopping pod watcher...")
    watcher_stop_event.set()
    try:
        await asyncio.wait_for(watcher_task, timeout=args.timeout_watcher_shutdown)
        logging.debug("Watcher task awaited successfully.")
    except asyncio.TimeoutError:
        logging.warning(f"Timeout ({args.timeout_watcher_shutdown}s) waiting for watcher task to complete. It might be stuck.")
    except Exception as e:
        logging.error(f"Error awaiting watcher task: {e}", exc_info=True)


    # --- Output Results ---
    # Determine base filename
    base_output_name = f"e2e_latency_results{'_' + args.output_suffix if args.output_suffix else ''}"
    csv_filename = f"{base_output_name}.csv"
    summary_filename = f"{base_output_name}_summary.json"

    # Write per-operation results to CSV
    if all_operation_results:
        # --- MODIFIED: Define fieldnames for CSV ---
        fieldnames = [
            "run_id", "cdc_name", "operation_type", "api_request_utc",
            "resource_event_utc", "e2e_latency_seconds", "primary_pod_name",
            "initial_pod_count", "final_pod_count", "target_pod_count",
            "status", "error_details"
        ]
        try:
            with open(csv_filename, "w", newline="") as csvfile:
                # Use extrasaction='ignore' to avoid errors if internal _dt keys are still present
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(all_operation_results) # Write all rows
            logging.info(f"Per-operation results written to {csv_filename}")
        except IOError:
            logging.exception(f"Failed to write per-operation results to {csv_filename}")
        except ValueError as e:
             logging.error(f"CSV Writing Error: {e}. Ensure all results have expected keys.")
    else:
        logging.info("No per-operation results to write to CSV.")

    # Write summary JSON
    summary_output = {
        "metadata": {
            "run_id": test_run_id,
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "args": vars(args)
        },
        "phase_timestamps": {
            k: v.isoformat() if isinstance(v, datetime.datetime) else None
            for k, v in phase_timestamps.items() if k != 'run_id'
        }
    }
    try:
        with open(summary_filename, "w") as f_summary:
            json.dump(summary_output, f_summary, indent=4)
        logging.info(f"Phase timestamps summary saved to {summary_filename}")
    except Exception as e:
        logging.error(f"Failed to save phase timestamps summary to {summary_filename}: {e}")


    # --- Cleanup ---
    if not args.skip_cleanup:
        await cleanup_cdcs(custom_api, args.namespace, test_run_id, api_info)
    else:
        logging.info("Skipping final cleanup of CDCs as per --skip-cleanup flag.")

    logging.info(f"E2E Latency Test Finished. Run ID: {test_run_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Measure E2E CDC reconciliation latency for creation, update, and deletion.")
    # --- Core arguments ---
    parser.add_argument(
        "-n", "--n-cdcs", type=int, required=True, help="Number of CDC resources to create and test."
    )
    parser.add_argument(
        "--cdc-template-yaml", type=str, required=True, help="Path to the CassandraDatacenter YAML template."
    )
    parser.add_argument(
        "--namespace", type=str, default="default", help="Kubernetes namespace to operate in."
    )
    parser.add_argument(
        "--cdc-pod-label-key", type=str, required=True,
        help="The label key on pods whose value is the name of the parent CDC (e.g., 'cassandra.datastax.com/datacenter')."
    )
    # --- Output arguments ---
    parser.add_argument(
        "--output-suffix", type=str, default="",
        help="Suffix to append to the output filenames (e.g., 'my-test' -> e2e_latency_results_my-test.csv/json)."
    )
    # --- Timing arguments ---
    parser.add_argument(
        "--inter-creation-delay", type=float, default=0.0,
        help="Delay in seconds between initiating each CDC creation task (default: 0.0)."
    )
    parser.add_argument(
        "--pause-between-phases", type=int, default=30,
        help="Pause duration in seconds between Create/Update and Update/Delete phases (default: 30)."
    )
    parser.add_argument(
        "--timeout-creation", type=int, default=600,
        help="Timeout in seconds for waiting for the first pod of a CDC to be created."
    )
    parser.add_argument(
        "--timeout-update", type=int, default=600,
        help="Timeout in seconds for waiting for the target pod count after a CDC update."
    )
    parser.add_argument(
        "--timeout-deletion", type=int, default=600,
        help="Timeout in seconds for waiting for all initial pods of a CDC to be deleted."
    )
    parser.add_argument(
        "--timeout-watcher-shutdown", type=float, default=10.0,
        help="Timeout in seconds for waiting for the pod watcher task to shut down cleanly."
    )
    # --- Phase Control ---
    parser.add_argument(
        "--skip-update-phase", action="store_true",
        help="If set, skips the UPDATE phase."
    )
    parser.add_argument(
        "--target-pod-count-update", type=int, default=2,
        help="The target number of pods to wait for during the UPDATE phase (default: 2)."
    )
    parser.add_argument(
        "--skip-cleanup", action="store_true",
        help="If set, skips the final cleanup of CDCs created during this test run."
    )
    # --- Debugging ---
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable DEBUG level logging."
    )
    # --- REMOVED Plotting Arguments ---


    cli_args = parser.parse_args()

    # Basic validation
    if not cli_args.cdc_pod_label_key.strip():
        logging.error("--cdc-pod-label-key cannot be empty.")
        sys.exit(1)
    if cli_args.inter_creation_delay < 0:
        logging.error("--inter-creation-delay cannot be negative.")
        sys.exit(1)
    if cli_args.pause_between_phases < 0:
        logging.error("--pause-between-phases cannot be negative.")
        sys.exit(1)
    if cli_args.target_pod_count_update <= 0:
        logging.error("--target-pod-count-update must be positive.")
        sys.exit(1)


    asyncio.run(main(cli_args))
