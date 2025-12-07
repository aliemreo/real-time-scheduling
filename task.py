from enum import Enum


class TaskType(Enum):
    PERIODIC = "P"
    DYNAMIC = "D"
    APERIODIC = "A"


class ServerType(Enum):
    NONE = "None"
    BACKGROUND = "Background"
    POLLER = "Poller"
    DEFERRABLE = "Deferrable"


class Task:
    """Single task class handling all task types (matches C++ design)"""

    _task_counter = 0

    def __init__(self, task_type: TaskType, execution_time: float,
                 period: float = 0, deadline: float = 0,
                 release_time: float = 0, server: ServerType = ServerType.NONE):
        """
        Single constructor handles all task types via default arguments

        Args:
            task_type: Type of task (PERIODIC, DYNAMIC, APERIODIC)
            execution_time: Execution time
            period: Period (0 for aperiodic)
            deadline: Deadline (defaults to period if 0)
            release_time: Release time
            server: Server type for aperiodic tasks
        """
        Task._task_counter += 1
        self.id = Task._task_counter
        self.type = task_type
        self.execution_time = execution_time
        self.period = period
        self.deadline = deadline if deadline > 0 else period
        self.release_time = release_time
        self.server = server

    def __repr__(self):
        """String representation based on task type"""
        if self.type == TaskType.PERIODIC:
            return f"P{self.id}"
        elif self.type == TaskType.DYNAMIC:
            return f"D{self.id}"
        elif self.type == TaskType.APERIODIC:
            server_str = f"_{self.server.value}" if self.server != ServerType.NONE else ""
            return f"A{self.id}{server_str}"
        return f"Task{self.id}"


class Job:
    """Represents a specific instance/job of a task for scheduling (matches C++ design)"""

    def __init__(self, task: Task, release_time: float):
        """
        Create a job instance

        Args:
            task: Reference to the task definition
            release_time: When this job is released
        """
        self.task = task
        self.remaining = task.execution_time
        self.abs_deadline = release_time + task.deadline
        self.current_release = release_time
        self.started = False
        self.start_time = None
        self.completion_time = None
        self.preemption_count = 0

    def is_complete(self) -> bool:
        """Check if job is complete"""
        return self.remaining <= 1e-9

    def is_deadline_missed(self, current_time: float) -> bool:
        """Check if deadline is missed"""
        return current_time > self.abs_deadline and not self.is_complete()

    def execute(self, duration: float) -> float:
        """
        Execute job for given duration

        Args:
            duration: Time to execute

        Returns:
            Actual execution time
        """
        self.started = True
        actual_time = min(duration, self.remaining)
        self.remaining = max(0.0, self.remaining - actual_time)
        return actual_time

    def __repr__(self):
        """String representation showing task and release time"""
        return f"{self.task}@{self.current_release}"


# Backward compatibility aliases (to minimize changes in other files initially)
PeriodicTask = Task
DynamicTask = Task
AperiodicTask = Task
TaskInstance = Job
