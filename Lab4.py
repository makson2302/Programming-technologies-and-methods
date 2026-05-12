# -*- coding: utf-8 -*-

import csv
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import date
from typing import List, Callable


class TemperatureMeasurement:
    """Класс, представляющий измерение температуры."""

    def __init__(self, obj_type: str, date_obj: date, location: str, value: float):
        self.obj_type = obj_type
        self.date = date_obj
        self.location = location
        self.value = value

    def __repr__(self) -> str:
        return (f"TemperatureMeasurement(obj_type={self.obj_type!r}, "
                f"date={self.date!r}, location={self.location!r}, value={self.value!r})")


class DataManager:
    """Управляет данными, загрузкой/сохранением, выполнением команд."""

    def __init__(self, filename: str):
        self.filename = filename
        self.measurements: List[TemperatureMeasurement] = []

    def load_from_file(self) -> None:
        """Загружает данные из основного файла."""
        try:
            with open(self.filename, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except FileNotFoundError:
            self.measurements = []
            return

        self.measurements = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    self.measurements.append(parse_line(line))
                except ValueError:
                    pass

    def save_to_file(self, filename: str = None) -> None:
        """Сохраняет данные в файл (если filename не указан, используется исходный)."""
        if filename is None:
            filename = self.filename
        with open(filename, 'w', encoding='utf-8') as file:
            for m in self.measurements:
                file.write(format_measurement(m) + '\n')

    def add_measurement(self, measurement: TemperatureMeasurement) -> None:
        """Добавляет измерение и сохраняет изменения."""
        self.measurements.append(measurement)
        self.save_to_file()

    def delete_measurement(self, index: int) -> None:
        """Удаляет измерение по индексу и сохраняет."""
        if 0 <= index < len(self.measurements):
            del self.measurements[index]
            self.save_to_file()

    def remove_by_condition(self, condition: Callable[[TemperatureMeasurement], bool]) -> int:
        """Удаляет все измерения, удовлетворяющие условию. Возвращает количество удалённых."""
        original_len = len(self.measurements)
        self.measurements = [m for m in self.measurements if not condition(m)]
        self.save_to_file()
        return original_len - len(self.measurements)

    def add_from_csv(self, csv_string: str) -> TemperatureMeasurement:
        """
        Создаёт измерение из CSV-строки (разделитель ';').
        Поддерживает форматы:
          - тип; ГГГГ.ММ.ДД; "место"; значение
          - ГГГГ.ММ.ДД; "место"; значение   (тип по умолчанию "Измерения температуры")
        """
        reader = csv.reader([csv_string], delimiter=';', quotechar='"')
        row = next(reader)
        if len(row) == 3:
            date_str = row[0].strip()
            location = row[1].strip()
            value_str = row[2].strip()
            obj_type = "Измерения температуры"
        elif len(row) == 4:
            obj_type = row[0].strip()
            date_str = row[1].strip()
            location = row[2].strip()
            value_str = row[3].strip()
        else:
            raise ValueError(f"Некорректный CSV: ожидается 3 или 4 поля, получено {len(row)}")

        year, month, day = map(int, date_str.split('.'))
        date_obj = date(year, month, day)
        value = float(value_str)
        return TemperatureMeasurement(obj_type, date_obj, location, value)

    def apply_commands(self, commands_file: str) -> None:
        """Выполняет команды из файла последовательно."""
        with open(commands_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                self._execute_command(line)

    def _execute_command(self, command_line: str) -> None:
        """Разбирает и выполняет одну команду."""
        if command_line.startswith('ADD'):
            args = command_line[3:].strip()
            if not args:
                raise ValueError("ADD: отсутствуют данные")
            measurement = self.add_from_csv(args)
            self.add_measurement(measurement)
        elif command_line.startswith('REM'):
            condition_str = command_line[3:].strip()
            if not condition_str:
                raise ValueError("REM: отсутствует условие")
            condition = parse_condition(condition_str)
            self.remove_by_condition(condition)
        elif command_line.startswith('SAVE'):
            filename = command_line[4:].strip()
            if not filename:
                raise ValueError("SAVE: отсутствует имя файла")
            self.save_to_file(filename)
        else:
            raise ValueError(f"Неизвестная команда: {command_line}")


def parse_line(line: str) -> TemperatureMeasurement:
    """Разбирает строку формата: тип дата "место" значение."""
    date_pattern = r'\d{4}\.\d{2}\.\d{2}'
    date_match = re.search(date_pattern, line)
    if not date_match:
        raise ValueError("Дата не найдена")
    obj_type = line[:date_match.start()].strip()
    after_date = line[date_match.end():].strip()
    quoted_pattern = r'"([^"]*)"'
    quoted_match = re.search(quoted_pattern, after_date)
    if not quoted_match:
        raise ValueError("Строковое свойство (место) не найдено")
    location = quoted_match.group(1)
    after_location = after_date[quoted_match.end():].strip()
    value_pattern = r'[-+]?\d+(?:\.\d+)?'
    value_match = re.search(value_pattern, after_location)
    if not value_match:
        raise ValueError("Числовое значение не найдено")
    value = float(value_match.group())
    year, month, day = map(int, date_match.group().split('.'))
    date_obj = date(year, month, day)
    return TemperatureMeasurement(obj_type, date_obj, location, value)


def format_measurement(measurement: TemperatureMeasurement) -> str:
    """Форматирует измерение для сохранения в файл."""
    date_str = measurement.date.strftime("%Y.%m.%d")
    value_str = f"{measurement.value:.10f}".rstrip('0').rstrip('.')
    return f'{measurement.obj_type} {date_str} "{measurement.location}" {value_str}'


def parse_condition(cond_str: str) -> Callable[[TemperatureMeasurement], bool]:
    """
    Разбирает условие вида: поле оператор значение
    Возвращает функцию-предикат.
    Примеры:
        'value > 30'
        'location == "Kitchen"'
        'date >= 2024.01.01'
    """
    fields = {
        'date': lambda m: m.date,
        'location': lambda m: m.location,
        'value': lambda m: m.value
    }
    pattern = r'(\w+)\s*(>=|<=|==|!=|>|<)\s*(.+)'
    match = re.match(pattern, cond_str)
    if not match:
        raise ValueError(f"Неверный формат условия: {cond_str}")
    field_name, operator, value_str = match.groups()
    if field_name not in fields:
        raise ValueError(f"Неизвестное поле: {field_name}")

    if field_name == 'date':
        try:
            value = date(*map(int, value_str.split('.')))
        except Exception:
            raise ValueError(f"Неверный формат даты в условии: {value_str}")
    elif field_name == 'location':
        if value_str.startswith('"') and value_str.endswith('"'):
            value = value_str[1:-1]
        else:
            value = value_str
    else:
        value = float(value_str)

    def predicate(meas: TemperatureMeasurement) -> bool:
        meas_value = fields[field_name](meas)
        if operator == '>':
            return meas_value > value
        elif operator == '<':
            return meas_value < value
        elif operator == '>=':
            return meas_value >= value
        elif operator == '<=':
            return meas_value <= value
        elif operator == '==':
            return meas_value == value
        elif operator == '!=':
            return meas_value != value
        return False

    return predicate


class AddMeasurementDialog(simpledialog.Dialog):
    """Диалог добавления измерения."""

    def __init__(self, parent):
        self.obj_type = tk.StringVar(value="Измерения температуры")
        self.date_str = tk.StringVar()
        self.location = tk.StringVar()
        self.value_str = tk.StringVar()
        self.result = None
        super().__init__(parent, title="Добавить измерение")

    def body(self, master):
        ttk.Label(master, text="Тип объекта:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.entry_type = ttk.Entry(master, textvariable=self.obj_type, width=30)
        self.entry_type.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(master, text="Дата (ГГГГ.ММ.ДД):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.entry_date = ttk.Entry(master, textvariable=self.date_str, width=30)
        self.entry_date.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(master, text="Место:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.entry_loc = ttk.Entry(master, textvariable=self.location, width=30)
        self.entry_loc.grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(master, text="Значение:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.entry_val = ttk.Entry(master, textvariable=self.value_str, width=30)
        self.entry_val.grid(row=3, column=1, padx=5, pady=2)

        return self.entry_type

    def validate(self):
        if not re.match(r'\d{4}\.\d{2}\.\d{2}', self.date_str.get()):
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ.ММ.ДД")
            return False
        try:
            float(self.value_str.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Значение должно быть числом")
            return False
        if not self.location.get().strip():
            messagebox.showerror("Ошибка", "Место не может быть пустым")
            return False
        return True

    def apply(self):
        self.result = True


class Application:
    """Главное окно приложения."""

    def __init__(self, root: tk.Tk, data_manager: DataManager):
        self.root = root
        self.data_manager = data_manager
        self.root.title("Измерения температуры")
        self.root.geometry("750x450")

        self.tree = ttk.Treeview(root, columns=("date", "location", "value"), show="headings")
        self.tree.heading("date", text="Дата")
        self.tree.heading("location", text="Место")
        self.tree.heading("value", text="Значение")
        self.tree.column("date", width=100)
        self.tree.column("location", width=400)
        self.tree.column("value", width=100)

        scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns")

        btn_frame = ttk.Frame(root)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5)

        ttk.Button(btn_frame, text="Добавить", command=self.add_measurement).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Удалить выделенное", command=self.delete_measurement).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Выполнить команды из файла", command=self.execute_commands).pack(side="left",
                                                                                                     padx=5)
        ttk.Button(btn_frame, text="Обновить", command=self.refresh_table).pack(side="left", padx=5)

        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        self.refresh_table()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def refresh_table(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for m in self.data_manager.measurements:
            self.tree.insert("", "end", values=(m.date.strftime("%Y.%m.%d"), m.location, m.value))

    def add_measurement(self) -> None:
        dialog = AddMeasurementDialog(self.root)
        if dialog.result is True:
            obj_type = dialog.obj_type.get().strip()
            date_str = dialog.date_str.get().strip()
            location = dialog.location.get().strip()
            value_str = dialog.value_str.get().strip()
            try:
                year, month, day = map(int, date_str.split('.'))
                date_obj = date(year, month, day)
                value = float(value_str)
                new_meas = TemperatureMeasurement(obj_type, date_obj, location, value)
                self.data_manager.add_measurement(new_meas)
                self.refresh_table()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать измерение: {e}")

    def delete_measurement(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Не выбрано ни одного измерения")
            return
        values = self.tree.item(selected[0], "values")
        date_str, location, value_str = values
        value = float(value_str)
        for i, m in enumerate(self.data_manager.measurements):
            if (m.date.strftime("%Y.%m.%d") == date_str and
                    m.location == location and
                    abs(m.value - value) < 1e-9):
                if messagebox.askyesno("Подтверждение", "Удалить выбранное измерение?"):
                    self.data_manager.delete_measurement(i)
                    self.refresh_table()
                return
        messagebox.showerror("Ошибка", "Не удалось найти измерение в данных")

    def execute_commands(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Выберите файл с командами",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if not file_path:
            return
        try:
            self.data_manager.apply_commands(file_path)
            self.refresh_table()
            messagebox.showinfo("Успех", "Команды успешно выполнены")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Ошибка", f"Ошибка при выполнении команд:\n{e}")

    def run_tests_and_coverage(self):
        """Запускает модульные тесты и выводит отчёт о покрытии."""
        try:
            import subprocess
            import sys
            import os

            test_file = "test_temperature_app.py"
            if not os.path.exists(test_file):
                print("Файл с тестами не найден:", test_file)
                return

            print("\n=== Запуск тестов и оценка покрытия ===")
            result = subprocess.run(
                [sys.executable, "-m", "coverage", "run", "-m", "unittest", test_file],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print("Ошибка при выполнении тестов:\n", result.stderr)
            else:
                print("Тесты успешно выполнены.")

            report = subprocess.run(
                [sys.executable, "-m", "coverage", "report", "-m"],
                capture_output=True, text=True
            )
            print("\nОтчёт о покрытии кода тестами:")
            print(report.stdout if report.stdout else report.stderr)

            subprocess.run([sys.executable, "-m", "coverage", "html"], capture_output=True)
            print("HTML-отчёт сохранён в папке 'htmlcov'")

        except Exception as e:
            print(f"Не удалось выполнить оценку покрытия: {e}")
            print("Убедитесь, что установлен пакет coverage (pip install coverage)")

    def on_closing(self):
        """Вызывается при закрытии главного окна."""
        self.run_tests_and_coverage()
        self.root.destroy()


def main():
    DATA_FILE = "temperature_data.txt"
    manager = DataManager(DATA_FILE)
    manager.load_from_file()
    root = tk.Tk()
    app = Application(root, manager)
    root.mainloop()


if __name__ == "__main__":
    main()
