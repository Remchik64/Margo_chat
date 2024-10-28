import streamlit as st
from tinydb import TinyDB, Query
import requests
import hashlib
from streamlit_extras.switch_page_button import switch_page
from googletrans import Translator
import os
import base64
from PIL import Image

# Проверяем аутентификацию
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    switch_page("registr")

# Инициализируем базы данных
chat_db = TinyDB('chat_history.json')
user_db = TinyDB('user_database.json')

# Папка с изображениями профиля (исправленный путь)
PROFILE_IMAGES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'profile_images'))
ASSISTANT_ICON_PATH = os.path.join(PROFILE_IMAGES_DIR, 'assistant_icon.png')  # Путь к иконке ассистента

# Проверяем существование файла иконки ассистента
if os.path.exists(ASSISTANT_ICON_PATH):
    try:
        assistant_avatar = Image.open(ASSISTANT_ICON_PATH)
    except Exception as e:
        st.error(f"Ошибка при открытии изображения ассистента: {e}")
        assistant_avatar = "🤖"  # Используем эмодзи по умолчанию
else:
    assistant_avatar = "🤖"  # Используем эмодзи по умолчанию

# Функция для получения объекта изображения профиля пользователя
def get_user_profile_image(username):
    User = Query()
    user_data = user_db.search(User.username == username)
    if user_data:
        user_data = user_data[0]
        if user_data.get('profile_image'):
            image_path = user_data['profile_image']
        else:
            image_path = os.path.join(PROFILE_IMAGES_DIR, "default_user_icon.png")
    else:
        image_path = os.path.join(PROFILE_IMAGES_DIR, "default_user_icon.png")

    #st.write(f"Загрузка изображения: {image_path}")  # Отладочный вывод

    if os.path.exists(image_path):
        try:
            return Image.open(image_path)
        except Exception as e:
            st.error(f"Ошибка при открытии изображения {image_path}: {e}")
            return "👤"  # Используем эмодзи по умолчанию
    else:
        st.error(f"Файл изображения не найден: {image_path}")
        return "👤"  # Используем эмодзи по умолчанию

# Определяем необходимые функции
def get_user_generations():
    User = Query()
    user_data = user_db.search(User.username == st.session_state.username)
    if not user_data:
        return 0
    return user_data[0].get('generations', 0)

if 'available_generations' not in st.session_state:
    st.session_state.available_generations = get_user_generations()

def update_user_generations(used_generations):
    User = Query()
    current_generations = get_user_generations()
    new_generations = max(current_generations - used_generations, 0)
    user_db.update({'generations': new_generations}, User.username == st.session_state.username)
    st.session_state.available_generations = new_generations

def get_message_hash(role, content):
    return hashlib.md5(f"{role}:{content}".encode()).hexdigest()

def submit_question():
    user_input = st.session_state.get('user_input', '')
    if not user_input:
        st.warning("Пожалуйста, введите ваш вопрос.")
        return

    payload = {"question": user_input}
    available_generations = get_user_generations()
    if available_generations <= 0:
        st.warning("У вас недостаточно генераций. Пожалуйста, купите больше.")
        return

    response = requests.post('https://flowise-renataraev64.amvera.io/api/v1/prediction/4a4a3f5c-9ebf-4243-8d4f-b3b69dd57313', json=payload)
    output = response.json()

    if 'text' not in output:
        st.warning("Ошибка получения ответа от API.")
        return

    response_text = output['text']
    translated_text = translate_text(response_text)
    if not translated_text:
        st.warning("Ошибка при переводе ответа.")
        return

    # Проверка дубликатов
    user_hash = get_message_hash("user", user_input)
    assistant_hash = get_message_hash("assistant", translated_text)

    if "message_hashes" not in st.session_state:
        st.session_state.message_hashes = set()

    if user_hash not in st.session_state.message_hashes:
        st.session_state.message_hashes.add(user_hash)
        user_avatar = get_user_profile_image(st.session_state.username)
        with st.chat_message("user", avatar=user_avatar):
            st.write(user_input)
        chat_db.insert({"role": "user", "content": user_input})

    if assistant_hash not in st.session_state.message_hashes:
        st.session_state.message_hashes.add(assistant_hash)
        with st.chat_message("assistant", avatar=assistant_avatar):
            st.write(translated_text)
        chat_db.insert({"role": "assistant", "content": translated_text})

    update_user_generations(1)

def translate_text(text):
    translator = Translator()
    translation = translator.translate(text, dest='ru')
    return translation.text

def clear_chat_history():
    chat_db.truncate()  # Очистка базы данных истории чата
    if "message_hashes" in st.session_state:
        del st.session_state["message_hashes"]  # Сброс хэшей сообщений

# Основной интерфейс
st.title("Бизнес-Идея")
st.sidebar.write(f"Доступные генерации: {st.session_state.available_generations}")

# Добавляем кнопку очистки чата
if st.sidebar.button("Очистить чат"):
    clear_chat_history()
    st.rerun()  # Обновляем страницу для отображения изменений

# Отображение истории сообщений
chat_history = chat_db.all()
for idx, msg in enumerate(chat_history):
    if msg["role"] == "user":
        avatar = get_user_profile_image(st.session_state.username)
    else:
        avatar = assistant_avatar
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

# Поле ввода с формой
with st.form(key='question_form'):
    st.text_input("Введите ваш вопрос", key="user_input")
    submit_button = st.form_submit_button("Отправить")

if submit_button:
    submit_question()

st.write(f"Streamlit version: {st.__version__}")