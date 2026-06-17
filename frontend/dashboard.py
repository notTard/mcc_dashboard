import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta

# Настройка страницы
st.set_page_config(
    page_title="Аналитика загрузки сотрудников ГВЦ",
    page_icon="📊",
    layout="wide"
)

# API endpoint
API_URL = "http://localhost:5000/api"

# Заголовок
st.title("📊 Дашборд аналитики загрузки сотрудников ГВЦ")
st.markdown("---")

# Функции загрузки данных
@st.cache_data(ttl=300)
def load_summary():
    response = requests.get(f"{API_URL}/summary")
    return response.json()

@st.cache_data(ttl=300)
def load_employee_load():
    response = requests.get(f"{API_URL}/employee_load")
    return pd.DataFrame(response.json())

@st.cache_data(ttl=300)
def load_trends(start_date, end_date):
    try:
        response = requests.get(f"{API_URL}/trends", params={
            'start': start_date,
            'end': end_date
        }, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Проверка что данные не пустые
        if not data:
            st.warning("Нет данных за выбранный период")
            # Создаём DataFrame с правильными колонками, но пустой
            return pd.DataFrame(columns=['date', 'hours_worked', 'tasks_completed', 'efficiency'])
        
        df = pd.DataFrame(data)
        
        # Преобразование колонки date в строку (если нужно)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        else:
            st.error("В данных нет колонки 'date'")
            return pd.DataFrame(columns=['date', 'hours_worked', 'tasks_completed', 'efficiency'])
        
        # Преобразование числовых колонок
        numeric_cols = ['hours_worked', 'tasks_completed', 'efficiency']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
        
    except Exception as e:
        st.error(f"Ошибка загрузки трендов: {e}")
        # Возвращаем пустой DataFrame с правильной структурой
        return pd.DataFrame(columns=['date', 'hours_worked', 'tasks_completed', 'efficiency'])

@st.cache_data(ttl=300)
def load_heatmap():
    response = requests.get(f"{API_URL}/heatmap")
    return pd.DataFrame(response.json())

# Sidebar фильтры
st.sidebar.header("🔍 Фильтры")

# Проверка соединения с бэкендом
try:
    health = requests.get(f"{API_URL}/health")
    if health.status_code != 200:
        st.error("❌ Ошибка соединения с бэкендом")
        st.stop()
except:
    st.error("❌ Не удалось подключиться к бэкенду. Убедитесь, что Flask запущен на порту 5000")
    st.stop()

# Фильтр дат
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("Дата начала", datetime(2024, 1, 1))
with col2:
    end_date = st.date_input("Дата окончания", datetime(2024, 12, 31))

# Загрузка данных
summary = load_summary()
employee_df = load_employee_load()
trends_df = load_trends(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
heatmap_df = load_heatmap()

# KPI карточки
st.subheader("📈 Ключевые показатели")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("👥 Всего сотрудников", summary['total_employees'])

with col2:
    st.metric("⏱️ Общее время работы (часы)", f"{summary['total_hours']:,.0f}")

with col3:
    st.metric("⭐ Средняя эффективность", f"{summary['avg_efficiency']}%")

with col4:
    st.metric("🕒 Переработки (часы)", f"{summary['total_overtime']:,.0f}")

st.markdown("---")

# Графики в две колонки
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Загрузка по сотрудникам")
    fig = px.bar(
        employee_df,
        x='employee',
        y='hours_worked',
        color='efficiency',
        title="Среднее количество часов",
        labels={'employee': 'Сотрудник', 'hours_worked': 'Часы', 'efficiency': 'Эффективность'},
        text='hours_worked'
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🎯 Эффективность сотрудников")
    fig = px.scatter(
        employee_df,
        x='hours_worked',
        y='efficiency',
        size='tasks_completed',
        color='employee',
        title="Эффективность vs Загрузка",
        labels={'hours_worked': 'Часы работы', 'efficiency': 'Эффективность'},
        hover_data=['employee', 'tasks_completed', 'overtime']
    )
    st.plotly_chart(fig, use_container_width=True)

# Тренды
st.subheader("📈 Динамика загрузки")
tab1, tab2 ,tab3= st.tabs(["Часы работы", "Задачи", "Эффективность"])

with tab1:
    fig = px.line(
        trends_df,
        x='date',
        y='hours_worked',
        title="Среднее количество часов по дням",
        labels={'date': 'Дата', 'hours_worked': 'Часы'}
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = px.area(
        trends_df,
        x='date',
        y='tasks_completed',
        title="Количество выполненных задач",
        labels={'date': 'Дата', 'tasks_completed': 'Задачи'}
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    fig = px.line(
        trends_df,
        x='date',
        y='efficiency',
        title="Динамика эффективности",
        labels={'date': 'Дата', 'efficiency': 'Эффективность'},
        range_y=[0.5, 1]
    )
    fig.add_hline(y=0.8, line_dash="dash", line_color="red", annotation_text="Целевой показатель")
    st.plotly_chart(fig, use_container_width=True)

# Тепловая карта
st.subheader("🔥 Тепловая карта загрузки по дням недели")
pivot_heatmap = heatmap_df.pivot(index='employee', columns='weekday', values='hours_worked')

fig = px.imshow(
    pivot_heatmap,
    text_auto=True,
    aspect="auto",
    title="Среднее количество часов по дням недели",
    labels=dict(x="День недели", y="Сотрудник", color="Часы"),
    color_continuous_scale="Viridis"
)
st.plotly_chart(fig, use_container_width=True)

# Таблица с детальными данными
st.subheader("📋 Детальная статистика")
st.dataframe(
    employee_df.style.format({
        'hours_worked': '{:.1f}',
        'tasks_completed': '{:.0f}',
        'efficiency': '{:.1%}',
        'overtime': '{:.1f}'
    }),
    use_container_width=True
)

# Footer
st.markdown("---")
st.caption("📅 Данные обновлены: " + datetime.now().strftime("%d.%m.%Y %H:%M:%S"))