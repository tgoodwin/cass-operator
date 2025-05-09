import argparse
import json
import logging
import requests
import datetime
import time
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)

# --- Constants ---
PROMETHEUS_URL = "http://localhost:9090"
METRIC_NAME = "controller_runtime_reconcile_time_seconds"
# Namespaces to query for controllers
TARGET_NAMESPACES = ["sleeve-system", "cass-operator"]
DEFAULT_STEP = "30s" # Prometheus query step resolution

def parse_utc_timestamp(ts_str: str) -> datetime.datetime | None:
    """Converts an ISO 8601 UTC timestamp string to a datetime object."""
    if not ts_str:
        return None
    try:
        # Ensure it's timezone-aware (UTC)
        dt = datetime.datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except ValueError:
        logging.error(f"Could not parse timestamp: {ts_str}")
        return None

def query_prometheus_range(query: str, start_time: datetime.datetime, end_time: datetime.datetime, step: str = DEFAULT_STEP) -> dict | None:
    """
    Queries Prometheus for a given PromQL query over a time range.
    Returns the JSON response or None on error.
    """
    start_ts = int(start_time.timestamp())
    end_ts = int(end_time.timestamp())

    url = f"{PROMETHEUS_URL}/api/v1/query_range"
    params = {
        "query": query,
        "start": start_ts,
        "end": end_ts,
        "step": step,
    }
    try:
        logging.debug(f"Querying Prometheus: {url} with params: {params}")
        response = requests.get(url, params=params, timeout=30) # Added timeout
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        if data["status"] == "success":
            return data["data"]["result"]
        else:
            logging.error(f"Prometheus query failed: {data.get('error', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to Prometheus or during request: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding Prometheus response: {e}")
        return None
    except KeyError as e:
        logging.error(f"Unexpected Prometheus response structure (missing key {e}): {response.text[:200]}...")
        return None


def calculate_avg_latency_query(metric_name: str, namespaces: list, lookback_window: str = "5m") -> str:
    """
    Generates PromQL query for average latency of a histogram.
    Filters by 'controller' and 'namespace' labels.
    """
    # Create a regex for namespaces: (namespace1|namespace2|...)
    namespace_regex = "|".join(namespaces)
    query = (
        f"sum(rate({metric_name}_sum{{namespace=~'{namespace_regex}'}}[{lookback_window}])) by (controller) / "
        f"sum(rate({metric_name}_count{{namespace=~'{namespace_regex}'}}[{lookback_window}])) by (controller)"
    )
    return query

def calculate_p99_latency_query(metric_name: str, namespaces: list, lookback_window: str = "5m") -> str:
    """
    Generates PromQL query for P99 latency of a histogram.
    Filters by 'controller' and 'namespace' labels.
    """
    namespace_regex = "|".join(namespaces)
    query = f"histogram_quantile(0.99, sum(rate({metric_name}_bucket{{namespace=~'{namespace_regex}'}}[{lookback_window}])) by (le, controller))"
    return query


def process_prometheus_results(results: list, metric_type: str) -> pd.DataFrame | None:
    """
    Processes Prometheus query results into a Pandas DataFrame.
    Each series (controller) becomes a column. Timestamps become the index.
    """
    if not results:
        logging.warning(f"No data returned from Prometheus for {metric_type}.")
        return None

    all_data = []
    for series in results:
        controller_name = series.get("metric", {}).get("controller", "unknown_controller")
        for value_pair in series.get("values", []):
            timestamp = datetime.datetime.fromtimestamp(value_pair[0], tz=datetime.timezone.utc)
            latency = float(value_pair[1])
            all_data.append({"timestamp": timestamp, "controller": controller_name, metric_type: latency})

    if not all_data:
        logging.warning(f"No data points found after processing Prometheus results for {metric_type}.")
        return None

    df = pd.DataFrame(all_data)
    # Pivot the table so each controller is a column and timestamps are the index
    # This makes plotting easier if multiple lines are on the same axes
    try:
        pivot_df = df.pivot(index='timestamp', columns='controller', values=metric_type)
    except Exception as e: # Can fail if there are duplicate timestamp/controller pairs, which shouldn't happen with range queries for distinct series
        logging.error(f"Error pivoting DataFrame for {metric_type}: {e}. Returning unpivoted data.")
        return df # Return unpivoted as a fallback
    return pivot_df


def plot_latency_over_time(df: pd.DataFrame, title: str, ylabel: str, output_filename: str):
    """Plots latency metrics over time for multiple controllers."""
    if df is None or df.empty:
        logging.warning(f"No data to plot for {title}.")
        return

    plt.figure(figsize=(15, 7))
    for controller_column in df.columns: # Iterate through controller columns if pivoted
        if isinstance(df, pd.DataFrame) and controller_column in df: # Check if df is DataFrame
             plt.plot(df.index, df[controller_column], label=controller_column, marker='.', linestyle='-')
        elif isinstance(df, pd.Series): # Handle case where only one controller's data might be returned as Series
             if df.name == controller_column: # Check if Series name matches
                  plt.plot(df.index, df, label=controller_column, marker='.', linestyle='-')

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10))
    plt.gcf().autofmt_xdate() # Auto-formats the x-axis labels for dates

    plt.title(title, fontsize=16)
    plt.xlabel("Time (UTC)", fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.legend(title="Controller", fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

    try:
        plt.savefig(output_filename)
        logging.info(f"Plot saved to {output_filename}")
    except Exception as e:
        logging.error(f"Failed to save plot to {output_filename}: {e}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Query Prometheus for controller runtime metrics and plot them.")
    parser.add_argument("summary_file", help="Path to the experiment summary JSON file.")
    parser.add_argument("--output-prefix", default=None,
                        help="Prefix for the output plot filenames.")
    parser.add_argument("--prometheus-url", default=PROMETHEUS_URL,
                        help=f"Prometheus server URL (default: {PROMETHEUS_URL}).")
    parser.add_argument("--step", default=DEFAULT_STEP,
                        help=f"Prometheus query step resolution (default: {DEFAULT_STEP}).")
    parser.add_argument("--lookback-window", default="5m",
                        help="Lookback window for rate/histogram calculations (e.g., '5m', '1h'). Default '5m'.")
    parser.add_argument("--debug", action="store_true", help="Enable DEBUG level logging.")

    args = parser.parse_args()

    # global PROMETHEUS_URL # Allow modification of global for Prometheus URL
    # PROMETHEUS_URL = args.prometheus_url

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.getLogger().setLevel(log_level)

    # Load experiment summary
    try:
        with open(args.summary_file, 'r') as f:
            summary = json.load(f)
    except FileNotFoundError:
        logging.error(f"Summary file not found: {args.summary_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding summary JSON from {args.summary_file}: {e}")
        sys.exit(1)

    phase_timestamps = summary.get("phase_timestamps", {})
    start_str = phase_timestamps.get("creation_phase_start_utc")
    end_str = phase_timestamps.get("deletion_phase_end_utc")

    if not start_str or not end_str:
        logging.error("Experiment start or end times are missing from the summary file.")
        sys.exit(1)

    experiment_start_time = parse_utc_timestamp(start_str)
    experiment_end_time = parse_utc_timestamp(end_str)

    if not experiment_start_time or not experiment_end_time:
        logging.error("Could not parse experiment start or end times.")
        sys.exit(1)

    logging.info(f"Experiment Time Range: {experiment_start_time.isoformat()} to {experiment_end_time.isoformat()}")

    # --- Query and Plot Average Latency ---
    avg_latency_query = calculate_avg_latency_query(METRIC_NAME, TARGET_NAMESPACES, args.lookback_window)
    logging.info(f"Querying AVG latency: {avg_latency_query}")
    avg_results = query_prometheus_range(avg_latency_query, experiment_start_time, experiment_end_time, args.step)
    avg_df = process_prometheus_results(avg_results, "avg_latency_seconds")
    if avg_df is not None and not avg_df.empty:
        plot_latency_over_time(
            avg_df,
            f"Average Controller Reconciliation Latency ({METRIC_NAME})",
            "Average Latency (seconds)",
            f"{args.output_prefix}_avg.png"
        )
    else:
        logging.warning("No data for average latency plot.")

    # --- Query and Plot P99 Latency ---
    p99_latency_query = calculate_p99_latency_query(METRIC_NAME, TARGET_NAMESPACES, args.lookback_window)
    logging.info(f"Querying P99 latency: {p99_latency_query}")
    p99_results = query_prometheus_range(p99_latency_query, experiment_start_time, experiment_end_time, args.step)
    p99_df = process_prometheus_results(p99_results, "p99_latency_seconds")

    if p99_df is not None and not p99_df.empty:
        plot_latency_over_time(
            p99_df,
            f"P99 Controller Reconciliation Latency ({METRIC_NAME})",
            "P99 Latency (seconds)",
            f"{args.output_prefix}_p99.png"
        )
    else:
        logging.warning("No data for P99 latency plot.")

    logging.info("Prometheus query script finished.")

if __name__ == "__main__":
    main()
