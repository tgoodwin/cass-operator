import argparse
import datetime
import logging
import sys
import time
import json # To load results file
import os
import math # For finding min/max

# Ensure these are installed: pip install matplotlib pandas prometheus-api-client requests
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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
    """Queries Prometheus using datetime objects."""
    if start_time_dt.tzinfo is None: start_time_dt = start_time_dt.replace(tzinfo=datetime.timezone.utc)
    if end_time_dt.tzinfo is None: end_time_dt = end_time_dt.replace(tzinfo=datetime.timezone.utc)
    logging.debug(f"Querying: {query}")
    logging.debug(f"Range (ISO):   {start_time_dt.isoformat()} to {end_time_dt.isoformat()}, Step: {step}")
    try:
        result = prom.custom_query_range(query=query, start_time=start_time_dt, end_time=end_time_dt, step=step)
        if not result: logging.warning(f"Query returned no data: {query}")
        return result
    except PrometheusApiClientException as e:
        logging.error(f"Prometheus query failed: {e}\nQuery: {query}")
        return None
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
        return pd.DataFrame(columns=[metric_name], index=pd.to_datetime([]))
    if len(result) > 1:
        labels = result[0].get('metric', {})
        logging.warning(f"Multiple series found for {metric_name}, using first series with labels: {labels}. Consider refining query labels.")
    series = result[0]
    values = series.get('values', [])
    if not values:
         logging.warning(f"First series for {metric_name} contains no values.")
         return pd.DataFrame(columns=[metric_name], index=pd.to_datetime([]))
    for timestamp, value in values:
        try:
            dt_obj = datetime.datetime.fromtimestamp(float(timestamp), tz=datetime.timezone.utc)
            numeric_value = float(value)
            if isinstance(value, str) and value.lower() == 'nan': numeric_value = float('nan')
            data.append([dt_obj, numeric_value])
        except (ValueError, TypeError) as e:
            logging.warning(f"Skipping invalid data point: time={timestamp}, value={value}, error={e}")
    if not data:
         logging.warning(f"No valid data points processed for {metric_name}.")
         return pd.DataFrame(columns=[metric_name], index=pd.to_datetime([]))
    df = pd.DataFrame(data, columns=['timestamp', metric_name])
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.set_index('timestamp')
    df = df.dropna(subset=[metric_name])
    return df

def calculate_average_metric(df, metric_name):
    """Calculates the mean of the metric column in the DataFrame."""
    if df.empty or metric_name not in df.columns or df[metric_name].isnull().all():
        return None
    return df[metric_name].mean()

def load_and_process_data(json_path, prom, query_interval, step):
    """Loads results JSON, queries Prometheus for latency metrics, returns processed data."""
    if not json_path or not os.path.exists(json_path):
        logging.warning(f"Results JSON file not found or not specified: {json_path}. Skipping.")
        return None

    try:
        with open(json_path, 'r') as f:
            experiment_results = json.load(f)
        logging.info(f"Loaded results from {json_path}")
    except Exception as e:
        logging.error(f"Error loading/parsing {json_path}: {e}")
        return None

    try:
        target_rates = sorted([float(r) for r in experiment_results.keys()])
        if not target_rates:
             logging.error(f"No valid rates found in {json_path}.")
             return None
    except ValueError:
         logging.error(f"Could not parse rates in {json_path} as numbers.")
         return None

    logging.info(f"Processing rates from {json_path}: {target_rates}")

    # --- Define PromQL Queries ---
    common_labels = f'job="{OPERATOR_METRICS_JOB}", namespace="{OPERATOR_NAMESPACE}"'
    controller_label = f'controller="{CONTROLLER_NAME}"'

    latency_p99_query = f'histogram_quantile(0.99, sum by (le, controller) (rate(controller_runtime_reconcile_time_seconds_bucket{{{common_labels}, {controller_label}}}[{query_interval}])))'
    latency_p95_query = f'histogram_quantile(0.95, sum by (le, controller) (rate(controller_runtime_reconcile_time_seconds_bucket{{{common_labels}, {controller_label}}}[{query_interval}])))'
    latency_avg_query = f'(sum(rate(controller_runtime_reconcile_time_seconds_sum{{{common_labels}, {controller_label}}}[{query_interval}])) / sum(rate(controller_runtime_reconcile_time_seconds_count{{{common_labels}, {controller_label}}}[{query_interval}])))'

    queries_to_fetch = {
        "p99 Latency (s)": latency_p99_query,
        "p95 Latency (s)": latency_p95_query,
        "Avg Latency (s)": latency_avg_query,
    }

    # --- Fetch and Process Data for each rate ---
    processed_data = {rate: {} for rate in target_rates}

    for rate in target_rates:
        rate_str = str(rate)
        if rate_str not in experiment_results: continue

        exp_info = experiment_results[rate_str]
        try:
            t_start_dt = datetime.datetime.fromtimestamp(exp_info['T_START'], tz=datetime.timezone.utc)
            t_end_dt = datetime.datetime.fromtimestamp(exp_info['T_END'], tz=datetime.timezone.utc)
        except (KeyError, ValueError, TypeError) as e:
            logging.error(f"Invalid timestamp data for rate {rate} in {json_path}: {e}")
            continue
        if t_start_dt >= t_end_dt:
            logging.error(f"T_START must be before T_END for rate {rate} in {json_path}.")
            continue

        logging.info(f"  Processing Rate: {rate} ops/s (Window: {t_start_dt.isoformat()} to {t_end_dt.isoformat()})")

        for metric_name, query in queries_to_fetch.items():
            result = query_prometheus_range(prom, query, t_start_dt, t_end_dt, step)
            df = result_to_dataframe(result, metric_name)
            avg_scalar_value = calculate_average_metric(df, metric_name)

            if avg_scalar_value is not None:
                logging.debug(f"    Avg {metric_name}: {avg_scalar_value:.4f}")
                processed_data[rate][metric_name] = avg_scalar_value
            else:
                logging.warning(f"    Could not calculate average for {metric_name} at rate {rate}")
                processed_data[rate][metric_name] = None

    return processed_data


# --- Main Script ---

def main():
    parser = argparse.ArgumentParser(description="Compare reconcile latency vs throughput for multiple experiment runs.")
    parser.add_argument("--prometheus-url", default="http://localhost:9090", help="URL of the Prometheus server.")
    # Arguments for different experiment results files
    parser.add_argument("--baseline-json", help="Path to the JSON results file for the baseline run.")
    parser.add_argument("--instrumented-json", help="Path to the JSON results file for the instrumented run.")
    parser.add_argument("--optimized-json", help="Path to the JSON results file for the optimized run.")

    parser.add_argument("--step", default="15s", help="Query resolution step (e.g., '15s', '1m').")
    parser.add_argument("--query-interval", default="1m", help="Interval used within PromQL rate/histogram functions (e.g., '1m', '2m').")
    parser.add_argument("--output-prefix", default="comparison_plot", help="Prefix for output plot filenames (e.g., 'comparison_plot_p99.png').")
    parser.add_argument("--show-plots", action='store_true', help="Show plots interactively instead of just saving.")

    args = parser.parse_args()

    # Check if at least one results file is provided
    if not any([args.baseline_json, args.instrumented_json, args.optimized_json]):
        logging.error("Must provide at least one results JSON file (--baseline-json, --instrumented-json, or --optimized-json).")
        sys.exit(1)

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

    # --- Load and Process Data for Each Run ---
    run_data = {}
    if args.baseline_json:
        logging.info("--- Processing Baseline Run ---")
        run_data["Baseline"] = load_and_process_data(args.baseline_json, prom, args.query_interval, args.step)
    if args.instrumented_json:
        logging.info("--- Processing Instrumented Run ---")
        run_data["Instrumented"] = load_and_process_data(args.instrumented_json, prom, args.query_interval, args.step)
    if args.optimized_json:
        logging.info("--- Processing Optimized Run ---")
        run_data["Optimized"] = load_and_process_data(args.optimized_json, prom, args.query_interval, args.step)

    # --- Generate Plots ---
    logging.info("Generating comparison plots...")

    metrics_to_plot = ["Avg Latency (s)", "p95 Latency (s)", "p99 Latency (s)"]
    run_styles = {
        "Baseline": {'marker': '^', 'linestyle': '--', 'color': 'green'},
        "Instrumented": {'marker': 's', 'linestyle': '-', 'color': 'red'},
        "Optimized": {'marker': 'o', 'linestyle': '-', 'color': 'blue'}
    }

    for metric in metrics_to_plot:
        fig, ax = plt.subplots(figsize=(10, 6))
        has_data = False

        for run_name, data in run_data.items():
            if data: # Check if data was loaded successfully
                rates = sorted(data.keys())
                values = [data[r].get(metric) for r in rates]
                # Filter out None values before plotting
                plot_rates = [r for r, v in zip(rates, values) if v is not None]
                plot_values = [v for v in values if v is not None]

                if plot_rates: # Only plot if there's valid data
                    style = run_styles.get(run_name, {'marker': 'x', 'linestyle': ':'}) # Default style
                    ax.plot(plot_rates, plot_values, label=run_name, **style)
                    has_data = True

        if not has_data:
            logging.warning(f"No data found to plot for metric '{metric}'. Skipping plot generation.")
            plt.close(fig) # Close the empty figure
            continue

        # Configure the plot
        metric_short_name = metric.split(" ")[0] # e.g., "Avg", "p95", "p99"
        ax.set_xlabel("Offered Load (Ops / second)")
        ax.set_ylabel(f"Avg Reconcile Latency ({metric_short_name}) (seconds)")
        ax.set_title(f"Comparison: {metric_short_name} Reconcile Latency vs. Offered Load")
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax.legend()
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        # Optional log scale for latency
        # ax.set_yscale('log')

        fig.tight_layout()
        filename = f"{args.output_prefix}_{metric_short_name.lower()}_comparison.png"
        logging.info(f"Saving plot to {filename}")
        fig.savefig(filename)

    if args.show_plots:
        logging.info("Displaying plots...")
        plt.show()

    logging.info("Script finished.")

if __name__ == "__main__":
    main()
