# fear_profile.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
import json
import os
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import random


@dataclass
class PlayerBehavior:
    """Данные о поведении игрока"""
    mouse_speed_avg: float = 0.0
    mouse_shaking: float = 0.0  # Дрожь мыши
    reaction_times: List[float] = None
    avoidance_patterns: List[str] = None  # Паттерны избегания
    stress_responses: List[float] = None  # Реакции на стресс

    def __post_init__(self):
        if self.reaction_times is None:
            self.reaction_times = []
        if self.avoidance_patterns is None:
            self.avoidance_patterns = []
        if self.stress_responses is None:
            self.stress_responses = []


@dataclass
class FearProfile:
    """Профиль страхов игрока"""
    player_id: str
    session_start: str
    session_end: Optional[str] = None

    # Базовые страхи
    claustrophobia_level: float = 0.0
    jump_scare_level: float = 0.0
    darkness_level: float = 0.0
    heights_level: float = 0.0
    loud_sounds_level: float = 0.0
    monsters_level: float = 0.0

    # Статистика
    total_jump_scares: int = 0
    time_in_darkness: float = 0.0
    narrow_spaces_entered: int = 0
    loud_sounds_heard: int = 0
    monsters_encountered: int = 0
    falls_experienced: int = 0

    # Поведение
    behavior: PlayerBehavior = None

    # Физиологические показатели (имитация)
    avg_heart_rate: float = 70.0
    max_stress_level: float = 0.0
    panic_attacks: int = 0

    def __post_init__(self):
        if self.behavior is None:
            self.behavior = PlayerBehavior()

    def update_from_game(self, game_data: dict):
        """Обновить профиль на основе игровых данных"""
        # Анализируем поведение
        stress = game_data.get('stress_level', 0)
        self.max_stress_level = max(self.max_stress_level, stress)

        if stress > 80:
            self.panic_attacks += 1

        # Логируем события
        if game_data.get('jump_scare_triggered', False):
            self.total_jump_scares += 1
            self.jump_scare_level += 0.1

        if game_data.get('in_darkness', False):
            self.time_in_darkness += 0.1
            self.darkness_level += 0.05

        if game_data.get('in_narrow_space', False):
            self.narrow_spaces_entered += 1
            self.claustrophobia_level += 0.08

        if game_data.get('loud_sound_played', False):
            self.loud_sounds_heard += 1
            self.loud_sounds_level += 0.07

        if game_data.get('monster_nearby', False):
            self.monsters_encountered += 1
            self.monsters_level += 0.12

        if game_data.get('height_danger', False):
            self.falls_experienced += 1
            self.heights_level += 0.15

        # Нормализуем уровни страхов (0-1)
        for attr in ['claustrophobia_level', 'jump_scare_level', 'darkness_level',
                     'heights_level', 'loud_sounds_level', 'monsters_level']:
            current = getattr(self, attr)
            setattr(self, attr, min(1.0, current))

    def calculate_dominant_fear(self) -> str:
        """Определить доминирующий страх"""
        fears = {
            'claustrophobia': self.claustrophobia_level,
            'jump_scare': self.jump_scare_level,
            'darkness': self.darkness_level,
            'heights': self.heights_level,
            'loud_sounds': self.loud_sounds_level,
            'monsters': self.monsters_level
        }

        if not any(fears.values()):
            return 'unknown'

        return max(fears, key=fears.get)

    def get_fear_intensity(self, fear_type: str) -> float:
        """Получить интенсивность страха (0-1)"""
        fear_map = {
            'claustrophobia': self.claustrophobia_level,
            'jump_scare': self.jump_scare_level,
            'darkness': self.darkness_level,
            'heights': self.heights_level,
            'loud_sounds': self.loud_sounds_level,
            'monsters': self.monsters_level
        }

        return fear_map.get(fear_type, 0.0)

    def save_to_file(self):
        """Сохранить профиль в файл"""
        os.makedirs('data', exist_ok=True)

        self.session_end = datetime.now().isoformat()

        filename = f"data/fear_profile_{self.player_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            data = asdict(self)
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        print(f"Профиль сохранен: {filename}")
        return filename


class FearManager:
    """Менеджер страхов для адаптации игры"""

    def __init__(self, player_id="player"):
        self.profile = FearProfile(
            player_id=player_id,
            session_start=datetime.now().isoformat()
        )
        self.current_stress = 30.0
        self.last_update = time.time()

    def update(self, game_data: dict):
        """Обновить данные на основе игровых событий"""
        current_time = time.time()

        if current_time - self.last_update > 1.0:  # Обновлять раз в секунду
            game_data['stress_level'] = self.current_stress
            self.profile.update_from_game(game_data)
            self.last_update = current_time

    def increase_stress(self, amount: float):
        """Увеличить уровень стресса"""
        self.current_stress = min(100.0, self.current_stress + amount)

    def decrease_stress(self, amount: float):
        """Уменьшить уровень стресса"""
        self.current_stress = max(0.0, self.current_stress - amount)

    def should_trigger_event(self, event_type: str) -> bool:
        """Определить, стоит ли запускать событие"""
        fear_intensity = self.profile.get_fear_intensity(event_type)

        # Базовая вероятность + влияние страха
        base_chance = 0.01
        fear_modifier = fear_intensity * 0.1

        return random.random() < (base_chance + fear_modifier)

    def get_event_intensity(self, event_type: str) -> float:
        """Получить интенсивность события на основе страха"""
        return self.profile.get_fear_intensity(event_type) * 0.5 + 0.5

    def end_session(self):
        """Завершить сессию"""
        self.profile.save_to_file()