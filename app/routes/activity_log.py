from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.models.activity_log import ActivityLog
from app.models.users import Users
from app.extensions import db
from datetime import datetime, timedelta, timezone

activity_log = Blueprint('activity_log', __name__)

# Простой словарь переводов
TRANSLATIONS = {
    'ru': {
        'Журнал действий': 'Журнал действий',
        'Все действия': 'Все действия',
        'Действия пользователя': 'Действия пользователя',
        'Фильтр по дате': 'Фильтр по дате',
        'Поиск': 'Поиск',
        'Пользователь': 'Пользователь',
        'Роль': 'Роль',
        'Действие': 'Действие',
        'Описание': 'Описание',
        'Дата': 'Дата',
        'IP адрес': 'IP адрес',
        'Страница': 'Страница',
        'Нет данных': 'Нет данных',
        'У вас нет прав для просмотра журнала действий': 'У вас нет прав для просмотра журнала действий',
        'Экспорт в CSV': 'Экспорт в CSV',
        'Очистить журнал': 'Очистить журнал',
        'Подтвердите удаление': 'Подтвердите удаление',
        'Все записи будут удалены': 'Все записи будут удалены',
        'Отмена': 'Отмена',
        'Удалить': 'Удалить',
    },
    'en': {
        'Журнал действий': 'Activity Log',
        'Все действия': 'All Actions',
        'Действия пользователя': 'User Actions',
        'Фильтр по дате': 'Date Filter',
        'Поиск': 'Search',
        'Пользователь': 'User',
        'Роль': 'Role',
        'Действие': 'Action',
        'Описание': 'Description',
        'Дата': 'Date',
        'IP адрес': 'IP Address',
        'Страница': 'Page',
        'Нет данных': 'No data',
        'У вас нет прав для просмотра журнала действий': 'You do not have permission to view the activity log',
        'Экспорт в CSV': 'Export to CSV',
        'Очистить журнал': 'Clear Log',
        'Подтвердите удаление': 'Confirm Deletion',
        'Все записи будут удалены': 'All records will be deleted',
        'Отмена': 'Cancel',
        'Удалить': 'Delete',
    }
}

def gettext(text):
    """Простая функция перевода"""
    language = session.get('language', 'ru')
    return TRANSLATIONS.get(language, {}).get(text, text)

def format_moscow_time(dt):
    """Форматирует время в московском формате"""
    if not dt:
        return "Нет данных"
    
    try:
        # Если время без часового пояса, считаем его московским
        if dt.tzinfo is None:
            moscow_tz = timezone(timedelta(hours=3))
            dt = dt.replace(tzinfo=moscow_tz)
        else:
            # Если время с часовым поясом, конвертируем в московское
            moscow_tz = timezone(timedelta(hours=3))
            dt = dt.astimezone(moscow_tz)
        
        return dt.strftime('%d.%m.%Y %H:%M:%S')
    except Exception:
        return "Ошибка времени"

@activity_log.context_processor
def inject_gettext():
    """Делает функцию gettext доступной в шаблонах"""
    return dict(gettext=gettext, format_moscow_time=format_moscow_time)

def is_admin():
    """Проверяет, является ли пользователь администратором"""
    return current_user.is_authenticated and current_user.role == 'Инженер ПТО'

@activity_log.route('/activity-log')
@login_required
def view_activity_log():
    """Страница журнала действий"""
    if not is_admin():
        return render_template('main/error.html', 
                             error=gettext("У вас нет прав для просмотра журнала действий"))
    
    # Логируем просмотр журнала действий
    ActivityLog.log_action(
        user_id=current_user.userid,
        user_login=current_user.login,
        action="Просмотр журнала действий",
        description=f"Администратор {current_user.login} открыл страницу журнала действий",
        ip_address=request.remote_addr,
        page_url=request.url,
        method=request.method
    )
    
    # Получаем параметры фильтрации
    page = request.args.get('page', 1, type=int)
    per_page = 50
    user_filter = request.args.get('user', '')
    action_filter = request.args.get('action', '')
    date_filter = request.args.get('date', '')
    
    # Базовый запрос
    query = ActivityLog.query
    
    # Применяем фильтры
    if user_filter:
        query = query.filter(ActivityLog.user_login.contains(user_filter))
    
    if action_filter:
        query = query.filter(ActivityLog.action.contains(action_filter))
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d')
            next_date = filter_date + timedelta(days=1)
            query = query.filter(
                ActivityLog.created_at >= filter_date,
                ActivityLog.created_at < next_date
            )
        except ValueError:
            pass
    
    # Получаем данные с пагинацией
    activities = query.order_by(ActivityLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Добавляем информацию о роли пользователя для каждой записи
    for activity in activities.items:
        if activity.user_id:
            user = Users.query.get(activity.user_id)
            if user:
                activity.user_role = user.role
            else:
                activity.user_role = "Неизвестно"
        else:
            activity.user_role = "Неавторизованный"
    
    # Статистика
    total_activities = ActivityLog.query.count()
    today_activities = ActivityLog.query.filter(
        ActivityLog.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    return render_template('main/activity_log.html',
                         activities=activities,
                         total_activities=total_activities,
                         today_activities=today_activities,
                         user_filter=user_filter,
                         action_filter=action_filter,
                         date_filter=date_filter)

@activity_log.route('/api/activity-log')
@login_required
def api_activity_log():
    """API для получения журнала действий"""
    if not is_admin():
        return jsonify({'error': gettext("У вас нет прав для просмотра журнала действий")}), 403
    
    limit = request.args.get('limit', 50, type=int)
    user_filter = request.args.get('user', '')
    action_filter = request.args.get('action', '')
    
    query = ActivityLog.query
    
    if user_filter:
        query = query.filter(ActivityLog.user_login.contains(user_filter))
    
    if action_filter:
        query = query.filter(ActivityLog.action.contains(action_filter))
    
    activities = query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
    
    return jsonify({
        'activities': [activity.to_dict() for activity in activities],
        'total': len(activities)
    })

@activity_log.route('/api/activity-log/clear', methods=['POST'])
@login_required
def clear_activity_log():
    """Очистка журнала действий"""
    if not is_admin():
        return jsonify({'error': gettext("У вас нет прав для очистки журнала действий")}), 403
    
    try:
        # Удаляем все записи
        ActivityLog.query.delete()
        db.session.commit()
        
        # Логируем действие очистки
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Очистка журнала",
            description=f"Администратор {current_user.login} очистил весь журнал действий",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        return jsonify({'success': True, 'message': 'Журнал действий очищен'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при очистке журнала: {str(e)}'}), 500

@activity_log.route('/api/activity-log/export')
@login_required
def export_activity_log():
    """Экспорт журнала действий в CSV"""
    if not is_admin():
        return jsonify({'error': gettext("У вас нет прав для экспорта журнала действий")}), 403
    
    try:
        activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).all()
        
        # Создаем CSV
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow(['ID', 'Пользователь', 'Действие', 'Описание', 'IP адрес', 'Страница', 'Дата'])
        
        # Данные
        for activity in activities:
            # Форматируем время в московском формате для CSV
            moscow_time = format_moscow_time(activity.created_at)
            if moscow_time == "Нет данных" or moscow_time == "Ошибка времени":
                moscow_time = ''
            
            writer.writerow([
                activity.id,
                activity.user_login,
                activity.action,
                activity.description,
                activity.ip_address,
                activity.page_url,
                moscow_time
            ])
        
        output.seek(0)
        
        # Логируем экспорт
        ActivityLog.log_action(
            user_id=current_user.userid,
            user_login=current_user.login,
            action="Экспорт журнала",
            description=f"Администратор {current_user.login} экспортировал журнал действий",
            ip_address=request.remote_addr,
            page_url=request.url,
            method=request.method
        )
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=activity_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': f'Ошибка при экспорте: {str(e)}'}), 500
