/**
 * Полноэкранный режим для мобильных устройств
 * Скрывает нативные элементы браузера и обеспечивает полноэкранное отображение
 */

(function() {
    'use strict';
    
    // Проверяем, что мы на мобильном устройстве
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    if (!isMobile) return;
    
    // Функция для скрытия UI браузера
    function hideBrowserUI() {
        try {
            // Скрываем адресную строку на iOS Safari
            if (window.navigator.standalone !== undefined) {
                // PWA режим - уже полноэкранный
                document.body.style.height = '100vh';
                document.body.style.height = '100dvh';
            } else {
                // Обычный браузер - пытаемся скрыть UI
                window.scrollTo(0, 1);
                setTimeout(() => window.scrollTo(0, 0), 100);
                
                // Дополнительные попытки скрыть UI
                setTimeout(() => {
                    window.scrollTo(0, 1);
                    setTimeout(() => window.scrollTo(0, 0), 50);
                }, 200);
                
                setTimeout(() => {
                    window.scrollTo(0, 1);
                    setTimeout(() => window.scrollTo(0, 0), 50);
                }, 500);
            }
        } catch (e) {
            console.warn('Не удалось скрыть UI браузера:', e);
        }
    }
    
    // Функция для предотвращения зума при двойном тапе
    function preventDoubleTapZoom() {
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function (event) {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
    }
    
    // Функция для предотвращения контекстного меню
    function preventContextMenu() {
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
        });
    }
    
    // Функция для установки правильной высоты viewport
    function setViewportHeight() {
        try {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
            
            // Обновляем высоту при изменении ориентации
            window.addEventListener('resize', () => {
                const vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', `${vh}px`);
            });
        } catch (e) {
            console.warn('Не удалось установить высоту viewport:', e);
        }
    }
    
    // Функция для улучшения производительности скроллинга
    function optimizeScrolling() {
        try {
            // Добавляем класс для оптимизации скроллинга
            document.body.classList.add('mobile-optimized');
            
            // Предотвращаем overscroll на iOS
            document.body.style.overscrollBehavior = 'contain';
            
            // Улучшаем производительность touch событий
            document.body.style.touchAction = 'manipulation';
        } catch (e) {
            console.warn('Не удалось оптимизировать скроллинг:', e);
        }
    }
    
    // Функция для обработки изменения ориентации
    function handleOrientationChange() {
        try {
            // Небольшая задержка для корректного расчета размеров
            setTimeout(() => {
                hideBrowserUI();
                setViewportHeight();
            }, 500);
        } catch (e) {
            console.warn('Ошибка при изменении ориентации:', e);
        }
    }
    
    // Инициализация при загрузке DOM
    function init() {
        try {
            // Устанавливаем высоту viewport
            setViewportHeight();
            
            // Скрываем UI браузера
            hideBrowserUI();
            
            // Предотвращаем зум при двойном тапе
            preventDoubleTapZoom();
            
            // Предотвращаем контекстное меню
            preventContextMenu();
            
            // Оптимизируем скроллинг
            optimizeScrolling();
            
            // Обрабатываем изменение ориентации
            window.addEventListener('orientationchange', handleOrientationChange);
            window.addEventListener('resize', handleOrientationChange);
            
            // Дополнительные попытки скрыть UI после загрузки
            setTimeout(hideBrowserUI, 1000);
            setTimeout(hideBrowserUI, 2000);
            setTimeout(hideBrowserUI, 3000);
            
        } catch (e) {
            console.warn('Ошибка инициализации полноэкранного режима:', e);
        }
    }
    
    // Запускаем инициализацию
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Экспортируем функции для внешнего использования
    window.MobileFullscreen = {
        hideUI: hideBrowserUI,
        setViewportHeight: setViewportHeight,
        handleOrientationChange: handleOrientationChange
    };
    
})();
