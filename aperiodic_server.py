"""
Aperiodic Server Algorithms
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from task import AperiodicTask, TaskInstance


class AperiodicServer(ABC):
    """Abstract base class for aperiodic servers"""

    def __init__(self, name: str, capacity: float = 0, period: float = 0):
        self.name = name
        self.capacity = capacity
        self.period = period
        self.current_capacity = capacity
        self.last_replenishment_time = 0

    @abstractmethod
    def can_serve(self, current_time: float) -> bool:
        """Check if server can serve aperiodic tasks"""
        pass

    @abstractmethod
    def consume(self, execution_time: float, current_time: float):
        """Consume server capacity"""
        pass

    @abstractmethod
    def replenish(self, current_time: float):
        """Replenish server capacity"""
        pass

    def reset(self):
        """Reset server state"""
        self.current_capacity = self.capacity
        self.last_replenishment_time = 0


class BackgroundServer(AperiodicServer):
    """
    Background Server - Aperiodic tasks execute when no periodic tasks are ready
    Lowest priority scheduling
    """

    def __init__(self):
        super().__init__("Background Server")

    def can_serve(self, current_time: float) -> bool:
        """Background server can always serve (if no higher priority tasks)"""
        return True

    def consume(self, execution_time: float, current_time: float):
        """No capacity tracking for background server"""
        pass

    def replenish(self, current_time: float):
        """No replenishment needed for background server"""
        pass


class PollingServer(AperiodicServer):
    """
    Polling Server - Periodic server with capacity that is replenished periodically
    Consumes capacity even when idle
    """

    def __init__(self, capacity: float, period: float):
        super().__init__("Polling Server", capacity, period)

    def can_serve(self, current_time: float) -> bool:
        """Can serve if capacity is available"""
        return self.current_capacity > 0

    def consume(self, execution_time: float, current_time: float):
        """Consume capacity (whether serving or idle)"""
        self.current_capacity -= execution_time
        if self.current_capacity < 0:
            self.current_capacity = 0

    def replenish(self, current_time: float):
        """Replenish capacity at period boundaries"""
        if current_time - self.last_replenishment_time >= self.period:
            self.current_capacity = self.capacity
            self.last_replenishment_time = current_time


class DeferrableServer(AperiodicServer):
    """
    Deferrable Server - Periodic server that preserves capacity when idle
    Only consumes capacity when actually serving aperiodic tasks
    """

    def __init__(self, capacity: float, period: float):
        super().__init__("Deferrable Server", capacity, period)
        self.is_active = False

    def can_serve(self, current_time: float) -> bool:
        """Can serve if capacity is available"""
        return self.current_capacity > 0

    def consume(self, execution_time: float, current_time: float):
        """Consume capacity only when serving aperiodic tasks"""
        self.current_capacity -= execution_time
        if self.current_capacity < 0:
            self.current_capacity = 0
        self.is_active = True

    def replenish(self, current_time: float):
        """Replenish capacity at period boundaries"""
        if current_time - self.last_replenishment_time >= self.period:
            self.current_capacity = self.capacity
            self.last_replenishment_time = current_time
            self.is_active = False

    def reset(self):
        """Reset server state"""
        super().reset()
        self.is_active = False


class SporadicServer(AperiodicServer):
    """
    Sporadic Server - Advanced server with deferred replenishment
    Replenishment occurs after a delay equal to the period from when capacity was consumed
    """

    def __init__(self, capacity: float, period: float):
        super().__init__("Sporadic Server", capacity, period)
        self.replenishment_queue = []  # List of (time, amount) tuples

    def can_serve(self, current_time: float) -> bool:
        """Can serve if capacity is available"""
        self._process_replenishments(current_time)
        return self.current_capacity > 0

    def consume(self, execution_time: float, current_time: float):
        """Consume capacity and schedule replenishment"""
        consumed = min(execution_time, self.current_capacity)
        if consumed > 0:
            self.current_capacity -= consumed
            # Schedule replenishment for consumed capacity
            replenishment_time = current_time + self.period
            self.replenishment_queue.append((replenishment_time, consumed))

    def replenish(self, current_time: float):
        """Process scheduled replenishments"""
        self._process_replenishments(current_time)

    def _process_replenishments(self, current_time: float):
        """Process all pending replenishments up to current time"""
        remaining_queue = []
        for replenish_time, amount in self.replenishment_queue:
            if replenish_time <= current_time:
                self.current_capacity = min(self.capacity, self.current_capacity + amount)
            else:
                remaining_queue.append((replenish_time, amount))
        self.replenishment_queue = remaining_queue

    def reset(self):
        """Reset server state"""
        super().reset()
        self.replenishment_queue = []


class ServerFactory:
    """Factory for creating aperiodic server instances"""

    @staticmethod
    def create_server(server_type: str, capacity: float = 0, period: float = 0) -> AperiodicServer:
        """Create server by type"""
        server_type = server_type.upper()

        if server_type == 'BACKGROUND':
            return BackgroundServer()
        elif server_type == 'POLLING':
            if capacity <= 0 or period <= 0:
                raise ValueError("Polling server requires positive capacity and period")
            return PollingServer(capacity, period)
        elif server_type == 'DEFERRABLE':
            if capacity <= 0 or period <= 0:
                raise ValueError("Deferrable server requires positive capacity and period")
            return DeferrableServer(capacity, period)
        elif server_type == 'SPORADIC':
            if capacity <= 0 or period <= 0:
                raise ValueError("Sporadic server requires positive capacity and period")
            return SporadicServer(capacity, period)
        else:
            raise ValueError(f"Unknown server type: {server_type}")

    @staticmethod
    def get_available_servers() -> List[str]:
        """Get list of available server types"""
        return [
            'Background',
            'Polling',
            'Deferrable',
            'Sporadic'
        ]
