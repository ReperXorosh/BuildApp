/**
 * Утилиты для работы с часовыми поясами на клиентской стороне
 */

// Список популярных часовых поясов
const TIMEZONES = [
    { value: 'Europe/Moscow', label: 'Москва (UTC+3)' },
    { value: 'Europe/Kiev', label: 'Киев (UTC+2)' },
    { value: 'Europe/Minsk', label: 'Минск (UTC+3)' },
    { value: 'Europe/Kaliningrad', label: 'Калининград (UTC+2)' },
    { value: 'Europe/Samara', label: 'Самара (UTC+4)' },
    { value: 'Asia/Yekaterinburg', label: 'Екатеринбург (UTC+5)' },
    { value: 'Asia/Omsk', label: 'Омск (UTC+6)' },
    { value: 'Asia/Novosibirsk', label: 'Новосибирск (UTC+7)' },
    { value: 'Asia/Krasnoyarsk', label: 'Красноярск (UTC+7)' },
    { value: 'Asia/Irkutsk', label: 'Иркутск (UTC+8)' },
    { value: 'Asia/Yakutsk', label: 'Якутск (UTC+9)' },
    { value: 'Asia/Vladivostok', label: 'Владивосток (UTC+10)' },
    { value: 'Asia/Magadan', label: 'Магадан (UTC+11)' },
    { value: 'Asia/Kamchatka', label: 'Камчатка (UTC+12)' },
    { value: 'Europe/London', label: 'Лондон (UTC+0/+1)' },
    { value: 'Europe/Paris', label: 'Париж (UTC+1/+2)' },
    { value: 'Europe/Berlin', label: 'Берлин (UTC+1/+2)' },
    { value: 'America/New_York', label: 'Нью-Йорк (UTC-5/-4)' },
    { value: 'America/Los_Angeles', label: 'Лос-Анджелес (UTC-8/-7)' },
    { value: 'Asia/Tokyo', label: 'Токио (UTC+9)' },
    { value: 'Asia/Shanghai', label: 'Шанхай (UTC+8)' },
    { value: 'Australia/Sydney', label: 'Сидней (UTC+10/+11)' }
];

/**
 * Определяет часовой пояс браузера
 * @returns {string} Часовой пояс в формате IANA
 */
function detectTimezone() {
    try {
        return Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch (error) {
        console.warn('Не удалось определить часовой пояс:', error);
        return 'Europe/Moscow'; // По умолчанию московское время
    }
}

/**
 * Получает смещение часового пояса в минутах
 * @param {string} timezone - Часовой пояс
 * @returns {number} Смещение в минутах
 */
function getTimezoneOffset(timezone = null) {
    const tz = timezone || detectTimezone();
    const now = new Date();
    const utc = new Date(now.getTime() + (now.getTimezoneOffset() * 60000));
    const targetTime = new Date(utc.toLocaleString("en-US", {timeZone: tz}));
    return (targetTime.getTime() - utc.getTime()) / (1000 * 60);
}

/**
 * Форматирует время в указанном часовом поясе
 * @param {Date} date - Дата для форматирования
 * @param {string} timezone - Часовой пояс
 * @param {string} format - Формат (short, medium, long)
 * @returns {string} Отформатированная дата
 */
function formatTimeInTimezone(date, timezone = null, format = 'short') {
    const tz = timezone || detectTimezone();
    
    const options = {
        timeZone: tz,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    };
    
    if (format === 'date') {
        options.hour = undefined;
        options.minute = undefined;
        options.second = undefined;
    } else if (format === 'time') {
        options.year = undefined;
        options.month = undefined;
        options.day = undefined;
    }
    
    return new Intl.DateTimeFormat('ru-RU', options).format(date);
}

/**
 * Отправляет часовой пояс на сервер
 * @param {string} timezone - Часовой пояс
 */
function sendTimezoneToServer(timezone) {
    fetch('/user/set-timezone', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ timezone: timezone })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Часовой пояс обновлен:', timezone);
            // Обновляем страницу для применения изменений
            if (data.reload) {
                window.location.reload();
            }
        } else {
            console.error('Ошибка обновления часового пояса:', data.error);
        }
    })
    .catch(error => {
        console.error('Ошибка отправки часового пояса:', error);
    });
}

/**
 * Получает CSRF токен из мета-тега
 * @returns {string} CSRF токен
 */
function getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute('content') : '';
}

/**
 * Инициализирует определение часового пояса при загрузке страницы
 */
function initTimezoneDetection() {
    // Проверяем, есть ли уже сохраненный часовой пояс
    const savedTimezone = localStorage.getItem('user_timezone');
    const detectedTimezone = detectTimezone();
    
    if (savedTimezone && savedTimezone !== detectedTimezone) {
        // Если сохраненный часовой пояс отличается от определенного, 
        // предлагаем пользователю выбрать
        showTimezoneNotification(detectedTimezone, savedTimezone);
    } else if (!savedTimezone) {
        // Если часовой пояс не сохранен, определяем и сохраняем
        sendTimezoneToServer(detectedTimezone);
        localStorage.setItem('user_timezone', detectedTimezone);
    }
}

/**
 * Показывает уведомление о смене часового пояса
 * @param {string} detected - Определенный часовой пояс
 * @param {string} saved - Сохраненный часовой пояс
 */
function showTimezoneNotification(detected, saved) {
    const notification = document.createElement('div');
    notification.className = 'alert alert-info alert-dismissible fade show position-fixed';
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    
    const timezoneLabel = TIMEZONES.find(tz => tz.value === detected)?.label || detected;
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi bi-clock me-2"></i>
            <div class="flex-grow-1">
                <strong>Обнаружен новый часовой пояс:</strong><br>
                <small>${timezoneLabel}</small>
            </div>
        </div>
        <div class="mt-2">
            <button class="btn btn-sm btn-primary me-2" onclick="updateTimezone('${detected}')">
                Обновить
            </button>
            <button class="btn btn-sm btn-secondary" onclick="dismissTimezoneNotification()">
                Позже
            </button>
        </div>
        <button type="button" class="btn-close" onclick="dismissTimezoneNotification()"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Автоматически скрываем через 10 секунд
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 10000);
}

/**
 * Обновляет часовой пояс пользователя
 * @param {string} timezone - Новый часовой пояс
 */
function updateTimezone(timezone) {
    sendTimezoneToServer(timezone);
    localStorage.setItem('user_timezone', timezone);
    dismissTimezoneNotification();
}

/**
 * Закрывает уведомление о часовом поясе
 */
function dismissTimezoneNotification() {
    const notification = document.querySelector('.alert-info.position-fixed');
    if (notification) {
        notification.remove();
    }
}

/**
 * Создает селектор часовых поясов
 * @param {string} currentTimezone - Текущий часовой пояс
 * @param {Function} onChange - Callback при изменении
 * @returns {HTMLElement} Элемент селектора
 */
function createTimezoneSelector(currentTimezone = 'Europe/Moscow', onChange = null) {
    const select = document.createElement('select');
    select.className = 'form-select';
    select.name = 'timezone';
    
    TIMEZONES.forEach(tz => {
        const option = document.createElement('option');
        option.value = tz.value;
        option.textContent = tz.label;
        if (tz.value === currentTimezone) {
            option.selected = true;
        }
        select.appendChild(option);
    });
    
    if (onChange) {
        select.addEventListener('change', (e) => {
            onChange(e.target.value);
        });
    }
    
    return select;
}

// Инициализируем при загрузке DOM
document.addEventListener('DOMContentLoaded', initTimezoneDetection);

// Экспортируем функции для глобального использования
window.TimezoneUtils = {
    detectTimezone,
    getTimezoneOffset,
    formatTimeInTimezone,
    sendTimezoneToServer,
    createTimezoneSelector,
    updateTimezone,
    TIMEZONES
};
