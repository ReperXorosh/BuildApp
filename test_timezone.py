#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы с часовыми поясами
"""

from datetime import datetime
import pytz

def test_timezone_behavior():
    """Тестирует поведение часовых поясов"""
    print("=== ТЕСТИРОВАНИЕ ЧАСОВЫХ ПОЯСОВ ===\n")
    
    # Московское время
    moscow_tz = pytz.timezone('Europe/Moscow')
    moscow_time = datetime.now(moscow_tz)
    
    # UTC время
    utc_tz = pytz.UTC
    utc_time = datetime.now(utc_tz)
    
    # Локальное время системы
    local_time = datetime.now()
    
    print(f"🕐 Московское время: {moscow_time}")
    print(f"🌍 UTC время: {utc_time}")
    print(f"💻 Локальное время: {local_time}")
    
    # Проверяем разницу
    print(f"\n📊 Разница UTC-Москва: {utc_time.astimezone(moscow_tz) - moscow_time}")
    
    # Тестируем сохранение и восстановление времени
    print(f"\n=== ТЕСТ СОХРАНЕНИЯ ВРЕМЕНИ ===")
    
    # Предполагаем, что время сохраняется в UTC в базе данных
    saved_time = moscow_time.astimezone(utc_tz)
    print(f"💾 Сохранено в UTC: {saved_time}")
    
    # Восстанавливаем московское время
    restored_time = saved_time.astimezone(moscow_tz)
    print(f"🔄 Восстановлено в Москве: {restored_time}")
    
    # Проверяем, что время совпадает
    print(f"✅ Время совпадает: {moscow_time == restored_time}")
    
    # Тестируем время без часового пояса
    print(f"\n=== ТЕСТ ВРЕМЕНИ БЕЗ ЧАСОВОГО ПОЯСА ===")
    naive_time = datetime.now()
    print(f"📅 Наивное время: {naive_time}")
    
    # Добавляем московский часовой пояс
    localized_time = moscow_tz.localize(naive_time)
    print(f"📍 Локализованное время: {localized_time}")
    
    # Конвертируем в UTC
    utc_converted = localized_time.astimezone(utc_tz)
    print(f"🌍 Конвертировано в UTC: {utc_converted}")
    
    # Обратно в Москву
    moscow_converted = utc_converted.astimezone(moscow_tz)
    print(f"🔄 Обратно в Москву: {moscow_converted}")

if __name__ == '__main__':
    test_timezone_behavior()
