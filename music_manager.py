# music_manager.py
import arcade
import os
import random


class MusicManager:
    """Менеджер фоновой музыки для хоррора"""

    def __init__(self):
        self.current_music = None
        self.music_volume = 0.3
        self.playlist = []
        self.current_track_index = -1
        self.music_enabled = True

        self.load_music()

    def load_music(self):
        """Загрузить музыку из папки custom_sounds/music"""
        music_folder = "custom_sounds/music"

        if os.path.exists(music_folder):
            for file in os.listdir(music_folder):
                if file.lower().endswith(('.wav', '.ogg', '.mp3')):
                    try:
                        path = os.path.join(music_folder, file)
                        self.playlist.append({
                            'path': path,
                            'name': file,
                            'type': self.detect_music_type(file)
                        })
                        print(f"🎵 Загружена музыка: {file}")
                    except Exception as e:
                        print(f"Ошибка загрузки музыки {file}: {e}")

        if not self.playlist:
            print("⚠️ Кастомная музыка не найдена. Создайте папку custom_sounds/music")

    def detect_music_type(self, filename: str) -> str:
        """Определить тип музыки по названию файла"""
        filename_lower = filename.lower()

        if any(word in filename_lower for word in ['tension', 'suspense', 'creepy']):
            return 'tension'
        elif any(word in filename_lower for word in ['chase', 'action', 'panic']):
            return 'action'
        elif any(word in filename_lower for word in ['calm', 'ambient', 'quiet']):
            return 'calm'
        elif any(word in filename_lower for word in ['menu', 'main', 'theme']):
            return 'menu'
        else:
            return 'ambient'

    def play_music(self, music_type: str = None, loop: bool = True):
        """Воспроизвести музыку"""
        if not self.music_enabled or not self.playlist:
            return

        # Фильтруем по типу если нужно
        available_tracks = self.playlist
        if music_type:
            available_tracks = [t for t in self.playlist if t['type'] == music_type]

        if not available_tracks:
            available_tracks = self.playlist

        # Выбираем случайный трек
        track = random.choice(available_tracks)

        try:
            # Останавливаем текущую музыку
            if self.current_music:
                self.current_music.stop()

            # Загружаем и воспроизводим новую
            self.current_music = arcade.load_sound(track['path'], streaming=True)
            self.current_music.play(volume=self.music_volume, loop=loop)
            print(f"🎶 Играет: {track['name']} ({track['type']})")

        except Exception as e:
            print(f"Ошибка воспроизведения музыки: {e}")

    def play_tension_music(self, stress_level: float):
        """Воспроизвести напряженную музыку в зависимости от стресса"""
        if stress_level > 80:
            self.play_music('action')
        elif stress_level > 60:
            self.play_music('tension')
        elif stress_level > 40:
            self.play_music('ambient')

    def stop_music(self):
        """Остановить музыку"""
        if self.current_music:
            self.current_music.stop()
            self.current_music = None

    def set_volume(self, volume: float):
        """Установить громкость музыки"""
        self.music_volume = max(0.0, min(1.0, volume))
        if self.current_music:
            # В Arcade нельзя изменить громкость на лету, нужно перезапустить
            pass

    def fade_out(self, duration: float = 2.0):
        """Плавное затухание музыки"""
        # В Arcade нет встроенного фейда, но можно эмулировать
        self.stop_music()