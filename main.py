import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# --- 1. НАСТРОЙКА БАЗЫ ДАННЫХ ---
SUPABASE_URL = "https://idowlywjfzqoishuvtdf.supabase.co"
SUPABASE_KEY = "sb_publishable_qEMDfDfxGHyPXmgwlmMjAA_jSj6ZtT-"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@st.cache_data  # Кэшируем, чтобы не дергать базу при каждом движении ползунка
def get_companies():
    response = supabase.table("companies").select("*").execute()
    return response.data


@st.cache_data
def get_company_data(company_id):
    coeffs = supabase.table("profession_coefficients").select("*").eq("company_id", company_id).execute()
    finances = supabase.table("financial_rates").select("*").eq("company_id", company_id).execute()
    return coeffs.data[0], finances.data[0]


# --- 2. НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="SWP: Работодатель", page_icon="🏭", layout="wide")
st.title("Система стратегического планирования кадров (MVP)")

# --- 3. БОКОВАЯ ПАНЕЛЬ (ВВОД ДАННЫХ) ---
st.sidebar.header("Настройки модели")

companies = get_companies()
if companies:
    # Создаем словарь для удобного выбора в выпадающем списке
    company_dict = {c['name']: c for c in companies}
    selected_name = st.sidebar.selectbox("Выберите предприятие", list(company_dict.keys()))
    current_company = company_dict[selected_name]

    # Подтягиваем коэффициенты для выбранной компании
    coeffs, finances = get_company_data(current_company['id'])

    st.sidebar.subheader("Текущее состояние")
    # Ползунки. Стартовые значения (value) берем из базы, но пользователь может их менять
    total_staff = st.sidebar.number_input("Численность работников", value=current_company['total_staff'])
    required_staff = st.sidebar.number_input("Требуемая численность", value=current_company['required_staff'])

    st.sidebar.subheader("Движение кадров (в год)")
    annual_loss = st.sidebar.slider("Ежегодное выбытие (чел)", min_value=0, max_value=300, value=105)
    external_arrival = st.sidebar.slider("Внешний приток (чел)", min_value=0, max_value=300, value=69)

    st.sidebar.subheader("Горизонт")
    horizon = st.sidebar.slider("Горизонт прогнозирования (лет)", min_value=1, max_value=15, value=10)

# --- 4. ОСНОВНОЙ ЭКРАН И ВКЛАДКИ ---
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Текущее состояние", "📉 Прогноз потерь", "🎓 Воронка подготовки", "💰 Финансы и Заказ"])

# Алгоритм 1: Текущее состояние
with tab1:
    st.subheader("Исходный профиль предприятия")
    col1, col2, col3 = st.columns(3)
    col1.metric("Текущая численность", f"{total_staff} чел.")
    col2.metric("Ежегодные потери", f"{annual_loss} чел.")
    col3.metric("Ежегодный приток", f"{external_arrival} чел.")

    st.info(f"Профессия для расчета: **{coeffs['profession_name']}**")

# Алгоритм 2 и 3: Прогноз потерь и расчет дефицита
with tab2:
    st.subheader("Прогноз изменения кадрового состава")

    # Математика: считаем падение численности по годам
    net_loss = annual_loss - external_arrival  # Чистая убыль в год

    # Создаем список данных для таблицы и графика
    forecast_data = []
    current_p = total_staff

    for year in range(horizon + 1):
        forecast_data.append({"Год": year, "Численность": current_p})
        current_p -= net_loss  # Вычитаем убыль каждый год

    df_forecast = pd.DataFrame(forecast_data)

    col_chart, col_table = st.columns([2, 1])

    with col_chart:
        # Рисуем простой линейный график встроенными средствами Streamlit
        st.line_chart(df_forecast.set_index("Год"))

    with col_table:
        st.dataframe(df_forecast, use_container_width=True)

    # Считаем итоговый дефицит через T лет
    final_staff = df_forecast.iloc[-1]["Численность"]
    total_deficit = required_staff - final_staff

    if total_deficit > 0:
        st.error(f"⚠️ Внимание! Накопленный кадровый дефицит через {horizon} лет составит: **{total_deficit} чел.**")
        st.warning(f"Необходимый поток для компенсации: **{net_loss} специалистов в год.**")
    else:
        st.success("Кадровый дефицит не прогнозируется.")

# Заглушки для следующих этапов
# --- ПЕРЕД НАЧАЛОМ tab3 НУЖНО ДОБАВИТЬ ИМПОРТ ---
# Убедись, что в самом верху файла (где import streamlit) есть эта строка:
import plotly.express as px

# ... (твой предыдущий код до tab3) ...

# Алгоритм 4: Формирование кадрового потенциала (Воронка)
with tab3:
    st.subheader("Обратная образовательная воронка")

    if net_loss > 0:
        st.write(
            "Для получения нужного числа специалистов через 5 лет, рассчитаем стартовый набор школьников с учетом потерь на всех этапах обучения.")

        # Даем пользователю возможность поиграть с эффективностью (по умолчанию берем из БД)
        base_eff_percent = int(coeffs['base_efficiency'] * 100)
        current_efficiency = st.slider("Эффективность профориентации (%)", min_value=5, max_value=80,
                                       value=base_eff_percent) / 100.0

        # Коэффициенты потерь из базы
        k1 = coeffs['k1_enrollment']
        k2 = coeffs['k2_graduation']
        k3 = coeffs['k3_employment']

        # Математика: Общая конверсия воронки
        total_conversion = current_efficiency * k1 * k2 * k3

        # Обратный расчет: сколько нужно на входе, чтобы получить net_loss на выходе
        required_students = int(net_loss / total_conversion) + 1

        st.info(f"🎯 Для закрытия дефицита в **{net_loss}** чел. требуется набрать **{required_students}** школьников.")

        # Считаем ступени воронки для графика
        val_1 = required_students
        val_2 = int(val_1 * current_efficiency)
        val_3 = int(val_2 * k1)
        val_4 = int(val_3 * k2)
        val_5 = int(val_4 * k3)

        # Отрисовка интерактивной воронки Plotly
        stages = ["Набор (Школьники)", "Выбрали профессию", "Поступили на обучение", "Завершили обучение",
                  "Трудоустроились на завод"]
        values = [val_1, val_2, val_3, val_4, val_5]

        fig = px.funnel(x=values, y=stages)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("Кадрового дефицита нет, набор не требуется.")

# Алгоритм 5 и 6: Экономика и Социальный заказ
with tab4:
    st.subheader("Финансовая модель и Социальный заказ")

    if net_loss > 0:
        cost_per_student = finances['cost_per_child']
        market_cost = finances['market_recruitment_cost']

        # Считаем бюджеты
        total_program_cost = required_students * cost_per_student
        market_alternative_cost = net_loss * market_cost

        col1, col2 = st.columns(2)
        col1.metric("Стоимость программы (инвестиции)", f"{total_program_cost:,.0f} ₽".replace(',', ' '))
        col2.metric("Схантить готовых с рынка", f"{market_alternative_cost:,.0f} ₽".replace(',', ' '))

        # Тот самый "крючок" для инвестора - расчет экономии
        if total_program_cost < market_alternative_cost:
            st.success(
                f"Выгода предприятия (ROI) составит: **{(market_alternative_cost - total_program_cost):,.0f} ₽**".replace(
                    ',', ' '))

        st.divider()
        st.subheader("📄 Итоговый социальный заказ")

        # Формируем итоговый текстовый документ
        st.code(f"""
ЗАКАЗЧИК: {current_company['name']}
ПРОФЕССИЯ: {coeffs['profession_name']}

ЦЕЛЕВОЙ РЕЗУЛЬТАТ: {net_loss} специалистов ежегодно
СРОК ПОДГОТОВКИ: {coeffs['training_years']} лет

НЕОБХОДИМЫЙ НАБОР: {required_students} участников (школьников)
БЮДЖЕТ ПРОГРАММЫ: {total_program_cost:,.0f} руб.
        """, language="text")