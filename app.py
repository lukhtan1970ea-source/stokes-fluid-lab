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

# 1. Температура досліду
T_C = st.sidebar.slider(
    "Температура рідини T (°C):", min_value=10, max_value=80, value=20, step=5
)

# 2. Вибір рідини (залишили тільки строго довідкові ньютонівські рідини)
liquid_name = st.sidebar.selectbox(
    "Виберіть рідину:", 
    ["Гліцерин", "Касторова олія", "Машинна олія (SAE 40)"]
)

# Залізобетонний масив ТОЧНИХ табличних даних із фізичних довідників
# Ключ - температура в °C. Значення - [густина rho_f, в'язкість eta]
lookup_table = {
    "Гліцерин": {
        10: [1265.0, 3.900], 15: [1262.0, 2.310], 20: [1260.0, 1.490], 25: [1257.0, 0.950],
        30: [1254.0, 0.620], 35: [1251.0, 0.420], 40: [1249.0, 0.280], 45: [1245.0, 0.210],
        50: [1241.0, 0.152], 55: [1238.0, 0.116], 60: [1235.0, 0.090], 65: [1231.0, 0.071],
        70: [1228.0, 0.057], 75: [1224.0, 0.046], 80: [1221.0, 0.038]
    },
    "Касторова олія": {
        10: [965.0, 2.420], 15: [963.0, 1.510], 20: [961.0, 0.950], 25: [958.0, 0.620],
        30: [955.0, 0.450], 35: [952.0, 0.310], 40: [950.0, 0.230], 45: [947.0, 0.170],
        50: [945.0, 0.125], 55: [942.0, 0.095], 60: [939.0, 0.073], 65: [936.0, 0.058],
        70: [934.0, 0.047], 75: [931.0, 0.039], 80: [928.0, 0.032]
    },
            "Машинна олія (SAE 40)": {
        10: [894.0, 1.210], 15: [891.0, 0.790], 20: [888.0, 0.550], 25: [885.0, 0.380],
        30: [882.0, 0.280], 35: [879.0, 0.200], 40: [876.0, 0.150], 45: [873.0, 0.116],
        50: [870.0, 0.090], 55: [867.0, 0.072], 60: [864.0, 0.060], 65: [861.0, 0.047],
        70: [858.0, 0.039], 75: [855.0, 0.032], 80: [852.0, 0.028]
    }


}


# Витягуємо точні дані для обраної точки досліду
rho_f = lookup_table[liquid_name][T_C][0]
eta = lookup_table[liquid_name][T_C][1]


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

<div class="controls" style="display: flex; gap: 10px; margin-bottom: 20px;">
    <button id="btn" onclick="startSimulation()" style="background-color: #ff4b4b; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 5px; cursor: pointer; font-weight: bold; width: 180px;">🚀 Скинути кульку</button>
    <button id="btn-lapA" onclick="recordLap('A')" disabled style="background-color: #4CAF50; color: white; border: none; padding: 10px 15px; font-size: 15px; border-radius: 5px; cursor: pointer; font-weight: bold; width: 130px;">⏱️ Мітка А</button>
    <button id="btn-lapB" onclick="recordLap('B')" disabled style="background-color: #4CAF50; color: white; border: none; padding: 10px 15px; font-size: 15px; border-radius: 5px; cursor: pointer; font-weight: bold; width: 130px;">⏱️ Мітка Б</button>
</div>

<!-- Панель ручної фіксації результатів студентом -->
<div id="results-panel" style="margin-top: 15px; font-size: 16px; background-color: #1e2530; padding: 10px 20px; border-radius: 6px; width: 320px; border: 1px solid #343b47;">
    <div style="display: flex; justify-content: space-between; margin: 5px 0;"><span>Зафіксовано t<sub>А</sub>:</span> <span id="valA" style="color: #00FFCC; font-family: monospace; font-weight: bold;">--.--- с</span></div>
    <div style="display: flex; justify-content: space-between; margin: 5px 0;"><span>Зафіксовано t<sub>Б</sub>:</span> <span id="valB" style="color: #00FFCC; font-family: monospace; font-weight: bold;">--.--- с</span></div>
    <div style="display: flex; justify-content: space-between; margin: 5px 0; border-top: 1px dashed #555; margin-top: 8px; padding-top: 5px; font-weight: bold;">
        <span>Різниця (Δt):</span> <span id="valDiff" style="color: #FFD700; font-family: monospace; font-weight: bold;">--.--- с</span>
    </div>
</div>


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
    // Физические константы, передаваемые из Python
    const v_term = {v_term};
    const tau = {tau};
    const H_cylinder = {H_cylinder};
    const H_stop_m = {H_stop_m};
    const t_bottom = {t_bottom};
    const scale = 400 / H_cylinder;

    let startTime = null;
    let animationId = null;
    let currentElapsed = 0; // Общая переменная для фиксации времени кнопками
    
    let timeA = null;
    let timeB = null;

    function startSimulation() {{
        cancelAnimationFrame(animationId);
        document.getElementById('ball').setAttribute('cy', 20);
        document.getElementById('stopwatch').innerText = "⏱️ Секундомір: 0.000 с";
        document.getElementById('stopwatch').style.color = "#FFD700";
        
        // Сброс результатов на панели
        timeA = null;
        timeB = null;
        document.getElementById('valA').innerText = "--.--- с";
        document.getElementById('valB').innerText = "--.--- с";
        document.getElementById('valDiff').innerText = "--.--- с";
        
        // Включаем зеленые кнопки меток
        document.getElementById('btn-lapA').disabled = false;
        document.getElementById('btn-lapB').disabled = false;
        
        startTime = performance.now();
        animate();
    }}

    function recordLap(label) {{
        if (label === 'A') {{
            timeA = currentElapsed;
            document.getElementById('valA').innerText = timeA.toFixed(3) + " с";
            document.getElementById('btn-lapA').disabled = true;
        }} else if (label === 'B') {{
            timeB = currentElapsed;
            document.getElementById('valB').innerText = timeB.toFixed(3) + " с";
            document.getElementById('btn-lapB').disabled = true;
        }}
        
        // Расчет разницы времени между метками
        if (timeA !== null && timeB !== null) {{
            let diff = timeB - timeA;
            document.getElementById('valDiff').innerText = diff.toFixed(3) + " с";
        }}
    }}

    function animate() {{
        let now = performance.now();
        currentElapsed = (now - startTime) / 1000; // Фиксируем точное время

        if (currentElapsed >= t_bottom) {{
            currentElapsed = t_bottom;
            document.getElementById('ball').setAttribute('cy', 20 + H_stop_m * scale);
            document.getElementById('stopwatch').innerText = "⏱️ Разом: " + currentElapsed.toFixed(3) + " с";
            document.getElementById('stopwatch').style.color = "#00FFCC";
            
            // Выключаем кнопки, если шарик уже упал
            document.getElementById('btn-lapA').disabled = true;
            document.getElementById('btn-lapB').disabled = true;
            return;
        }}

        // Физический расчет координаты центра шарика
        let y_curr = v_term * currentElapsed - v_term * tau * (1 - Math.exp(-currentElapsed / tau));
        if (y_curr > H_stop_m) y_curr = H_stop_m;

        // Двигаем шарик и обновляем секундомер
        document.getElementById('ball').setAttribute('cy', 20 + y_curr * scale);
        document.getElementById('stopwatch').innerText = "⏱️ Секундомір: " + currentElapsed.toFixed(3) + " с";

        animationId = requestAnimationFrame(animate);
    }}
</script>

    </body>
    </html>
    """
    
    components.html(html_src, height=720)

 # Оновлена таблиця констант без готового значення в'язкості
st.write("---")
st.subheader("📋 Довідкові дані лабораторної установки")
df_info = pd.DataFrame({
    "Параметр (Одиниці вимірювання)": [
        "Температура досліду (°C)",
        "Густина рідини (кг/м³)",
        "Густина матеріалу кульки (кг/м³)",
        "Радіус кульки (мм)",
        "Відстань між мітками А та Б (м)",
    ],
    "Значення": [
        f"{T_C}",
        f"{rho_f}", 
        f"{rho_s}", 
        f"{r_mm}", 
        f"{L_distance:.2f}"
    ]
})
st.table(df_info)
