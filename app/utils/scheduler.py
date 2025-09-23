"""
Модуль для автоматического выполнения задач по расписанию
"""
import logging
from datetime import date, datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask import current_app

from app.extensions import db
from app.models.objects import PlannedWork, DailyReport, Object, WorkExecution
from app.models.settings import SystemSetting
from app.utils.timezone_utils import get_moscow_now

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    """Класс для управления автоматическими задачами"""
    
    def __init__(self, app=None):
        self.scheduler = None
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Инициализация планировщика с приложением Flask"""
        self.app = app
        
        # Настройка хранилища задач (временно используем память)
        from apscheduler.jobstores.memory import MemoryJobStore
        jobstores = {
            'default': MemoryJobStore()
        }
        
        # Настройка исполнителей
        executors = {
            'default': ThreadPoolExecutor(20),
        }
        
        # Настройки планировщика
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        # Создание планировщика
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Europe/Moscow'  # Московское время
        )
        
        # Регистрация задач
        self._register_jobs()
        
        # Запуск планировщика
        self.scheduler.start()
        logger.info("Планировщик задач запущен")
        
        # Немедленно выполняем задачи при запуске (облегченные)
        self._run_initial_tasks()
    
    def _register_jobs(self):
        """Регистрация автоматических задач"""
        
        # Обновление статуса просроченных работ - каждый день в 00:05
        self.scheduler.add_job(
            func=update_overdue_works_job,
            trigger=CronTrigger(hour=0, minute=5),
            id='update_overdue_works',
            name='Обновление статуса просроченных работ',
            replace_existing=True
        )
        
        # Генерация ежедневных отчетов - каждый день в 23:55
        self.scheduler.add_job(
            func=generate_daily_reports_job,
            trigger=CronTrigger(hour=23, minute=55),
            id='generate_daily_reports',
            name='Генерация ежедневных отчетов',
            replace_existing=True
        )
        
        # Дополнительная проверка просроченных работ - каждый час
        self.scheduler.add_job(
            func=update_overdue_works_job,
            trigger=CronTrigger(minute=0),
            id='hourly_overdue_check',
            name='Ежечасная проверка просроченных работ',
            replace_existing=True
        )
        
        # Проверка пропущенных отчетов - каждый день в 00:10
        self.scheduler.add_job(
            func=generate_missing_reports_job,
            trigger=CronTrigger(hour=0, minute=10),
            id='generate_missing_reports',
            name='Проверка и генерация пропущенных отчетов',
            replace_existing=True
        )
        
        logger.info("Автоматические задачи зарегистрированы")
    
    def _run_initial_tasks(self):
        """Выполняет задачи сразу при запуске приложения"""
        try:
            logger.info("Выполняем начальные задачи...")
            
            # Обновляем просроченные работы (это быстро)
            updated_count = self.update_overdue_works()
            logger.info(f"Обновлено просроченных работ при запуске: {updated_count}")
            
            # Легкая проверка пропущенных отчетов: только за последние 1-2 дня
            generated_count = self.generate_missing_reports(light_mode=True)
            logger.info(f"Сгенерировано пропущенных отчетов при запуске (light): {generated_count}")
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении начальных задач: {e}")
    
    def update_overdue_works(self):
        """Обновление статуса просроченных работ"""
        with self.app.app_context():
            try:
                logger.info("Начинаем обновление статуса просроченных работ")
                
                # Используем существующий метод из модели
                updated_count = PlannedWork.update_overdue_works()
                
                logger.info(f"Обновлено просроченных работ: {updated_count}")
                return updated_count
                
            except Exception as e:
                logger.error(f"Ошибка при обновлении просроченных работ: {e}")
                return 0
    
    def generate_daily_reports(self):
        """Генерация ежедневных отчетов за вчерашний день"""
        with self.app.app_context():
            try:
                logger.info("Начинаем генерацию ежедневных отчетов")
                
                # Генерируем отчеты за вчерашний день
                yesterday = get_moscow_now().date() - timedelta(days=1)
                
                # Получаем все объекты
                objects = Object.query.all()
                generated_count = 0
                
                for obj in objects:
                    try:
                        # Проверяем, существует ли уже отчет за эту дату
                        existing_report = DailyReport.query.filter_by(
                            object_id=obj.id,
                            report_date=yesterday
                        ).first()
                        
                        if existing_report:
                            logger.info(f"Отчет для объекта {obj.name} за {yesterday} уже существует")
                            continue
                        
                        # Генерируем новый отчет
                        report = self._generate_report_for_object(obj.id, yesterday)
                        if report:
                            generated_count += 1
                            logger.info(f"Создан отчет для объекта {obj.name} за {yesterday}")
                        
                    except Exception as e:
                        logger.error(f"Ошибка при создании отчета для объекта {obj.id}: {e}")
                        continue
                
                logger.info(f"Сгенерировано отчетов: {generated_count}")
                return generated_count
                
            except Exception as e:
                logger.error(f"Ошибка при генерации ежедневных отчетов: {e}")
                return 0
    
    def _generate_report_for_object(self, object_id, report_date):
        """Генерация отчета для конкретного объекта за конкретную дату"""
        try:
            # Получаем объект
            obj = Object.query.get(object_id)
            if not obj:
                return None
            
            # Подсчитываем статистику
            # Запланированные работы - все работы со статусом 'planned'
            planned_works = PlannedWork.query.filter_by(object_id=object_id).filter(
                PlannedWork.status == 'planned'
            ).all()
            
            completed_works = db.session.query(PlannedWork).join(
                WorkExecution, PlannedWork.id == WorkExecution.planned_work_id
            ).filter(
                PlannedWork.object_id == object_id,
                WorkExecution.execution_date == report_date
            ).all()
            
            overdue_works = PlannedWork.query.filter_by(object_id=object_id).filter(
                PlannedWork.planned_date < report_date,
                PlannedWork.status.in_(['planned', 'in_progress'])
            ).all()
            
            # Создаем новый отчет
            daily_report = DailyReport(
                object_id=object_id,
                report_date=report_date,
                planned_works_count=len(planned_works),
                completed_works_count=len(completed_works),
                overdue_works_count=len(overdue_works),
                status='draft',
                created_by=None  # Системный отчет
            )
            
            db.session.add(daily_report)
            db.session.commit()
            
            return daily_report
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при создании отчета для объекта {object_id}: {e}")
            return None
    
    def generate_report_for_today(self):
        """Генерация отчетов за сегодня (для ручного вызова)"""
        with self.app.app_context():
            try:
                today = get_moscow_now().date()
                objects = Object.query.all()
                generated_count = 0
                
                for obj in objects:
                    try:
                        # Проверяем, существует ли уже отчет за сегодня
                        existing_report = DailyReport.query.filter_by(
                            object_id=obj.id,
                            report_date=today
                        ).first()
                        
                        if existing_report:
                            continue
                        
                        # Генерируем новый отчет
                        report = self._generate_report_for_object(obj.id, today)
                        if report:
                            generated_count += 1
                        
                    except Exception as e:
                        logger.error(f"Ошибка при создании отчета для объекта {obj.id}: {e}")
                        continue
                
                logger.info(f"Сгенерировано отчетов за сегодня: {generated_count}")
                return generated_count
                
            except Exception as e:
                logger.error(f"Ошибка при генерации отчетов за сегодня: {e}")
                return 0
    
    def generate_missing_reports(self, light_mode: bool = False):
        """Генерация отчетов за пропущенные дни.
        light_mode=True: ограничиться небольшим диапазоном (например, последние 2 дня).
        В полноценном режиме использовать сохраненную последнюю обработанную дату.
        """
        with self.app.app_context():
            try:
                logger.info("Начинаем генерацию пропущенных отчетов...")
                
                # Получаем все объекты
                objects = Object.query.all()
                if not objects:
                    logger.info("Нет объектов для генерации отчетов")
                    return 0
                
                # Определяем диапазон дат для проверки
                today = get_moscow_now().date()

                if light_mode:
                    # Проверяем только вчера и сегодня
                    start_date = today - timedelta(days=2)
                else:
                    # Читаем последнюю полностью обработанную дату
                    last_processed = SystemSetting.get('daily_reports_last_processed_date')
                    if last_processed:
                        try:
                            last_dt = datetime.strptime(last_processed, '%Y-%m-%d').date()
                            start_date = last_dt + timedelta(days=1)
                        except Exception:
                            start_date = today - timedelta(days=7)
                    else:
                        # Если нет записи — начинаем с ближайшей даты в таблице, но не раньше чем 14 дней назад
                        earliest_report = DailyReport.query.order_by(DailyReport.report_date.asc()).first()
                        if earliest_report:
                            start_date = max(earliest_report.report_date, today - timedelta(days=14))
                        else:
                            start_date = today - timedelta(days=7)
                
                # Проверяем каждый день от start_date до сегодня включительно
                current_date = start_date
                total_generated = 0
                
                while current_date <= today:
                    logger.info(f"Проверяем отчеты за {current_date}")
                    
                    for obj in objects:
                        try:
                            # Проверяем, существует ли уже отчет за эту дату
                            existing_report = DailyReport.query.filter_by(
                                object_id=obj.id,
                                report_date=current_date
                            ).first()
                            
                            if existing_report:
                                continue
                            
                            # Генерируем новый отчет
                            report = self._generate_report_for_object(obj.id, current_date)
                            if report:
                                total_generated += 1
                                logger.info(f"Создан отчет для объекта {obj.name} за {current_date}")
                            
                        except Exception as e:
                            logger.error(f"Ошибка при создании отчета для объекта {obj.id} за {current_date}: {e}")
                            continue
                    
                    current_date += timedelta(days=1)
                
                # В полном режиме фиксируем последнюю обработанную дату
                if not light_mode:
                    SystemSetting.set('daily_reports_last_processed_date', today.strftime('%Y-%m-%d'))
                
                logger.info(f"Всего сгенерировано пропущенных отчетов: {total_generated}")
                return total_generated
                
            except Exception as e:
                logger.error(f"Ошибка при генерации пропущенных отчетов: {e}")
                return 0
    
    def shutdown(self):
        """Остановка планировщика"""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Планировщик задач остановлен")

# Глобальные функции-задачи для планировщика
def update_overdue_works_job():
    """Задача для обновления просроченных работ"""
    from flask import current_app
    with current_app.app_context():
        try:
            updated_count = PlannedWork.update_overdue_works()
            logger.info(f"Автоматически обновлено просроченных работ: {updated_count}")
            return updated_count
        except Exception as e:
            logger.error(f"Ошибка при автоматическом обновлении просроченных работ: {e}")
            return 0

def generate_daily_reports_job():
    """Задача для генерации ежедневных отчетов"""
    from flask import current_app
    with current_app.app_context():
        try:
            from datetime import timedelta
            yesterday = get_moscow_now().date() - timedelta(days=1)
            
            # Получаем все объекты
            objects = Object.query.all()
            generated_count = 0
            
            for obj in objects:
                try:
                    # Проверяем, существует ли уже отчет за эту дату
                    existing_report = DailyReport.query.filter_by(
                        object_id=obj.id,
                        report_date=yesterday
                    ).first()
                    
                    if existing_report:
                        continue
                    
                    # Генерируем новый отчет
                    report = _generate_report_for_object_job(obj.id, yesterday)
                    if report:
                        generated_count += 1
                    
                except Exception as e:
                    logger.error(f"Ошибка при создании отчета для объекта {obj.id}: {e}")
                    continue
            
            logger.info(f"Автоматически сгенерировано отчетов: {generated_count}")
            return generated_count
            
        except Exception as e:
            logger.error(f"Ошибка при автоматической генерации отчетов: {e}")
            return 0

def generate_missing_reports_job():
    """Задача для генерации пропущенных отчетов"""
    from flask import current_app
    with current_app.app_context():
        try:
            from app.utils.scheduler import scheduler
            generated_count = scheduler.generate_missing_reports()
            logger.info(f"Автоматически сгенерировано пропущенных отчетов: {generated_count}")
            return generated_count
            
        except Exception as e:
            logger.error(f"Ошибка при автоматической генерации пропущенных отчетов: {e}")
            return 0

def _generate_report_for_object_job(object_id, report_date):
    """Генерация отчета для конкретного объекта за конкретную дату (для задач)"""
    try:
        # Получаем объект
        obj = Object.query.get(object_id)
        if not obj:
            return None
        
        # Подсчитываем статистику
        # Запланированные работы - все работы со статусом 'planned'
        planned_works = PlannedWork.query.filter_by(object_id=object_id).filter(
            PlannedWork.status == 'planned'
        ).all()
        
        completed_works = db.session.query(PlannedWork).join(
            WorkExecution, PlannedWork.id == WorkExecution.planned_work_id
        ).filter(
            PlannedWork.object_id == object_id,
            WorkExecution.execution_date == report_date
        ).all()
        
        overdue_works = PlannedWork.query.filter_by(object_id=object_id).filter(
            PlannedWork.planned_date < report_date,
            PlannedWork.status.in_(['planned', 'in_progress'])
        ).all()
        
        # Создаем новый отчет
        daily_report = DailyReport(
            object_id=object_id,
            report_date=report_date,
            planned_works_count=len(planned_works),
            completed_works_count=len(completed_works),
            overdue_works_count=len(overdue_works),
            status='draft',
            created_by=None  # Системный отчет
        )
        
        db.session.add(daily_report)
        db.session.commit()
        
        return daily_report
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при создании отчета для объекта {object_id}: {e}")
        return None

# Глобальный экземпляр планировщика
scheduler = TaskScheduler()
