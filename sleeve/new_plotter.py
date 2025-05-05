import argparse
import datetime
import logging
import sys
import time
import json # To load results file
import os
import math # For finding min/max

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates # For formatting time axis
import pandas as pd
from prometheus_api_client import PrometheusConnect
from prometheus_api_client.exceptions import PrometheusApiClientException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Prometheus Query Configuration ---
# TODO: **Verify these details match your Prometheus setup and operator deployment**
OPERATOR_METRICS_JOB = "cass-operator-controller-manager-metrics-service" # Job name scraping operator metrics
OPERATOR_NAMESPACE = "cass-operator"       # Namespace where the operator pod runs
CONTROLLER_NAME = "cassandradatacenter_controller" # Name of the specific controller to measure
OPERATOR_POD_LABEL_SELECTOR = 'control-plane=controller-manager' # Label selector to find the operator pod(s)

# --- Helper Functions ---

def query_prometheus_range(prom, query, start_time_dt, end_time_dt, step):
    """
    Queries Prometheus using datetime objects.

    Args:
        prom (PrometheusConnect): Initialized Prometheus client.
        query (str): The PromQL query string.
        start_time_dt (datetime): Start timestamp (datetime object, expected to be timezone-aware).
        end_time_dt (datetime): End timestamp (datetime object, expected to be timezone-aware).
        step (str): Query resolution step (e.g., '15s').

    Returns:
        list: The result from Prometheus, or None if an error occurred.
    """
    # Ensure timestamps are timezone-aware (UTC) before passing to API client or logging
    if start_time_dt.tzinfo is None:
        start_time_dt = start_time_dt.replace(tzinfo=datetime.timezone.utc)
    if end_time_dt.tzinfo is None:
        end_time_dt = end_time_dt.replace(tzinfo=datetime.timezone.utc)

    logging.debug(f"Querying: {query}")
    # Log ISO format for human readability
    logging.debug(f"Range (ISO):   {start_time_dt.isoformat()} to {end_time_dt.isoformat()}, Step: {step}")

    try:
        # Pass datetime objects directly to the client library function
        logging.info(f"querying! Start Time: {start_time_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}, End Time: {end_time_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        result = prom.custom_query_range(
            query=query,
            start_time=start_time_dt, # Pass datetime object
            end_time=end_time_dt,     # Pass datetime object
            step=step,
        )
        if not result: logging.warning(f"Query returned no data: {query}")
        return result
    except PrometheusApiClientException as e:
        logging.error(f"Prometheus query failed: {e}\nQuery: {query}")
        return None
    # Catch potential type errors if non-datetime objects were somehow passed
    except AttributeError as e:
         logging.error(f"AttributeError during query (likely non-datetime passed): {e}\nQuery: {query}")
         return None
    except Exception as e:
        logging.error(f"Unexpected error during query: {e}\nQuery: {query}")
        return None

def result_to_dataframe(result, metric_name):
    """Converts Prometheus query result (matrix) to a Pandas DataFrame."""
    data = []
    if not result or not isinstance(result, list) or len(result) == 0:
        logging.warning(f"No data or invalid format received for metric: {metric_name}")
        # Return empty DataFrame with datetime index
        return pd.DataFrame(columns=[metric_name], index=pd.to_datetime([]))

    if len(result) > 1:
        labels = result[0].get('metric', {})
        logging.warning(f"Multiple series found for {metric_name}, using first series with labels: {labels}. Consider refining query labels.")

    series = result[0] # Assume the first series is the one we want
    values = series.get('values', [])
    if not values:
         logging.warning(f"First series for {metric_name} contains no values.")
         return pd.DataFrame(columns=[metric_name], index=pd.to_datetime([]))

    for timestamp, value in values:
        try:
            # Prometheus timestamps are typically UTC
            dt_obj = datetime.datetime.fromtimestamp(float(timestamp), tz=datetime.timezone.utc)
            numeric_value = float(value)
            # Handle potential Prometheus 'NaN' strings
            if isinstance(value, str) and value.lower() == 'nan':
                numeric_value = float('nan')
            data.append([dt_obj, numeric_value])
        except (ValueError, TypeError) as e:
            logging.warning(f"Skipping invalid data point for {metric_name}: time={timestamp}, value={value}, error={e}")

    if not data:
         logging.warning(f"No valid data points processed for {metric_name}.")
         return pd.DataFrame(columns=[metric_name], index=pd.to_datetime([]))

    df = pd.DataFrame(data, columns=['timestamp', metric_name])
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True) # Ensure UTC timezone
    df = df.set_index('timestamp')
    # Drop rows where the metric value could not be parsed as float
    df = df.dropna(subset=[metric_name])
    return df

# --- Main Script ---

def main():
    parser = argparse.ArgumentParser(description="Query Prometheus and plot overall reconcile latency over time.")
    parser.add_argument("--prometheus-url", default="http://localhost:9090", help="URL of the Prometheus server.")
    parser.add_argument("--results-json", default="load_results.json", help="Path to the JSON file containing experiment timestamps.")
    parser.add_argument("--step", default="15s", help="Query resolution step (e.g., '15s', '1m'). Should be >= scrape interval.")
    parser.add_argument("--query-interval", default="1m", help="Interval used within PromQL rate/histogram functions (e.g., '1m', '2m').")
    parser.add_argument("--output-prefix", default="overall_latency_plot", help="Prefix for output plot filename (e.g., 'overall_latency_plot.png').")
    parser.add_argument("--show-plots", action='store_true', help="Show plots interactively instead of just saving.")

    args = parser.parse_args()

    # --- Load Experiment Data ---
    if not os.path.exists(args.results_json):
        logging.error(f"Results JSON file not found: {args.results_json}")
        sys.exit(1)

    try:
        with open(args.results_json, 'r') as f:
            experiment_results = json.load(f)
        logging.info(f"Loaded results from {args.results_json}")
    except Exception as e:
        logging.error(f"Error loading/parsing {args.results_json}: {e}")
        sys.exit(1)

    # --- Determine Overall Time Range ---
    min_start_epoch = math.inf
    max_end_epoch = 0
    if not experiment_results:
        logging.error("Results JSON is empty. Cannot determine time range.")
        sys.exit(1)

    for rate_str, data in experiment_results.items():
        try:
            min_start_epoch = min(min_start_epoch, data['T_START'])
            max_end_epoch = max(max_end_epoch, data['T_END'])
        except (KeyError, TypeError) as e:
            logging.warning(f"Skipping invalid entry for rate '{rate_str}' in JSON: {e}")
            continue

    if min_start_epoch == math.inf or max_end_epoch == 0 or min_start_epoch >= max_end_epoch:
        logging.error("Could not determine valid overall time range from results JSON.")
        sys.exit(1)

    # Convert epoch to datetime objects (UTC)
    overall_start_time = datetime.datetime.fromtimestamp(min_start_epoch, tz=datetime.timezone.utc)
    overall_end_time = datetime.datetime.fromtimestamp(max_end_epoch, tz=datetime.timezone.utc)
    logging.info(f"Overall experiment time range: {overall_start_time.isoformat()} to {overall_end_time.isoformat()}")


    # --- Connect to Prometheus ---
    try:
        logging.info(f"Connecting to Prometheus at {args.prometheus_url}")
        prom = PrometheusConnect(url=args.prometheus_url, disable_ssl=True if args.prometheus_url.startswith('http://') else False)
        if not prom.check_prometheus_connection():
            logging.error(f"Could not connect to Prometheus at {args.prometheus_url}")
            sys.exit(1)
        logging.info("Prometheus connection successful.")
    except Exception as e:
        logging.error(f"Failed to initialize Prometheus connection: {e}")
        sys.exit(1)

    # --- Define PromQL Queries ---
    # Ensure these labels match your environment
    common_labels = f'job="{OPERATOR_METRICS_JOB}", namespace="{OPERATOR_NAMESPACE}"'
    controller_label = f'controller="{CONTROLLER_NAME}"'
    query_interval = args.query_interval

    # Latency Queries (calculating time series)
    latency_p99_query = f'histogram_quantile(0.99, sum by (le, controller) (rate(controller_runtime_reconcile_time_seconds_bucket{{{common_labels}, {controller_label}}}[{query_interval}])))'
    latency_p95_query = f'histogram_quantile(0.95, sum by (le, controller) (rate(controller_runtime_reconcile_time_seconds_bucket{{{common_labels}, {controller_label}}}[{query_interval}])))'
    latency_avg_query = f'(sum(rate(controller_runtime_reconcile_time_seconds_sum{{{common_labels}, {controller_label}}}[{query_interval}])) / sum(rate(controller_runtime_reconcile_time_seconds_count{{{common_labels}, {controller_label}}}[{query_interval}])))'

    queries_to_fetch = {
        "p99 Latency (s)": latency_p99_query,
        "p95 Latency (s)": latency_p95_query,
        "Avg Latency (s)": latency_avg_query,
    }

    # --- Fetch and Process Data ---
    latency_dataframes = {}

    logging.info(f"Querying Prometheus for the full range...")
    for metric_name, query in queries_to_fetch.items():
        # Pass datetime objects directly to the query function
        result = query_prometheus_range(prom, query, overall_start_time, overall_end_time, args.step)
        df = result_to_dataframe(result, metric_name)
        if not df.empty:
            logging.info(f"  Successfully fetched data for {metric_name} ({len(df)} points)")
            latency_dataframes[metric_name] = df
        else:
             logging.warning(f"  No data returned or processed for {metric_name}")
             # Create an empty dataframe to avoid plotting errors later
             latency_dataframes[metric_name] = pd.DataFrame(columns=[metric_name], index=pd.to_datetime([]))


    # --- Generate Plot ---
    logging.info("Generating latency plot...")
    fig, ax = plt.subplots(figsize=(14, 7)) # Wider figure for time series

    # Plot each latency metric time series
    # Check if DataFrame exists and is not empty before plotting
    if "p99 Latency (s)" in latency_dataframes and not latency_dataframes["p99 Latency (s)"].empty:
        ax.plot(latency_dataframes["p99 Latency (s)"].index, latency_dataframes["p99 Latency (s)"]["p99 Latency (s)"], label='p99 Latency', marker='.', linestyle='-')
    if "p95 Latency (s)" in latency_dataframes and not latency_dataframes["p95 Latency (s)"].empty:
        ax.plot(latency_dataframes["p95 Latency (s)"].index, latency_dataframes["p95 Latency (s)"]["p95 Latency (s)"], label='p95 Latency', marker='.', linestyle='-')
    if "Avg Latency (s)" in latency_dataframes and not latency_dataframes["Avg Latency (s)"].empty:
        ax.plot(latency_dataframes["Avg Latency (s)"].index, latency_dataframes["Avg Latency (s)"]["Avg Latency (s)"], label='Avg Latency', marker='.', linestyle='-')

    # Configure the plot
    ax.set_xlabel("Time")
    ax.set_ylabel("Reconcile Latency (seconds)")
    ax.set_title("Overall Controller Reconcile Latency During Load Test")
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    # Only show legend if there's something to label
    if any(not df.empty for df in latency_dataframes.values()):
        ax.legend()
    else:
        logging.warning("No latency data was plotted.")


    # Format the X-axis to show time clearly
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S', tz=datetime.timezone.utc)) # Show HH:MM:SS in UTC
    fig.autofmt_xdate() # Rotate date labels for better fit

    # Optional: Set y-axis to log scale if latency varies greatly
    # ax.set_yscale('log')
    ax.set_ylim(bottom=0) # Ensure y-axis starts at 0

    fig.tight_layout()
    latency_filename = f"{args.output_prefix}_overall.png"
    logging.info(f"Saving latency plot to {latency_filename}")
    fig.savefig(latency_filename)

    if args.show_plots:
        logging.info("Displaying plot...")
        plt.show()

    logging.info("Script finished.")

if __name__ == "__main__":
    main()
