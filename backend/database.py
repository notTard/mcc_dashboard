from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
import pandas as pd

db = SQLAlchemy()

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    tab_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    hire_date = db.Column(db.Date)
    
    # Связь с загрузкой
    workloads = db.relationship('Workload', backref='employee', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tab_number': self.tab_number,
            'name': self.name,
            'department': self.department,
            'position': self.position
        }

class Workload(db.Model):
    __tablename__ = 'workload'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    hours_worked = db.Column(db.Float, default=0)
    tasks_completed = db.Column(db.Integer, default=0)
    efficiency = db.Column(db.Float, default=0)
    overtime = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'date': self.date.strftime('%Y-%m-%d'),
            'hours_worked': self.hours_worked,
            'tasks_completed': self.tasks_completed,
            'efficiency': self.efficiency,
            'overtime': self.overtime
        }

def init_db(app):
    """Инициализация базы данных"""
    with app.app_context():
        db.create_all()
        print("✅ База данных инициализирована")
        
        # Проверка, есть ли данные
        if Employee.query.count() == 0:
            load_sample_data()

def load_sample_data():
    """Загрузка тестовых данных (только если БД пуста)"""
    print("📊 Загрузка тестовых данных...")
    
    # Сотрудники
    employees = [
        Employee(tab_number='001', name='Иванов Иван', department='Приём', position='Специалист'),
        Employee(tab_number='002', name='Петров Пётр', department='Отправка', position='Ведущий специалист'),
        Employee(tab_number='003', name='Сидорова Анна', department='Приём', position='Специалист'),
        Employee(tab_number='004', name='Кузнецов Сергей', department='Обработка', position='Начальник отдела'),
        Employee(tab_number='005', name='Соколова Елена', department='Отправка', position='Специалист')
    ]
    
    for emp in employees:
        db.session.add(emp)
    db.session.commit()
    
    # Генерация нагрузки (последние 30 дней)
    import random
    from datetime import datetime, timedelta
    
    for employee in employees:
        for i in range(30):
            date = datetime.now().date() - timedelta(days=i)
            hours = random.uniform(6, 10)
            tasks = random.randint(5, 15)
            efficiency = random.uniform(0.7, 1.0)
            overtime = max(0, hours - 8)
            
            workload = Workload(
                employee_id=employee.id,
                date=date,
                hours_worked=round(hours, 1),
                tasks_completed=tasks,
                efficiency=round(efficiency, 2),
                overtime=round(overtime, 1)
            )
            db.session.add(workload)
    
    db.session.commit()
    print(f"✅ Загружено {Employee.query.count()} сотрудников и {Workload.query.count()} записей нагрузки")