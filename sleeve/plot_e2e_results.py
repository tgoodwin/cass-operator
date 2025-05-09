import argparse
import json
import datetime
import logging
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import csv
import pandas as pd # Import pandas
import seaborn as sns # Import seaborn

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)

def load_run_data(suffix: str, base_filename: str = "e2e_latency_results") -> dict | None:
    """Loads operation results (CSV) and phase timestamps (JSON) for a given suffix."""
    csv_filename = f"{base_filename}{'_' + suffix if suffix else ''}.csv"
    json_filename = f"{base_filename}{'_' + suffix if suffix else ''}_summary.json"

    run_data = {"operation_results": [], "phase_timestamps": None, "metadata": None, "suffix": suffix} # Store suffix for easier identification

    # Load CSV data
    if not os.path.exists(csv_filename):
        logging.error(f"Input CSV file not found: {csv_filename}")
        return None
    try:
        with open(csv_filename, 'r', newline='') as f_csv:
            reader = csv.DictReader(f_csv)
            for row in reader:
                 try:
                      if row.get('e2e_latency_seconds') is not None and row['e2e_latency_seconds'] != '':
                           row['e2e_latency_seconds'] = float(row['e2e_latency_seconds'])
                      else:
                           row['e2e_latency_seconds'] = None # Ensure it's None if empty or missing
                 except (ValueError, TypeError):
                      logging.warning(f"Could not convert latency '{row.get('e2e_latency_seconds')}' to float for row: {row}. Setting to None.")
                      row['e2e_latency_seconds'] = None
                 run_data["operation_results"].append(row)
        logging.info(f"Loaded {len(run_data['operation_results'])} operation results from {csv_filename}")
    except Exception as e:
        logging.error(f"Error reading or processing CSV file {csv_filename}: {e}")
        return None

    # Load JSON summary data
    if not os.path.exists(json_filename):
        logging.error(f"Input JSON summary file not found: {json_filename}")
        # Allow continuing if only CSV is present and box plots are requested
        if not run_data["operation_results"]:
            return None
        logging.warning(f"JSON summary {json_filename} not found, proceeding with CSV data only (throughput plots might be affected).")
    else:
        try:
            with open(json_filename, 'r') as f_json:
                summary_data = json.load(f_json)
            if "metadata" not in summary_data or "phase_timestamps" not in summary_data:
                 logging.error(f"JSON file {json_filename} is missing required keys (metadata, phase_timestamps).")
                 if not run_data["operation_results"]: return None # Still fail if no CSV either
            else:
                run_data["metadata"] = summary_data["metadata"]
                run_data["phase_timestamps"] = summary_data["phase_timestamps"]
                logging.info(f"Loaded summary data from {json_filename} (Run ID: {run_data.get('metadata', {}).get('run_id', 'N/A')})")
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from {json_filename}: {e}")
            if not run_data["operation_results"]: return None
        except Exception as e:
            logging.error(f"Unexpected error loading {json_filename}: {e}")
            if not run_data["operation_results"]: return None
    return run_data


def calculate_throughput_data(operation_results: list, phase_timestamps: dict) -> dict:
    """Calculates relative completion times and cumulative counts for each phase for a SINGLE run."""
    throughput_data = {
        "CREATE": {"times": [], "counts": []},
        "UPDATE": {"times": [], "counts": []},
        "DELETE": {"times": [], "counts": []},
    }

    phase_starts = {
        "CREATE": phase_timestamps.get("creation_phase_start_utc"),
        "UPDATE": phase_timestamps.get("update_phase_start_utc"),
        "DELETE": phase_timestamps.get("deletion_phase_start_utc"),
    }

    phase_start_dts = {}
    for phase, start_iso in phase_starts.items():
        if isinstance(start_iso, str):
            try:
                phase_start_dts[phase] = datetime.datetime.fromisoformat(start_iso)
            except (ValueError, TypeError):
                logging.error(f"Could not parse phase start timestamp for {phase}: {start_iso}")
                phase_start_dts[phase] = None
        else:
             phase_start_dts[phase] = None

    for res in operation_results:
        op_type = res.get("operation_type")
        status = res.get("status")
        event_time_iso = res.get("resource_event_utc")

        if op_type in throughput_data and status == "SUCCESS" and isinstance(event_time_iso, str):
            phase_start_dt = phase_start_dts.get(op_type)
            if not phase_start_dt:
                logging.debug(f"Skipping result for {op_type} {res.get('cdc_name')} due to missing phase start time.")
                continue
            try:
                event_time_dt = datetime.datetime.fromisoformat(event_time_iso)
                relative_time_sec = (event_time_dt - phase_start_dt).total_seconds()
                if relative_time_sec >= 0:
                    throughput_data[op_type]["times"].append(relative_time_sec)
                else:
                     logging.warning(f"Operation {op_type} for {res.get('cdc_name')} completed before phase start? Relative time: {relative_time_sec:.2f}s. Skipping.")
            except (ValueError, TypeError):
                 logging.warning(f"Could not parse resource_event_utc for {op_type} {res.get('cdc_name')}: {event_time_iso}. Skipping.")
                 continue

    for phase, data in throughput_data.items():
        if data["times"]:
            sorted_indices = np.argsort(data["times"])
            data["times"] = np.array(data["times"])[sorted_indices]
            data["counts"] = np.arange(1, len(data["times"]) + 1)
            logging.info(f"Processed {len(data['times'])} successful {phase} operations for throughput plot.")
        else:
            data["times"] = np.array([])
            data["counts"] = np.array([])
            logging.info(f"No successful {phase} operations found for throughput plot.")
    return throughput_data


def plot_throughput_comparison(
        throughput_data_dict: dict,
        output_png_filename: str
    ):
    """Generates a single PNG comparing throughput subplots for each phase across runs."""
    phases_present = set()
    for run_name, run_data in throughput_data_dict.items():
        for phase, phase_data in run_data.items():
            if phase_data["times"].any():
                 phases_present.add(phase)

    phase_order = ["CREATE", "UPDATE", "DELETE"]
    sorted_phases = [p for p in phase_order if p in phases_present]

    if not sorted_phases:
        logging.warning("No throughput data available to plot for any phase in any run.")
        return

    num_phases = len(sorted_phases)
    fig, axes = plt.subplots(num_phases, 1, figsize=(10, 5 * num_phases), sharex=False, squeeze=False)
    axes = axes.flatten()
    fig.suptitle('Throughput Comparison: Cumulative Operations Completed vs. Time', fontsize=16)

    styles = {
        "Baseline": {"linestyle": '-', "color": "blue", "marker": "o", "markersize": 3},
        "Instrumented": {"linestyle": '-', "color": "red", "marker": "x", "markersize": 4}
    }
    default_style = {"linestyle": ':', "color": "grey", "marker": ".", "markersize": 2}

    for i, phase in enumerate(sorted_phases):
        ax = axes[i]
        max_time_phase = 0
        max_count_phase = 0

        for run_name, run_data in throughput_data_dict.items():
            phase_data = run_data.get(phase)
            if phase_data and phase_data["times"].any():
                times = phase_data["times"]
                counts = phase_data["counts"]
                plot_times = np.concatenate(([0], times))
                plot_counts = np.concatenate(([0], counts))
                style = styles.get(run_name, default_style)
                ax.step(plot_times, plot_counts, where='post', label=f"{run_name} (n={counts[-1] if len(counts)>0 else 0})", **style)
                max_time_phase = max(max_time_phase, times[-1] if len(times)>0 else 0)
                max_count_phase = max(max_count_phase, counts[-1] if len(counts)>0 else 0)

        ax.set_title(f'{phase} Phase Throughput')
        ax.set_xlabel('Time Since Phase Start (seconds)')
        ax.set_ylabel(f'Cumulative Successful {phase}s')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_xlim(left=0, right=max_time_phase * 1.05 if max_time_phase > 0 else 10)
        ax.set_ylim(bottom=0, top=max_count_phase * 1.1 if max_count_phase > 0 else 10)
        if len(throughput_data_dict) > 1:
             ax.legend()

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    try:
        plt.savefig(output_png_filename)
        logging.info(f"Throughput comparison plot saved to {output_png_filename}")
    except Exception as e:
        logging.error(f"Failed to save throughput plot to {output_png_filename}: {e}")
    plt.close(fig)

def extract_latency_data_for_boxplot(all_run_data_dict: dict) -> pd.DataFrame | None:
    """
    Extracts and combines latency data from multiple runs into a single DataFrame
    suitable for box plotting.

    Args:
        all_run_data_dict (dict): A dictionary where keys are run names (e.g., "Baseline")
                                  and values are the loaded data dictionaries for that run.

    Returns:
        pd.DataFrame | None: A DataFrame with columns like 'run_name', 'operation_type',
                              'e2e_latency_seconds', or None if no valid data.
    """
    latency_records = []
    for run_name, run_data in all_run_data_dict.items():
        operation_results = run_data.get("operation_results", [])
        for res in operation_results:
            op_type = res.get("operation_type")
            latency = res.get("e2e_latency_seconds") # Already float or None
            status = res.get("status")

            if status == "SUCCESS" and op_type and latency is not None:
                latency_records.append({
                    "run_name": run_name,
                    "operation_type": op_type,
                    "e2e_latency_seconds": latency
                })

    if not latency_records:
        logging.warning("No successful operations with latency data found for box plots.")
        return None

    return pd.DataFrame(latency_records)

def plot_latency_box_plots(latency_df: pd.DataFrame, output_png_filename: str):
    """
    Generates box plots for latency data, comparing runs if multiple are present.
    Plots latencies for CREATE, UPDATE, DELETE operations side-by-side.
    """
    if latency_df is None or latency_df.empty:
        logging.warning("No latency data to plot for box plots.")
        return

    # Filter for relevant operation types if necessary, though usually we plot all available
    plot_order = ["CREATE", "UPDATE", "DELETE"]
    latency_df_filtered = latency_df[latency_df['operation_type'].isin(plot_order)]

    if latency_df_filtered.empty:
        logging.warning(f"No latency data for operations {plot_order}. Cannot create box plot.")
        return

    plt.figure(figsize=(12, 7)) # Adjust as needed

    # hue will differentiate between 'Baseline' and 'Instrumented' runs
    sns.boxplot(x='operation_type', y='e2e_latency_seconds', hue='run_name',
                data=latency_df_filtered, order=plot_order, palette="pastel")

    plt.title('E2E Latency Distribution by Operation Type and Run', fontsize=16)
    plt.xlabel('Operation Type', fontsize=12)
    plt.ylabel('E2E Latency (seconds)', fontsize=12)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Run Type')
    plt.tight_layout()

    try:
        plt.savefig(output_png_filename)
        logging.info(f"Latency box plots saved to {output_png_filename}")
    except Exception as e:
        logging.error(f"Failed to save latency box plot to {output_png_filename}: {e}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Plot E2E latency results comparison.")
    parser.add_argument(
        "--baseline-suffix", type=str, required=True,
        help="Suffix used for the baseline run's output files (e.g., 'baseline_v1')."
    )
    parser.add_argument(
        "--instrumented-suffix", type=str, default=None,
        help="Suffix used for the instrumented/comparison run's output files (e.g., 'instrumented_v2'). Optional."
    )
    parser.add_argument(
        "--output-png", type=str, required=True,
        help="Path to save the output PNG plot file."
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable DEBUG level logging."
    )
    parser.add_argument(
        "--results-base-name", type=str, default="e2e_latency_results",
        help="Base filename for the results files (default: e2e_latency_results)."
    )
    # New flag for box plots
    parser.add_argument(
        "--create-box-plots",
        action="store_true",
        help="If set, create box plots of latencies. Otherwise, plot throughput curves."
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.getLogger().setLevel(log_level)

    logging.info(f"--- Loading Baseline Data (Suffix: {args.baseline_suffix}) ---")
    baseline_data = load_run_data(args.baseline_suffix, args.results_base_name)
    if not baseline_data:
        logging.error("Failed to load baseline data. Exiting.")
        sys.exit(1)

    all_run_data_dict = {"Baseline": baseline_data}

    if args.instrumented_suffix:
        logging.info(f"--- Loading Instrumented Data (Suffix: {args.instrumented_suffix}) ---")
        instrumented_data = load_run_data(args.instrumented_suffix, args.results_base_name)
        if not instrumented_data:
             logging.warning("Failed to load instrumented data. Plotting will only show baseline.")
        else:
             all_run_data_dict["Instrumented"] = instrumented_data

    if args.create_box_plots:
        logging.info("Box plot generation requested.")
        latency_df_for_boxplot = extract_latency_data_for_boxplot(all_run_data_dict)
        if latency_df_for_boxplot is not None and not latency_df_for_boxplot.empty:
            plot_latency_box_plots(latency_df_for_boxplot, args.output_png)
        else:
            logging.error("Could not generate latency data for box plots. No plot created.")
    else:
        logging.info("Throughput curve generation requested.")
        all_throughput_data = {}
        for run_name, run_data in all_run_data_dict.items():
            logging.info(f"Calculating throughput for {run_name} run...")
            operation_results = run_data.get("operation_results", [])
            phase_timestamps = run_data.get("phase_timestamps", {})
            if not operation_results or not phase_timestamps:
                 logging.warning(f"Missing operation results or phase timestamps for {run_name}. Skipping throughput calculation.")
                 continue
            all_throughput_data[run_name] = calculate_throughput_data(operation_results, phase_timestamps)

        if all_throughput_data:
            plot_throughput_comparison(all_throughput_data, args.output_png)
        else:
            logging.error("No throughput data could be calculated for any run. No plot generated.")

    logging.info("Plotting script finished.")

if __name__ == "__main__":
    main()