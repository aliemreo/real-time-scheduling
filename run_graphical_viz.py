import sys
import subprocess
import re
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

def run_cpp_simulation(input_file):
    """
    Compiles and runs the C++ simulation.
    """
    executable_name = "run_ali"
    if sys.platform == "win32":
        executable_name += ".exe"

    # Run the compiled C++ executable
    executable_path = f".{os.path.sep}{executable_name}"
    try:
        print(f"[INFO] Running C++ simulation: {executable_path} {input_file}")
        process = subprocess.run(
            [executable_path, input_file],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[SUCCESS] Simulation completed successfully\n")
        return process.stdout
    except FileNotFoundError:
        print(f"\n[ERROR] Executable '{executable_path}' not found.")
        print("Please make sure 'run_ali.cpp' is compiled.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] The C++ program crashed or returned an error.")
        print(f"--- C++ stdout ---\n{e.stdout}")
        print(f"--- C++ stderr ---\n{e.stderr}")
        sys.exit(1)

def parse_cpp_output(output):
    """
    Parses the C++ output and extracts scheduling information.
    Returns schedules with task execution intervals and job information.
    """
    schedules = {}
    summaries = {}
    current_scheduler = None
    in_schedule_section = False
    in_summary_section = False

    # Track job releases and deadlines
    job_info = {}  # {scheduler: [(time, task, event_type)]}

    for line in output.splitlines():
        if line.startswith("=== ") and " Scheduling ===" in line:
            current_scheduler = line.strip("= ")
            schedules[current_scheduler] = []
            summaries[current_scheduler] = {'completed': 0, 'missed': 0, 'missed_details': ''}
            job_info[current_scheduler] = []
            in_schedule_section = False
            in_summary_section = False
            continue

        if current_scheduler and "Time\tTask\tAction" in line:
            in_schedule_section = True
            in_summary_section = False
            continue

        if line.startswith("Summary:"):
            in_schedule_section = False
            in_summary_section = True
            continue

        if in_summary_section and current_scheduler:
            if "Completed jobs:" in line:
                try:
                    summaries[current_scheduler]['completed'] = int(line.split(':')[1].strip())
                except:
                    pass
            elif "Missed deadlines:" in line:
                try:
                    summaries[current_scheduler]['missed'] = int(line.split(':')[1].strip())
                except:
                    pass
            elif "Deadline misses for tasks:" in line:
                summaries[current_scheduler]['missed_details'] = line.split(':', 1)[1].strip()

        if not line.strip():
            in_schedule_section = False
            continue

        if in_schedule_section:
            parts = line.split()
            if len(parts) >= 2:
                try:
                    time = float(parts[0])
                    task_name = parts[1]
                    schedules[current_scheduler].append((time, task_name))
                except (ValueError, IndexError):
                    continue

    return schedules, summaries, job_info

def draw_graphical_schedule(scheduler_name, events, total_duration, summary=None, output_file=None):
    """
    Creates a graphical Gantt chart matching the reference image style.
    """
    if not events:
        print(f"No events to visualize for {scheduler_name}")
        return

    # Convert events to intervals
    intervals = []
    for i in range(len(events)):
        start_time = int(events[i][0])
        task_name = events[i][1]
        end_time = int(total_duration)
        if i + 1 < len(events):
            end_time = int(events[i+1][0])
        intervals.append({'task': task_name, 'start': start_time, 'end': end_time})

    # Get unique tasks (excluding IDLE)
    tasks = sorted(list(set(item['task'] for item in intervals if item['task'] != 'IDLE')))

    # Task colors - matching the reference image
    task_colors = {
        'T1(P)': '#C0392B',  # Dark Red
        'T1(D)': '#C0392B',
        'T2(P)': '#2980B9',  # Navy Blue
        'T2(D)': '#2980B9',
        'T3(P)': '#F39C12',  # Orange/Yellow
        'T3(D)': '#F39C12',
        'T4(P)': '#27AE60',  # Green
        'T4(D)': '#27AE60',
        'T1(A)': '#C0392B',
        'T2(A)': '#2980B9',
        'T3(A)': '#F39C12',
        'T4(A)': '#27AE60',
    }

    # Patterns for tasks (matching screenshot)
    task_patterns = {
        'T1(P)': None, 'T1(D)': None, 'T1(A)': None,
        'T2(P)': None, 'T2(D)': None, 'T2(A)': None,
        'T3(P)': '///', 'T3(D)': '///', 'T3(A)': '///',
        'T4(P)': 'xxx', 'T4(D)': 'xxx', 'T4(A)': 'xxx',
    }

    # Create figure - matching screenshot aspect ratio
    fig, ax = plt.subplots(figsize=(18, 6))

    # Set up the plot area
    arrow_section_height = 2.5  # Height for arrows
    timeline_bar_height = 0.8
    bottom_margin = 0.5

    ax.set_xlim(-0.5, total_duration + 0.5)
    ax.set_ylim(0, arrow_section_height + timeline_bar_height + bottom_margin)

    # Draw vertical grid lines
    for t in range(0, total_duration + 1):
        ax.axvline(x=t, color='#CCCCCC', linestyle='-', linewidth=0.8, alpha=0.6, zorder=0)

    # Draw horizontal grid lines
    for y in np.arange(0, arrow_section_height + timeline_bar_height + bottom_margin, 0.25):
        ax.axhline(y=y, color='#E0E0E0', linestyle='-', linewidth=0.5, alpha=0.4, zorder=0)

    # SECTION 1: Draw arrows at the top (arrivals and deadlines)
    arrow_y_base = arrow_section_height
    arrow_height = 0.6

    for idx, task in enumerate(tasks):
        y_offset = arrow_y_base - (idx * 0.7)
        color = task_colors.get(task, '#95A5A6')

        # Determine period (simplified - would need to parse from input)
        if 'T1' in task:
            period = 4
            release = 0
        elif 'T2' in task:
            period = 6
            release = 0
        elif 'T3' in task:
            period = 12
            release = 0
        else:
            period = 8
            release = 0

        # Draw arrival arrows (solid up arrows)
        for t in range(release, total_duration, period):
            ax.arrow(t, y_offset - arrow_height/2, 0, arrow_height,
                    head_width=0.3, head_length=0.15, fc=color, ec=color, lw=2, zorder=5)

        # Draw deadline arrows (dashed down arrows)
        for t in range(release + period, total_duration + 1, period):
            # Dashed line going down
            ax.plot([t, t], [y_offset, y_offset - arrow_height],
                   color=color, linestyle='--', linewidth=1.5, zorder=4)
            # Arrow head
            ax.arrow(t, y_offset - arrow_height + 0.15, 0, -0.15,
                    head_width=0.3, head_length=0.15, fc=color, ec=color, lw=1.5, zorder=5)

    # SECTION 2: Draw the timeline bar at the bottom
    timeline_y = bottom_margin

    for interval in intervals:
        task = interval['task']
        start = interval['start']
        end = interval['end']

        if task == 'IDLE':
            # IDLE sections in light gray
            color = '#ECEFF1'
            hatch = None
            edgecolor = '#B0BEC5'
        else:
            color = task_colors.get(task, '#95A5A6')
            hatch = task_patterns.get(task, None)
            edgecolor = '#34495E'

        rect = Rectangle((start, timeline_y), end - start, timeline_bar_height,
                        facecolor=color, edgecolor=edgecolor, linewidth=1.2,
                        hatch=hatch, alpha=0.85, zorder=3)
        ax.add_patch(rect)

    # Add time axis at top
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(range(0, total_duration + 1))
    ax2.set_xticklabels(range(0, total_duration + 1), fontsize=9)
    ax2.tick_params(axis='x', which='both', length=0)

    # Add time axis at bottom
    ax.set_xticks(range(0, total_duration + 1))
    ax.set_xticklabels(range(0, total_duration + 1), fontsize=9)
    ax.set_xlabel('Time Units (EPSITES)', fontsize=10, fontweight='bold')
    ax.tick_params(axis='x', which='both', length=0)

    # Remove y-axis
    ax.set_yticks([])
    ax.yaxis.set_visible(False)

    # Remove spines
    for spine in ['top', 'right', 'left', 'bottom']:
        ax.spines[spine].set_visible(False)
        ax2.spines[spine].set_visible(False)

    # Add title
    plt.suptitle(scheduler_name, fontsize=14, fontweight='bold', y=0.98)

    # Add legend for tasks
    legend_elements = []
    for task in tasks:
        color = task_colors.get(task, '#95A5A6')
        hatch = task_patterns.get(task, None)
        legend_elements.append(mpatches.Patch(facecolor=color, edgecolor='#34495E',
                                             hatch=hatch, label=task, linewidth=1.2))

    # Add IDLE to legend
    legend_elements.append(mpatches.Patch(facecolor='#ECEFF1', edgecolor='#B0BEC5',
                                         label='IDLE', linewidth=1.2))

    ax.legend(handles=legend_elements, loc='upper left', fontsize=9,
             framealpha=0.95, title='Tasks', ncol=len(legend_elements))

    # Add summary text box
    if summary:
        summary_text = f"Completed Jobs: {summary['completed']}  |  Missed Deadlines: {summary['missed']}"
        props = dict(boxstyle='round', facecolor='#FFF9C4', alpha=0.8, edgecolor='#F57C00')
        ax.text(0.98, 0.02, summary_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='bottom', horizontalalignment='right',
               bbox=props)

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=200, bbox_inches='tight', facecolor='white')
        print(f"  [OK] Saved: {output_file}")

    plt.close()  # Close instead of show to avoid blocking

def main():
    """
    Main function to run the simulation and create graphical visualization.
    """
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <input_file>")
        print(f"Example: python run_graphical_viz.py example_periodic.txt")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"[ERROR] Input file not found: {input_file}")
        sys.exit(1)

    print(f"{'='*80}")
    print(f"Real-Time Scheduling Simulator - Graphical Visualization".center(80))
    print(f"{'='*80}\n")
    print(f"Input File: {input_file}\n")

    # Run C++ simulation
    cpp_output = run_cpp_simulation(input_file)

    if not cpp_output:
        print(f"[ERROR] Failed to get output from C++ program.")
        sys.exit(1)

    # Parse output
    schedules, summaries, job_info = parse_cpp_output(cpp_output)

    if not schedules:
        print(f"[INFO] No schedules were found in the C++ program output.")
        return

    # Find maximum simulation time
    max_time = 0
    for events in schedules.values():
        if events:
            last_event_time = events[-1][0]
            if last_event_time > max_time:
                max_time = last_event_time

    total_sim_duration = 50
    if any("Poller" in s or "Deferable" in s for s in schedules.keys()):
        total_sim_duration = 30
    if max_time > total_sim_duration:
        total_sim_duration = int(max_time + 1)

    print(f"[INFO] Generating graphical visualizations (duration: {total_sim_duration} ticks)\n")

    # Create visualizations for each schedule
    for idx, (name, events) in enumerate(schedules.items()):
        summary = summaries.get(name, None)

        # Generate output filename
        output_file = f"schedule_{name.replace(' ', '_').replace('/', '_')}.png"

        print(f"Creating visualization {idx+1}/{len(schedules)}: {name}")
        draw_graphical_schedule(name, events, total_sim_duration, summary, output_file)

    print(f"\n{'='*80}")
    print(f"Visualization Complete!".center(80))
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
