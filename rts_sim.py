#!/usr/bin/env python3
"""
Real-Time Scheduling Simulator - Enhanced CLI Interface
Command-line interface supporting 'sim' and 'gen' modes
"""

import sys
import argparse
from parser import TaskFileParser, ParseError, TaskSet
from scheduler import SchedulerFactory
from aperiodic_server import ServerFactory
from simulator import Simulator, SimulationConfig


class OutputFormatter:
    """Handles different output verbosity levels"""

    def __init__(self, mode: str = 'minimal'):
        """
        mode: 'minimal', 'detailed' (-d), or 'verbose' (-v)
        """
        self.mode = mode

    def print_header(self, scheduler_name: str, task_count: int):
        """Print simulation header"""
        if self.mode == 'minimal':
            print(f"Scheduler: {scheduler_name}")
        elif self.mode == 'detailed':
            print("=" * 70)
            print(f"Real-Time Scheduling Simulation".center(70))
            print("=" * 70)
            print(f"Scheduler: {scheduler_name}")
            print(f"Total Tasks: {task_count}")
            print("=" * 70)
        elif self.mode == 'verbose':
            print("=" * 70)
            print(f"Real-Time Scheduling Simulation - VERBOSE MODE".center(70))
            print("=" * 70)
            print(f"Scheduler: {scheduler_name}")
            print(f"Total Tasks Loaded: {task_count}")
            print("=" * 70)

    def print_task_set(self, task_set: TaskSet):
        """Print task set information"""
        if self.mode == 'minimal':
            return

        print("\nTask Set:")
        print("-" * 70)

        if task_set.periodic_tasks:
            print("\nPeriodic Tasks:")
            print(f"{'ID':<6} {'Release':<10} {'Exec':<10} {'Period':<10} {'Deadline':<10}")
            print("-" * 50)
            for task in task_set.periodic_tasks:
                print(f"{task.id:<6} {task.release_time:<10.2f} {task.execution_time:<10.2f} "
                      f"{task.period:<10.2f} {task.deadline:<10.2f}")

        if task_set.dynamic_tasks:
            print("\nDynamic Tasks:")
            print(f"{'ID':<6} {'Exec':<10} {'Period':<10} {'Deadline':<10}")
            print("-" * 40)
            for task in task_set.dynamic_tasks:
                print(f"{task.id:<6} {task.execution_time:<10.2f} "
                      f"{task.period:<10.2f} {task.deadline:<10.2f}")

        if task_set.aperiodic_tasks:
            print("\nAperiodic Tasks:")
            print(f"{'ID':<6} {'Release':<10} {'Exec':<10}")
            print("-" * 30)
            for task in task_set.aperiodic_tasks:
                print(f"{task.id:<6} {task.release_time:<10.2f} {task.execution_time:<10.2f}")

    def print_events(self, events: list):
        """Print scheduling events"""
        if self.mode == 'minimal':
            return

        if self.mode == 'detailed':
            print("\nKey Scheduling Events (first 20):")
            print("-" * 70)
            for event in events[:20]:
                print(event)
            if len(events) > 20:
                print(f"... and {len(events) - 20} more events")

        elif self.mode == 'verbose':
            print("\n\nAll Scheduling Events:")
            print("-" * 70)
            for event in events:
                print(event)

    def print_results(self, stats: dict, utilization: dict):
        """Print final results"""
        print("\n")
        print("=" * 70)
        print("SIMULATION RESULTS".center(70))
        print("=" * 70)

        # Task completion summary
        print(f"\nTask Completion:")
        print(f"  Total Tasks:       {stats['total_tasks']}")
        print(f"  Completed:         {stats['completed_tasks']}")
        print(f"  Missed Deadlines:  {stats['missed_deadlines']}")
        print(f"  Success Rate:      {stats['success_rate']:.2f}%")

        # Schedulability result
        if stats['missed_deadlines'] == 0:
            print(f"\n  [OK] ALL TASKS SCHEDULABLE")
        else:
            print(f"\n  [FAIL] SOME TASKS MISSED DEADLINES")

        if self.mode in ['detailed', 'verbose']:
            # Timing statistics
            if 'avg_response_time' in stats:
                print(f"\nTiming Statistics:")
                print(f"  Avg Response Time:   {stats['avg_response_time']:.2f}")
                print(f"  Max Response Time:   {stats['max_response_time']:.2f}")
                if 'avg_completion_time' in stats:
                    print(f"  Avg Completion Time: {stats['avg_completion_time']:.2f}")

            # Utilization analysis
            print(f"\nUtilization Analysis:")
            print(f"  Total Utilization:     {utilization['total_utilization']:.4f}")
            print(f"  RM Schedulable:        {'Yes' if utilization['schedulable_rm'] else 'No'}")
            print(f"  EDF Schedulable:       {'Yes' if utilization['schedulable_edf'] else 'No'}")

        print("=" * 70)


def simulate(args):
    """Run simulation mode"""
    # Parse arguments
    algorithm = args.algorithm.upper()
    view_mode = 'minimal'
    if args.detailed:
        view_mode = 'detailed'
    elif args.verbose:
        view_mode = 'verbose'

    formatter = OutputFormatter(view_mode)

    # Read from stdin or file
    if args.input:
        input_file = args.input
    else:
        # Read from stdin
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write(sys.stdin.read())
            input_file = tmp.name

    try:
        # Load task set
        task_set = TaskFileParser.parse_file(input_file)

        # Create scheduler
        try:
            scheduler = SchedulerFactory.create_scheduler(algorithm)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            print(f"Available schedulers: RM, EDF, DM, FCFS, SJF, LST", file=sys.stderr)
            sys.exit(1)

        # Print header
        formatter.print_header(scheduler.name, len(task_set.tasks))

        # Print task set
        formatter.print_task_set(task_set)

        # Configure simulation
        sim_time = args.time if args.time else 100
        context_switch = args.context_switch if args.context_switch else 0

        config = SimulationConfig(
            simulation_time=sim_time,
            time_quantum=0.5,
            preemptive=True,
            context_switch_overhead=context_switch
        )

        # Create and run simulator
        simulator = Simulator(scheduler, config)
        simulator.load_task_set(task_set)

        if view_mode == 'verbose':
            print("\nRunning simulation...")

        results = simulator.run()

        # Calculate utilization
        utilization = simulator.calculate_utilization()

        # Print events
        formatter.print_events(simulator.scheduler.schedule_events)

        # Print results
        formatter.print_results(results, utilization)

    except ParseError as e:
        print(f"Parse Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        if view_mode == 'verbose':
            traceback.print_exc()
        sys.exit(1)


def generate(args):
    """Run generation mode"""
    try:
        from generator import TaskGenerator
    except ImportError:
        print("Error: generator.py not found. Generator mode is not available.", file=sys.stderr)
        sys.exit(1)

    # Parse arguments
    num_tasks = args.num_tasks if args.num_tasks else None
    if args.random:
        import random
        num_tasks = random.randint(5, 10)
    elif not num_tasks:
        num_tasks = 5

    # Determine settings
    if args.detailed:
        import random
        context_switch = args.context_switch if args.context_switch else random.uniform(0.1, 0.5)
        varied_arrivals = True
    else:
        context_switch = args.context_switch if args.context_switch else 0
        varied_arrivals = False

    utilization = args.utilization if args.utilization else 0.7

    # Create generator
    generator = TaskGenerator(
        num_tasks=num_tasks,
        context_switch=context_switch,
        varied_arrivals=varied_arrivals,
        target_utilization=utilization
    )

    # Generate and output
    if args.output:
        generator.write_to_file(args.output)
        print(f"Generated {num_tasks} tasks to {args.output}", file=sys.stderr)
    else:
        # Print to stdout
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            generator.write_to_file(tmp.name)
            with open(tmp.name, 'r') as f:
                print(f.read())


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Real-Time Scheduling Simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Simulate with RM algorithm from file
  python rts_sim.py sim -a RM -i example1_simple.txt

  # Simulate with EDF, detailed output
  python rts_sim.py sim -d -a EDF -i tasks.txt

  # Generate 10 tasks
  python rts_sim.py gen -n 10 -o tasks.txt

  # Generate and simulate
  python rts_sim.py gen -n 8 | python rts_sim.py sim -a EDF -v
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Simulation command
    sim_parser = subparsers.add_parser('sim', help='Run simulation')
    sim_parser.add_argument('-a', '--algorithm', required=True,
                            choices=['RM', 'EDF', 'DM', 'FCFS', 'SJF', 'LST'],
                            help='Scheduling algorithm')
    sim_parser.add_argument('-i', '--input', type=str,
                            help='Input file (if not specified, reads from stdin)')
    sim_parser.add_argument('-d', '--detailed', action='store_true',
                            help='Detailed output')
    sim_parser.add_argument('-v', '--verbose', action='store_true',
                            help='Verbose output (shows all events)')
    sim_parser.add_argument('-t', '--time', type=float,
                            help='Simulation time (default: 100)')
    sim_parser.add_argument('-c', '--context-switch', type=float,
                            help='Context switch overhead (default: 0)')

    # Generation command
    gen_parser = subparsers.add_parser('gen', help='Generate task file')
    gen_parser.add_argument('-n', '--num-tasks', type=int,
                            help='Number of tasks (minimum 5)')
    gen_parser.add_argument('-r', '--random', action='store_true',
                            help='Random number of tasks (5-10)')
    gen_parser.add_argument('-d', '--detailed', action='store_true',
                            help='Enable context switching and varied arrivals')
    gen_parser.add_argument('-c', '--context-switch', type=float,
                            help='Context switch overhead')
    gen_parser.add_argument('-u', '--utilization', type=float,
                            help='Target utilization (default: 0.7)')
    gen_parser.add_argument('-o', '--output', type=str,
                            help='Output file (if not specified, prints to stdout)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'sim':
        simulate(args)
    elif args.command == 'gen':
        generate(args)


if __name__ == "__main__":
    main()
