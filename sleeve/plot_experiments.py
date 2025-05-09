import argparse
import datetime
import logging
import sys
import time

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from prometheus_api_client import PrometheusConnect
from prometheus_api_client.exceptions import PrometheusApiClientException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Details for Operator Metrics
OPERATOR_METRICS_JOB = "cass-operator-controller-manager-metrics-service"
OPERATOR_NAMESPACE = "cass-operator"       # e.g., "cass-operator-system"
CONTROLLER_NAME = "cassandradatacenter_controller"      # e.g., "cassandradatacenter"
# Name of the container within the operator pod
OPERATOR_CONTAINER_NAME = "manager"    # e.g., "manager"

# Details for Node Exporter Metrics
NODE_EXPORTER_JOB = "node-exporter"     # e.g., "node-exporter"
NODE_INSTANCE_LABEL = "instance"
# Value of the NODE_INSTANCE_LABEL for the dedicated node your operator runs on
DEDICATED_NODE_NAME = "172.20.0.2:9100" # e.g., "10.0.1.5:9100" or "ip-10-0-1-5.ec2.internal"


def parse_timestamp(ts_str):
    """Parses ISO 8601 timestamp string into a datetime object."""
    try:
        # Handle potential 'Z' for UTC
        if ts_str.endswith('Z'):
            ts_str = ts_str[:-1] + '+00:00'
        return datetime.datetime.fromisoformat(ts_str)
    except ValueError:
        logging.error(f"Invalid timestamp format: {ts_str}. Expected ISO 8601 format (e.g., YYYY-MM-DDTHH:MM:SSZ).")
        sys.exit(1)

def query_prometheus_range(prom, query, start_time, end_time, step):
    """Queries Prometheus for a given time range and handles potential errors."""
    logging.info(f"Querying: {query}")
    logging.info(f"Range: {start_time.isoformat()} to {end_time.isoformat()}, Step: {step}")
    try:
        result = prom.custom_query_range(
            query=query,
            start_time=start_time,
            end_time=end_time,
            step=step,
        )
        return result
    except PrometheusApiClientException as e:
        logging.error(f"Prometheus query failed: {e}")
        logging.error(f"Failed query: {query}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during query: {e}")
        logging.error(f"Failed query: {query}")
        return None

def result_to_dataframe(result, metric_name):
    """Converts Prometheus query result to a Pandas DataFrame."""
    data = []
    if not result:
        logging.warning(f"No data returned for metric: {metric_name}")
        return pd.DataFrame(columns=['timestamp', metric_name])

    # Handle potential variations in result structure (matrix vs vector)
    # This script assumes range queries returning a matrix
    if isinstance(result, list) and len(result) > 0:
         # Use the first series if multiple are returned (e.g. different controllers for reconcile rate)
         # More specific label matching in the query is preferred
        if len(result) > 1:
             logging.warning(f"Multiple series found for {metric_name}, using the first one. Consider refining query labels.")
        series = result[0] # Assume the first series is the one we want
        values = series.get('values', [])
        for timestamp, value in values:
            try:
                dt_obj = datetime.datetime.fromtimestamp(float(timestamp), tz=datetime.timezone.utc)
                numeric_value = float(value)
                data.append([dt_obj, numeric_value])
            except (ValueError, TypeError) as e:
                logging.warning(f"Skipping invalid data point for {metric_name}: time={timestamp}, value={value}, error={e}")

    df = pd.DataFrame(data, columns=['timestamp', metric_name])
    df = df.set_index('timestamp')
    return df

def calculate_relative_time(df, t_start):
    """Adds a 'relative_seconds' column based on the start time."""
    if df.empty:
        df['relative_seconds'] = []
        return df
    # Ensure t_start is timezone-aware (UTC) like the timestamps from Prometheus
    if t_start.tzinfo is None:
        t_start = t_start.replace(tzinfo=datetime.timezone.utc)

    df['relative_seconds'] = (df.index - t_start).total_seconds()
    return df


def main():
    parser = argparse.ArgumentParser(description="Query Prometheus and plot experiment results.")
    parser.add_argument("--prometheus-url", default="http://localhost:9090", help="URL of the Prometheus server.")
    # Removed --experiments, --starts, --ends arguments
    parser.add_argument("--step", default="5s", help="Query resolution step (e.g., '15s', '1m').")
    parser.add_argument("--latency-metric", default="avg", choices=['p95', 'p99', 'avg'], help="Which reconcile latency metric to plot (p95, p99, avg).")
    parser.add_argument("--output", help="Output file name to save the plot (e.g., plot.png). Shows plot if not specified.")

    args = parser.parse_args()

    experiments_to_run = [
        {
            "name": "baseline",
            "start_str": "2025-04-30T01:46:47+00:00",
            "end_str": "2025-04-30T01:51:47+00:00"
        },
        {
            "name": "instrumented",
            "start_str": "2025-04-30T01:56:19+00:00",
            "end_str": "2025-04-30T02:01:19+00:00"
        },
        {
            "name": "optimized",
            "start_str": "2025-04-30T02:05:41+00:00",
            "end_str": "2025-04-30T02:10:41+00:00"
        },
    ]

    try:
        logging.info(f"Connecting to Prometheus at {args.prometheus_url}")
        prom = PrometheusConnect(url=args.prometheus_url, disable_ssl=True)
        # Check connection
        if not prom.check_prometheus_connection():
            logging.error(f"Could not connect to Prometheus at {args.prometheus_url}")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Failed to initialize Prometheus connection: {e}")
        sys.exit(1)

    reconcile_rate_query = f"""
    sum(rate(controller_runtime_reconcile_total{{
        job="{OPERATOR_METRICS_JOB}",
        namespace="{OPERATOR_NAMESPACE}",
        controller="{CONTROLLER_NAME}"
    }}[1m]))
    """
    memory_usage_query = f"""
    container_memory_working_set_bytes{{
        namespace="{OPERATOR_NAMESPACE}",
        container="{OPERATOR_CONTAINER_NAME}",
    }}
    """
    cpu_usage_query = f"""
    100 * (
      1 - avg by ({NODE_INSTANCE_LABEL}) (
        rate(node_cpu_seconds_total{{
            mode="idle",
            job="{NODE_EXPORTER_JOB}",
            {NODE_INSTANCE_LABEL}="{DEDICATED_NODE_NAME}"
        }}[1m])
      )
    )
    """
    latency_quantile = 0.95 if args.latency_metric == "p95" else 0.99
    if args.latency_metric == "avg":
         latency_query = f"""
         sum(rate(controller_runtime_reconcile_time_seconds_sum{{
             job="{OPERATOR_METRICS_JOB}",
             namespace="{OPERATOR_NAMESPACE}",
             controller="{CONTROLLER_NAME}"
         }}[1m]))
         /
         sum(rate(controller_runtime_reconcile_time_seconds_count{{
             job="{OPERATOR_METRICS_JOB}",
             namespace="{OPERATOR_NAMESPACE}",
             controller="{CONTROLLER_NAME}"
         }}[1m]))
         """
    else:
        latency_query = f"""
        histogram_quantile({latency_quantile}, sum by (le, controller) (
          rate(controller_runtime_reconcile_time_seconds_bucket{{
            job="{OPERATOR_METRICS_JOB}",
            namespace="{OPERATOR_NAMESPACE}",
            controller="{CONTROLLER_NAME}"
          }}[1m])
        ))
        """

    queries = {
        "Reconcile Rate (inv/s)": reconcile_rate_query,
        "Node Memory Usage (bytes)": memory_usage_query,
        "Node CPU Usage (%)": cpu_usage_query,
        f"Reconcile Latency ({args.latency_metric.upper()}) (s)": latency_query,
    }

    # --- Fetch Data for Each Experiment ---
    experiment_data = {} # { metric_name: { experiment_name: dataframe } }

    # Iterate over the hardcoded list instead of args
    for experiment in experiments_to_run:
        exp_name = experiment["name"]
        start_str = experiment["start_str"]
        end_str = experiment["end_str"]

        logging.info(f"--- Processing Experiment: {exp_name} ---")
        t_start = parse_timestamp(start_str)
        t_end = parse_timestamp(end_str)

        if t_start >= t_end:
            logging.error(f"T_START must be before T_END for experiment '{exp_name}'.")
            continue

        for metric_name, query in queries.items():
            result = query_prometheus_range(prom, query, t_start, t_end, args.step)
            df = result_to_dataframe(result, metric_name) # Use metric_name as column name
            df_relative = calculate_relative_time(df, t_start)

            if metric_name not in experiment_data:
                experiment_data[metric_name] = {}
            experiment_data[metric_name][exp_name] = df_relative


    # --- Plotting ---
    logging.info("Generating plots...")
    num_metrics = len(queries)
    fig, axes = plt.subplots(num_metrics, 1, figsize=(12, num_metrics * 4), sharex=True) # Share X axis (relative time)

    if num_metrics == 1: # Handle case where only one subplot is needed
        axes = [axes]

    metric_names = list(queries.keys())

    for i, metric_name in enumerate(metric_names):
        ax = axes[i]
        if metric_name in experiment_data:
            # Use the names from the hardcoded list for labels
            for exp_details in experiments_to_run:
                exp_name = exp_details["name"]
                if exp_name in experiment_data[metric_name]:
                    df = experiment_data[metric_name][exp_name]
                    if not df.empty:
                        # Plot using relative seconds
                        ax.plot(df['relative_seconds'], df[metric_name], label=exp_name, marker='.', linestyle='-')
                    else:
                        logging.warning(f"No data to plot for '{metric_name}' in experiment '{exp_name}'")
                else:
                    # This case shouldn't happen if fetching worked, but good to have
                    logging.warning(f"Data for experiment '{exp_name}' not found for metric '{metric_name}'.")
        else:
             logging.warning(f"No data found for metric '{metric_name}' across all experiments.")

        ax.set_title(metric_name)
        ax.set_ylabel(metric_name.split('(')[-1].split(')')[0].strip()) # Extract unit from title
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax.legend()
        # Optional: Add formatting for time on x-axis if needed, though relative seconds might be clearer
        # ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

    axes[-1].set_xlabel("Time Elapsed Since Workload Start (seconds)")
    fig.suptitle("Operator Performance Comparison", fontsize=16)
    fig.tight_layout(rect=[0, 0.03, 1, 0.97]) # Adjust layout to prevent title overlap

    if args.output:
        logging.info(f"Saving plot to {args.output}")
        plt.savefig(args.output)
    else:
        logging.info("Displaying plot...")
        plt.show()

    logging.info("Script finished.")

if __name__ == "__main__":
    main()

