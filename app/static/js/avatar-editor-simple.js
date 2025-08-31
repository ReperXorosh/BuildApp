// Простой и надежный редактор аватаров
class SimpleAvatarEditor {
    constructor(containerId, inputId, previewId) {
        console.log('🔧 Создание SimpleAvatarEditor...');
        
        this.container = document.getElementById(containerId);
        this.input = document.getElementById(inputId);
        this.preview = document.getElementById(previewId);
        
        if (!this.container || !this.input || !this.preview) {
            console.error('❌ Не найдены необходимые элементы');
            return;
        }
        
        this.canvas = null;
        this.ctx = null;
        this.image = null;
        this.isDragging = false;
        this.dragStart = { x: 0, y: 0 };
        this.offset = { x: 0, y: 0 };
        this.scale = 1;
        
        console.log('✅ SimpleAvatarEditor создан');
    }
    
    // Создание интерфейса редактора
    createInterface() {
        console.log('🎨 Создание интерфейса редактора...');
        
        // Очищаем контейнер
        this.container.innerHTML = '';
        
        // Создаем canvas
        this.canvas = document.createElement('canvas');
        this.canvas.width = 300;
        this.canvas.height = 300;
        this.canvas.style.border = '3px solid #007bff';
        this.canvas.style.borderRadius = '50%';
        this.canvas.style.cursor = 'move';
        this.canvas.style.maxWidth = '100%';
        this.canvas.style.height = 'auto';
        this.canvas.style.margin = '0 auto';
        this.canvas.style.display = 'block';
        
        this.ctx = this.canvas.getContext('2d');
        
        // Создаем контейнер для canvas
        const canvasContainer = document.createElement('div');
        canvasContainer.className = 'text-center mb-3';
        canvasContainer.style.border = '2px solid #e9ecef';
        canvasContainer.style.borderRadius = '10px';
        canvasContainer.style.padding = '20px';
        canvasContainer.style.backgroundColor = '#f8f9fa';
        canvasContainer.appendChild(this.canvas);
        
        // Создаем кнопки управления
        const controls = document.createElement('div');
        controls.className = 'd-flex justify-content-center gap-2 mb-3 flex-wrap';
        controls.innerHTML = `
            <button type="button" class="btn btn-outline-primary btn-sm" onclick="simpleAvatarEditor.rotate(-90)">
                <i class="bi bi-arrow-counterclockwise"></i> Повернуть влево
            </button>
            <button type="button" class="btn btn-outline-primary btn-sm" onclick="simpleAvatarEditor.rotate(90)">
                <i class="bi bi-arrow-clockwise"></i> Повернуть вправо
            </button>
            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="simpleAvatarEditor.reset()">
                <i class="bi bi-arrow-clockwise"></i> Сбросить
            </button>
        `;
        
        // Создаем подсказки
        const hints = document.createElement('div');
        hints.className = 'alert alert-info small';
        hints.innerHTML = `
            <strong>💡 Как использовать редактор:</strong><br>
            • Перетаскивайте изображение мышкой<br>
            • Используйте колесико мыши для масштабирования<br>
            • Нажмите кнопки для поворота
        `;
        
        // Добавляем все элементы в контейнер
        this.container.appendChild(canvasContainer);
        this.container.appendChild(controls);
        this.container.appendChild(hints);
        
        // Привязываем события
        this.bindEvents();
        
        console.log('✅ Интерфейс редактора создан');
    }
    
    // Привязка событий
    bindEvents() {
        if (!this.canvas) return;
        
        // Перетаскивание
        this.canvas.addEventListener('mousedown', (e) => {
            this.isDragging = true;
            this.dragStart = this.getMousePos(e);
            this.canvas.style.cursor = 'grabbing';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (this.isDragging) {
                const pos = this.getMousePos(e);
                this.offset.x += pos.x - this.dragStart.x;
                this.offset.y += pos.y - this.dragStart.y;
                this.dragStart = pos;
                this.draw();
            }
        });
        
        document.addEventListener('mouseup', () => {
            this.isDragging = false;
            if (this.canvas) {
                this.canvas.style.cursor = 'move';
            }
        });
        
        // Масштабирование
        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            this.scale = Math.max(0.5, Math.min(3, this.scale * delta));
            this.draw();
        });
        
        console.log('✅ События привязаны');
    }
    
    // Загрузка изображения
    loadImage(file) {
        console.log('📁 Загрузка изображения...');
        
        const reader = new FileReader();
        reader.onload = (e) => {
            this.image = new Image();
            this.image.onload = () => {
                console.log('✅ Изображение загружено');
                this.reset();
                this.draw();
            };
            this.image.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
    
    // Отрисовка
    draw() {
        if (!this.image || !this.canvas) return;
        
        // Очищаем canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Создаем круглую маску
        this.ctx.save();
        this.ctx.beginPath();
        this.ctx.arc(this.canvas.width / 2, this.canvas.height / 2, this.canvas.width / 2 - 3, 0, 2 * Math.PI);
        this.ctx.clip();
        
        // Вычисляем размеры и позицию
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const scaledWidth = this.image.width * this.scale;
        const scaledHeight = this.image.height * this.scale;
        
        // Рисуем изображение
        this.ctx.drawImage(
            this.image,
            centerX - scaledWidth / 2 + this.offset.x,
            centerY - scaledHeight / 2 + this.offset.y,
            scaledWidth,
            scaledHeight
        );
        
        this.ctx.restore();
        
        // Обновляем предпросмотр
        this.updatePreview();
    }
    
    // Обновление предпросмотра
    updatePreview() {
        if (!this.canvas || !this.preview) return;
        
        // Создаем временный canvas для предпросмотра
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = 64;
        tempCanvas.height = 64;
        const tempCtx = tempCanvas.getContext('2d');
        
        // Создаем круглую маску
        tempCtx.save();
        tempCtx.beginPath();
        tempCtx.arc(32, 32, 32, 0, 2 * Math.PI);
        tempCtx.clip();
        
        // Копируем изображение
        tempCtx.drawImage(this.canvas, 0, 0, 64, 64);
        tempCtx.restore();
        
        // Обновляем preview
        this.preview.src = tempCanvas.toDataURL();
        this.preview.style.display = 'inline-block';
    }
    
    // Поворот
    rotate(degrees) {
        if (!this.image) return;
        
        console.log(`🔄 Поворот на ${degrees} градусов`);
        
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        
        const angle = degrees * Math.PI / 180;
        const cos = Math.abs(Math.cos(angle));
        const sin = Math.abs(Math.sin(angle));
        const newWidth = this.image.width * cos + this.image.height * sin;
        const newHeight = this.image.width * sin + this.image.height * cos;
        
        tempCanvas.width = newWidth;
        tempCanvas.height = newHeight;
        
        tempCtx.translate(newWidth / 2, newHeight / 2);
        tempCtx.rotate(angle);
        tempCtx.drawImage(this.image, -this.image.width / 2, -this.image.height / 2);
        
        const newImage = new Image();
        newImage.onload = () => {
            this.image = newImage;
            this.draw();
        };
        newImage.src = tempCanvas.toDataURL();
    }
    
    // Сброс
    reset() {
        console.log('🔄 Сброс настроек');
        this.offset = { x: 0, y: 0 };
        this.scale = 1;
        this.draw();
    }
    
    // Получение позиции мыши
    getMousePos(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }
    
    // Получение отредактированного изображения
    getEditedImage() {
        if (!this.image || !this.canvas) return null;
        
        console.log('💾 Получение отредактированного изображения');
        
        const outputCanvas = document.createElement('canvas');
        outputCanvas.width = 200;
        outputCanvas.height = 200;
        const outputCtx = outputCanvas.getContext('2d');
        
        // Создаем круглую маску
        outputCtx.save();
        outputCtx.beginPath();
        outputCtx.arc(100, 100, 100, 0, 2 * Math.PI);
        outputCtx.clip();
        
        // Масштабируем координаты
        const scale = 200 / 300;
        const centerX = 100;
        const centerY = 100;
        const scaledWidth = this.image.width * this.scale * scale;
        const scaledHeight = this.image.height * this.scale * scale;
        
        outputCtx.drawImage(
            this.image,
            centerX - scaledWidth / 2 + this.offset.x * scale,
            centerY - scaledHeight / 2 + this.offset.y * scale,
            scaledWidth,
            scaledHeight
        );
        
        outputCtx.restore();
        
        return outputCanvas.toDataURL('image/jpeg', 0.9);
    }
}

// Глобальная переменная
let simpleAvatarEditor = null;

// Функция для инициализации редактора
function initSimpleAvatarEditor() {
    console.log('🚀 Инициализация SimpleAvatarEditor...');
    
    const container = document.getElementById('avatar-editor-container');
    const input = document.getElementById('avatar');
    const preview = document.getElementById('avatar-preview');
    
    if (!container || !input || !preview) {
        console.error('❌ Не найдены необходимые элементы для редактора');
        return false;
    }
    
    // Создаем редактор
    simpleAvatarEditor = new SimpleAvatarEditor('avatar-editor-container', 'avatar', 'avatar-preview');
    
    // Обработчик выбора файла
    input.addEventListener('change', function(e) {
        const file = e.target.files[0];
        console.log('📁 Файл выбран:', file?.name);
        
        if (file) {
            // Проверка размера
            if (file.size > 2 * 1024 * 1024) {
                alert('Размер файла не должен превышать 2 МБ');
                this.value = '';
                return;
            }
            
            // Проверка типа
            const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
            if (!validTypes.includes(file.type)) {
                alert('Поддерживаются только форматы: PNG, JPG, JPEG');
                this.value = '';
                return;
            }
            
            console.log('✅ Файл прошел валидацию');
            
            // Показываем контейнер
            container.style.display = 'block';
            console.log('✅ Контейнер показан');
            
            // Создаем интерфейс редактора
            simpleAvatarEditor.createInterface();
            
            // Загружаем изображение
            simpleAvatarEditor.loadImage(file);
            
        } else {
            console.log('📁 Файл не выбран');
            container.style.display = 'none';
        }
    });
    
    console.log('✅ SimpleAvatarEditor инициализирован');
    return true;
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 DOM загружен, инициализируем редактор...');
    initSimpleAvatarEditor();
});

console.log('📦 SimpleAvatarEditor загружен');
