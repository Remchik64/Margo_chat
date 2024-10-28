import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from tinydb import TinyDB, Query

# Проверка аутентификации
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    switch_page("registr")

st.set_page_config(page_title="Оплата", layout="wide")

# Инициализация базы данных пользователей
user_db = TinyDB('user_database.json')

# Получение данных пользователя
User = Query()
user_data = user_db.search(User.username == st.session_state.username)

if not user_data:
    st.error("Пользователь не найден.")
else:
    user_data = user_data[0]
    # Инициализация баланса, если его нет
    if 'balance' not in user_data:
        user_db.update({'balance': 0.0}, User.username == st.session_state.username)
        user_data['balance'] = 0.0
    
    # Инициализация генераций, если их нет
    if 'generations' not in user_data:
        user_db.update({'generations': 0}, User.username == st.session_state.username)
        user_data['generations'] = 0

    st.write(f"Ваш баланс: {round(user_data['balance'], 2)} рублей")

# Инициализация атрибутов, если они не существуют
if "generations_to_buy" not in st.session_state:
    st.session_state.generations_to_buy = 0

if "rubles_to_pay" not in st.session_state:
    st.session_state.rubles_to_pay = 0

st.title("Страница оплаты")

# Отображение баланса
st.header("Баланс")
st.write(f"Ваш баланс: {round(user_data['balance'], 2)} рублей")
st.write(f"Доступные генерации: {user_data.get('generations', 0)}")

# Покупка генераций
st.header("Покупка генераций")
generations_to_buy = st.number_input("Количество генераций для покупки", min_value=1, step=1)

def calculate_cost(generations):
    return generations * 3  # 1 генерация = 3 рубля

cost = calculate_cost(generations_to_buy)
st.write(f"Стоимость: {cost} рублей")

if st.button("Купить генерации"):
    if user_data['balance'] >= cost:
        new_balance = user_data['balance'] - cost
        new_generations = user_data.get('generations', 0) + generations_to_buy
        user_db.update({'balance': new_balance, 'generations': new_generations}, User.username == st.session_state.username)
        st.success(f"Вы успешно купили {generations_to_buy} генераций!")
        st.write(f"Новый баланс: {round(new_balance, 2)} рублей")
        st.write(f"Доступные генерации: {new_generations}")
    else:
        st.error("Недостаточно средств на балансе.")

# Пополнение баланса (для демонстрационных целей)
st.header("Пополнение баланса")
amount_to_add = st.number_input("Сумма для пополнения (в рублях)", min_value=10, step=10)

if st.button("Пополнить баланс"):
    new_balance = user_data['balance'] + amount_to_add
    user_db.update({'balance': new_balance}, User.username == st.session_state.username)
    st.success(f"Баланс успешно пополнен на {amount_to_add} рублей!")
    st.write(f"Новый баланс: {round(new_balance, 2)} рублей")

# Добавляем поле 'generations' для каждого пользователя
for user in user_db.all():
    if 'generations' not in user:
        user_db.update({'generations': 0}, User.username == user['username'])
