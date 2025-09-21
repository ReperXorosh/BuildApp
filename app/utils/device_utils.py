import hashlib
import re
from flask import request

def generate_device_fingerprint():
    """Генерирует отпечаток устройства на основе доступной информации"""
    components = []
    
    # User Agent
    user_agent = request.headers.get('User-Agent', '')
    if user_agent:
        components.append(user_agent)
    
    # Accept-Language
    accept_language = request.headers.get('Accept-Language', '')
    if accept_language:
        components.append(accept_language)
    
    # Accept-Encoding
    accept_encoding = request.headers.get('Accept-Encoding', '')
    if accept_encoding:
        components.append(accept_encoding)
    
    # Screen resolution (если доступно через JavaScript)
    # Это будет добавлено позже через JavaScript
    
    # Создаем хеш из всех компонентов
    fingerprint_string = '|'.join(components)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()

def get_device_name():
    """Определяет название устройства на основе User Agent"""
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # Мобильные устройства
    if 'iphone' in user_agent:
        return 'iPhone'
    elif 'ipad' in user_agent:
        return 'iPad'
    elif 'android' in user_agent:
        # Пытаемся извлечь модель Android устройства
        android_match = re.search(r'android [\d.]+; ([^)]+)', user_agent)
        if android_match:
            return f'Android ({android_match.group(1)})'
        return 'Android'
    
    # Браузеры на десктопе
    elif 'chrome' in user_agent:
        return 'Chrome'
    elif 'firefox' in user_agent:
        return 'Firefox'
    elif 'safari' in user_agent and 'chrome' not in user_agent:
        return 'Safari'
    elif 'edge' in user_agent:
        return 'Edge'
    elif 'opera' in user_agent:
        return 'Opera'
    
    # Операционные системы
    elif 'windows' in user_agent:
        return 'Windows'
    elif 'macintosh' in user_agent or 'mac os' in user_agent:
        return 'macOS'
    elif 'linux' in user_agent:
        return 'Linux'
    
    return 'Unknown Device'

def is_mobile_device():
    """Определяет, является ли устройство мобильным"""
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile_indicators = ['mobile', 'iphone', 'ipad', 'android', 'blackberry', 'windows phone']
    return any(indicator in user_agent for indicator in mobile_indicators)

def get_client_ip():
    """Получает IP адрес клиента"""
    # Проверяем заголовки прокси
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr
