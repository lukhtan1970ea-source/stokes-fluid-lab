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

    # Динамічний радіус кульки на екрані (в пікселях)
    r_pixels = float(r_mm * 3.0)
    
    # Визначаємо фізичну точку зупинки центру мас кульки
    scale_factor = 400 / H_cylinder
    r_screen_m = r_pixels / scale_factor
    H_stop_m = H_cylinder - r_screen_m

    # Функція розрахунку часу падіння до потрібної позначки
    def get_time_for_distance(y_target, v_t, t_rel):
        t_arr = np.linspace(0, 180.0, 50000)
        y_arr = v_t * t_arr - v_t * t_rel * (1 - np.exp(-t_arr / t_rel))
        idx = np.searchsorted(y_arr, y_target)
        return t_arr[idx] if idx < len(t_arr) else 180.0

    t_bottom = get_time_for_distance(H_stop_m, v_term, tau)

    # --- Інтерфейс лабораторного стенду ---
    st.subheader("🧪 Віртуальний стенд")
    st.caption("Керуйте експериментом за допомогою кнопок нижче. Фіксуйте час проходження міток А та Б вручну.")

    # Збираємо чистий HTML без синтаксичних конфліктів всередині f-строки
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
            .controls {{
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }}
            button {{
                color: white;
                border: none;
                padding: 10px 15px;
                font-size: 15px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
            }}
            #btn-start {{ background-color: #ff4b4b; width: 180px; }}
            #btn-start:hover {{ background-color: #ff3333; }}
            .btn-lap {{ background-color: #4CAF50; width: 130px; }}
            .btn-lap:hover {{ background-color: #45a049; }}
            .btn-lap:disabled {{ background-color: #555; cursor: not-allowed; opacity: 0.6; }}
            
            #results-panel {{
                margin-top: 15px;
                font-size: 16px;
                background-color: #1e2530;
                padding: 10px 20px;
                border-radius: 6px;
                width: 320px;
                border: 1px solid #343b47;
            }}
            .res-row {{
                display: flex;
                justify-content: space-between;
                margin: 5px 0;
            }}
            .res-val {{ color: #00FFCC; font-family: monospace; font-weight: bold; }}
            
            svg {{
                background-color: #1e1e1e;
                border-radius: 8px;
                margin-top: 5px;
            }}
        </style>
    </head>
    <body>

        <div id="stopwatch">⏱️ Секундомір: 0.000 с</div>
        
        <div class="controls">
            <button id="btn-start" onclick="startSimulation()">🚀 Скинути кульку</button>
            <button id="btn-lapA" class="btn-lap" onclick="recordLap('A')" disabled>⏱️ Мітка А</button>
            <button id="btn-lapB" class="btn-lap" onclick="recordLap('B')" disabled>⏱️ Мітка Б</button>
        </div>

        <svg width="250" height="440" viewBox="0 0 250 440" xmlns="http://w3.org">
            <defs>
                <radialGradient id="ballGradient" cx="35%" cy="35%" r="65%">
                    <stop offset="0%" stop-color="#ffffff" />
                    <stop offset="40%" stop-color="#a6a6a6" />
                    <stop offset="100%" stop-color="#404040" />
                </radialGradient>
            </defs>

            <!-- Рідина в циліндрі (задній план) -->
            <rect x="85" y="20" width="80" height="400" fill="rgba(0, 150, 255, 0.15)" stroke="#ffffff" stroke-width="3" rx="5" />
            
            <!-- Кулька (середній план) -->
            <circle id="ball" cx="125" y="20" r="{r_pixels}" fill="url(#ballGradient)" stroke="#222" stroke-width="1" />
            
            <!-- Мітка А (передній план) -->
            <line x1="65" y1="{20 + (y_start_label * 400 / H_cylinder)}" x2="185" y2="{20 + (y_start_label * 400 / H_cylinder)}" stroke="#ff3333" stroke-width="2.5" stroke-dasharray="5" />
            <text x="5" y="{25 + (y_start_label * 400 / H_cylinder)}" fill="#ff3333" font-size="14" font-weight="bold" font-family="sans-serif">Мітка А</text>
            
            <!-- Мітка Б (передній план) -->
            <line x1="65" y1="{20 + (y_end_label * 400 / H_cylinder)}" x2="185" y2="{20 + (y_end_label * 400 / H_cylinder)}" stroke="#ff3333" stroke-width="2.5" stroke-dasharray="5" />
            <text x="5" y="{25 + (y_end_label * 400 / H_cylinder)}" fill="#ff3333" font-size="14" font-weight="bold" font-family="sans-serif">Мітка Б</text>
        </svg>

        <div id="results-panel">
            <div class="res-row"><span>Зафіксовано t<sub>А</sub>:</span> <span id="valA" class="res-val">--.--- с</span></div>
            <div class="res-row"><span>Зафіксовано t<sub>Б</sub>:</span> <span id="valB" class="res-val">--.--- с</span></div>
            <div class="res-row" style="border-top: 1px dashed #555; margin-top: 8px; padding-top: 5px; font-weight: bold;">
                <span>Різниця (Δt):</span> <span id="valDiff" class="res-val" style="color: #FFD700;">--.--- с</span>
            </div>
        </div>

        <script>
            const v_term = {v_term};
            const tau = {tau};
            const H_cylinder = {H_cylinder};
            const H_stop_m = {H_stop_m};
            const t_bottom = {t_bottom};
            const scale = 400 / H_cylinder;

            let startTime = null;
            let animationId = null;
            let currentElapsed = 0;
            
            let timeA = null;
            let timeB = null;

            function startSimulation() {{
                cancelAnimationFrame(animationId);
                document.getElementById('ball').setAttribute('cy', 20);
                document.getElementById('stopwatch').innerText = "⏱️ Секундомір: 0.000 с";
                document.getElementById('stopwatch').style.color = "#FFD700";
                
                timeA = null;
                timeB = null;
                document.getElementById('valA').innerText = "--.--- с";
                document.getElementById('valB').innerText = "--.--- с";
                document.getElementById('valDiff').innerText = "--.--- с";
                
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
                
                if (timeA !== null && timeB !== null) {{
                    let diff = timeB - timeA;
                    document.getElementById('valDiff').innerText = diff.toFixed(3) + " с";
                }}
            }}

            function animate() {{
                let now = performance.now();
                currentElapsed = (now - startTime) / 1000;

                if (currentElapsed >= t_bottom) {{
currentElapsed = t_bottom;document.getElementById('ball').setAttribute('cy', 20 + H_stop_m * scale);document.getElementById('stopwatch').innerText = "⏱️ Разом: " + currentElapsed.toFixed(3) + " с";document.getElementById('stopwatch').style.color = "#00FFCC";document.getElementById('btn-lapA').disabled = true;document.getElementById('btn-lapB').disabled = true;return;}}let y_val = v_term * currentElapsed - v_term * tau * (1 - Math.exp(-currentElapsed / tau));if (y_val > H_stop_m) y_val = H_stop_m;document.getElementById('ball').setAttribute('cy', 20 + y_val * scale);document.getElementById('stopwatch').innerText = "⏱️ Секундомір: " + currentElapsed.toFixed(3) + " с";animationId = requestAnimationFrame(animate);}}"""components.html(html_src, height=650)# Таблиця константst.write("---")st.subheader("📋 Довідкові дані лабораторної установки")df_info = pd.DataFrame({"Параметр (Одиниці вимірювання)": ["Густина рідини (кг/м³)","Густина матеріалу кольки (кг/м³)","Радіус кульки (мм)","Відстань між мітками А та Б (м)",],"Значення": [f"{rho_f}", f"{rho_s}", f"{r_mm}", f"{L_distance:.2f}"]})st.table(df_info)
