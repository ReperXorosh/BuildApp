# Utils package

# Импортируем основные утилиты для удобства использования
from .mobile_detection import is_mobile_device, is_tablet_device, get_device_type
from .timezone_utils import get_moscow_now, format_moscow_time, to_moscow_time
from .activity_logger import log_activity, log_page_view, log_user_action

__all__ = [
    'is_mobile_device',
    'is_tablet_device', 
    'get_device_type',
    'get_moscow_now',
    'format_moscow_time',
    'to_moscow_time',
    'log_activity',
    'log_page_view',
    'log_user_action'
]
