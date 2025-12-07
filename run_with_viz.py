import sys
import subprocess
import re
import os

# Fix Windows console encoding for Unicode support
if sys.platform == "win32":
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors='replace')
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors='replace')
    except:
        pass

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)  # Initialize colorama for Windows support
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    print("[WARNING] colorama not installed. Run: pip install colorama for colored output")
    # Fallback empty color codes
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = LIGHTRED_EX = LIGHTGREEN_EX = LIGHTBLUE_EX = LIGHTMAGENTA_EX = LIGHTYELLOW_EX = LIGHTCYAN_EX = ""
    class Back:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = BLACK = ""
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ""

def print_header(text, char="=", color=Fore.CYAN):
    """Print a styled header"""
    width = 80
    print(f"\n{color}{Style.BRIGHT}{char * width}")
    print(f"{text.center(width)}")
    print(f"{char * width}{Style.RESET_ALL}\n")

def print_box(title, content, color=Fore.YELLOW):
    """Print content in a styled box"""
    width = 70
    print(f"{color}{Style.BRIGHT}┌{'─' * (width-2)}┐")
    print(f"│ {title.ljust(width-4)} │")
    print(f"├{'─' * (width-2)}┤{Style.RESET_ALL}")
    for line in content:
        print(f"{color}│{Style.RESET_ALL} {line.ljust(width-4)} {color}│{Style.RESET_ALL}")
    print(f"{color}└{'─' * (width-2)}┘{Style.RESET_ALL}")

def run_cpp_simulation(input_file):
    """
    Compiles and runs the C++ simulation.
    First, it tries to compile using 'make'.
    Then, it runs the executable with the provided input file and captures the output.
    """
    executable_name = "run_ali"
    if sys.platform == "win32":
        executable_name += ".exe"

    # Try to compile the C++ code using 'make'
    try:
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Trying to compile C++ code with 'make'...")
        # shell=True can be helpful, especially on Windows
        compile_process = subprocess.run("make", capture_output=True, text=True, shell=True)
        if compile_process.returncode != 0:
            # Make failed, print the error but continue, as exe might exist
            print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} 'make' command failed. Assuming executable already exists.")
            if compile_process.stdout:
                print(f"--- make stdout ---\n{compile_process.stdout}")
            if compile_process.stderr:
                print(f"--- make stderr ---\n{compile_process.stderr}")
        else:
            print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} 'make' completed successfully. ✓")
    except FileNotFoundError:
        print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} 'make' command not found. Assuming executable already exists.")

    # Run the compiled C++ executable
    executable_path = f".{os.path.sep}{executable_name}"
    try:
        print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} Running C++ simulation: {Style.BRIGHT}{executable_path}{Style.RESET_ALL} {input_file}")
        process = subprocess.run(
            [executable_path, input_file],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Simulation completed successfully ✓\n")
        return process.stdout
    except FileNotFoundError:
        print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} Executable '{executable_path}' not found.")
        print("Please make sure 'run_ali.cpp' is compiled (e.g., by running 'make' or 'g++').")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\n{Fore.RED}[ERROR]{Style.RESET_ALL} The C++ program crashed or returned an error.")
        print(f"--- C++ stdout ---\n{e.stdout}")
        print(f"--- C++ stderr ---\n{e.stderr}")
        sys.exit(1)

def parse_cpp_output(output):
    """
    Parses the full text output from the C++ simulator and separates
    it into distinct schedules for each algorithm.
    Also extracts summary statistics.
    """
    schedules = {}
    summaries = {}
    current_scheduler = None
    in_schedule_section = False
    in_summary_section = False

    for line in output.splitlines():
        # Check for a new scheduler header, e.g., "=== Rate Monotonic Scheduling ==="
        if line.startswith("=== ") and " Scheduling ===" in line:
            current_scheduler = line.strip("= ")
            schedules[current_scheduler] = []
            summaries[current_scheduler] = {'completed': 0, 'missed': 0, 'missed_details': ''}
            in_schedule_section = False
            in_summary_section = False
            continue

        # The line "Time  Task    Action" marks the start of the events for the current scheduler
        if current_scheduler and "Time\tTask\tAction" in line:
            in_schedule_section = True
            in_summary_section = False
            continue

        # "Summary:" marks the start of summary section
        if line.startswith("Summary:"):
            in_schedule_section = False
            in_summary_section = True
            continue

        # Parse summary statistics
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

        # An empty line ends sections
        if not line.strip():
            in_schedule_section = False
            continue

        # If we're in a schedule section, parse the event line
        if in_schedule_section:
            parts = line.split()
            if len(parts) >= 2:
                try:
                    time = int(parts[0])
                    task_name = parts[1]
                    schedules[current_scheduler].append((time, task_name))
                except (ValueError, IndexError):
                    # Ignore lines that don't fit the "time task ..." format
                    continue
    return schedules, summaries

def get_task_color(task_name):
    """Assign colors to different tasks"""
    if "IDLE" in task_name:
        return Fore.WHITE + Style.DIM
    elif "(P)" in task_name:  # Periodic
        return Fore.LIGHTGREEN_EX
    elif "(D)" in task_name:  # Dynamic
        return Fore.LIGHTMAGENTA_EX
    elif "(A)" in task_name:  # Aperiodic
        return Fore.LIGHTCYAN_EX
    else:
        # Assign colors based on task number
        colors = [Fore.LIGHTBLUE_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTRED_EX, Fore.LIGHTMAGENTA_EX]
        task_num = hash(task_name) % len(colors)
        return colors[task_num]

def draw_schedule_diagram(scheduler_name, events, total_duration, summary=None):
    """
    Draws an enhanced text-based Gantt chart for a single schedule with colors.
    """
    print_header(f"📊 {scheduler_name}", "═", Fore.CYAN)

    if not events:
        print(f"  {Fore.YELLOW}(No schedule events to draw.){Style.RESET_ALL}")
        return

    # Convert event start points into time intervals
    intervals = []
    for i in range(len(events)):
        start_time = events[i][0]
        task_name = events[i][1]
        # The end time is the start time of the next event, or the total duration
        end_time = total_duration
        if i + 1 < len(events):
            end_time = events[i+1][0]

        intervals.append({'task': task_name, 'start': start_time, 'end': end_time})

    # Get all unique task names, keeping IDLE at the bottom
    tasks = sorted(list(set(item['task'] for item in intervals)))
    if "IDLE" in tasks:
        tasks.remove("IDLE")
        tasks.append("IDLE")

    # Create the character grid for the diagram
    display_duration = min(total_duration, 120)  # Limit width to 120 chars
    diagram = {task: ['░'] * display_duration for task in tasks}

    for item in intervals:
        task = item['task']
        for t in range(item['start'], item['end']):
            if t < display_duration:
                diagram[task][t] = '█'

    max_task_len = max(len(task) for task in tasks) if tasks else 0

    # Print legend
    print(f"{Style.BRIGHT}Legend:{Style.RESET_ALL}")
    legend_items = []
    for task in tasks:
        if task != "IDLE":
            color = get_task_color(task)
            legend_items.append(f"{color}█{Style.RESET_ALL} {task}")

    # Print legend in columns
    if legend_items:
        num_cols = 4
        for i in range(0, len(legend_items), num_cols):
            print("  " + "  ".join(legend_items[i:i+num_cols]))
    print()

    # Print the diagram header
    print(f"{Style.BRIGHT}{'Task':<{max_task_len}} │ Timeline (time units){Style.RESET_ALL}")
    print(f"{'─' * max_task_len}─┼─{'─' * display_duration}")

    # Print the diagram rows with colors
    for task in tasks:
        row_chars = diagram[task]
        color = get_task_color(task)

        # Build colored row
        colored_row = ""
        current_char = row_chars[0]
        run_start = 0

        for i in range(1, len(row_chars) + 1):
            if i == len(row_chars) or row_chars[i] != current_char:
                # End of run, output it
                segment = current_char * (i - run_start)
                if current_char == '█':
                    colored_row += f"{color}{segment}{Style.RESET_ALL}"
                else:
                    colored_row += f"{Fore.WHITE}{Style.DIM}{segment}{Style.RESET_ALL}"

                if i < len(row_chars):
                    current_char = row_chars[i]
                    run_start = i

        task_label = f"{color}{Style.BRIGHT}{task}{Style.RESET_ALL}" if task != "IDLE" else f"{Fore.WHITE}{Style.DIM}{task}{Style.RESET_ALL}"
        print(f"{task_label:<{max_task_len + 20}} │ {colored_row}")

    # Print the time axis
    print(f"{'─' * max_task_len}─┴─{'─' * display_duration}")
    time_axis = "".join(str(i % 10) for i in range(display_duration))
    print(f"{' ' * max_task_len}   {Fore.CYAN}{time_axis}{Style.RESET_ALL}")

    if display_duration >= 10:
        # Tens markers
        tens_axis_formatted = ""
        for i in range(display_duration):
            if i % 10 == 0 and i > 0:
                tens_axis_formatted += str(i // 10)
            else:
                tens_axis_formatted += " "
        if tens_axis_formatted.strip():
            print(f"{' ' * max_task_len}   {Fore.CYAN}{Style.DIM}{tens_axis_formatted}{Style.RESET_ALL}")

    # Print summary statistics if available
    if summary:
        print()
        content = [
            f"✓ Completed Jobs:   {Fore.GREEN}{summary['completed']}{Style.RESET_ALL}",
            f"✗ Missed Deadlines: {Fore.RED if summary['missed'] > 0 else Fore.GREEN}{summary['missed']}{Style.RESET_ALL}"
        ]
        if summary['missed'] > 0 and summary['missed_details']:
            content.append(f"  Details: {Fore.YELLOW}{summary['missed_details']}{Style.RESET_ALL}")

        print_box("📈 Summary Statistics", content, Fore.YELLOW)
    print()

def main():
    """
    Main function to run the simulation and visualization.
    """
    if len(sys.argv) < 2:
        print(f"{Fore.RED}Usage:{Style.RESET_ALL} python {sys.argv[0]} <input_file_for_cpp_program>")
        print(f"{Fore.CYAN}Example:{Style.RESET_ALL} python run_with_viz.py example_periodic.txt")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Input file not found: {input_file}")
        sys.exit(1)

    # Print welcome banner
    print_header("🚀 Real-Time Scheduling Simulator with Visualization", "=", Fore.MAGENTA)
    print(f"{Style.BRIGHT}Input File:{Style.RESET_ALL} {Fore.CYAN}{input_file}{Style.RESET_ALL}\n")

    # 1. Run the C++ program and get its output
    cpp_output = run_cpp_simulation(input_file)

    if not cpp_output:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Failed to get output from C++ program.")
        sys.exit(1)

    # 2. Parse the output into separate schedules
    schedules, summaries = parse_cpp_output(cpp_output)

    if not schedules:
        print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} No schedules were found in the C++ program output.")
        return

    # 3. Find the maximum simulation time from all events to set the diagram's duration
    max_time = 0
    for events in schedules.values():
        if events:
            # The time of the last event gives a good estimate of the duration
            last_event_time = events[-1][0]
            if last_event_time > max_time:
                max_time = last_event_time

    # Use the hardcoded simulation time from the C++ file if possible, otherwise estimate
    # The C++ files use 50 for periodic and 30 for aperiodic
    total_sim_duration = 50
    if any("Poller" in s or "Deferable" in s for s in schedules.keys()):
        total_sim_duration = 30
    # Ensure the diagram is at least as long as the last event
    if max_time > total_sim_duration:
        total_sim_duration = max_time + 1

    print(f"\n{Fore.CYAN}[INFO]{Style.RESET_ALL} Generating diagrams with estimated total duration: {Style.BRIGHT}{total_sim_duration}{Style.RESET_ALL} ticks.")
    if total_sim_duration > 120:
        print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} Schedule duration is long, diagram will be truncated to 120 ticks.")

    # 4. Draw a diagram for each schedule found
    for name, events in schedules.items():
        summary = summaries.get(name, None)
        draw_schedule_diagram(name, events, total_sim_duration, summary)

    # 5. Print comparison summary
    if len(schedules) > 1:
        print_header("📊 Algorithm Comparison", "═", Fore.GREEN)
        comparison_data = []
        for name in schedules.keys():
            if name in summaries:
                s = summaries[name]
                status = f"{Fore.GREEN}✓ PASS{Style.RESET_ALL}" if s['missed'] == 0 else f"{Fore.RED}✗ FAIL{Style.RESET_ALL}"
                comparison_data.append(f"{name:<30} | Jobs: {s['completed']:3d} | Missed: {s['missed']:3d} | {status}")

        if comparison_data:
            print(f"{Style.BRIGHT}{'Algorithm':<30} | {'Jobs':<11} | {'Missed':<10} | Status{Style.RESET_ALL}")
            print("─" * 80)
            for line in comparison_data:
                print(line)
            print()

    print_header("✨ Visualization Complete!", "=", Fore.GREEN)

if __name__ == "__main__":
    main()