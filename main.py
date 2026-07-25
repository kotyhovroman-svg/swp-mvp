import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# --- 1. НАСТРОЙКА БАЗЫ ДАННЫХ ---
SUPABASE_URL = "https://idowlywjfzqoishuvtdf.supabase.co"
SUPABASE_KEY = "sb_publishable_qEMDfDfxGHyPXmgwlmMjAA_jSj6ZtT-"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- 2. ФУНКЦИИ АВТОРИЗАЦИИ (Именно их Питон не мог найти) ---
def login_user(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response.user, None
    except Exception as e:
        return None, str(e)


def logout_user():
    supabase.auth.sign_out()


# --- 3. ФУНКЦИИ ПОЛУЧЕНИЯ ДАННЫХ ---
@st.cache_data
def get_companies():
    response = supabase.table("companies").select("*").execute()
    return response.data


@st.cache_data
def get_company_data(company_id):
    coeffs = supabase.table("profession_coefficients").select("*").eq("company_id", company_id).execute()
    finances = supabase.table("financial_rates").select("*").eq("company_id", company_id).execute()
    return coeffs.data[0], finances.data[0]


# --- 4. НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="SWP: Работодатель", page_icon="🏭", layout="wide")

# --- 5. ЛОГИКА АВТОРИЗАЦИИ НА ЭКРАНЕ ---
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    # ТРЮК С КОЛОНКАМИ: создаем 3 колонки.
    # Цифры [1, 1, 1] означают пропорции. Они будут одинаковой ширины.
    # Если захочешь сделать форму чуть шире, напиши [1, 2, 1]
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:  # Помещаем наш интерфейс строго в центральную колонку
        # Используем HTML, чтобы отцентрировать сам заголовок
        st.markdown("<h3 style='text-align: center;'>🔑 Вход в систему SWP</h3>", unsafe_allow_html=True)
        st.write("")  # Добавляем пустую строку для воздуха

        with st.form("login_form"):
            # Добавили placeholder, чтобы внутри полей были серые подсказки
            email = st.text_input("Email")
            password = st.text_input("Пароль", type="password")

            # use_container_width=True растянет кнопку логина красиво на всю ширину нашей узкой колонки
            submit = st.form_submit_button("Войти", use_container_width=True)

            if submit:
                user, error = login_user(email, password)
                if user:
                    st.session_state.user = user
                    st.success("Успешный вход!")
                    st.rerun()
                else:
                    st.error(f"Ошибка входа: {error}")

    # ОСТАНАВЛИВАЕМ ВЫПОЛНЕНИЕ КОДА ЗДЕСЬ, ЕСЛИ НЕ АВТОРИЗОВАН
    st.stop()

# =====================================================================
# ВЕСЬ КОД НИЖЕ ВЫПОЛНЯЕТСЯ ТОЛЬКО ЕСЛИ ПОЛЬЗОВАТЕЛЬ УСПЕШНО ВОШЕЛ
# =====================================================================

st.title("Система стратегического планирования кадров (MVP)")

# --- 6. БОКОВАЯ ПАНЕЛЬ И ВЫБОР ДАННЫХ ---
st.sidebar.success(f"Вы вошли как: **{st.session_state.user.email}**")
if st.sidebar.button("Выйти"):
    logout_user()
    st.session_state.user = None
    st.rerun()

st.sidebar.header("Настройки модели")

# Дальше идет твой код с companies = get_companies(), ползунками и вкладками (tab1, tab2...)
# ...

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
# Алгоритм 4: Формирование кадрового потенциала (Многолетняя воронка)
with tab3:
    st.subheader("Динамика образовательной воронки")

    if net_loss > 0:
        st.write(
            f"Расчет потока школьников на горизонт **{horizon} лет** с учетом ежегодного роста эффективности профориентации.")

        # Получаем базовые параметры из БД
        base_eff = coeffs['base_efficiency']
        eff_growth = coeffs['efficiency_growth']
        k1 = coeffs['k1_enrollment']
        k2 = coeffs['k2_graduation']
        k3 = coeffs['k3_employment']

        # Считаем данные по годам (от 1 до horizon)
        funnel_data = []
        total_students_horizon = 0  # Сюда будем плюсовать всех детей за все годы

        for year in range(1, horizon + 1):
            # Эффективность растет каждый год (Например: 20% -> 23% -> 26%)
            current_eff = base_eff + (year - 1) * eff_growth
            if current_eff > 1.0: current_eff = 1.0  # Защита от превышения 100%

            total_conversion = current_eff * k1 * k2 * k3
            required_intake = int(net_loss / total_conversion) + 1

            total_students_horizon += required_intake  # Накапливаем общий поток

            funnel_data.append({
                "Год программы": f"Год {year}",
                "Эффективность": f"{int(current_eff * 100)}%",
                "Необходимый набор (чел)": required_intake
            })

        df_funnel = pd.DataFrame(funnel_data)

        col_f1, col_f2 = st.columns([1, 1])

        with col_f1:
            st.write("**Снижение потребности в наборе** (за счет роста эффективности)")
            # График: как падает потребность в наборе детей с годами
            fig_bar = px.bar(df_funnel, x="Год программы", y="Необходимый набор (чел)", text="Необходимый набор (чел)")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_f2:
            st.write("**Воронка 1-го года (Детально)**")
            # Отрисуем красивую воронку конкретно для стартового года
            first_year_intake = df_funnel.iloc[0]["Необходимый набор (чел)"]
            val_1 = first_year_intake
            val_2 = int(val_1 * base_eff)
            val_3 = int(val_2 * k1)
            val_4 = int(val_3 * k2)
            val_5 = int(val_4 * k3)

            stages = ["Набор (Школьники)", "Выбрали профессию", "Поступили на обучение", "Завершили обучение",
                      "Трудоустроились"]
            values = [val_1, val_2, val_3, val_4, val_5]

            fig_funnel = px.funnel(x=values, y=stages)
            st.plotly_chart(fig_funnel, use_container_width=True)

        # Выводим таблицу с расчетами
        st.dataframe(df_funnel.set_index("Год программы"), use_container_width=True)

    else:
        st.success("Кадрового дефицита нет, набор не требуется.")

# Алгоритм 5 и 6: Экономика и Социальный заказ
with tab4:
    st.subheader("Финансовая модель и Социальный заказ")

    if net_loss > 0:
        cost_per_student = finances['cost_per_child']
        market_cost = finances['market_recruitment_cost']

        # Считаем бюджеты НА ВЕСЬ ГОРИЗОНТ
        total_program_cost = total_students_horizon * cost_per_student

        # Альтернатива: сколько бы стоило нанять этих людей с рынка за тот же горизонт
        total_needed_over_horizon = net_loss * horizon
        market_alternative_cost = total_needed_over_horizon * market_cost

        st.info(f"Смета рассчитана накопительным итогом на весь горизонт планирования: **{horizon} лет**")

        col1, col2 = st.columns(2)
        col1.metric(f"Бюджет программы (за {horizon} лет)", f"{total_program_cost:,.0f} ₽".replace(',', ' '))
        col2.metric(f"Схантить {total_needed_over_horizon} готовых с рынка",
                    f"{market_alternative_cost:,.0f} ₽".replace(',', ' '))

        if total_program_cost < market_alternative_cost:
            st.success(
                f"Выгода предприятия (ROI) за {horizon} лет составит: **{(market_alternative_cost - total_program_cost):,.0f} ₽**".replace(
                    ',', ' '))

        st.divider()
        st.subheader("📄 Итоговый социальный заказ")

        st.code(f"""
ЗАКАЗЧИК: {current_company['name']}
ПРОФЕССИЯ: {coeffs['profession_name']}

ГОРИЗОНТ ПРОГРАММЫ: {horizon} лет
ЦЕЛЕВОЙ РЕЗУЛЬТАТ: {total_needed_over_horizon} специалистов за период (по {net_loss} ежегодно)
СРОК ПОДГОТОВКИ: {coeffs['training_years']} лет

ОБЩИЙ НАБОР (СУММАРНО): {total_students_horizon} участников (школьников)
ИТОГОВЫЙ БЮДЖЕТ: {total_program_cost:,.0f} руб.
        """, language="text")