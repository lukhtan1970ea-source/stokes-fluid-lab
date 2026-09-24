import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Настройка сторінки
st.set_page_config(
    page_title="Лабораторна робота: Метод Стокса", layout="wide"
)

st.title("🔬 Віртуальна лабораторна робота")
st.header("Визначення динамічної в'язкості рідини методом Стокса")

# Теоретична довідка
with st.expander("📖 Коротка теорія"):
    st.markdown(
        """
    При падінні сферичного тіла в в'язкій рідині на нього діють три сили:
    1. **Сила тяжіння:** \(F_g = m g = \frac{4}{3} \pi r^3 \rho_s g\)
    2. **Виштовхувальна сила (Архімеда):** \(F_A = \frac{4}{3} \pi r^3 \rho_f g\)
    3. **Сила опору середовища (Сила Стокса):** \(F_{st} = 6 \pi \eta r v\)
    
    Рівняння руху кульки: \(m \frac{dv}{dt} = F_g - F_A - F_{st}\)
    
    Коли сили урівноважуються, кулька рухається з **термінальною (усталеною) швидкістю** \(v_0\):
    \[v_0 = \frac{2}{9} \frac{r^2 g (\rho_s - \rho_f)}{\eta}\]
    
    **Завдання студента:** виміряти час падіння кульки між мітками, знайти усталену швидкість та експериментально розрахувати коефіцієнт динамічної в'язкості \(\eta\).
    """
    )

# --- Бічна панель параметрів ---
st.sidebar.header("⚙️ Параметри експерименту")

# Розширений список рідин
liquid_options = {
    "Гліцерин": {"rho": 1260.0, "eta": 1.49},
    "Касторова олія": {"rho": 961.0, "eta": 0.95},
    "Машинна олія (SAE 40)": {"rho": 888.0, "eta": 0.32},
    "Рідкий мед": {"rho": 1420.0, "eta": 10.0},
    "Згущене молоко (натуральне)": {"rho": 1300.0, "eta": 2.5},
    "Цукровий сироп (70%)": {"rho": 1350.0, "eta": 0.4, "note": "Кетчуп є неньютонівською рідиною, тому замінено сиропом"},
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

# Константи та розрахунок руху
g = 9.81
V = (4 / 3) * np.pi * (r**3)
m = V * rho_s

# Термінальна швидкість та час релаксації
v_term = (2 / 9) * (r**2) * g * (rho_s - rho_f) / eta
tau = m / (6 * np.pi * eta * r)

# Параметри циліндра
H_cylinder = 0.5  # висота циліндра 50 см
y_start_label = 0.1  # Верхня мітка (10 см від верху)
y_end_label = 0.4  # Нижня мітка (40 см від верху)
L_distance = y_end_label - y_start_label  # Експериментальна відстань (30 см)

# Перевірка умови падіння (якщо кулька легша за рідину)
if rho_s <= rho_f:
    st.error(
        "❌ Помилка: Густина кульки менша або дорівнює густині рідини! Кулька не буде тонути. Змініть матеріал кульки або рідину."
    )
else:
    # --- Основний інтерфейс ---
    col_anim, col_graph = st.columns([1, 1.5])

    with col_anim:
        st.subheader("🧪 Віртуальний циліндр")

        # Кнопка запуску симуляції
        start_sim = st.button("🚀 Запустити кульку")

        # Контейнер для графіка-анімації
        anim_placeholder = st.empty()

        # Функція для малювання циліндра та кульки
        def draw_cylinder(y_ball=0.0):
            fig = go.Figure()
            # Цилиндр
            fig.add_shape(
                type="rect",
                x0=-0.2,
                y0=0,
                x1=0.2,
                y1=H_cylinder,
                line=dict(color="White", width=3),
                fillcolor="rgba(173, 216, 230, 0.3)",
            )
            # Верхня мітка (Старт відліку)
            fig.add_hline(
                y=H_cylinder - y_start_label,
                line_color="Red",
                line_width=2,
                annotation_text="Мітка А (Старт)",
                annotation_position="top left",
            )
            # Нижня мітка (Стоп відліку)
            fig.add_hline(
                y=H_cylinder - y_end_label,
                line_color="Red",
                line_width=2,
                annotation_text="Мітка Б (Стоп)",
                annotation_position="bottom left",
            )
            # Кулька
            fig.add_trace(
                go.Scatter(
                    x=[0],
                    y=[H_cylinder - y_ball],
                    mode="markers",
                    marker=dict(
                        size=r_mm * 6, color="DarkSlateGray", line=dict(width=1, color="White")
                    ),
                    name="Кулька",
                )
            )

            fig.update_layout(
                xaxis=dict(visible=False, range=[-0.5, 0.5]),
                yaxis=dict(
                    title="Висота (м)", range=[-0.05, H_cylinder + 0.05]
                ),
                height=500,
                margin=dict(l=20, r=20, t=20, b=20),
                template="plotly_dark",
                showlegend=False,
            )
            return fig

        # Початковий стан середовища
        if not start_sim:
            anim_placeholder.plotly_chart(draw_cylinder(0.0), use_container_width=True)
            st.info("Натисніть кнопку 'Запустити кульку' для початку вимірів.")
        else:
            # Анімація руху
            t_start = time.time()
            sim_time = 0.0

            # Розрахуємо точний аналітичний час проходження міток для виведення на секундомір
            # y(t) = v_term * t - v_term * tau * (1 - exp(-t/tau))
            # Для простоти інтерфейсу виведемо реальний час симуляції
            t_a = None
            t_b = None

            status_text = st.empty()
            stopwatch_text = st.empty()

            while sim_time < 5.0:  # Обмеження симуляції 5 секунд
                sim_time = time.time() - t_start

                # Чисельно або аналітично знаходимо координату y (вниз від поверхні)
                # Оскільки рух у в'язкому середовищі швидко стає лінійним:
                y_ball = v_term * sim_time - v_term * tau * (
                    1 - np.exp(-sim_time / tau)
                )

                if y_ball >= H_cylinder:
                    y_ball = H_cylinder
                    anim_placeholder.plotly_chart(
                        draw_cylinder(y_ball), use_container_width=True
                    )
                    break

                # Фіксація часу на мітках
                if y_ball >= y_start_label and t_a is None:
                    t_a = sim_time
                if y_ball >= y_end_label and t_b is None:
                    t_b = sim_time

                anim_placeholder.plotly_chart(
                    draw_cylinder(y_ball), use_container_width=True
                )

                # Оновлення секундоміра
                stopwatch_text.metric(
                    label="⏱️ Віртуальний секундомір", value=f"{sim_time:.3f} с"
                )
                time.sleep(0.03)  # Контроль плавності кадрів

            # Виведення результатів вимірювання для студентів
            st.success("🏁 Кулька досягла дна циліндра!")
            st.write(f"**Результати для вашого протоколу:**")
            st.write(f"• Час проходження мітки А: `{t_a:.3f} с`" if t_a else "• Мітка А не досягнута")
            st.write(f"• Час проходження мітки Б: `{t_b:.3f} с`" if t_b else "• Мітка Б не досягнута")
            if t_a and t_b:
                st.info(
                    f"⏱️ **Експериментальний час падіння (t_Б - t_А):** `{(t_b - t_a):.3f} с` на відстані `{L_distance*100:.0f} см`"
                )

    with col_graph:
        st.subheader("📈 Графіки динаміки процесу")

        # Тимчасова сітка для теоретичного графіка
        t_grid = np.linspace(0, max(3.0, 5 * tau), 300)
        v_grid = v_term * (1 - np.exp(-t_grid / tau))

        fig_v = go.Figure()
        fig_v.add_trace(
            go.Scatter(
                x=t_grid, y=v_grid, mode="lines", name="Швидкість v(t)"
            )
        )
        fig_v.add_hline(
            y=v_term,
            line_dash="dash",
            line_color="red",
            annotation_text=f"v_term = {v_term:.3f} м/с",
        )
        fig_v.update_layout(
            title="Залежність швидкості кульки від часу",
            xaxis_title="Час t (с)",
            yaxis_title="Швидкість v (м/с)",
            template="plotly_dark",
        )
        st.plotly_chart(fig_v, use_container_width=True)

        # Таблиця констант середовища (без формул перевірки)
        st.subheader("📋 Довідкові дані системи")
        df_info = pd.DataFrame(
            {
                "Параметр (Одиниці вимірювання)": [
                    "Густина рідини (кг/м³)",
                    "Густина матеріалу кульки (кг/м³)",
                    "Радіус кульки (мм)",
                    "Відстань між мітками А та Б (м)",
                ],
                "Значення": [
                    f"{rho_f}",
                    f"{rho_s}",
                    f"{r_mm}",
                    f"{L_distance:.2f}",
                ],
            }
        )
        st.table(df_info)

