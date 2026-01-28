import arcade
import os
import random


class SoundManager:
    """Менеджер звуков"""

    def __init__(self, sound_mode="level2"):
        """
        sound_mode:
        - "level1": ТОЛЬКО скримеры
        - "level2": ВСЕ звуки
        """
        self.sounds = {}
        self.sound_volume = 1.0
        self.sound_mode = sound_mode

        self.load_all_sounds()

    def load_custom_sounds(self):
        """Загрузить кастомные звуки"""
        custom_folder = "custom_sounds"

        if not os.path.exists(custom_folder):
            return False

        sound_categories = {
            'scream': ['scare', 'scream', 'terror', 'demonic', 'distorted', 'quick', 'long'],
            'ambient': ['ambient', 'creepy', 'wind', 'howl', 'distant', 'echo'],
            'music': ['music', 'theme', 'panic', 'tension', 'menu'],
            'monster': ['monster', 'growl', 'breathing', 'moan', 'demon', 'claws'],
            'footstep': ['step', 'footstep', 'drag', 'quick', 'stone', 'wood'],
            'heartbeat': ['heartbeat', 'pulse', 'slow', 'fast', 'panic'],
            'door': ['door', 'creak', 'slam'],
            'whisper': ['whisper', 'nonsense'],
            'drip': ['drip', 'water', 'book', 'drop'],
            'sudden': ['sudden', 'impact', 'glass', 'metal', 'break', 'clang', 'chain']
        }

        for category in sound_categories.keys():
            self.sounds[category] = []

        total_files = 0

        for root, dirs, files in os.walk(custom_folder):
            for file in files:
                file_lower = file.lower()

                if not file_lower.endswith(('.wav', '.ogg', '.mp3')):
                    continue

                file_path = os.path.join(root, file)
                file_assigned = False

                for category, keywords in sound_categories.items():
                    for keyword in keywords:
                        if keyword in file_lower:
                            try:
                                sound = arcade.load_sound(file_path)
                                self.sounds[category].append({
                                    'sound': sound,
                                    'path': file_path,
                                    'name': file
                                })
                                total_files += 1
                                file_assigned = True
                                break
                            except:
                                file_assigned = True
                                break
                    if file_assigned:
                        break

        return total_files > 0

    def load_all_sounds(self):
        """Загрузить все звуки"""
        self.load_custom_sounds()

    def play_sound(self, sound_type: str, volume: float = 1.0):
        """Воспроизвести звук"""
        # LEVEL 1: только скримеры
        if self.sound_mode == "level1" and sound_type != 'scream':
            return False

        if sound_type not in self.sounds:
            return False

        if not self.sounds[sound_type]:
            return False

        try:
            sound_data = random.choice(self.sounds[sound_type])
            final_volume = self.sound_volume * volume
            sound_data['sound'].play(volume=final_volume)
            return True
        except:
            return False

    def set_volume(self, volume: float):
        """Установить громкость"""
        self.sound_volume = max(0.0, min(1.0, volume))