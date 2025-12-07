"""
Input file parser for Real-Time Scheduling Simulator
"""

from typing import List, Tuple, Optional
from task import Task, TaskType, ServerType


class ConsumptionRule:
    """Server consumption rule"""
    def __init__(self, rule_type: str):
        self.rule_type = rule_type


class ReplenishmentRule:
    """Server replenishment rule"""
    def __init__(self, rule_type: str, period: Optional[float] = None):
        self.rule_type = rule_type
        self.period = period


class TaskSet:
    """Container for parsed task set and configuration"""

    def __init__(self):
        self.tasks: List[Task] = []
        self.periodic_tasks: List[Task] = []
        self.dynamic_tasks: List[Task] = []
        self.aperiodic_tasks: List[Task] = []
        self.consumption_rules: List[ConsumptionRule] = []
        self.replenishment_rules: List[ReplenishmentRule] = []

    def add_task(self, task: Task):
        """Add task to appropriate list"""
        self.tasks.append(task)

        if task.type == TaskType.PERIODIC:
            self.periodic_tasks.append(task)
        elif task.type == TaskType.DYNAMIC:
            self.dynamic_tasks.append(task)
        elif task.type == TaskType.APERIODIC:
            self.aperiodic_tasks.append(task)


class ParseError(Exception):
    """Exception raised for parsing errors"""
    def __init__(self, line_number: int, message: str):
        self.line_number = line_number
        super().__init__(f"Line {line_number}: {message}")


class TaskFileParser:
    """Parser for task input files"""

    @staticmethod
    def parse_file(filename: str) -> TaskSet:
        """Parse input file and return TaskSet"""
        task_set = TaskSet()

        try:
            with open(filename, 'r') as file:
                for line_num, line in enumerate(file, 1):
                    try:
                        TaskFileParser._parse_line(line.strip(), task_set, line_num)
                    except ValueError as e:
                        raise ParseError(line_num, str(e))
        except FileNotFoundError:
            raise ParseError(0, f"File not found: {filename}")
        except IOError as e:
            raise ParseError(0, f"Error reading file: {str(e)}")

        return task_set

    @staticmethod
    def _parse_line(line: str, task_set: TaskSet, line_num: int):
        """Parse a single line"""
        # Skip comments and empty lines
        if not line or line.startswith('#'):
            return

        parts = line.split()
        if not parts:
            return

        task_type = parts[0].upper()

        try:
            if task_type == 'P':
                task = TaskFileParser._parse_periodic_task(parts)
                task_set.add_task(task)

            elif task_type == 'D':
                task = TaskFileParser._parse_dynamic_task(parts)
                task_set.add_task(task)

            elif task_type == 'A':
                task = TaskFileParser._parse_aperiodic_task(parts)
                task_set.add_task(task)

            elif task_type == 'CONSUMPTION_RULE':
                rule = TaskFileParser._parse_consumption_rule(parts)
                task_set.consumption_rules.append(rule)

            elif task_type == 'REPLENISHMENT_RULE':
                rule = TaskFileParser._parse_replenishment_rule(parts)
                task_set.replenishment_rules.append(rule)

            else:
                raise ValueError(f"Unknown task type: {task_type}")

        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid format: {str(e)}")

    @staticmethod
    def _parse_periodic_task(parts: List[str]) -> Task:
        """Parse periodic task: P [ri] ei pi [di]"""
        if len(parts) == 3:
            # P ei pi
            _, ei, pi = parts
            return Task(TaskType.PERIODIC, float(ei), float(pi))

        elif len(parts) == 4:
            # P ri ei pi
            _, ri, ei, pi = parts
            return Task(TaskType.PERIODIC, float(ei), float(pi), 0, float(ri))

        elif len(parts) == 5:
            # P ri ei pi di
            _, ri, ei, pi, di = parts
            return Task(TaskType.PERIODIC, float(ei), float(pi), float(di), float(ri))

        else:
            raise ValueError(f"Invalid periodic task format. Expected 3-5 fields, got {len(parts)}")

    @staticmethod
    def _parse_dynamic_task(parts: List[str]) -> Task:
        """Parse dynamic task: D ei pi di"""
        if len(parts) != 4:
            raise ValueError(f"Invalid dynamic task format. Expected 4 fields, got {len(parts)}")

        _, ei, pi, di = parts
        return Task(TaskType.DYNAMIC, float(ei), float(pi), float(di))

    @staticmethod
    def _parse_aperiodic_task(parts: List[str]) -> Task:
        """Parse aperiodic task: A ri ei [server_type]"""
        if len(parts) < 3:
            raise ValueError(f"Invalid aperiodic task format. Expected at least 3 fields, got {len(parts)}")

        _, ri, ei = parts[:3]
        server_type = ServerType.NONE

        if len(parts) >= 4:
            server_str = parts[3]
            try:
                server_type = ServerType(server_str)
            except ValueError:
                raise ValueError(f"Invalid server type: {server_str}")

        return Task(TaskType.APERIODIC, float(ei), 0, 0, float(ri), server_type)

    @staticmethod
    def _parse_consumption_rule(parts: List[str]) -> ConsumptionRule:
        """Parse consumption rule: CONSUMPTION_RULE <rule_definition>"""
        if len(parts) < 2:
            raise ValueError("Invalid consumption rule format")

        rule_type = ' '.join(parts[1:])
        return ConsumptionRule(rule_type)

    @staticmethod
    def _parse_replenishment_rule(parts: List[str]) -> ReplenishmentRule:
        """Parse replenishment rule: REPLENISHMENT_RULE <rule_definition> [period]"""
        if len(parts) < 2:
            raise ValueError("Invalid replenishment rule format")

        rule_type = parts[1]
        period = None

        if len(parts) >= 3 and rule_type.upper() == 'PERIODIC':
            try:
                period = float(parts[2])
            except ValueError:
                raise ValueError(f"Invalid period value: {parts[2]}")

        return ReplenishmentRule(rule_type, period)

    @staticmethod
    def validate_task_set(task_set: TaskSet) -> Tuple[bool, List[str]]:
        """Validate task set and return (is_valid, error_messages)"""
        errors = []

        for task in task_set.tasks:
            # Validate execution time
            if task.execution_time <= 0:
                errors.append(f"{task}: execution time must be positive")

            # Validate release time
            if task.release_time < 0:
                errors.append(f"{task}: release time cannot be negative")

            # Validate periodic/dynamic tasks
            if task.type in (TaskType.PERIODIC, TaskType.DYNAMIC):
                if task.period <= 0:
                    errors.append(f"{task}: period must be positive")

                if task.deadline <= 0:
                    errors.append(f"{task}: deadline must be positive")

        return len(errors) == 0, errors
