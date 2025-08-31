class AvatarEditor {
    constructor(containerId, inputId, previewId) {
        this.container = document.getElementById(containerId);
        this.input = document.getElementById(inputId);
        this.preview = document.getElementById(previewId);
        this.canvas = null;
        this.ctx = null;
        this.image = null;
        this.isDragging = false;
        this.dragStart = { x: 0, y: 0 };
        this.offset = { x: 0, y: 0 };
        this.scale = 1;
        this.minScale = 0.5;
        this.maxScale = 3;
        this.isInitialized = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
    }
    
    createCanvas() {
        if (this.isInitialized) return;
        
        // Создаем canvas для редактирования
        this.canvas = document.createElement('canvas');
        this.canvas.width = 300;
        this.canvas.height = 300;
        this.canvas.style.border = '2px solid #007bff';
        this.canvas.style.borderRadius = '50%';
        this.canvas.style.cursor = 'move';
        this.canvas.style.maxWidth = '100%';
        this.canvas.style.height = 'auto';
        
        this.ctx = this.canvas.getContext('2d');
        
        // Добавляем canvas в контейнер
        const canvasContainer = document.createElement('div');
        canvasContainer.className = 'text-center mb-3';
        canvasContainer.appendChild(this.canvas);
        
        // Вставляем canvas перед preview
        this.preview.parentNode.insertBefore(canvasContainer, this.preview);
        
        // Скрываем оригинальный preview
        this.preview.style.display = 'none';
        
        this.setupControls();
        this.bindCanvasEvents();
        this.isInitialized = true;
    }
    
    bindEvents() {
        // Обработка выбора файла
        this.input.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file && this.isValidImage(file)) {
                this.createCanvas(); // Создаем редактор только при выборе файла
                this.loadImage(file);
            } else if (!file) {
                this.hideEditor(); // Скрываем редактор если файл не выбран
            }
        });
    }
    
    bindCanvasEvents() {
        if (!this.canvas) return;
        
        // Обработка перетаскивания
        this.canvas.addEventListener('mousedown', (e) => {
            this.isDragging = true;
            this.dragStart = this.getMousePos(e);
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
        });
        
        // Обработка колесика мыши для масштабирования
        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            this.scale = Math.max(this.minScale, Math.min(this.maxScale, this.scale * delta));
            this.draw();
        });
    }
    
    hideEditor() {
        // Удаляем canvas и контролы если они есть
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.remove();
        }
        
        // Показываем оригинальный preview
        this.preview.style.display = 'inline-block';
        this.preview.src = this.preview.getAttribute('data-default-src') || "{{ url_for('static', filename='img/default-avatar.png') }}";
        
        this.isInitialized = false;
        this.canvas = null;
        this.ctx = null;
        this.image = null;
    }
    
    setupControls() {
        // Создаем панель управления
        const controls = document.createElement('div');
        controls.className = 'd-flex justify-content-center gap-2 mb-3';
        controls.innerHTML = `
            <button type="button" class="btn btn-outline-primary btn-sm" onclick="avatarEditor.rotate(-90)">
                <svg width="16" height="16" fill="currentColor">
                    <path d="M8 3a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.5.5H6a.5.5 0 0 1 0-1h1.5V3.5A.5.5 0 0 1 8 3zm3.5 1a.5.5 0 0 1 .5.5v5a.5.5 0 0 1-.5.5h-5a.5.5 0 0 1 0-1h4.5V2.5a.5.5 0 0 1 .5-.5z"/>
                </svg>
                Повернуть влево
            </button>
            <button type="button" class="btn btn-outline-primary btn-sm" onclick="avatarEditor.rotate(90)">
                <svg width="16" height="16" fill="currentColor">
                    <path d="M8 3a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.5.5H6a.5.5 0 0 1 0-1h1.5V3.5A.5.5 0 0 1 8 3zm3.5 1a.5.5 0 0 1 .5.5v5a.5.5 0 0 1-.5.5h-5a.5.5 0 0 1 0-1h4.5V2.5a.5.5 0 0 1 .5-.5z"/>
                </svg>
                Повернуть вправо
            </button>
            <button type="button" class="btn btn-outline-secondary btn-sm" onclick="avatarEditor.reset()">
                <svg width="16" height="16" fill="currentColor">
                    <path d="M8 3a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.5.5H6a.5.5 0 0 1 0-1h1.5V3.5A.5.5 0 0 1 8 3zm3.5 1a.5.5 0 0 1 .5.5v5a.5.5 0 0 1-.5.5h-5a.5.5 0 0 1 0-1h4.5V2.5a.5.5 0 0 1 .5-.5z"/>
                </svg>
                Сбросить
            </button>
        `;
        
        // Вставляем контролы после canvas
        this.canvas.parentNode.appendChild(controls);
        
        // Добавляем подсказки
        const hints = document.createElement('div');
        hints.className = 'text-muted small text-center';
        hints.innerHTML = `
            <div>💡 <strong>Советы:</strong></div>
            <div>• Перетаскивайте изображение мышкой</div>
            <div>• Используйте колесико мыши для масштабирования</div>
            <div>• Нажмите кнопки для поворота</div>
        `;
        this.canvas.parentNode.appendChild(hints);
    }
    
    isValidImage(file) {
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
        return validTypes.includes(file.type);
    }
    
    loadImage(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            this.image = new Image();
            this.image.onload = () => {
                this.reset();
                this.draw();
            };
            this.image.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
    
    getMousePos(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }
    
    draw() {
        if (!this.image || !this.canvas) return;
        
        // Очищаем canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Создаем круглую маску
        this.ctx.save();
        this.ctx.beginPath();
        this.ctx.arc(this.canvas.width / 2, this.canvas.height / 2, this.canvas.width / 2 - 2, 0, 2 * Math.PI);
        this.ctx.clip();
        
        // Вычисляем размеры и позицию изображения
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
    
    updatePreview() {
        if (!this.canvas) return;
        
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
        
        // Копируем изображение с основного canvas
        tempCtx.drawImage(this.canvas, 0, 0, 64, 64);
        tempCtx.restore();
        
        // Обновляем preview
        this.preview.src = tempCanvas.toDataURL();
        this.preview.style.display = 'inline-block';
    }
    
    rotate(degrees) {
        if (!this.image) return;
        
        // Создаем временный canvas для поворота
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        
        // Вычисляем новые размеры после поворота
        const angle = degrees * Math.PI / 180;
        const cos = Math.abs(Math.cos(angle));
        const sin = Math.abs(Math.sin(angle));
        const newWidth = this.image.width * cos + this.image.height * sin;
        const newHeight = this.image.width * sin + this.image.height * cos;
        
        tempCanvas.width = newWidth;
        tempCanvas.height = newHeight;
        
        // Поворачиваем изображение
        tempCtx.translate(newWidth / 2, newHeight / 2);
        tempCtx.rotate(angle);
        tempCtx.drawImage(this.image, -this.image.width / 2, -this.image.height / 2);
        
        // Создаем новое изображение
        const newImage = new Image();
        newImage.onload = () => {
            this.image = newImage;
            this.draw();
        };
        newImage.src = tempCanvas.toDataURL();
    }
    
    reset() {
        this.offset = { x: 0, y: 0 };
        this.scale = 1;
        this.draw();
    }
    
    getEditedImage() {
        if (!this.image || !this.canvas) return null;
        
        // Создаем canvas с отредактированным изображением
        const outputCanvas = document.createElement('canvas');
        outputCanvas.width = 200;
        outputCanvas.height = 200;
        const outputCtx = outputCanvas.getContext('2d');
        
        // Создаем круглую маску
        outputCtx.save();
        outputCtx.beginPath();
        outputCtx.arc(100, 100, 100, 0, 2 * Math.PI);
        outputCtx.clip();
        
        // Масштабируем координаты для выходного размера
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

// Глобальная переменная для доступа к редактору
let avatarEditor = null;

// НЕ создаем автоматическую инициализацию для профиля
// Редактор будет создаваться только при выборе файла
