import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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
    # Розрахунок руху для передачі в JavaScript
    v_term = (2 / 9) * (r**2) * g * (rho_s - rho_f) / eta
    tau = m / (6 * np.pi * eta * r)

    # Динамічний радіус кульки на екрані (в пікселях) підв'язуємо до повзунка
    # Робимо базовий радіус помітним, наприклад: 5 мм = 15 пікселів, 1 мм = 5 пікселів
    r_pixels = float(r_mm * 3.0)
    
    # Визначаємо фізичну точку зупинки центру мас кульки з урахуванням її поточного радіуса на екрані
    scale_factor = 400 / H_cylinder
    r_screen_m = r_pixels / scale_factor
    H_stop_m = H_cylinder - r_screen_m  # точка зупинки центру мас кульки

    # Функція розрахунку часу падіння до потрібної позначки
    def get_time_for_distance(y_target, v_t, t_rel):
        t_arr = np.linspace(0, 180.0, 50000)
        y_arr = v_t * t_arr - v_t * t_rel * (1 - np.exp(-t_arr / t_rel))
        idx = np.searchsorted(y_arr, y_target)
        return t_arr[idx] if idx < len(t_arr) else 180.0

    # Точний час падіння до торкання дна нижнім краєм (динамічно залежить від радіуса)
    t_bottom = get_time_for_distance(H_stop_m, v_term, tau)

    # --- Інтерфейс лабораторного стенду ---
    st.subheader("🧪 Віртуальний стенд")
    st.caption("Натисніть кнопку 'Запустити кульку' всередині вікна стенду. Слідкуйте за секундоміром у момент перетину червоних міток.")

    # Передаємо змінні в HTML/JS код за допомогою f-рядка
    html_src = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                background-color: #0e1117;
                color: white;
                font-family: sans-serif;
                margin: 0;
                padding: 10px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            #stopwatch {{
                font-size: 28px;
                color: #FFD700;
                font-weight: bold;
                margin-bottom: 15px;
                font-family: monospace;
            }}
            #btn {{
                background-color: #ff4b4b;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                margin-bottom: 20px;
                width: 250px;
            }}
            #btn:hover {{
                background-color: #ff3333;
            }}
            svg {{
                background-color: #1e1e1e;
                border-radius: 8px;
            }}
        </style>
    </head>
    <body>

        <div id="stopwatch">⏱️ Секундомір: 0.000 с</div>
        <button id="btn" onclick="startSimulation()">🚀 Скинути кульку</button>

        <svg width="250" height="440" viewBox="0 0 250 440" xmlns="http://w3.org">
            <!-- Рідина в циліндрі (задній план) -->
            <rect x="85" y="20" width="80" height="400" fill="rgba(0, 150, 255, 0.15)" stroke="#ffffff" stroke-width="3" rx="5" />
            
            <!-- Кулька (середній план, малюється під мітками) -->
            <circle id="ball" cx="125" y="20" r="{r_pixels}" fill="#a0a0a0" stroke="#ffffff" stroke-width="2" />
            
            <!-- Мітка А (передній план - перенесено вниз, перекриває кульку) -->
            <line x1="65" y1="{20 + (y_start_label * 400 / H_cylinder)}" x2="185" y2="{20 + (y_start_label * 400 / H_cylinder)}" stroke="#ff3333" stroke-width="2.5" stroke-dasharray="5" />
            <text x="5" y="{25 + (y_start_label * 400 / H_cylinder)}" fill="#ff3333" font-size="14" font-weight="bold" font-family="sans-serif">Мітка А</text>
            
            <!-- Мітка Б (передній план - перенесено вниз, перекриває кульку) -->
            <line x1="65" y1="{20 + (y_end_label * 400 / H_cylinder)}" x2="185" y2="{20 + (y_end_label * 400 / H_cylinder)}" stroke="#ff3333" stroke-width="2.5" stroke-dasharray="5" />
            <text x="5" y="{25 + (y_end_label * 400 / H_cylinder)}" fill="#ff3333" font-size="14" font-weight="bold" font-family="sans-serif">Мітка Б</text>
        </svg>

        <script>
            // Фізичні константи передані з Python
            const v_term = {v_term};
            const tau = {tau};
            const H_cylinder = {H_cylinder};
            const H_stop_m = {H_stop_m};
            const t_bottom = {t_bottom};
            const scale = 400 / H_cylinder;

            let startTime = null;
            let animationId = null;

            function startSimulation() {{
                cancelAnimationFrame(animationId);
                document.getElementById('ball').setAttribute('cy', 20);
                document.getElementById('stopwatch').innerText = "⏱️ Секундомір: 0.000 с";
                document.getElementById('stopwatch').style.color = "#FFD700";
                
                startTime = performance.now();
                animate();
            }}

            function animate() {{
                let now = performance.now();
                let elapsed_seconds = (now - startTime) / 1000;

                if (elapsed_seconds >= t_bottom) {{
                    elapsed_seconds = t_bottom;
                    document.getElementById('ball').setAttribute('cy', 20 + H_stop_m * scale);
                    document.getElementById('stopwatch').innerText = "⏱️ Разом: " + elapsed_seconds.toFixed(3) + " с";
                    document.getElementById('stopwatch').style.color = "#00FFCC";
                    return;
                }}

                let y_curr = v_term * elapsed_seconds - v_term * tau * (1 - Math.exp(-elapsed_seconds / tau));
                if (y_curr > H_stop_m) y_curr = H_stop_m;

                document.getElementById('ball').setAttribute('cy', 20 + y_curr * scale);
                document.getElementById('stopwatch').innerText = "⏱️ Секундомір: " + elapsed_seconds.toFixed(3) + " с";

                animationId = requestAnimationFrame(animate);
            }}
        </script>
    </body>
    </html>
    """
    
    components.html(html_src, height=560)

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
