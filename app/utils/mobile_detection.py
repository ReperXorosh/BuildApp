"""
Утилиты для определения мобильных устройств
"""
import re
from flask import request


def is_mobile_device():
    """
    Определяет, является ли устройство мобильным на основе User-Agent
    """
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # Дополнительная проверка для Safari на iOS
    if 'safari' in user_agent and ('iphone' in user_agent or 'ipad' in user_agent or 'ipod' in user_agent):
        return True
    
    # Паттерны для мобильных устройств
    mobile_patterns = [
        r'android',
        r'iphone',
        r'ipad',
        r'ipod',
        r'blackberry',
        r'windows phone',
        r'mobile',
        r'opera mini',
        r'opera mobi',
        r'kindle',
        r'silk',
        r'webos',
        r'palm',
        r'symbian',
        r'fennec',
        r'maemo',
        r'minimo',
        r'netfront',
        r'up\.browser',
        r'up\.link',
        r'audiovox',
        r'avantgo',
        r'benq',
        r'cell',
        r'cldc',
        r'cmd-',
        r'danger',
        r'docomo',
        r'elaine',
        r'htc',
        r'iemobile',
        r'j2me',
        r'java',
        r'midp-',
        r'mot-',
        r'motorola',
        r'netfront',
        r'newt',
        r'nintendo',
        r'nitro',
        r'nokia',
        r'novarra',
        r'openwave',
        r'palm',
        r'panasonic',
        r'pantech',
        r'philips',
        r'playstation',
        r'proxinet',
        r'proximus',
        r'qtek',
        r'samsung',
        r'sanyo',
        r'sch-',
        r'sec-',
        r'sendo',
        r'sgh-',
        r'sharp',
        r'sie-',
        r'siemens',
        r'smartphone',
        r'sony',
        r'sph-',
        r'symbian',
        r't-mobile',
        r'telus',
        r'tim-',
        r'toshiba',
        r'treo',
        r'tsm-',
        r'upg1',
        r'ups-',
        r'vertu',
        r'vodafone',
        r'wap',
        r'wellcom',
        r'wig',
        r'wmlb',
        r'xda',
        r'xoom',
        r'zte'
    ]
    
    # Проверяем каждый паттерн
    for pattern in mobile_patterns:
        if re.search(pattern, user_agent):
            return True
    
    return False


def is_tablet_device():
    """
    Определяет, является ли устройство планшетом
    """
    user_agent = request.headers.get('User-Agent', '').lower()
    
    tablet_patterns = [
        r'ipad',
        r'android(?!.*mobile)',
        r'kindle',
        r'silk',
        r'playbook',
        r'bb10',
        r'rim tablet'
    ]
    
    for pattern in tablet_patterns:
        if re.search(pattern, user_agent):
            return True
    
    return False


def get_device_type():
    """
    Возвращает тип устройства: 'mobile', 'tablet', 'desktop'
    """
    if is_tablet_device():
        return 'tablet'
    elif is_mobile_device():
        return 'mobile'
    else:
        return 'desktop'


def get_screen_size_category():
    """
    Определяет категорию размера экрана на основе User-Agent
    """
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # Большие планшеты и десктопы
    if 'ipad pro' in user_agent or 'surface' in user_agent:
        return 'large'
    
    # Обычные планшеты
    if is_tablet_device():
        return 'medium'
    
    # Мобильные устройства
    if is_mobile_device():
        return 'small'
    
    # Десктопы по умолчанию
    return 'large'


def is_touch_device():
    """
    Определяет, поддерживает ли устройство touch-интерфейс
    """
    user_agent = request.headers.get('User-Agent', '').lower()
    
    touch_patterns = [
        r'android',
        r'iphone',
        r'ipad',
        r'ipod',
        r'blackberry',
        r'windows phone',
        r'touch',
        r'kindle',
        r'silk',
        r'webos',
        r'palm',
        r'playbook',
        r'bb10',
        r'rim tablet',
        r'surface'
    ]
    
    for pattern in touch_patterns:
        if re.search(pattern, user_agent):
            return True
    
    return False
