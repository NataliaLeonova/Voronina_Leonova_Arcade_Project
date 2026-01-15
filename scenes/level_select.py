# level_select.py
import arcade
import json
import os
from data_models import CalibrationData


class LevelSelectView(arcade.View):
    """Экран после калибровки - ОДНОРАЗОВЫЙ"""

    def __init__(self, calibration_data: CalibrationData):
        super().__init__()
        self.calibration_data = calibration_data
        self.active = True  # Флаг активности
        self.transitioning = False  # Флаг перехода

        # Анализ
        self.reaction_score = calibration_data.calculate_reaction_score()
        self.reaction_pattern = calibration_data.get_reaction_pattern()

        # Сохраняем данные
        self.save_calibration_data()

        print("=" * 50)
        print("Готово! Нажмите ПРОБЕЛ для Уровня 1")
        print("=" * 50)

    def save_calibration_data(self):
        """Сохранить данные калибровки (только один раз)"""
        if hasattr(self, '_data_saved'):
            return

        os.makedirs('data', exist_ok=True)

        if self.calibration_data.reaction_intervals:
            avg_time = sum(self.calibration_data.reaction_intervals) / len(self.calibration_data.reaction_intervals)
        else:
            avg_time = 0

        data = {
            'reaction_score': self.reaction_score,
            'reaction_pattern': self.reaction_pattern,
            'avg_hold_time': avg_time,
            'total_clicks': len(self.calibration_data.click_times)
        }

        filename = f"data/calibration_{int(self.reaction_score)}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Данные сохранены: {filename}")
        self._data_saved = True

    def on_show_view(self):
        """При показе экрана"""
        # Включаем активность
        self.active = True
        self.transitioning = False

    def on_draw(self):
        """Отрисовка - ТОЛЬКО если активно"""
        if not self.active:
            return

        self.clear()
        arcade.set_background_color((20, 0, 40))

        # Используем arcade.Text для производительности
        if self.calibration_data.reaction_intervals:
            avg_time = sum(self.calibration_data.reaction_intervals) / len(self.calibration_data.reaction_intervals)
        else:
            avg_time = 0

        # Создаем текстовые объекты если еще не созданы
        if not hasattr(self, 'text_objects'):
            self.text_objects = [
                arcade.Text(
                    "КАЛИБРОВКА ЗАВЕРШЕНА",
                    self.window.width // 2,
                    self.window.height - 100,
                    arcade.color.WHITE,
                    36,
                    anchor_x="center"
                ),
                arcade.Text(
                    f"Оценка: {self.reaction_score:.1f}/100",
                    self.window.width // 2,
                    self.window.height - 180,
                    (57, 255, 20),
                    28,
                    anchor_x="center"
                ),
                arcade.Text(
                    f"Среднее время: {avg_time:.3f}с",
                    self.window.width // 2,
                    self.window.height - 230,
                    arcade.color.LIGHT_GRAY,
                    24,
                    anchor_x="center"
                ),
                arcade.Text(
                    f"Паттерн: {self.reaction_pattern}",
                    self.window.width // 2,
                    self.window.height - 280,
                    arcade.color.LIGHT_GRAY,
                    24,
                    anchor_x="center"
                ),
                arcade.Text(
                    "НАЖМИТЕ ПРОБЕЛ ДЛЯ УРОВНЯ 1",
                    self.window.width // 2,
                    150,
                    (136, 8, 8),
                    32,
                    anchor_x="center"
                ),
                arcade.Text(
                    "ESC - В главное меню",
                    self.window.width // 2,
                    100,
                    arcade.color.GRAY,
                    18,
                    anchor_x="center"
                )
            ]

        # Рисуем все текстовые объекты
        for text in self.text_objects:
            text.draw()

    def on_key_press(self, symbol: int, modifiers: int):
        """Обработка нажатия клавиш - ТОЛЬКО если активно и не в процессе перехода"""
        if not self.active or self.transitioning:
            return

        if symbol == arcade.key.SPACE:
            self.transitioning = True
            self.start_level1()
        elif symbol == arcade.key.ESCAPE:
            self.transitioning = True
            self.back_to_menu()

    def start_level1(self):
        """Запустить первый уровень"""
        print("=" * 50)
        print("ЗАПУСК ЛАБИРИНТА...")
        print("=" * 50)

        # НЕМЕДЛЕННО отключаем себя
        self.active = False

        # Импортируем и создаем лабиринт
        from scenes.level1_maze import Level1MazeView
        maze_view = Level1MazeView(self.calibration_data)

        # Сразу переходим
        self.window.show_view(maze_view)

    def back_to_menu(self):
        """Вернуться в меню"""
        self.active = False
        from scenes.main_menu import MainMenuView
        menu_view = MainMenuView()
        self.window.show_view(menu_view)