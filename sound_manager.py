# sound_manager.py
import arcade
import random


class SoundManager:
    """Менеджер звуков для хоррора"""

    def __init__(self):
        self.sounds = {}
        self.background_sounds = []
        self.load_sounds()

    def load_sounds(self):
        """Загрузить все звуки"""
        try:
            # Проверяем существующие звуки
            available_sounds = [
                # Проверенные звуки из arcade
                (":resources:sounds/explosion2.wav", 'jump_scare'),
                (":resources:sounds/explosion1.wav", 'jump_scare'),
                (":resources:sounds/rockHit2.wav", 'heartbeat'),
                (":resources:sounds/upgrade4.wav", 'door_creak'),
                (":resources:sounds/upgrade5.wav", 'door_creak'),
                (":resources:sounds/hurt3.wav", 'monster_growl'),
                (":resources:sounds/hurt4.wav", 'monster_growl'),
                (":resources:sounds/hurt5.wav", 'monster_growl'),
                (":resources:sounds/coin1.wav", 'footstep'),
                (":resources:sounds/coin2.wav", 'footstep'),
                (":resources:sounds/coin3.wav", 'footstep'),
                (":resources:sounds/laser2.wav", 'whisper'),
                (":resources:sounds/laser4.wav", 'whisper'),
                (":resources:sounds/hurt1.wav", 'scream'),
                (":resources:sounds/laser1.wav", 'wind'),
                (":resources:sounds/coin4.wav", 'drip'),
            ]

            # Загружаем только доступные звуки
            for path, category in available_sounds:
                try:
                    sound = arcade.load_sound(path)

                    if category not in self.sounds:
                        self.sounds[category] = []

                    self.sounds[category].append(sound)
                    print(f"Загружен звук: {category} из {path}")

                except Exception as e:
                    print(f"Не удалось загрузить {path}: {e}")

            print(f"Успешно загружено {sum(len(v) for v in self.sounds.values())} звуков")

        except Exception as e:
            print(f"Критическая ошибка загрузки звуков: {e}")
            # Создаем заглушки
            self.sounds = {
                'jump_scare': [None],
                'heartbeat': [None],
                'door_creak': [None],
                'monster_growl': [None],
                'footstep': [None],
                'whisper': [None],
                'scream': [None],
                'wind': [None],
                'drip': [None]
            }

    def play_sound(self, sound_name: str, volume: float = 1.0):
        """Воспроизвести звук"""
        if sound_name in self.sounds and self.sounds[sound_name]:
            sound_list = self.sounds[sound_name]
            sound = random.choice(sound_list)

            if sound is not None:
                try:
                    sound.play(volume=volume)
                except Exception as e:
                    # Тихий fallback
                    pass

    def play_random_background(self):
        """Воспроизвести случайный фоновый звук"""
        if random.random() < 0.05:  # 5% шанс
            sound_type = random.choice(['wind', 'drip', 'door_creak', 'whisper'])
            if sound_type in self.sounds:
                self.play_sound(sound_type, volume=0.2)

    def play_heartbeat(self, stress_level: float):
        """Воспроизвести сердцебиение в зависимости от стресса"""
        if stress_level > 50:
            if random.random() < 0.1 + (stress_level - 50) / 500:
                volume = 0.1 + (stress_level / 100) * 0.3
                self.play_sound('heartbeat', volume=volume)

    def play_footstep(self):
        """Воспроизвести звук шага"""
        if random.random() < 0.4:
            self.play_sound('footstep', volume=0.15)