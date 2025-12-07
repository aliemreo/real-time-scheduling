"""
Terminal Visualization Integration
Integrates the ANSI terminal visualization with the RTS simulator
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
from scheduler import ScheduleEvent

# ANSI helpers
def bg_rgb(r, g, b): return f"\x1b[48;2;{r};{g};{b}m"
def fg_rgb(r, g, b): return f"\x1b[38;2;{r};{g};{b}m"
RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"

# Data structures
@dataclass
class VisTask:
    """Task definition for visualization"""
    name: str
    arrivals: List[int]
    color: Tuple[int, int, int]

@dataclass
class SchedulingResults:
    """Container for scheduling results"""
    tasks: List[VisTask]
    time_slots: int
    cpu_schedule: List[str]
    preemptions: List[int]
    deadline_status: Dict[str, Dict]
    scheduler_name: str = "Unknown"


class SimulatorToVisualizationAdapter:
    """Converts simulator results to visualization format"""

    TASK_COLORS = [
        (220, 50, 50),   # Red
        (50, 100, 200),  # Blue
        (230, 180, 50),  # Yellow
        (60, 180, 80),   # Green
        (200, 100, 200), # Purple
        (255, 140, 0),   # Orange
        (100, 200, 200), # Cyan
        (200, 100, 100), # Pink
    ]

    def convert_from_simulator(self, simulator, max_time: int = None) -> SchedulingResults:
        """Convert simulator results to SchedulingResults format"""
        if max_time is None:
            max_time = int(simulator.config.simulation_time)

        # Convert tasks
        vis_tasks = self._convert_tasks(simulator.task_set, simulator.task_instances, max_time)

        # Build CPU schedule
        cpu_schedule = self._build_cpu_schedule(simulator.scheduler.schedule_events, max_time)

        # Detect preemptions
        preemptions = []
        for event in simulator.scheduler.schedule_events:
            time_idx = int(event.time)
            if time_idx < max_time and event.event_type == 'PREEMPT':
                preemptions.append(time_idx)

        # Build deadline status
        deadline_status = self._build_deadline_status(
            vis_tasks,
            simulator.scheduler.completed_tasks,
            simulator.scheduler.missed_deadlines
        )

        return SchedulingResults(
            tasks=vis_tasks,
            time_slots=max_time,
            cpu_schedule=cpu_schedule,
            preemptions=preemptions,
            deadline_status=deadline_status,
            scheduler_name=simulator.scheduler.name
        )

    def _convert_tasks(self, task_set, task_instances, max_time) -> List[VisTask]:
        """Convert task set to visualization tasks"""
        vis_tasks = []

        # Group instances by task ID
        task_groups = {}
        for instance in task_instances:
            task_id = instance.task.id
            if task_id not in task_groups:
                task_groups[task_id] = []
            task_groups[task_id].append(instance)

        # Create vis tasks
        color_idx = 0
        for task_id in sorted(task_groups.keys()):
            instances = task_groups[task_id]
            task = instances[0].task

            # Collect arrivals within time window
            arrivals = [int(inst.current_release) for inst in instances
                       if inst.current_release < max_time]

            # Use the task's actual representation (P1, D1, A1 etc.)
            name = str(task).split('@')[0] if '@' in str(task) else str(task)

            vis_tasks.append(VisTask(
                name=name,
                arrivals=arrivals,
                color=self.TASK_COLORS[color_idx % len(self.TASK_COLORS)]
            ))
            color_idx += 1

        return vis_tasks

    def _build_cpu_schedule(self, events: List[ScheduleEvent], max_time: int) -> List[str]:
        """Build CPU schedule array"""
        schedule = ["IDLE"] * max_time

        current_task = None
        start_time = 0

        for event in events:
            if event.event_type == 'START' and event.task:
                current_task = event.task
                start_time = int(event.time)
            elif event.event_type in ['COMPLETE', 'PREEMPT', 'DEADLINE_MISS'] and current_task:
                end_time = min(int(event.time), max_time)
                task_name = str(current_task.task).split('@')[0]

                # Fill schedule
                for t in range(start_time, end_time):
                    if t < max_time:
                        schedule[t] = task_name

                if event.event_type in ['COMPLETE', 'DEADLINE_MISS']:
                    current_task = None

        return schedule

    def _build_deadline_status(self, vis_tasks: List[VisTask],
                               completed: List, missed: List) -> Dict[str, Dict]:
        """Build deadline status for each task"""
        status = {}

        # Count missed deadlines per task
        missed_counts = {}
        for task_inst in missed:
            task_name = str(task_inst.task).split('@')[0]
            missed_counts[task_name] = missed_counts.get(task_name, 0) + 1

        for vis_task in vis_tasks:
            missed_count = missed_counts.get(vis_task.name, 0)

            if missed_count > 0:
                status[vis_task.name] = {
                    'icon': 'X',
                    'status': f'{missed_count} deadline(s) missed',
                    'color': 'red'
                }
            else:
                # Check if any were completed
                completed_count = sum(1 for t in completed
                                     if str(t.task).split('@')[0] == vis_task.name)
                if completed_count > 0:
                    status[vis_task.name] = {
                        'icon': 'OK',
                        'status': 'All deadlines met',
                        'color': 'green'
                    }
                else:
                    status[vis_task.name] = {
                        'icon': '-',
                        'status': 'No instances scheduled',
                        'color': 'yellow'
                    }

        return status


def visualize_schedule(results: SchedulingResults):
    """Visualize scheduling results with ANSI terminal graphics"""

    # Header
    print(f"\n{BOLD}+{'=' * 70}+{RESET}")
    print(f"{BOLD}|{' ' * 20}REAL-TIME SCHEDULING ANALYZER{' ' * 21}|{RESET}")
    print(f"{BOLD}+{'=' * 70}+{RESET}\n")

    # Task arrivals
    _print_task_arrivals(results)

    # Execution timeline
    _print_execution_timeline(results)

    # Statistics
    _print_statistics(results)

    # Deadline analysis
    _print_deadline_analysis(results)

    # Legend
    _print_legend(results)

    print(f"\n{DIM}Scheduler: {results.scheduler_name}{RESET}\n")


def _print_task_arrivals(results: SchedulingResults):
    """Print task arrival events"""
    print(f"{BOLD}TASK ARRIVALS{RESET}")
    max_display = min(results.time_slots, 40)
    print("Time Slot      | " + "".join(f"{t:2d} " for t in range(max_display)))
    print("---------------+-" + "-" * (max_display * 3))

    for task in results.tasks:
        line = f"{task.name:14s} | "
        for t in range(max_display):
            if t in task.arrivals:
                r, g, b = task.color
                line += f"{fg_rgb(r, g, b)}^{RESET}  "
            else:
                line += f"{DIM}.{RESET}  "
        print(line)

    print("---------------+-" + "-" * (max_display * 3))


def _print_execution_timeline(results: SchedulingResults):
    """Print execution timeline"""
    print(f"\n{BOLD}EXECUTION TIMELINE{RESET}")
    max_display = min(results.time_slots, 40)

    # Show context switches
    if results.preemptions:
        switch_line = "Context Switch | "
        for t in range(max_display):
            if t in results.preemptions:
                switch_line += f"{fg_rgb(230, 180, 50)}@{RESET}  "
            else:
                switch_line += f"{DIM}.{RESET}  "
        print(switch_line)

    # CPU Timeline
    exec_line = "CPU Timeline   | "
    for t in range(max_display):
        if t < len(results.cpu_schedule):
            cpu_task = results.cpu_schedule[t]

            if cpu_task == "IDLE":
                exec_line += f"{bg_rgb(150, 150, 150)}   {RESET}"
            else:
                task = next((ta for ta in results.tasks if ta.name == cpu_task), None)
                if task:
                    r, g, b = task.color
                    exec_line += f"{bg_rgb(r, g, b)}   {RESET}"
                else:
                    exec_line += f"{bg_rgb(150, 150, 150)}   {RESET}"

    print(exec_line)
    time_axis = "Time Slot      | " + "".join(f"{t:2d} " for t in range(max_display))
    print(time_axis)


def _print_statistics(results: SchedulingResults):
    """Print scheduling statistics"""
    print(f"\n{BOLD}SCHEDULING STATISTICS{RESET}")

    total_slots = results.time_slots
    idle_slots = sum(1 for u in results.cpu_schedule if u == "IDLE")
    cpu_util = 100 * (total_slots - idle_slots) / total_slots if total_slots > 0 else 0

    print(f"  CPU Utilization:  {cpu_util:.1f}%")
    print(f"  Total Time Slots: {total_slots}")
    print(f"  Idle Slots:       {idle_slots}")

    # Task execution time
    print(f"\n{BOLD}TASK EXECUTION TIME{RESET}")
    task_counts = {}
    for task in results.tasks:
        count = sum(1 for u in results.cpu_schedule if u == task.name)
        task_counts[task.name] = count

    for task_name, count in sorted(task_counts.items()):
        pct = 100 * count / total_slots if total_slots > 0 else 0
        bar_width = 30
        filled = int(bar_width * count / total_slots) if total_slots > 0 else 0
        bar = "#" * filled + "-" * (bar_width - filled)

        task = next((t for t in results.tasks if t.name == task_name), None)
        if task:
            r, g, b = task.color
            print(f"  {task_name}:  {fg_rgb(r, g, b)}[{bar}]{RESET} {count:2d} slots ({pct:4.1f}%)")


def _print_deadline_analysis(results: SchedulingResults):
    """Print deadline analysis"""
    print(f"\n{BOLD}DEADLINE ANALYSIS{RESET}")

    color_map = {'green': (60, 180, 80), 'yellow': (230, 180, 50), 'red': (220, 50, 50)}

    for task in results.tasks:
        info = results.deadline_status[task.name]
        c = color_map[info['color']]
        print(f"  {fg_rgb(*c)}{info['icon']}{RESET} {task.name}: {info['status']}")


def _print_legend(results: SchedulingResults):
    """Print legend"""
    print(f"\n{BOLD}LEGEND{RESET}")
    print(f"  Tasks:   ", end="")
    for i, task in enumerate(results.tasks):
        r, g, b = task.color
        print(f"{bg_rgb(r, g, b)}  {RESET} {task.name}  ", end="")
        if (i + 1) % 4 == 0 and i < len(results.tasks) - 1:
            print()
            print(f"           ", end="")
    print()

    print(f"  Symbols: {fg_rgb(220, 50, 50)}^{RESET} Arrival  ", end="")
    if any(results.preemptions):
        print(f"{fg_rgb(230, 180, 50)}@{RESET} Context Switch", end="")
    print()
