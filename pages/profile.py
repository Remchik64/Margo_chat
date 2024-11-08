import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from tinydb import TinyDB, Query
import os
from PIL import Image

# Проверка аутентификации
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("Пожалуйста, войдите в систему.")
    switch_page("registr")

st.set_page_config(page_title="Личный кабинет", layout="wide")

# Инициализация базы данных пользователей
user_db = TinyDB('user_database.json')

# Папка с изображениями профиля
PROFILE_IMAGES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'profile_images'))

# Получение данных пользователя
User = Query()
user_data = user_db.search(User.username == st.session_state.username)
if not user_data:
    st.error("Пользователь не найден.")
    switch_page("registr")
else:
    user_data = user_data[0]

st.title(f"Личный кабинет {user_data['username']}")

# Отображение информации о пользователе
st.header("Личная информация")
st.write(f"Email: {user_data['email']}")

# Отображение текущей фотографии профиля
st.subheader("Фотография профиля")
if user_data.get('profile_image') and os.path.exists(user_data['profile_image']):
    st.image(user_data['profile_image'], width=150)
    # Добавляем кнопку для удаления аватара
    if st.button("Удалить фотографию профиля"):
        old_image_path = user_data.get('profile_image')
        if old_image_path and old_image_path != os.path.join(PROFILE_IMAGES_DIR, "default_user_icon.png"):
            if os.path.exists(old_image_path):
                try:
                    os.remove(old_image_path)
                    st.success("Старое изображение успешно удалено.")
                except Exception as e:
                    st.error(f"Ошибка при удалении файла: {e}")
        # Обновляем данные пользователя в базе
        user_db.update({'profile_image': None}, User.username == st.session_state.username)
        st.success("Фотография профиля удалена")
        st.rerun()  # Перезагружаем страницу для обновления изменений
else:
    st.write("Фотография профиля не установлена.")

# Зона для обновления данных
st.header("Обновление данных")
new_email = st.text_input("Новый email", value=user_data['email'])
new_password = st.text_input("Новый пароль", type="password")
confirm_password = st.text_input("Подтвердите новый пароль", type="password")

# Загрузка новой фотографии профиля
new_profile_image = st.file_uploader("Обновите фотографию профиля", type=["png", "jpg", "jpeg"])

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

if new_profile_image is not None:
    if new_profile_image.size > MAX_FILE_SIZE:
        st.error("Размер файла превышает 2MB.")
        st.stop()

    try:
        img = Image.open(new_profile_image)
        img.verify()
    except (IOError, SyntaxError) as e:
        st.error("Файл не является допустимым изображением.")
        st.stop()

    st.image(new_profile_image, width=150)

if st.button("Обновить данные"):
    updates = {}
    if new_email and new_email != user_data['email']:
        updates['email'] = new_email

    if new_password:
        if new_password != confirm_password:
            st.error("Пароли не совпадают")
            st.stop()
        else:
            updates['password'] = new_password

    if new_profile_image is not None:
        # Сохранение новой фотографии профиля
        image_filename = f"{user_data['username']}_{new_profile_image.name}"
        image_path = os.path.join(PROFILE_IMAGES_DIR, image_filename)
        try:
            with open(image_path, "wb") as f:
                f.write(new_profile_image.getbuffer())
            updates['profile_image'] = image_path
            st.success("Новое изображение профиля успешно сохранено.")
        except Exception as e:
            st.error(f"Ошибка при сохранении файла: {e}")
            st.stop()

        # Удаление старого изображения (если оно не является стандартным)
        old_image_path = user_data.get('profile_image')
        if old_image_path and old_image_path != os.path.join(PROFILE_IMAGES_DIR, "default_user_icon.png"):
            if os.path.exists(old_image_path):
                try:
                    os.remove(old_image_path)
                    st.success("Старое изображение успешно удалено.")
                except Exception as e:
                    st.error(f"Ошибка при удалении файла: {e}")

    if updates:
        try:
            user_db.update(updates, User.username == st.session_state.username)
            st.success("Данные успешно обновлены")
            st.rerun()  # Перезагружаем страницу для обновления данных
        except Exception as e:
            st.error(f"Ошибка при обновлении данных: {e}")
    else:
        st.info("Нет изменений для обновления.")

# Зона для выхода из аккаунта
if st.button("Выйти"):
    st.session_state.authenticated = False
    st.session_state.username = None
    switch_page("registr")

# После проверки аутентификации
is_admin = st.session_state.get('is_admin', False)

if is_admin:
    st.header("Админ-панель")
    # Показать всех пользователей
    all_users = user_db.all()
    st.subheader("Список пользователей")
    for user in all_users:
        st.write(f"Пользователь: {user['username']}")
        st.write(f"Email: {user['email']}")
        st.write("---")