# -*- coding: utf-8 -*-
import unittest
import tempfile
import os
from datetime import date
from Lab4 import (
    TemperatureMeasurement, DataManager, parse_line, format_measurement,
    parse_condition
)


class TestParsing(unittest.TestCase):

    def test_parse_line(self):
        line = 'Измерения температуры 2023.10.05 "Комната" 23.5'
        m = parse_line(line)
        self.assertEqual(m.obj_type, "Измерения температуры")
        self.assertEqual(m.date, date(2023, 10, 5))
        self.assertEqual(m.location, "Комната")
        self.assertEqual(m.value, 23.5)

    def test_format_measurement(self):
        m = TemperatureMeasurement("Test", date(2024, 1, 15), "Улица", -2.7)
        formatted = format_measurement(m)
        self.assertEqual(formatted, 'Test 2024.01.15 "Улица" -2.7')

    def test_parse_condition_value(self):
        pred = parse_condition("value > 30")
        m1 = TemperatureMeasurement("", date.today(), "", 31)
        m2 = TemperatureMeasurement("", date.today(), "", 29)
        self.assertTrue(pred(m1))
        self.assertFalse(pred(m2))

    def test_parse_condition_location(self):
        pred = parse_condition('location == "Kitchen"')
        m1 = TemperatureMeasurement("", date.today(), "Kitchen", 22.0)
        m2 = TemperatureMeasurement("", date.today(), "Living", 22.0)
        self.assertTrue(pred(m1))
        self.assertFalse(pred(m2))

    def test_parse_condition_date(self):
        pred = parse_condition("date >= 2024.01.01")
        m1 = TemperatureMeasurement("", date(2024, 5, 1), "", 0)
        m2 = TemperatureMeasurement("", date(2023, 12, 31), "", 0)
        self.assertTrue(pred(m1))
        self.assertFalse(pred(m2))

    def test_add_from_csv_full(self):
        dm = DataManager("dummy.txt")
        csv_str = 'Измерения; 2024.02.10; "Балкон"; 18.5'
        m = dm.add_from_csv(csv_str)
        self.assertEqual(m.obj_type, "Измерения")
        self.assertEqual(m.date, date(2024, 2, 10))
        self.assertEqual(m.location, "Балкон")
        self.assertEqual(m.value, 18.5)

    def test_add_from_csv_minimal(self):
        dm = DataManager("dummy.txt")
        csv_str = '2024.02.10; "Балкон"; 18.5'
        m = dm.add_from_csv(csv_str)
        self.assertEqual(m.obj_type, "Измерения температуры")
        self.assertEqual(m.location, "Балкон")

    def test_apply_commands(self):
        # Подготовка временного файла данных
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as data_file:
            data_file.write('Temp 2024.01.01 "Room" 20.0\n')
            data_file.flush()
            dm = DataManager(data_file.name)
            dm.load_from_file()

        # Файл команд
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as cmd_file:
            cmd_file.write('ADD NewType; 2024.03.01; "Office"; 22.5\n')
            cmd_file.write('REM value < 21\n')
            cmd_file.write(f'SAVE {data_file.name}_out.txt\n')
            cmd_file.flush()
            dm.apply_commands(cmd_file.name)

        # Проверки
        self.assertEqual(len(dm.measurements), 1)
        self.assertEqual(dm.measurements[0].location, "Office")
        self.assertEqual(dm.measurements[0].value, 22.5)

        # Проверка сохранённого файла
        with open(f"{data_file.name}_out.txt", 'r') as f:
            content = f.read()
        self.assertIn("Office", content)
        self.assertNotIn("Room", content)

        # Удаление временных файлов
        os.unlink(data_file.name)
        os.unlink(cmd_file.name)
        os.unlink(f"{data_file.name}_out.txt")


if __name__ == '__main__':
    unittest.main()
