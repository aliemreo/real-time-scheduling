"""
Real-Time Scheduling Simulator - Main Interface
"""

import sys
from typing import Optional
from parser import TaskFileParser, ParseError, TaskSet
from scheduler import SchedulerFactory
from aperiodic_server import ServerFactory, AperiodicServer
from simulator import Simulator, SimulationConfig


class RTSchedulerUI:
    """Console-based user interface for the scheduler"""

    def __init__(self):
        self.task_set: Optional[TaskSet] = None
        self.simulator: Optional[Simulator] = None

    def run(self):
        """Main UI loop"""
        print("=" * 70)
        print("Real-Time Scheduling Simulator".center(70))
        print("=" * 70)
        print()

        while True:
            self.print_main_menu()
            choice = input("\nEnter your choice: ").strip()

            if choice == '1':
                self.load_task_file()
            elif choice == '2':
                self.display_task_set()
            elif choice == '3':
                self.configure_and_run_simulation()
            elif choice == '4':
                self.display_results()
            elif choice == '5':
                self.display_utilization()
            elif choice == '6':
                self.display_gantt_chart()
            elif choice == '7':
                print("\nThank you for using Real-Time Scheduling Simulator!")
                sys.exit(0)
            else:
                print("\n❌ Invalid choice. Please try again.")

            input("\nPress Enter to continue...")

    def print_main_menu(self):
        """Print main menu"""
        print("\n" + "=" * 70)
        print("MAIN MENU".center(70))
        print("=" * 70)
        print("1. Load Task File")
        print("2. Display Task Set")
        print("3. Configure and Run Simulation")
        print("4. Display Simulation Results")
        print("5. Display Utilization Analysis")
        print("6. Display Gantt Chart")
        print("7. Exit")
        print("=" * 70)

    def load_task_file(self):
        """Load task file"""
        print("\n" + "-" * 70)
        print("LOAD TASK FILE")
        print("-" * 70)

        filename = input("Enter task file path: ").strip()

        try:
            self.task_set = TaskFileParser.parse_file(filename)
            is_valid, errors = TaskFileParser.validate_task_set(self.task_set)

            if not is_valid:
                print("\n⚠️  Warning: Task set validation errors:")
                for error in errors:
                    print(f"  - {error}")
                proceed = input("\nProceed anyway? (y/n): ").strip().lower()
                if proceed != 'y':
                    self.task_set = None
                    return

            print(f"\n✓ Successfully loaded {len(self.task_set.tasks)} tasks")
            print(f"  - Periodic tasks: {len(self.task_set.periodic_tasks)}")
            print(f"  - Dynamic tasks: {len(self.task_set.dynamic_tasks)}")
            print(f"  - Aperiodic tasks: {len(self.task_set.aperiodic_tasks)}")

        except ParseError as e:
            print(f"\n❌ Error: {e}")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")

    def display_task_set(self):
        """Display loaded task set"""
        print("\n" + "-" * 70)
        print("TASK SET")
        print("-" * 70)

        if not self.task_set:
            print("No task set loaded. Please load a task file first.")
            return

        # Display periodic tasks
        if self.task_set.periodic_tasks:
            print("\nPeriodic Tasks:")
            print(f"{'ID':<6} {'Release':<10} {'Exec':<10} {'Period':<10} {'Deadline':<10}")
            print("-" * 50)
            for task in self.task_set.periodic_tasks:
                print(f"{task.id:<6} {task.release_time:<10.2f} {task.execution_time:<10.2f} "
                      f"{task.period:<10.2f} {task.deadline:<10.2f}")

        # Display dynamic tasks
        if self.task_set.dynamic_tasks:
            print("\nDynamic Tasks:")
            print(f"{'ID':<6} {'Exec':<10} {'Period':<10} {'Deadline':<10}")
            print("-" * 40)
            for task in self.task_set.dynamic_tasks:
                print(f"{task.id:<6} {task.execution_time:<10.2f} "
                      f"{task.period:<10.2f} {task.deadline:<10.2f}")

        # Display aperiodic tasks
        if self.task_set.aperiodic_tasks:
            print("\nAperiodic Tasks:")
            print(f"{'ID':<6} {'Release':<10} {'Exec':<10} {'Server':<15}")
            print("-" * 45)
            for task in self.task_set.aperiodic_tasks:
                server = task.server_type.value if task.server_type else "None"
                print(f"{task.id:<6} {task.release_time:<10.2f} "
                      f"{task.execution_time:<10.2f} {server:<15}")

    def configure_and_run_simulation(self):
        """Configure simulation parameters and run"""
        print("\n" + "-" * 70)
        print("SIMULATION CONFIGURATION")
        print("-" * 70)

        if not self.task_set:
            print("No task set loaded. Please load a task file first.")
            return

        # Select scheduler
        print("\nAvailable Schedulers:")
        schedulers = SchedulerFactory.get_available_schedulers()
        for i, sched in enumerate(schedulers, 1):
            print(f"{i}. {sched}")

        scheduler_choice = input("\nSelect scheduler (1-{}): ".format(len(schedulers))).strip()
        try:
            scheduler_idx = int(scheduler_choice) - 1
            if scheduler_idx < 0 or scheduler_idx >= len(schedulers):
                raise ValueError()

            scheduler_name = schedulers[scheduler_idx].split()[0]
            scheduler = SchedulerFactory.create_scheduler(scheduler_name)
        except:
            print("❌ Invalid choice. Using RM scheduler.")
            scheduler = SchedulerFactory.create_scheduler('RM')

        # Select aperiodic server
        aperiodic_server = None
        if self.task_set.aperiodic_tasks:
            print("\nAvailable Aperiodic Servers:")
            servers = ServerFactory.get_available_servers()
            for i, serv in enumerate(servers, 1):
                print(f"{i}. {serv}")

            server_choice = input("\nSelect server (1-{}): ".format(len(servers))).strip()
            try:
                server_idx = int(server_choice) - 1
                if server_idx < 0 or server_idx >= len(servers):
                    raise ValueError()

                server_type = servers[server_idx]

                if server_type in ['Polling', 'Deferrable', 'Sporadic']:
                    capacity = float(input("Enter server capacity: "))
                    period = float(input("Enter server period: "))
                    aperiodic_server = ServerFactory.create_server(server_type, capacity, period)
                else:
                    aperiodic_server = ServerFactory.create_server(server_type)
            except Exception as e:
                print(f"❌ Error: {e}. Using Background server.")
                aperiodic_server = ServerFactory.create_server('Background')

        # Simulation parameters
        try:
            sim_time = float(input("\nEnter simulation time (default 100): ") or "100")
            time_quantum = float(input("Enter time quantum (default 0.5): ") or "0.5")
            preemptive = input("Preemptive scheduling? (y/n, default y): ").strip().lower() != 'n'
        except ValueError:
            print("❌ Invalid input. Using default values.")
            sim_time = 100
            time_quantum = 0.5
            preemptive = True

        # Create and run simulation
        config = SimulationConfig(sim_time, time_quantum, preemptive)
        self.simulator = Simulator(scheduler, config, aperiodic_server)
        self.simulator.load_task_set(self.task_set)

        print("\n" + "=" * 70)
        print("Running simulation...")
        print("=" * 70)

        results = self.simulator.run()

        print("\n✓ Simulation completed!")
        print(f"\nScheduler: {results['scheduler']}")
        print(f"Total Tasks: {results['total_tasks']}")
        print(f"Completed: {results['completed_tasks']}")
        print(f"Missed Deadlines: {results['missed_deadlines']}")
        print(f"Success Rate: {results['success_rate']:.2f}%")

    def display_results(self):
        """Display detailed simulation results"""
        print("\n" + "-" * 70)
        print("SIMULATION RESULTS")
        print("-" * 70)

        if not self.simulator:
            print("No simulation has been run yet.")
            return

        results = self.simulator.scheduler.get_statistics()

        print(f"\nScheduler: {results['scheduler']}")
        print(f"Simulation Time: {results['total_time']:.2f}")
        print(f"\nTask Statistics:")
        print(f"  Total Tasks: {results['total_tasks']}")
        print(f"  Completed: {results['completed_tasks']}")
        print(f"  Missed Deadlines: {results['missed_deadlines']}")
        print(f"  Success Rate: {results['success_rate']:.2f}%")

        if 'avg_response_time' in results:
            print(f"\nTiming Statistics:")
            print(f"  Average Response Time: {results['avg_response_time']:.2f}")
            print(f"  Maximum Response Time: {results['max_response_time']:.2f}")
            if 'avg_completion_time' in results:
                print(f"  Average Completion Time: {results['avg_completion_time']:.2f}")

        # Display events
        print("\n" + "-" * 70)
        print("SCHEDULE EVENTS (first 50)")
        print("-" * 70)

        for i, event in enumerate(self.simulator.scheduler.schedule_events[:50]):
            print(event)

        if len(self.simulator.scheduler.schedule_events) > 50:
            print(f"... and {len(self.simulator.scheduler.schedule_events) - 50} more events")

    def display_utilization(self):
        """Display utilization analysis"""
        print("\n" + "-" * 70)
        print("UTILIZATION ANALYSIS")
        print("-" * 70)

        if not self.simulator:
            print("No simulation has been run yet.")
            return

        util = self.simulator.calculate_utilization()

        print(f"\nPeriodic Task Utilization: {util['periodic_utilization']:.4f}")
        print(f"Dynamic Task Utilization: {util['dynamic_utilization']:.4f}")
        print(f"Total Utilization: {util['total_utilization']:.4f}")

        print(f"\nSchedulability Analysis:")
        print(f"  RM Schedulable: {'Yes' if util['schedulable_rm'] else 'No'}")
        print(f"  EDF Schedulable: {'Yes' if util['schedulable_edf'] else 'No'}")

    def display_gantt_chart(self):
        """Display ASCII Gantt chart"""
        print("\n" + "-" * 70)
        print("GANTT CHART")
        print("-" * 70)

        if not self.simulator:
            print("No simulation has been run yet.")
            return

        chart_data = self.simulator.generate_gantt_chart_data()

        if not chart_data:
            print("No execution data available.")
            return

        print("\nTime | Task Execution")
        print("-" * 70)

        for start, duration, task_name in chart_data[:100]:
            bar_length = int(duration * 2)  # Scale factor
            bar = "█" * max(1, bar_length)
            print(f"{start:5.1f} | {task_name:<10} {bar}")

        if len(chart_data) > 100:
            print(f"... and {len(chart_data) - 100} more executions")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Command-line mode
        filename = sys.argv[1]
        print(f"Loading task file: {filename}")

        try:
            task_set = TaskFileParser.parse_file(filename)
            print(f"Loaded {len(task_set.tasks)} tasks")

            # Run with default settings
            scheduler = SchedulerFactory.create_scheduler('RM')
            config = SimulationConfig(100, 0.5, True)
            simulator = Simulator(scheduler, config)
            simulator.load_task_set(task_set)

            print("\nRunning simulation...")
            results = simulator.run()

            print(f"\nResults:")
            print(f"  Completed: {results['completed_tasks']}")
            print(f"  Missed Deadlines: {results['missed_deadlines']}")
            print(f"  Success Rate: {results['success_rate']:.2f}%")

        except ParseError as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Interactive mode
        ui = RTSchedulerUI()
        ui.run()


if __name__ == "__main__":
    main()
