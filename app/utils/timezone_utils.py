#!/usr/bin/env python3
"""
Утилиты для работы с московским временем
Централизованная система для корректного отображения времени в приложении
"""

from datetime import datetime, timedelta, date
import pytz

# Московский часовой пояс
MOSCOW_TZ = pytz.timezone('Europe/Moscow')
UTC_TZ = pytz.UTC

def get_moscow_now():
    """Возвращает текущее время в московском часовом поясе"""
    return datetime.now(MOSCOW_TZ)

def to_moscow_time(dt):
    """
    Конвертирует любое время в московское время
    
    Args:
        dt: datetime объект или date объект (с часовым поясом или без)
    
    Returns:
        datetime объект в московском часовом поясе
    """
    if dt is None:
        return None
    
    # Если это date объект, конвертируем его в datetime
    if isinstance(dt, date) and not isinstance(dt, datetime):
        # Преобразуем date в datetime (например, начало дня)
        dt = datetime.combine(dt, datetime.min.time())
    
    # Если время без часового пояса, считаем его UTC (как сохраняется в базе данных)
    if dt.tzinfo is None:
        dt = UTC_TZ.localize(dt)
    
    # Конвертируем в московское время
    return dt.astimezone(MOSCOW_TZ)

def format_moscow_time(dt, format_str='%d.%m.%Y %H:%M:%S'):
    """
    Форматирует время в московском часовом поясе
    
    Args:
        dt: datetime объект или date объект
        format_str: строка формата
    
    Returns:
        Отформатированная строка времени
    """
    if dt is None:
        return 'Не указано'
    
    moscow_time = to_moscow_time(dt)
    return moscow_time.strftime(format_str)

def parse_moscow_time(time_str, format_str='%d.%m.%Y %H:%M:%S'):
    """
    Парсит строку времени как московское время
    
    Args:
        time_str: строка с временем
        format_str: строка формата
    
    Returns:
        datetime объект в московском часовом поясе
    """
    try:
        naive_dt = datetime.strptime(time_str, format_str)
        return MOSCOW_TZ.localize(naive_dt)
    except ValueError:
        return None

def get_moscow_date_range(start_date, end_date):
    """
    Получает диапазон дат в московском времени
    
    Args:
        start_date: начальная дата
        end_date: конечная дата
    
    Returns:
        tuple (start_moscow, end_moscow)
    """
    start_moscow = to_moscow_time(start_date) if start_date else None
    end_moscow = to_moscow_time(end_date) if end_date else None
    return start_moscow, end_moscow

def is_same_moscow_day(dt1, dt2):
    """
    Проверяет, относятся ли два времени к одному дню в московском времени
    
    Args:
        dt1: первое время
        dt2: второе время
    
    Returns:
        bool: True если даты совпадают
    """
    if dt1 is None or dt2 is None:
        return False
    
    moscow1 = to_moscow_time(dt1)
    moscow2 = to_moscow_time(dt2)
    
    return moscow1.date() == moscow2.date()

def get_moscow_week_range(date=None):
    """
    Получает диапазон недели в московском времени
    
    Args:
        date: дата (по умолчанию текущая)
    
    Returns:
        tuple (start_of_week, end_of_week)
    """
    if date is None:
        date = get_moscow_now()
    else:
        date = to_moscow_time(date)
    
    start_of_week = date - timedelta(days=date.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    return start_of_week, end_of_week

def get_moscow_month_range(date=None):
    """
    Получает диапазон месяца в московском времени
    
    Args:
        date: дата (по умолчанию текущая)
    
    Returns:
        tuple (start_of_month, end_of_month)
    """
    if date is None:
        date = get_moscow_now()
    else:
        date = to_moscow_time(date)
    
    start_of_month = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    if date.month == 12:
        end_of_month = date.replace(year=date.year + 1, month=1, day=1) - timedelta(microseconds=1)
    else:
        end_of_month = date.replace(month=date.month + 1, day=1) - timedelta(microseconds=1)
    
    return start_of_month, end_of_month
