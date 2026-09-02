from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseIDRAdapter(ABC):
    """
    Abstract interface for evaluating IDR navigation solutions against simulated sensor streams.
    Decouples the simulator from the internal mobile IDR engine implementation.
    """

    @abstractmethod
    def process_stream(self, sensor_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consumes a time-series list of simulated sensor observation records
        and produces a time-series list of estimated navigation states.
        """
        pass
