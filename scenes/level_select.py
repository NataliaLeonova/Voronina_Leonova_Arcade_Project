import arcade
import json
import os
from data_models import CalibrationData


class LevelSelectView(arcade.View):
    """Экран после калибровки с отображением данных"""

    def __init__(self, calibration_data: CalibrationData):
        super().__init__()
        self.calibration_data = calibration_data
        self.active = True
        self.transitioning = False

        # Анализ данных калибровки
        self.reaction_score = calibration_data.calculate_reaction_score()
        self.reaction_pattern = calibration_data.get_reaction_pattern()

        # Дополнительная статистика
        if calibration_data.reaction_intervals:
            self.avg_time = sum(calibration_data.reaction_intervals) / len(calibration_data.reaction_intervals)
            self.min_time = min(calibration_data.reaction_intervals)
            self.max_time = max(calibration_data.reaction_intervals)
            self.total_clicks = len(calibration_data.click_times)
        else:
            self.avg_time = 0
            self.min_time = 0
            self.max_time = 0
            self.total_clicks = 0

        # Определяем характеристику игрока
        self.player_trait = self._determine_player_trait()

        # Сохраняем данные
        self.save_calibration_data()

        # Текстовые объекты
        self.text_objects = []

    def _determine_player_trait(self):
        """Определить характеристику игрока на основе реакций"""
        if not self.calibration_data.reaction_intervals:
            return "неопределенный"

        avg = self.avg_time

        if avg < 0.05:
            return "Молниеносный"
        elif avg < 0.1:
            return "Быстрый как ветер"
        elif avg < 0.2:
            return "Спокойный"
        elif avg < 0.3:
            return "Осторожный"
        elif avg < 0.5:
            return "Медлительный"
        else:
            return "Флегматик"

    def save_calibration_data(self):
        """Сохранить данные калибровки"""
        if hasattr(self, '_data_saved'):
            return

        os.makedirs('data', exist_ok=True)

        data = {
            'reaction_score': self.reaction_score,
            'reaction_pattern': self.reaction_pattern,
            'player_trait': self.player_trait,
            'avg_hold_time': self.avg_time,
            'min_hold_time': self.min_time,
            'max_hold_time': self.max_time,
            'total_clicks': self.total_clicks,
            'reaction_intervals': self.calibration_data.reaction_intervals
        }

        filename = f"data/calibration_{int(self.reaction_score)}_{self.player_trait}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._data_saved = True

    def on_show_view(self):
        """При показе экрана создаем текстовые объекты"""
        self.active = True
        self.transitioning = False

        # Очищаем старые текстовые объекты
        self.text_objects = []

        # Заголовок
        self.text_objects.append(arcade.Text(
            "АНАЛИЗ КАЛИБРОВКИ",
            self.window.width // 2,
            self.window.height - 100,
            (136, 8, 8),
            36,
            anchor_x="center"
        ))

        # Оценка реакции
        score_color = (57, 255, 20) if self.reaction_score > 70 else (255, 200, 50) if self.reaction_score > 40 else (
            255, 100, 100)
        self.text_objects.append(arcade.Text(
            f"ОЦЕНКА РЕАКЦИИ: {self.reaction_score:.0f}/100",
            self.window.width // 2,
            self.window.height - 160,
            score_color,
            28,
            anchor_x="center"
        ))

        # Характеристика игрока
        trait_color = (100, 200, 255) if "Молниеносный" in self.player_trait else (255, 215,
                                                                                   0) if "Быстрый" in self.player_trait else (
            150, 255, 150)
        self.text_objects.append(arcade.Text(
            f"ХАРАКТЕРИСТИКА: {self.player_trait}",
            self.window.width // 2,
            self.window.height - 200,
            trait_color,
            24,
            anchor_x="center"
        ))

        # Статистика реакций
        self.text_objects.append(arcade.Text(
            "СТАТИСТИКА РЕАКЦИЙ:",
            self.window.width // 2,
            self.window.height - 250,
            (200, 200, 255),
            22,
            anchor_x="center"
        ))

        if self.calibration_data.reaction_intervals:
            y_pos = self.window.height - 280
            stats = [
                f"Среднее время: {self.avg_time:.3f} сек",
                f"Самое быстрое: {self.min_time:.3f} сек",
                f"Самое медленное: {self.max_time:.3f} сек",
                f"Всего кликов: {self.total_clicks}",
                f"Паттерн: {self.reaction_pattern}"
            ]

            for stat in stats:
                self.text_objects.append(arcade.Text(
                    stat,
                    self.window.width // 2,
                    y_pos,
                    (220, 220, 220),
                    20,
                    anchor_x="center"
                ))
                y_pos -= 28

        # Интерпретация
        self.text_objects.append(arcade.Text(
            "ИНТЕРПРЕТАЦИЯ:",
            self.window.width // 2,
            y_pos - 20,
            (255, 200, 100),
            22,
            anchor_x="center"
        ))

        interpretation = self._get_interpretation()
        y_pos -= 50

        # Разбиваем интерпретацию на строки если нужно
        words = interpretation.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line + " " + word) <= 40:
                current_line += " " + word
            else:
                lines.append(current_line.strip())
                current_line = word

        if current_line:
            lines.append(current_line.strip())

        for line in lines:
            self.text_objects.append(arcade.Text(
                line,
                self.window.width // 2,
                y_pos,
                (200, 200, 200),
                18,
                anchor_x="center"
            ))
            y_pos -= 26

        # Подсказка для продолжения
        self.text_objects.append(arcade.Text(
            "НАЖМИТЕ ПРОБЕЛ ДЛЯ НАЧАЛА УРОВНЯ 1",
            self.window.width // 2,
            150,
            (136, 8, 8),
            32,
            anchor_x="center",
            bold=True
        ))

        self.text_objects.append(arcade.Text(
            "ESC - В главное меню",
            self.window.width // 2,
            100,
            (150, 150, 150),
            18,
            anchor_x="center"
        ))

    def _get_interpretation(self):
        """Получить интерпретацию данных калибровки"""
        if self.reaction_score > 85:
            return "Отличные реакции! Вы быстро реагируете на опасность и сохраняете контроль."
        elif self.reaction_score > 70:
            return "Хорошие реакции. Вы стабильны и предсказуемы в своих действиях."
        elif self.reaction_score > 50:
            return "Средние реакции. Иногда вы быстры, иногда осторожны - это интересно для анализа."
        elif self.reaction_score > 30:
            return "Замедленные реакции. Вы склонны к осторожности и обдумыванию действий."
        else:
            return "Очень медленные реакции. Возможно, вы легко поддаетесь панике или чрезмерно осторожны."

    def on_draw(self):
        """Отрисовка"""
        if not self.active:
            return

        self.clear()
        arcade.set_background_color((15, 5, 30))

        # Фоновый узор
        import math
        import time as tm
        elapsed = tm.time()

        for i in range(10):
            x = self.window.width // 2 + math.sin(elapsed + i) * 50
            y = self.window.height // 2 + math.cos(elapsed + i) * 50
            size = 20 + math.sin(elapsed * 2 + i) * 10
            alpha = 30 + int(math.sin(elapsed + i) * 20)

            arcade.draw_circle_filled(
                x, y, size,
                (40, 20, 60, alpha)
            )

        # Рисуем все текстовые объекты
        for text in self.text_objects:
            text.draw()

        # Анимация для кнопки старта
        import time
        pulse = (time.time() % 1.0) * 2
        if pulse < 1.0:
            alpha = int(pulse * 50)
        else:
            alpha = int((2.0 - pulse) * 50)

        # Подсветка кнопки
        arcade.draw_lrbt_rectangle_filled(
            self.window.width // 2 - 250,
            self.window.width // 2 + 250,
            130,
            170,
            (136, 8, 8, alpha // 3)
        )

    def on_key_press(self, symbol: int, modifiers: int):
        """Обработка нажатия клавиш"""
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
        self.active = False

        from scenes.level1_maze import Level1MazeView
        maze_view = Level1MazeView(self.calibration_data)
        self.window.show_view(maze_view)

    def back_to_menu(self):
        """Вернуться в меню"""
        self.active = False
        from scenes.main_menu import MainMenuView
        menu_view = MainMenuView()
        self.window.show_view(menu_view)