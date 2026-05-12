import re
from datetime import date

class TemperatureMeasurement:
    """Класс, представляющий измерение температуры."""
    def __init__(self, date_obj: date, location: str, value: float):
        self.date = date_obj
        self.location = location
        self.value = value

    def __repr__(self):
        return f"TemperatureMeasurement(date={self.date}, location='{self.location}', value={self.value})"

def parse_temperature_measurement(input_str: str) -> TemperatureMeasurement:
    """
    Преобразует текстовую строку в объект TemperatureMeasurement.

    Формат строки:
        <тип_объекта> <дата> <место_в_кавычках> <значение>
    где:
        - тип_объекта может содержать пробелы (извлекается автоматически до первой даты)
        - дата в формате ГГГГ.ММ.ДД
        - место - строковое свойство в двойных кавычках
        - значение - дробное число (точка как разделитель)

    Пример:
        "Измерения температуры 2023.10.05 \"Комната\" 23.5"
    """
    # 1. Находим дату (формат ГГГГ.ММ.ДД)
    date_pattern = r'\d{4}\.\d{2}\.\d{2}'
    date_match = re.search(date_pattern, input_str)
    if not date_match:
        raise ValueError("Дата не найдена в строке")

    # 2. Извлекаем тип объекта (всё до найденной даты, очищаем от лишних пробелов)
    type_name = input_str[:date_match.start()].strip()  # тип не используется, но можно сохранить

    # 3. Оставшаяся часть строки после даты
    after_date = input_str[date_match.end():].strip()

    # 4. Извлекаем строковое свойство в кавычках
    quoted_pattern = r'"([^"]*)"'
    quoted_match = re.search(quoted_pattern, after_date)
    if not quoted_match:
        raise ValueError("Строковое свойство (место) в кавычках не найдено")
    location = quoted_match.group(1)

    # 5. Оставшаяся часть после строки в кавычках
    after_location = after_date[quoted_match.end():].strip()

    # 6. Извлекаем дробное значение (число с точкой)
    value_pattern = r'[-+]?\d+(?:\.\d+)?'
    value_match = re.search(value_pattern, after_location)
    if not value_match:
        raise ValueError("Числовое значение не найдено")
    value = float(value_match.group())

    # 7. Преобразуем дату из строки в объект date
    date_str = date_match.group()
    year, month, day = map(int, date_str.split('.'))
    date_obj = date(year, month, day)

    return TemperatureMeasurement(date_obj, location, value)

def main():
    print("Программа для создания объектов измерения температуры")
    print("Формат строки: <любой текст> ГГГГ.ММ.ДД \"место\" значение")
    print("Для выхода введите пустую строку или 'exit'\n")

    while True:
        user_input = input("Введите строку: ").strip()
        if not user_input or user_input.lower() == 'exit':
            print("Выход из программы.")
            break

        try:
            measurement = parse_temperature_measurement(user_input)
            print("Результат:", measurement)
        except Exception as e:
            print(f"Ошибка при разборе строки: {e}")

if __name__ == "__main__":
    main()
