# game_state.py - без вывода
import json
import os
from datetime import datetime


class GameState:
    """Хранитель состояния игры между уровнями"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GameState, cls).__new__(cls)
            cls._instance.current_fear_profile = None
            cls._instance.calibration_data = None
            cls._instance.level1_results = None
        return cls._instance

    def save_level1_results(self, results: dict):
        """Сохранить результаты уровня 1"""
        self.level1_results = results

        if self.current_fear_profile is None:
            self.current_fear_profile = {
                'player_id': f"player_{int(datetime.now().timestamp())}",
                'session_start': datetime.now().isoformat(),
                'jump_scare_level': results.get('final_stress', 0) / 100,
                'total_jump_scares': results.get('triggered_jumpscares', 0),
                'max_stress_level': results.get('final_stress', 0),
                'avg_heart_rate': 70 + (results.get('final_stress', 0) * 0.3)
            }

        os.makedirs('data', exist_ok=True)
        filename = f"data/game_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = {
            'fear_profile': self.current_fear_profile,
            'level1_results': results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_fear_profile(self):
        """Получить текущий профиль страхов"""
        return self.current_fear_profile

    def load_from_file(self):
        """Загрузить состояние из файла"""
        if not os.path.exists('data'):
            return None

        state_files = []
        for file in os.listdir('data'):
            if file.startswith('game_state_') and file.endswith('.json'):
                state_files.append(file)

        if state_files:
            state_files.sort(reverse=True)
            latest_file = os.path.join('data', state_files[0])

            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.current_fear_profile = data.get('fear_profile', {})
                self.level1_results = data.get('level1_results', {})
                return True

            except Exception:
                pass

        return None