"""
Real-Time Scheduling Simulator Engine
"""

from typing import List, Optional, Dict, Tuple
from task import Task, TaskType, Job
from scheduler import Scheduler, ScheduleEvent
from aperiodic_server import AperiodicServer, BackgroundServer
from parser import TaskSet
import math


class SimulationConfig:
    """Configuration for simulation"""

    def __init__(self, simulation_time: float = 100, time_quantum: float = 0.5,
                 preemptive: bool = True, context_switch_overhead: float = 0):
        self.simulation_time = simulation_time
        self.time_quantum = time_quantum
        self.preemptive = preemptive
        self.context_switch_overhead = context_switch_overhead


class Simulator:
    """Main simulation engine"""

    def __init__(self, scheduler: Scheduler, config: SimulationConfig,
                 aperiodic_server: Optional[AperiodicServer] = None):
        self.scheduler = scheduler
        self.config = config
        self.aperiodic_server = aperiodic_server if aperiodic_server else BackgroundServer()

        self.task_set: Optional[TaskSet] = None
        self.task_instances: List[Job] = []
        self.ready_queue: List[Job] = []
        self.current_task: Optional[Job] = None

    def load_task_set(self, task_set: TaskSet):
        """Load task set for simulation"""
        self.task_set = task_set
        self._generate_task_instances()

    def _generate_task_instances(self):
        """Generate task instances for simulation period"""
        self.task_instances = []

        # Generate periodic task instances
        for task in self.task_set.periodic_tasks:
            release_time = task.release_time
            while release_time < self.config.simulation_time:
                job = Job(task, release_time)
                self.task_instances.append(job)
                release_time += task.period

        # Add dynamic tasks
        for task in self.task_set.dynamic_tasks:
            job = Job(task, 0)
            self.task_instances.append(job)

        # Add aperiodic tasks
        for task in self.task_set.aperiodic_tasks:
            job = Job(task, task.release_time)
            self.task_instances.append(job)

        # Sort by release time
        self.task_instances.sort(key=lambda t: t.current_release)

    def run(self) -> Dict:
        """Run simulation and return results"""
        self.scheduler.reset()
        self.ready_queue = []
        self.current_task = None

        current_time = 0.0

        # Add initial event
        self.scheduler.add_event(ScheduleEvent(0, None, 'START', 'Simulation started'))

        while current_time < self.config.simulation_time:
            # Check for new task arrivals
            self._check_arrivals(current_time)

            # Check for deadline misses
            self._check_deadline_misses(current_time)

            # Replenish aperiodic server
            self.aperiodic_server.replenish(current_time)

            # Separate periodic and aperiodic tasks
            periodic_ready = [t for t in self.ready_queue if t.task.type != TaskType.APERIODIC]
            aperiodic_ready = [t for t in self.ready_queue if t.task.type == TaskType.APERIODIC]

            # Select next task
            next_task = None

            # First try to schedule periodic/dynamic tasks
            if periodic_ready:
                next_task = self.scheduler.select_task(periodic_ready)

            # If no periodic tasks, try aperiodic tasks with server
            elif aperiodic_ready and self.aperiodic_server.can_serve(current_time):
                next_task = self.scheduler.select_task(aperiodic_ready)

            # Handle task execution
            if next_task:
                # Check for preemption
                if self.current_task and self.current_task != next_task and self.config.preemptive:
                    self.scheduler.add_event(
                        ScheduleEvent(current_time, self.current_task, 'PREEMPT',
                                      f"Preempted by {next_task.task}")
                    )
                    self.current_task.preemption_count += 1

                # Start new task if needed
                if self.current_task != next_task:
                    # Apply context switch overhead
                    if self.current_task is not None and self.config.context_switch_overhead > 0:
                        current_time += self.config.context_switch_overhead
                        self.scheduler.add_event(
                            ScheduleEvent(current_time, None, 'CONTEXT_SWITCH',
                                          f"Context switch overhead: {self.config.context_switch_overhead}")
                        )
                        self.scheduler.current_time = current_time

                    if next_task.start_time is None:
                        next_task.start_time = current_time
                        self.scheduler.add_event(
                            ScheduleEvent(current_time, next_task, 'START',
                                          f"Started execution")
                        )

                self.current_task = next_task

                # Execute task
                execution_time = min(self.config.time_quantum, next_task.remaining)
                next_task.execute(execution_time)

                # Consume server capacity if aperiodic
                if next_task.task.type == TaskType.APERIODIC:
                    self.aperiodic_server.consume(execution_time, current_time)

                current_time += execution_time
                self.scheduler.current_time = current_time

                # Check if task completed
                if next_task.is_complete():
                    next_task.completion_time = current_time
                    self.ready_queue.remove(next_task)
                    self.scheduler.completed_tasks.append(next_task)
                    self.scheduler.add_event(
                        ScheduleEvent(current_time, next_task, 'COMPLETE',
                                      f"Completed (RT={next_task.remaining:.2f})")
                    )
                    self.current_task = None

            else:
                # Idle time
                if self.current_task is not None:
                    self.current_task = None

                # Advance to next event
                next_event_time = self._find_next_event_time(current_time)
                if next_event_time > current_time:
                    self.scheduler.add_event(
                        ScheduleEvent(current_time, None, 'IDLE',
                                      f"Idle until {next_event_time:.2f}")
                    )
                    current_time = next_event_time
                else:
                    current_time += self.config.time_quantum

                self.scheduler.current_time = current_time

        # Add final event
        self.scheduler.add_event(
            ScheduleEvent(current_time, None, 'END', 'Simulation completed')
        )

        return self.scheduler.get_statistics()

    def _check_arrivals(self, current_time: float):
        """Check for task arrivals and add to ready queue"""
        arrived = [t for t in self.task_instances
                   if t.current_release <= current_time
                   and t not in self.ready_queue
                   and not t.is_complete()
                   and t not in self.scheduler.completed_tasks
                   and t not in self.scheduler.missed_deadlines]

        for task in arrived:
            self.ready_queue.append(task)
            self.scheduler.add_event(
                ScheduleEvent(current_time, task, 'ARRIVAL',
                              f"Arrived (deadline={task.abs_deadline:.2f})")
            )

    def _check_deadline_misses(self, current_time: float):
        """Check for missed deadlines"""
        for task in list(self.ready_queue):
            if task.is_deadline_missed(current_time):
                self.ready_queue.remove(task)
                self.scheduler.missed_deadlines.append(task)
                self.scheduler.add_event(
                    ScheduleEvent(current_time, task, 'DEADLINE_MISS',
                                  f"Deadline missed (deadline={task.abs_deadline:.2f})")
                )
                if self.current_task == task:
                    self.current_task = None

    def _find_next_event_time(self, current_time: float) -> float:
        """Find time of next event (task arrival, deadline, etc.)"""
        next_time = self.config.simulation_time

        # Check for next arrival
        for task in self.task_instances:
            if task.current_release > current_time and task.current_release < next_time:
                if task not in self.ready_queue and task not in self.scheduler.completed_tasks:
                    next_time = task.current_release

        return next_time

    def calculate_utilization(self) -> Dict[str, float]:
        """Calculate CPU utilization"""
        if not self.task_set:
            return {}

        periodic_util = 0.0
        for task in self.task_set.periodic_tasks:
            periodic_util += task.execution_time / task.period

        dynamic_util = 0.0
        for task in self.task_set.dynamic_tasks:
            dynamic_util += task.execution_time / task.period

        total_util = periodic_util + dynamic_util

        return {
            'periodic_utilization': periodic_util,
            'dynamic_utilization': dynamic_util,
            'total_utilization': total_util,
            'schedulable_rm': periodic_util <= self._rm_bound(len(self.task_set.periodic_tasks)),
            'schedulable_edf': total_util <= 1.0
        }

    def _rm_bound(self, n: int) -> float:
        """Calculate RM schedulability bound for n tasks"""
        if n == 0:
            return 1.0
        return n * (2 ** (1 / n) - 1)
