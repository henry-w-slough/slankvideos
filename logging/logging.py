"""
Global logging module to access stored log functionality.
Logs are stored in a dictionary. To get it, call get()
"""
from dataclasses import dataclass
from enum import Enum, auto
from collections import deque



class Severity(Enum):
    INFO = auto()
    WARNING = auto()
    ERROR = auto()


@dataclass
class Log:
    message: str
    severity: Severity


_max_logs = 5000
_logs: deque[Log] = deque(maxlen=_max_logs)


def log(message: str, severity: Severity) -> None:
    """Adds a Log object with the given values to the log history."""
    _logs.append(
        Log(message, severity)
    )


def get_logs() -> list[Log]:
    """All logs added during the lifetime of the program."""
    #have to return a copy of _logs since its a deque
    return list(_logs)


def clear_log() -> None:
    """Removes all items from the log."""
    _logs.clear()


def set_max_logs(max: int) -> None:
    """Sets the maximum amount of persistent logs. Rebuilds logs
    in it's current state to the new size by removing oldest logs."""
    global _logs, _max_logs
    _max_logs = max
    _logs = deque(_logs, maxlen=max)  




    