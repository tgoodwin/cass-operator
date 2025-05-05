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
import matplotlib.dates as mdates # For formatting time axis
import numpy as np # For checking NaN and finding max
import pandas as pd
from prometheus_api_client import PrometheusConnect
from prometheus_api_client.exceptions import PrometheusApiClientException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Prometheus Query Configuration ---
# TODO: **Verify these details match your Prometheus setup and operator deployment**
OPERATOR_METRICS_JOB = "cass-operator-controller-manager-metrics-service" # Job name scraping operator metrics
OPERATOR_NAMESPACE = "cass-operator"       # Namespace where the operator pod runs
CONTROLLER_NAME = "cassandradatacenter_controller" # Name of the specific controller to measure
# OPERATOR_POD_LABEL_SELECTOR = 'control-plane=controller-manager' # Removed as requested

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

    # Handle multiple series - sum them up for rates, use first for latency quantiles/averages
    processed_values = {} # timestamp -> value
    is_rate_metric = metric_name.endswith("Rate (rec/s)")

    if is_rate_metric:
        logging.debug(f"Processing {len(result)} series for rate metric: {metric_name}")
        for series in result:
            values = series.get('values', [])
            for timestamp, value in values:
                try:
                    ts = float(timestamp)
                    val = float(value)
                    if isinstance(value, str) and value.lower() == 'nan': val = 0.0
                    processed_values[ts] = processed_values.get(ts, 0.0) + val
                except (ValueError, TypeError) as e:
                    logging.warning(f"Skipping invalid data point for rate {metric_name}: time={timestamp}, value={value}, error={e}")
        data = [[datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc), val] for ts, val in processed_values.items()]
        data.sort()
    else: # Process as single series (latency)
        if len(result) > 1:
            labels = result[0].get('metric', {})
            logging.warning(f"Multiple series found for non-rate metric {metric_name}, using first series with labels: {labels}.")
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
                logging.warning(f"Skipping invalid data point for {metric_name}: time={timestamp}, value={value}, error={e}")

    if not data:
         logging.warning(f"No valid data points processed for {metric_name}.")
         return pd.DataFrame(columns=[metric_name], index=pd.to_datetime([]))

    df = pd.DataFrame(data, columns=['timestamp', metric_name])
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.set_index('timestamp')
    df = df.dropna(subset=[metric_name])
    return df


def calculate_average_metric_for_step(full_df, metric_name, t_start_dt, t_end_dt):
    """Calculates the mean of a metric within a specific time slice of a DataFrame."""
    if t_start_dt.tzinfo is None: t_start_dt = t_start_dt.replace(tzinfo=datetime.timezone.utc)
    if t_end_dt.tzinfo is None: t_end_dt = t_end_dt.replace(tzinfo=datetime.timezone.utc)
    step_df = full_df[(full_df.index >= t_start_dt) & (full_df.index <= t_end_dt)]
    if step_df.empty or metric_name not in step_df.columns or step_df[metric_name].isnull().all():
        return None
    return step_df[metric_name].mean()

def load_process_and_query_data(json_path, prom, query_interval, step):
    """
    Loads results JSON, queries Prometheus for latency & rate time series,
    and calculates per-step average scalar latencies.

    Returns:
        dict: Contains 'time_series' (dict of metric_name -> DataFrame) and
              'step_averages' (dict of rate -> {metric_name: avg_value}).
              Returns None if loading or processing fails critically.
    """
    if not json_path or not os.path.exists(json_path):
        logging.warning(f"Results JSON file not found or not specified: {json_path}. Skipping.")
        return None
    try:
        with open(json_path, 'r') as f: experiment_results = json.load(f)
        logging.info(f"Loaded results from {json_path}")
    except Exception as e:
        logging.error(f"Error loading/parsing {json_path}: {e}")
        return None

    # --- Determine Overall Time Range for this run ---
    min_start_epoch = math.inf
    max_end_epoch = 0
    target_rates_from_json = {}
    if not experiment_results:
        logging.error(f"Results JSON {json_path} is empty.")
        return None
    for rate_str, data in experiment_results.items():
        try:
            rate = float(rate_str)
            t_start = data['T_START']
            t_end = data['T_END']
            min_start_epoch = min(min_start_epoch, t_start)
            max_end_epoch = max(max_end_epoch, t_end)
            target_rates_from_json[rate] = {'T_START': t_start, 'T_END': t_end}
        except (KeyError, ValueError, TypeError) as e:
            logging.warning(f"Skipping invalid entry for rate '{rate_str}' in {json_path}: {e}")
            continue
    if min_start_epoch == math.inf or max_end_epoch == 0 or min_start_epoch >= max_end_epoch:
        logging.error(f"Could not determine valid overall time range from {json_path}.")
        return None
    target_rates = sorted(target_rates_from_json.keys())
    overall_start_time = datetime.datetime.fromtimestamp(min_start_epoch, tz=datetime.timezone.utc)
    overall_end_time = datetime.datetime.fromtimestamp(max_end_epoch, tz=datetime.timezone.utc)
    logging.info(f"Processing rates from {json_path}: {target_rates}")
    logging.info(f"Overall time range for {json_path}: {overall_start_time.isoformat()} to {overall_end_time.isoformat()}")

    # --- Define PromQL Queries (Removed pod selector) ---
    common_labels = f'job="{OPERATOR_METRICS_JOB}", namespace="{OPERATOR_NAMESPACE}"'
    controller_label = f'controller="{CONTROLLER_NAME}"'
    # Latency
    latency_p99_query = f'histogram_quantile(0.99, sum by (le, controller) (rate(controller_runtime_reconcile_time_seconds_bucket{{{common_labels}, {controller_label}}}[{query_interval}])))'
    latency_p95_query = f'histogram_quantile(0.95, sum by (le, controller) (rate(controller_runtime_reconcile_time_seconds_bucket{{{common_labels}, {controller_label}}}[{query_interval}])))'
    latency_avg_query = f'(sum(rate(controller_runtime_reconcile_time_seconds_sum{{{common_labels}, {controller_label}}}[{query_interval}])) / sum(rate(controller_runtime_reconcile_time_seconds_count{{{common_labels}, {controller_label}}}[{query_interval}])))'
    # Reconcile Rates
    reconcile_total_query = f'sum(rate(controller_runtime_reconcile_total{{{common_labels}, {controller_label}}}[{query_interval}]))'
    reconcile_error_query = f'sum(rate(controller_runtime_reconcile_total{{{common_labels}, {controller_label}, result="error"}}[{query_interval}]))'
    reconcile_non_error_query = f'sum(rate(controller_runtime_reconcile_total{{{common_labels}, {controller_label}, result!="error"}}[{query_interval}]))'

    queries_to_fetch = {
        "p99 Latency (s)": latency_p99_query,
        "p95 Latency (s)": latency_p95_query,
        "Avg Latency (s)": latency_avg_query,
        "Total Reconcile Rate (rec/s)": reconcile_total_query,
        "Error Reconcile Rate (rec/s)": reconcile_error_query,
        "Non-Error Reconcile Rate (rec/s)": reconcile_non_error_query,
    }

    # --- Fetch Full Time Series Data ---
    time_series_data = {}
    logging.info(f"Querying Prometheus for the full range of {json_path}...")
    query_buffer = datetime.timedelta(seconds=60)
    query_start = overall_start_time - query_buffer
    query_end = overall_end_time + query_buffer

    for metric_name, query in queries_to_fetch.items():
        result = query_prometheus_range(prom, query, query_start, query_end, step)
        df = result_to_dataframe(result, metric_name)
        if not df.empty:
            logging.info(f"  Successfully fetched time series for {metric_name} ({len(df)} points)")
            time_series_data[metric_name] = df[(df.index >= overall_start_time) & (df.index <= overall_end_time)]
        else:
             logging.warning(f"  No time series data returned or processed for {metric_name}")
             time_series_data[metric_name] = pd.DataFrame(columns=[metric_name], index=pd.to_datetime([]))

    # --- Calculate Per-Step Averages from Time Series (Only for Latency) ---
    step_average_data = {rate: {} for rate in target_rates}
    logging.info(f"Calculating per-step average latencies for {json_path}...")
    latency_metrics = ["Avg Latency (s)", "p95 Latency (s)", "p99 Latency (s)"]
    for rate in target_rates:
        rate_info = target_rates_from_json[rate]
        t_start_dt = datetime.datetime.fromtimestamp(rate_info['T_START'], tz=datetime.timezone.utc)
        t_end_dt = datetime.datetime.fromtimestamp(rate_info['T_END'], tz=datetime.timezone.utc)

        for metric_name in latency_metrics:
            if metric_name in time_series_data:
                full_df = time_series_data[metric_name]
                avg_scalar_value = calculate_average_metric_for_step(full_df, metric_name, t_start_dt, t_end_dt)
                if avg_scalar_value is not None:
                    logging.debug(f"    Rate {rate} - Avg {metric_name}: {avg_scalar_value:.4f}")
                    step_average_data[rate][metric_name] = avg_scalar_value
                else:
                    logging.warning(f"    Rate {rate} - Could not calculate average for {metric_name}")
                    step_average_data[rate][metric_name] = None
            else:
                 step_average_data[rate][metric_name] = None # Ensure key exists even if data fetch failed

    return {
        'time_series': time_series_data,
        'step_averages': step_average_data,
        'overall_start_time': overall_start_time
    }

# --- Main Script ---

def main():
    parser = argparse.ArgumentParser(description="Compare reconcile latency vs throughput and vs time for multiple experiment runs.")
    parser.add_argument("--prometheus-url", default="http://localhost:9090", help="URL of the Prometheus server.")
    parser.add_argument("--baseline-json", help="Path to the JSON results file for the baseline run.")
    parser.add_argument("--instrumented-json", help="Path to the JSON results file for the instrumented run.")
    parser.add_argument("--optimized-json", help="Path to the JSON results file for the optimized run.")
    parser.add_argument("--step", default="15s", help="Query resolution step (e.g., '15s', '1m').")
    parser.add_argument("--query-interval", default="1m", help="Interval used within PromQL rate/histogram functions (e.g., '1m', '2m').")
    parser.add_argument("--output-prefix", default="comparison_plot", help="Prefix for output plot filenames.")
    parser.add_argument("--show-plots", action='store_true', help="Show plots interactively instead of just saving.")

    args = parser.parse_args()

    if not any([args.baseline_json, args.instrumented_json, args.optimized_json]):
        logging.error("Must provide at least one results JSON file.")
        sys.exit(1)

    # --- Connect to Prometheus ---
    try:
        logging.info(f"Connecting to Prometheus at {args.prometheus_url}")
        prom = PrometheusConnect(url=args.prometheus_url, disable_ssl=True if args.prometheus_url.startswith('http://') else False)
        if not prom.check_prometheus_connection(): raise Exception("Connection Check Failed")
        logging.info("Prometheus connection successful.")
    except Exception as e:
        logging.error(f"Failed to initialize Prometheus connection: {e}")
        sys.exit(1)

    # --- Load and Process Data for Each Run ---
    run_data = {}
    run_names = []
    if args.baseline_json:
        logging.info("--- Processing Baseline Run ---")
        data = load_process_and_query_data(args.baseline_json, prom, args.query_interval, args.step)
        if data: run_data["Baseline"] = data; run_names.append("Baseline")
    if args.instrumented_json:
        logging.info("--- Processing Instrumented Run ---")
        data = load_process_and_query_data(args.instrumented_json, prom, args.query_interval, args.step)
        if data: run_data["Instrumented"] = data; run_names.append("Instrumented")
    if args.optimized_json:
        logging.info("--- Processing Optimized Run ---")
        data = load_process_and_query_data(args.optimized_json, prom, args.query_interval, args.step)
        if data: run_data["Optimized"] = data; run_names.append("Optimized")

    if not run_data:
        logging.error("No data successfully processed from any input JSON file. Exiting.")
        sys.exit(1)

    # --- Generate Plots ---
    logging.info("Generating comparison plots...")

    latency_metrics = ["Avg Latency (s)", "p95 Latency (s)", "p99 Latency (s)"]
    rate_metrics = ["Total Reconcile Rate (rec/s)", "Error Reconcile Rate (rec/s)", "Non-Error Reconcile Rate (rec/s)"]
    rate_plot_titles = ["Total Rate", "Error Rate", "Success/Requeue Rate"] # For individual plot titles
    rate_plot_styles = { # Colors for the rate plots
        "Total Reconcile Rate (rec/s)": {'color': 'blue', 'linestyle': '-'},
        "Error Reconcile Rate (rec/s)": {'color': 'red', 'linestyle': '--'},
        "Non-Error Reconcile Rate (rec/s)": {'color': 'green', 'linestyle': '-.'}
    }

    figures = [] # Keep track of created figures

    # --- Plot 1: Latency vs. Throughput (using step averages) ---
    logging.info("Generating Latency vs. Offered Load plots...")
    run_styles_load = { # Keep original markers/styles for this plot type
        "Baseline": {'marker': '^', 'linestyle': '--', 'color': 'green'},
        "Instrumented": {'marker': 's', 'linestyle': '-', 'color': 'red'},
        "Optimized": {'marker': 'o', 'linestyle': '-', 'color': 'blue'}
    }
    for metric in latency_metrics:
        fig, ax = plt.subplots(figsize=(10, 6))
        figures.append(fig)
        has_data = False
        metric_short_name = metric.split(" ")[0]

        for run_name in run_names:
            if run_name in run_data and run_data[run_name]['step_averages']:
                data = run_data[run_name]['step_averages']
                rates = sorted(data.keys())
                values = [data[r].get(metric) for r in rates]
                plot_rates = [r for r, v in zip(rates, values) if v is not None]
                plot_values = [v for v in values if v is not None]
                if plot_rates:
                    style = run_styles_load.get(run_name, {'marker': 'x', 'linestyle': ':'})
                    ax.plot(plot_rates, plot_values, label=run_name, **style)
                    has_data = True

        if not has_data:
            logging.warning(f"No data found for '{metric}' vs Load plot. Skipping.")
            plt.close(fig); figures.remove(fig); continue

        ax.set_xlabel("Offered Load (Ops / second)")
        ax.set_ylabel(f"Avg Reconcile Latency ({metric_short_name}) (seconds)")
        ax.set_title(f"Comparison: {metric_short_name} Reconcile Latency vs. Offered Load")
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax.legend()
        ax.set_xlim(left=0); ax.set_ylim(bottom=0)
        fig.tight_layout()
        filename = f"{args.output_prefix}_{metric_short_name.lower()}_vs_load_comparison.png"
        logging.info(f"Saving plot to {filename}")
        fig.savefig(filename)
        if not args.show_plots: plt.close(fig)

    # --- Plot 2: Latency vs. Time (Stacked, Consistent Y Scale, Circle Markers) ---
    logging.info("Generating Latency vs. Time stacked plot...")
    fig_lat_time, axes_lat_time = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    figures.append(fig_lat_time)
    fig_lat_time.suptitle("Comparison: Reconcile Latency Over Time", fontsize=16)

    max_relative_time_lat = 0
    max_latency_overall = 0
    run_styles_time = { # Styles for time series plots (consistent marker)
        "Baseline": {'linestyle': '--', 'color': 'green', 'marker': '.'},
        "Instrumented": {'linestyle': '-', 'color': 'red', 'marker': '.'},
        "Optimized": {'linestyle': '-', 'color': 'blue', 'marker': '.'}
    }

    # First pass: find max values for scaling
    for metric in latency_metrics:
        for run_name in run_names:
             if run_name in run_data and run_data[run_name]['time_series']:
                df = run_data[run_name]['time_series'].get(metric)
                if df is not None and not df.empty:
                    # Use percentile to avoid extreme outliers skewing scale too much
                    q99 = df[metric].quantile(0.99)
                    if not np.isnan(q99):
                         max_latency_overall = max(max_latency_overall, q99)

    y_lim_lat = max_latency_overall * 1.15 if max_latency_overall > 0 else 1.0 # Add 15% padding

    # Second pass: plot data
    for i, metric in enumerate(latency_metrics):
        ax = axes_lat_time[i]
        has_data_for_metric = False
        for run_name in run_names:
             if run_name in run_data and run_data[run_name]['time_series']:
                df = run_data[run_name]['time_series'].get(metric)
                if df is not None and not df.empty:
                    style = run_styles_time.get(run_name, {'marker': '.', 'linestyle': ':'}) # Use time series styles
                    start_time = run_data[run_name]['overall_start_time']
                    relative_seconds = (df.index - start_time).total_seconds()
                    ax.plot(relative_seconds, df[metric], label=run_name, markersize=3, **style) # Use markersize
                    has_data_for_metric = True
                    max_relative_time_lat = max(max_relative_time_lat, relative_seconds.max())

        if not has_data_for_metric:
            logging.warning(f"No time series data for metric '{metric}'. Subplot empty.")
            ax.text(0.5, 0.5, f"No data for {metric}", ha='center', va='center', transform=ax.transAxes)

        metric_short_name = metric.split(" ")[0]
        ax.set_ylabel(f"{metric_short_name} Latency (s)")
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax.legend()
        ax.set_ylim(bottom=0, top=y_lim_lat) # Apply consistent Y limit

    axes_lat_time[-1].set_xlabel("Time Since Experiment Start (seconds)")
    if max_relative_time_lat > 0: axes_lat_time[-1].set_xlim(left=0, right=max_relative_time_lat)
    else: axes_lat_time[-1].set_xlim(left=0)

    fig_lat_time.tight_layout(rect=[0, 0.03, 1, 0.96])
    time_filename_lat = f"{args.output_prefix}_latency_vs_time_stacked.png"
    logging.info(f"Saving stacked latency time plot to {time_filename_lat}")
    fig_lat_time.savefig(time_filename_lat)
    if not args.show_plots: plt.close(fig_lat_time)


    # --- Plot 3: Individual Reconcile Rate vs. Time Plots ---
    logging.info("Generating individual Reconcile Rate vs. Time plots...")
    for run_name in run_names:
        if run_name not in run_data or not run_data[run_name]['time_series']:
            logging.warning(f"No time series data found for run '{run_name}'. Skipping rate plot.")
            continue

        fig_rate, ax_rate = plt.subplots(figsize=(14, 7)) # Single plot per run
        figures.append(fig_rate)
        has_data = False
        max_relative_time_rate = 0

        run_ts_data = run_data[run_name]['time_series']
        start_time = run_data[run_name]['overall_start_time']

        for metric in rate_metrics:
            if metric in run_ts_data:
                df = run_ts_data[metric]
                if df is not None and not df.empty:
                    style = rate_plot_styles.get(metric, {'linestyle': ':'}) # Use specific rate styles
                    relative_seconds = (df.index - start_time).total_seconds()
                    # Use small circle marker
                    ax_rate.plot(relative_seconds, df[metric], label=metric.split(" ")[0], markersize=3, **style)
                    has_data = True
                    max_relative_time_rate = max(max_relative_time_rate, relative_seconds.max())

        if not has_data:
            logging.warning(f"No rate data found to plot for run '{run_name}'. Skipping plot.")
            plt.close(fig_rate); figures.remove(fig_rate); continue

        # Configure the plot
        ax_rate.set_xlabel("Time Since Experiment Start (seconds)")
        ax_rate.set_ylabel("Reconcile Rate (rec/s)")
        ax_rate.set_title(f"{run_name}: Reconcile Rate Composition Over Time")
        ax_rate.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax_rate.legend()
        ax_rate.set_ylim(bottom=0)
        if max_relative_time_rate > 0: ax_rate.set_xlim(left=0, right=max_relative_time_rate)
        else: ax_rate.set_xlim(left=0)

        fig_rate.tight_layout()
        filename = f"{args.output_prefix}_{run_name.lower()}_reconcile_rates_vs_time.png"
        logging.info(f"Saving plot to {filename}")
        fig_rate.savefig(filename)
        if not args.show_plots: plt.close(fig_rate)


    # --- Show all plots if requested ---
    if args.show_plots:
        if figures:
            logging.info("Displaying plots...")
            plt.show() # Attempt to show all figures created
        else:
            logging.warning("No plots were generated to display.")

    logging.info("Script finished.")

if __name__ == "__main__":
    main()
