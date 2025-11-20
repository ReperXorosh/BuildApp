"""
Утилиты для определения мобильных устройств

Для принудительного переключения версии используйте:
- URL параметр: ?mobile=1 (мобильная) или ?mobile=0 (десктопная)
- Cookie: force_mobile=1 (мобильная) или force_desktop=1 (десктопная)
"""
import re
from flask import request


def is_mobile_device():
    """
    Определяет, является ли устройство мобильным на основе User-Agent
    Приоритет: сначала проверяем десктопные браузеры, затем мобильные
    
    Также проверяет:
    - Параметр ?mobile=1 или ?mobile=0 в URL (приоритет)
    - Cookie 'force_mobile' или 'force_desktop' (второй приоритет)
    """
    # ПРИОРИТЕТ 0: Принудительное переключение через параметр URL
    mobile_param = request.args.get('mobile')
    if mobile_param == '1':
        return True
    elif mobile_param == '0':
        return False
    
    # ПРИОРИТЕТ 0.5: Принудительное переключение через cookie
    force_mobile = request.cookies.get('force_mobile')
    force_desktop = request.cookies.get('force_desktop')
    if force_mobile == '1':
        return True
    elif force_desktop == '1':
        return False
    
    user_agent = request.headers.get('User-Agent', '').lower()
    
    if not user_agent:
        return False
    
    # ПРИОРИТЕТ 1: Проверяем явные десктопные операционные системы
    desktop_os_indicators = [
        'windows nt',      # Windows
        'windows 10',     # Windows 10
        'windows 11',     # Windows 11
        'macintosh',      # macOS
        'mac os x',       # macOS (старые версии)
        'mac os',         # macOS (старые версии)
        'x11',            # Linux X11
        'linux',          # Linux (но не Android!)
        'win64',          # Windows 64-bit
        'wow64',          # Windows on Windows 64
        'win32',          # Windows 32-bit
        'freebsd',        # FreeBSD
        'openbsd',        # OpenBSD
        'netbsd'          # NetBSD
    ]
    
    # Проверяем наличие десктопной ОС
    has_desktop_os = any(indicator in user_agent for indicator in desktop_os_indicators)
    
    # ПРИОРИТЕТ 2: Проверяем популярные десктопные браузеры
    desktop_browser_indicators = [
        'edg/',           # Microsoft Edge (десктоп)
        'chrome/',        # Google Chrome (десктоп)
        'firefox/',       # Firefox (десктоп)
        'safari/',        # Safari (десктоп, но не iOS!)
        'opera/',         # Opera (десктоп)
        'msie',           # Internet Explorer
        'trident/',       # Internet Explorer
        'rv:'             # Internet Explorer
    ]
    
    has_desktop_browser = any(indicator in user_agent for indicator in desktop_browser_indicators)
    
    # Если есть десктопная ОС И десктопный браузер, это точно десктоп
    if has_desktop_os and has_desktop_browser:
        # Дополнительная проверка: если это Windows/Mac/Linux БЕЗ мобильных индикаторов - точно десктоп
        mobile_os_indicators = ['android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone', 'mobile']
        has_mobile_os = any(indicator in user_agent for indicator in mobile_os_indicators)
        
        if not has_mobile_os:
            return False
    
    # ПРИОРИТЕТ 3: Если есть десктопная ОС без мобильных индикаторов - это десктоп
    if has_desktop_os:
        mobile_os_indicators = ['android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone']
        has_mobile_os = any(indicator in user_agent for indicator in mobile_os_indicators)
        
        # Если есть десктопная ОС и нет мобильной ОС - это десктоп
        if not has_mobile_os:
            return False
    
    # ПРИОРИТЕТ 4: Проверяем мобильные операционные системы
    # Android (но не Linux десктоп!)
    if 'android' in user_agent:
        return True
    
    # iOS устройства
    if 'iphone' in user_agent or 'ipad' in user_agent or 'ipod' in user_agent:
        return True
    
    # Другие мобильные ОС
    if any(indicator in user_agent for indicator in ['blackberry', 'windows phone', 'webos', 'palm']):
        return True
    
    # ПРИОРИТЕТ 5: Проверяем специфичные мобильные браузеры и устройства
    mobile_specific_patterns = [
        r'opera mini',
        r'opera mobi',
        r'kindle',
        r'silk',
        r'fennec',
        r'maemo',
        r'minimo',
        r'up\.browser',
        r'up\.link',
        r'iemobile',
        r'mobile.*safari',  # Mobile Safari (но не десктопный Safari!)
        r'wml',
        r'wap'
    ]
    
    for pattern in mobile_specific_patterns:
        if re.search(pattern, user_agent):
            return True
    
    # По умолчанию считаем десктопом
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
