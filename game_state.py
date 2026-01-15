# game_state.py
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

        # Обновляем профиль страхов
        if self.current_fear_profile is None:
            from fear_profile import FearProfile
            self.current_fear_profile = FearProfile(
                player_id=f"player_{int(datetime.now().timestamp())}",
                session_start=datetime.now().isoformat()
            )

        # Обновляем данные страхов на основе результатов
        self.current_fear_profile.total_jump_scares = results.get('triggered_jumpscares', 0)
        self.current_fear_profile.jump_scare_level = results.get('final_stress', 0) / 100
        self.current_fear_profile.avg_heart_rate = 70 + (results.get('final_stress', 0) * 0.3)
        self.current_fear_profile.max_stress_level = results.get('final_stress', 0)

        # Сохраняем в файл
        os.makedirs('data', exist_ok=True)
        filename = f"data/game_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = {
            'fear_profile': {
                'player_id': self.current_fear_profile.player_id,
                'jump_scare_level': self.current_fear_profile.jump_scare_level,
                'total_jump_scares': self.current_fear_profile.total_jump_scares,
                'max_stress_level': self.current_fear_profile.max_stress_level
            },
            'level1_results': results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Сохранено состояние игры: {filename}")

    def get_fear_profile(self):
        """Получить текущий профиль страхов"""
        return self.current_fear_profile

    def load_from_file(self):
        """Загрузить состояние из файла"""
        if not os.path.exists('data'):
            return None

        # Ищем последний файл состояния
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

                from fear_profile import FearProfile

                self.current_fear_profile = FearProfile(
                    player_id=data['fear_profile']['player_id'],
                    session_start=datetime.now().isoformat()
                )

                self.current_fear_profile.jump_scare_level = data['fear_profile']['jump_scare_level']
                self.current_fear_profile.total_jump_scares = data['fear_profile']['total_jump_scares']
                self.current_fear_profile.max_stress_level = data['fear_profile']['max_stress_level']

                self.level1_results = data['level1_results']

                print(f"Загружено состояние игры: {latest_file}")
                return True

            except Exception as e:
                print(f"Ошибка загрузки состояния: {e}")

        return None