import time
import numpy as np
import pandas as pd
import streamlit as st

# Налаштування сторінки
st.set_page_config(
    page_title="Лабораторна робота: Метод Стокса", layout="centered"
)

st.title("🔬 Віртуальна лабораторна робота")
st.header("Визначення динамічної в'язкості рідини методом Стокса")

# --- Бічна панель параметрів ---
st.sidebar.header("⚙️ Параметри експерименту")

# Список рідин
liquid_options = {
    "Гліцерин": {"rho": 1260.0, "eta": 1.49},
    "Касторова олія": {"rho": 961.0, "eta": 0.95},
    "Машинна олія (SAE 40)": {"rho": 888.0, "eta": 0.32},
    "Рідкий мед": {"rho": 1420.0, "eta": 10.0},
    "Згущене молоко": {"rho": 1300.0, "eta": 2.5},
    "Цукровий сироп (70%)": {"rho": 1350.0, "eta": 0.4},
}

liquid_name = st.sidebar.selectbox("Виберіть рідину:", list(liquid_options.keys()))
rho_f = liquid_options[liquid_name]["rho"]
eta = liquid_options[liquid_name]["eta"]

# Вибір матеріалу кульки
ball_options = {"Сталь": 7800.0, "Свинець": 11340.0, "Скло": 2500.0}
ball_type = st.sidebar.selectbox("Матеріал кульки:", list(ball_options.keys()))
rho_s = ball_options[ball_type]

# Геометрія кульки
r_mm = st.sidebar.slider(
    "Радіус кульки r (мм):", min_value=1.0, max_value=5.0, value=2.5, step=0.1
)
r = r_mm / 1000.0  # в метри

# Фізичні константи
g = 9.81
V = (4 / 3) * np.pi * (r**3)
m = V * rho_s

# Розміри циліндра та міток (в метрах)
H_cylinder = 0.5        # повна висота рідини 50 см
y_start_label = 0.1     # Мітка А на відстані 10 см від верху
y_end_label = 0.4       # Мітка Б на відстані 40 см від верху
L_distance = y_end_label - y_start_label 

# Перевірка умови падіння
if rho_s <= rho_f:
    st.error(
        "❌ Помилка: Густина кульки менша або дорівнює густині рідини! Кулька не буде тонути. Змініть матеріал або рідину."
    )
else:
    # Розрахунок руху
    v_term = (2 / 9) * (r**2) * g * (rho_s - rho_f) / eta
    tau = m / (6 * np.pi * eta * r)

    # Функція розрахунку часу падіння до дна
    def get_time_for_distance(y_target, v_t, t_rel):
        t_arr = np.linspace(0, 180.0, 50000)
        y_arr = v_t * t_arr - v_t * t_rel * (1 - np.exp(-t_arr / t_rel))
        idx = np.searchsorted(y_arr, y_target)
        return t_arr[idx] if idx < len(t_arr) else 180.0

    t_bottom = get_time_for_distance(H_cylinder, v_term, tau)

    # --- Інтерфейс лабораторного стенду ---
    st.subheader("🧪 Віртуальний стенд")
    st.caption("Натисніть кнопку нижче, щоб скинути кульку. Слідкуйте за секундоміром у момент перетину червоних міток.")

    # Кнопка запуску
    start_btn = st.button("🚀 Скинути кульку", use_container_width=True)

    # Створюємо два порожніх контейнери: один для секундоміра, другий для самої колби
    stopwatch_placeholder = st.empty()
    cylinder_placeholder = st.empty()

    # Функція генерації надлегкої SVG-графіки колби
    def render_svg_cylinder(y_curr_m, time_s):
        # Переводимо метри в пікселі для малювання (висота колби 400px)
        scale = 400 / H_cylinder
        y_pixel = y_curr_m * scale
        y_A = y_start_label * scale
        y_B = y_end_label * scale
        
        svg_code = f"""
        <div style="display: flex; justify-content: center; background-color: #1e1e1e; padding: 20px; border-radius: 10px;">
            <svg width="200" height="440" viewBox="0 0 200 440" xmlns="http://w3.org">
                <!-- Рідина в циліндрі -->
                <rect x="60" y="20" width="80" height="400" fill="rgba(0, 150, 255, 0.15)" stroke="#ffffff" stroke-width="3" rx="5" />
                
                <!-- Мітка А (Старт) -->
                <line x1="45" y1="{20 + y_A}" x2="155" y2="{20 + y_A}" stroke="#ff3333" stroke-width="2" stroke-dasharray="4" />
                <text x="5" y="{25 + y_A}" fill="#ff3333" font-size="12" font-family="sans-serif">Мітка А</text>
                
                <!-- Мітка Б (Стоп) -->
                <line x1="45" y1="{20 + y_B}" x2="155" y2="{20 + y_B}" stroke="#ff3333" stroke-width="2" stroke-dasharray="4" />
                <text x="5" y="{25 + y_B}" fill="#ff3333" font-size="12" font-family="sans-serif">Мітка Б</text>
                
                <!-- Кулька -->
                <circle cx="100" y="{20 + y_pixel}" r="10" fill="#a0a0a0" stroke="#ffffff" stroke-width="1.5" />
            </svg>
        </div>
        """
        return svg_code

    # Початковий стан (кулька вгорі, час 0)
    stopwatch_placeholder.markdown(f"<h2 style='text-align: center; color: #FFD700;'>⏱️ Секундомір: 0.000 с</h2>", unsafe_allow_html=True)
    cylinder_placeholder.html(render_svg_cylinder(0.0, 0.0))

    # Логіка анімації при натисканні кнопки
    if start_btn:
        # Розраховуємо параметри реального часу для плавної промальовки
        # Робимо крок у 0.03 секунди (приблизно 30 кадрів на секунду)
        dt = 0.030 
        current_time = 0.0
        
        t_start = time.time()
        
        while current_time <= t_bottom:
            # Обчислюємо точну фізичну координату кульки для цієї мікросекунди
            y_ball = v_term * current_time - v_term * tau * (1 - np.exp(-current_time / tau))
            if y_ball > H_cylinder:
                y_ball = H_cylinder

            # Миттєво оновлюємо текст секундоміра та графіку без перемальовки сторінки
            stopwatch_placeholder.markdown(f"<h2 style='text-align: center; color: #FFD700;'>⏱️ Секундомір: {current_time:.3f} с</h2>", unsafe_allow_html=True)
            cylinder_placeholder.html(render_svg_cylinder(y_ball, current_time))
            
            # Контроль кроку за часом процесора
            time.sleep(dt)
            current_time += dt

        # Фінальний акорд — фіксуємо кульку точно на дні
        stopwatch_placeholder.markdown(f"<h2 style='text-align: center; color: #00FFCC;'>⏱️ Разом: {t_bottom:.3f} с</h2>", unsafe_allow_html=True)
        cylinder_placeholder.html(render_svg_cylinder(H_cylinder, t_bottom))

    # Таблиця констант
    st.write("---")
    st.subheader("📋 Довідкові дані лабораторної установки")
    df_info = pd.DataFrame({
        "Параметр (Одиниці вимірювання)": [
            "Густина рідини (кг/м³)",
            "Густина матеріалу кульки (кг/м³)",
            "Радіус кульки (мм)",
            "Відстань між мітками А та Б (м)",
        ],
        "Значення": [f"{rho_f}", f"{rho_s}", f"{r_mm}", f"{L_distance:.2f}"]
    })
    st.table(df_info)
