from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from database import db, Employee, Workload, init_db
from datetime import datetime, timedelta
from sqlalchemy import text  

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Инициализация БД
db.init_app(app)
init_db(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        # Проверка подключения к БД 
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        db_status = 'ok'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Получение общей сводки из БД"""
    from sqlalchemy import func
    
    total_employees = Employee.query.count()
    
    result = db.session.query(
        func.sum(Workload.hours_worked).label('total_hours'),
        func.avg(Workload.efficiency).label('avg_efficiency'),
        func.sum(Workload.overtime).label('total_overtime')
    ).first()
    
    summary = {
        'total_employees': total_employees,
        'total_hours': round(result.total_hours or 0, 1),
        'avg_efficiency': round((result.avg_efficiency or 0) * 100, 1),
        'total_overtime': round(result.total_overtime or 0, 1)
    }
    
    return jsonify(summary)

@app.route('/api/employee_load', methods=['GET'])
def get_employee_load():
    """Загрузка по сотрудникам"""
    from sqlalchemy import func
    
    results = db.session.query(
        Employee.name,
        Employee.department,
        func.avg(Workload.hours_worked).label('hours_worked'),
        func.avg(Workload.tasks_completed).label('tasks_completed'),
        func.avg(Workload.efficiency).label('efficiency'),
        func.sum(Workload.overtime).label('overtime')
    ).join(Workload).group_by(Employee.id).all()
    
    data = []
    for r in results:
        data.append({
            'employee': str(r.name),  
            'department': str(r.department) if r.department else '',
            'hours_worked': float(r.hours_worked) if r.hours_worked else 0.0, 
            'tasks_completed': float(r.tasks_completed) if r.tasks_completed else 0.0, 
            'efficiency': float(r.efficiency) if r.efficiency else 0.0,  
            'overtime': float(r.overtime) if r.overtime else 0.0  
        })
    
    return jsonify(data)

@app.route('/api/trends', methods=['GET'])
def get_trends():
    """Динамика загрузки с фильтрацией по датам"""
    start_date = request.args.get('start', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end', datetime.now().strftime('%Y-%m-%d'))
    
    from sqlalchemy import func
    
    try:
        results = db.session.query(
            Workload.date,
            func.avg(Workload.hours_worked).label('hours_worked'),
            func.sum(Workload.tasks_completed).label('tasks_completed'),
            func.avg(Workload.efficiency).label('efficiency')
        ).filter(
            Workload.date >= start_date,
            Workload.date <= end_date
        ).group_by(Workload.date).order_by(Workload.date).all()
        
        data = []
        for r in results:
            data.append({
                'date': r.date.strftime('%Y-%m-%d'), 
                'hours_worked': float(r.hours_worked) if r.hours_worked else 0.0,
                'tasks_completed': int(r.tasks_completed) if r.tasks_completed else 0,
                'efficiency': float(r.efficiency) if r.efficiency else 0.0
            })
        
        # Если данных нет, вернуть хотя бы пустой список
        if not data:
            # Возвращаем тестовые данные для отладки
            return jsonify([])
        
        return jsonify(data)
        
    except Exception as e:
        print(f"Ошибка в get_trends: {e}")
        return jsonify([])  # Возвращаем пустой список при ошибке

@app.route('/api/heatmap', methods=['GET'])
def get_heatmap():
    """Тепловая карта загрузки"""
    from sqlalchemy import func
    
    # Используем SQL для получения дней недели
    results = db.session.query(
        Employee.name.label('employee'),
        func.extract('dow', Workload.date).label('weekday_num'),
        func.avg(Workload.hours_worked).label('hours_worked')
    ).join(Workload).group_by(
        Employee.id, 
        func.extract('dow', Workload.date)
    ).all()
    
    # Преобразование номера дня в название
    weekdays = {
        0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 
        3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'
    }
    
    data = []
    for r in results:
        data.append({
            'employee': r.employee,
            'weekday': weekdays.get(int(r.weekday_num), 'Unknown'),
            'hours_worked': round(r.hours_worked, 1)
        })
    
    return jsonify(data)

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """Список всех сотрудников"""
    employees = Employee.query.all()
    return jsonify([e.to_dict() for e in employees])

if __name__ == '__main__':
    app.run(debug=True, port=5000)