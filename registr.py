import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from tinydb import TinyDB, Query
import os
from PIL import Image

st.set_page_config(page_title="Вход/Регистрация", layout="wide", initial_sidebar_state="collapsed")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

# Инициализация базы данных пользователей
user_db = TinyDB('user_database.json')

# Убедимся, что папка для хранения изображений профиля существует
PROFILE_IMAGES_DIR = 'profile_images'
if not os.path.exists(PROFILE_IMAGES_DIR):
    os.makedirs(PROFILE_IMAGES_DIR)

# Функция для регистрации пользователя
def register_user(username, email, password, profile_image_path=None):
    User = Query()
    if user_db.search(User.username == username):
        return False, "Пользователь с таким именем уже существует"
    if user_db.search(User.email == email):
        return False, "Пользователь с таким email уже существует"
    user_data = {
        'username': username,
        'email': email,
        'password': password,
        'profile_image': profile_image_path if profile_image_path else "profile_images/default_user_icon.png"
    }
    user_db.insert(user_data)
    return True, "Регистрация успешна"

def check_admin_credentials(username, password):
    try:
        return (username == st.secrets["admin"]["username"] and 
                password == st.secrets["admin"]["password"])
    except:
        return False

# Функция для входа в систему
def login(username, password):
    # Сначала проверяем админ-доступ
    if check_admin_credentials(username, password):
        return True
        
    User = Query()
    user = user_db.search((User.username == username) & (User.password == password))
    return bool(user)

# Заголовок
st.title("Вход в систему")

# Форма для входа
username = st.text_input("Имя пользователя")
password = st.text_input("Пароль", type="password")

# Кнопки для входа и регистрации
if st.button("Login"):
    if username and password:  # Проверка на пустые поля
        if login(username, password):
            st.session_state.authenticated = True
            st.session_state.username = username
            # Добавляем флаг админа
            st.session_state.is_admin = check_admin_credentials(username, password)
            st.success("Вы вошли в систему")
            switch_page("app")  # Перенаправление в основное приложение
        else:
            st.error("Неправильный логин или пароль.")
    else:
        st.error("Пожалуйста, введите имя пользователя и пароль.")

# Кнопка для регистрации
if not st.session_state.get("authenticated", False):
    if st.button("Зарегистрироваться"):
        st.session_state.show_registration_form = True

# Проверка состояния для отображения формы регистрации
if "show_registration_form" not in st.session_state:
    st.session_state.show_registration_form = False

if st.session_state.show_registration_form:
    with st.form("registration_form"):
        reg_username = st.text_input("Имя пользователя для регистрации")
        reg_email = st.text_input("Email")
        reg_password = st.text_input("Пароль", type="password")
        reg_confirm_password = st.text_input("Подтвердите пароль", type="password")
        
        # Добавляем загрузчик файла для фотографии профиля
        reg_profile_image = st.file_uploader("Загрузите фотографию профиля", type=["png", "jpg", "jpeg"])
        
        if reg_profile_image is not None:
            st.image(reg_profile_image, width=150)
        
        submit_button = st.form_submit_button("Зарегистрироваться")

        if submit_button:
            if not reg_username or not reg_email or not reg_password or not reg_confirm_password:
                st.error("Пожалуйста, заполните все поля.")
            elif reg_password != reg_confirm_password:
                st.error("Пароли не совпадают")
            else:
                # Сохранение фотографии профиля
                if reg_profile_image is not None:
                    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
                    if reg_profile_image.size > MAX_FILE_SIZE:
                        st.error("Размер файла превышает 2MB.")
                        st.stop()
                    # Генерация уникального имени файла
                    image_filename = f"{reg_username}_{reg_profile_image.name}"
                    image_path = os.path.join(PROFILE_IMAGES_DIR, image_filename)
                    with open(image_path, "wb") as f:
                        f.write(reg_profile_image.getbuffer())
                    try:
                        img = Image.open(reg_profile_image)
                        img.verify()
                    except (IOError, SyntaxError) as e:
                        st.error("Файл не является допустимым изображением.")
                        st.stop()
                else:
                    image_path = os.path.join(PROFILE_IMAGES_DIR, "default_user_icon.png")  # Путь к стандартной иконке

                success, message = register_user(reg_username, reg_email, reg_password, image_path)
                if success:
                    st.success(message)
                    st.session_state.username = reg_username
                    st.session_state.authenticated = True
                    switch_page("app")
                else:
                    st.error(message)

# Добавление CSS для кнопок
st.markdown(
    """
    <style>
    .stButton {
        margin-left: 0px;  /* Установите отрицательный отступ для сдвига влево */
        margin-right: 0px;  /* Установите положительный отступ для сдвига вправо */
    }
    </style>
    """,
    unsafe_allow_html=True
)