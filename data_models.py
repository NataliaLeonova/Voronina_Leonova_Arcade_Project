# data_models.py
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class CalibrationData:
    """Данные калибровки реакций"""
    click_times: List[float] = None
    release_times: List[float] = None
    reaction_intervals: List[float] = None
    mouse_positions: List[Tuple[float, float]] = None
    start_time: float = 0

    def __post_init__(self):
        if self.click_times is None:
            self.click_times = []
        if self.release_times is None:
            self.release_times = []
        if self.reaction_intervals is None:
            self.reaction_intervals = []
        if self.mouse_positions is None:
            self.mouse_positions = []

    def add_click(self, timestamp: float, mouse_pos: Tuple[float, float]):
        self.click_times.append(timestamp)
        self.mouse_positions.append(mouse_pos)

    def add_release(self, timestamp: float):
        self.release_times.append(timestamp)
        if len(self.click_times) == len(self.release_times):
            hold_time = timestamp - self.click_times[-1]
            self.reaction_intervals.append(hold_time)

    def calculate_reaction_score(self) -> float:
        if not self.reaction_intervals:
            return 50.0

        avg_hold = sum(self.reaction_intervals) / len(self.reaction_intervals)
        score = max(0, 100 - (avg_hold * 200))
        return min(100, score)

    def get_reaction_pattern(self) -> str:
        if not self.reaction_intervals:
            return "normal"

        avg = sum(self.reaction_intervals) / len(self.reaction_intervals)

        if avg < 0.1:
            return "instant"
        elif avg < 0.3:
            return "fast"
        elif avg < 0.8:
            return "medium"
        else:
            return "slow"


@dataclass
class ReactionEvent:
    """Событие реакции в лабиринте"""
    timestamp: float
    event_type: str  # 'jumpscare', 'unexpected_sound', 'darkness', etc.
    mouse_delta: Tuple[float, float]  # Изменение позиции мыши
    reaction_time: float
    stress_level: float