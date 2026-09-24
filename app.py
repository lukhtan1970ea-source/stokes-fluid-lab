import numpy as np
import pandas as pd
import plotly.graph_objects as go
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
        t_arr = np.linspace(0, 120.0, 50000) # Збільшено ліміт часу до 2 хвилин для дуже в'язких середовищ
        y_arr = v_t * t_arr - v_t * t_rel * (1 - np.exp(-t_arr / t_rel))
        idx = np.searchsorted(y_arr, y_target)
        return t_arr[idx] if idx < len(t_arr) else 120.0

    # Динамічно визначаємо час повного падіння, щоб адаптувати шкалу
    t_bottom = get_time_for_distance(H_cylinder, v_term, tau)

    # Генеруємо кадри анімації падіння (150 кадрів для ідеальної плавності)
    num_frames = 150
    t_frames = np.linspace(0, t_bottom, num_frames)
    y_frames = v_term * t_frames - v_term * tau * (1 - np.exp(-t_frames / tau))
    y_frames = np.clip(y_frames, 0, H_cylinder)

    # --- Інтерфейс лабораторного стенду ---
    st.subheader("🧪 Віртуальний стенд")
    st.caption("Натисніть кнопку ▶ PLAY під циліндром, щоб скинути кульку. Слідкуйте за часом проходження міток.")

    # Побудова інтерактивної анімації Plotly
    fig = go.Figure(
        data=[
            # Початковий стан кульки
            go.Scatter(
                x=[0], y=[H_cylinder], mode="markers",
                marker=dict(size=22, color="LightSlateGray", line=dict(width=2, color="White")),
                name="Кулька"
            )
        ],
        layout=go.Layout(
            xaxis=dict(visible=False, range=[-0.5, 0.5]),
            yaxis=dict(title="Висота рідини (м)", range=[-0.02, H_cylinder + 0.03], fixedrange=True),
            height=600, margin=dict(l=10, r=10, t=10, b=10),
            template="plotly_dark", showlegend=False,
            
            # Кнопки PLAY / PAUSE всередині контейнера графіка
            updatemenus=[dict(
                type="buttons", showactive=False, x=0.05, y=-0.05,
                buttons=[
                    dict(label="▶ PLAY (Скинути кульку)", method="animate",
                         args=[None, dict(frame=dict(duration=float(t_bottom*1000/num_frames), redraw=False), fromcurrent=True)]),
                    dict(label="⏸ PAUSE", method="animate",
                         args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")])
                ]
            )],
            
            # Динамічний повзунок-секундомір, який підлаштовується під будь-яку рідину
            sliders=[dict(
                steps=[dict(method="animate", args=[[f"frame_{i}"], dict(mode="immediate", frame=dict(duration=0, redraw=False))], label=f"{t_frames[i]:.3f} с") for i in range(num_frames)],
                x=0.05, y=-0.15, currentvalue=dict(font=dict(size=14, color="Gold"), prefix="⏱️ Час падіння: ", visible=True)
            )]
        ),
        frames=[go.Frame(
            data=[go.Scatter(x=[0], y=[H_cylinder - y_frames[i]])],
            name=f"frame_{i}"
        ) for i in range(num_frames)]
    )

    # Візуальні елементи циліндра та червоні мітки А і Б
    fig.add_shape(
        type="rect", x0=-0.15, y0=0, x1=0.15, y1=H_cylinder,
        line=dict(color="White", width=3), fillcolor="rgba(0, 150, 255, 0.12)"
    )
    fig.add_hline(
        y=H_cylinder - y_start_label, line_color="Red", line_width=2,
        annotation_text="Мітка А (Старт)", annotation_position="top left"
    )
    fig.add_hline(
        y=H_cylinder - y_end_label, line_color="Red", line_width=2,
        annotation_text="Мітка Б (Стоп)", annotation_position="bottom left"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Таблиця констант
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
