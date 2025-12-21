import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import base64
from pathlib import Path

# --- Конфигурация страницы ---
st.set_page_config(
    page_title="Классификатор писем",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Добавляем путь к модулям проекта ---
sys.path.append(str(Path(__file__).parent))

# --- Пути к файлам ---
# --- Пути к файлам ---
DATA_DIR = Path(r"D:\Hackaton_mail")
CATEGORIES_FILE = DATA_DIR / "categories" / "new_cats.txt"
INPUT_DIR = DATA_DIR / "data_input"
RESULTS_DIR = DATA_DIR / "data_output"
LOGO_PATH = DATA_DIR / "logo.jpg"

# Создаем директории если их нет
for directory in [DATA_DIR, INPUT_DIR, RESULTS_DIR]:
    directory.mkdir(exist_ok=True)

# --- Импорт классификатора ---
try:
    from classifier import (
        load_categories,
        classify_emails,
        process_email_file,
        save_results_to_csv
    )

    CLASSIFIER_AVAILABLE = True
except ImportError as e:
    st.error(f"Ошибка импорта classifier.py: {e}")
    st.info("Убедитесь, что файл classifier.py находится в той же директории")
    CLASSIFIER_AVAILABLE = False
except Exception as e:
    st.error(f"Ошибка при загрузке классификатора: {e}")
    CLASSIFIER_AVAILABLE = False


# --- Функция для отображения логотипа и заголовка ---
def show_header():
    """Отображает заголовок с логотипом"""

    # CSS стили
    st.markdown("""
    <style>
        .header-container {
            display: flex;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #E5E7EB;
        }
        .logo {
            height: 60px;
            width: auto;
            margin-right: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .title-text {
            color: #1E3A8A;
            font-size: 2.8rem;
            font-weight: 800;
            margin: 0;
            background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            color: #6B7280;
            font-size: 1.2rem;
            margin-top: 5px;
            font-weight: 400;
        }
        .stats-badge {
            display: inline-block;
            background: #10B981;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
            margin-left: 10px;
            vertical-align: middle;
        }
        .stButton>button {
            background-color: #4F46E5;
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #4338CA;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        }
    </style>
    """, unsafe_allow_html=True)

    # Проверяем наличие логотипа
    if LOGO_PATH.exists():
        # Кодируем логотип в base64
        logo_bytes = LOGO_PATH.read_bytes()
        logo_base64 = base64.b64encode(logo_bytes).decode()

        # Отображаем заголовок с логотипом
        st.markdown(f"""
        <div class="header-container">
            <img src="data:image/jpeg;base64,{logo_base64}" class="logo" alt="Логотип">
            <div>
                <h1 class="title-text">Классификатор электронных писем</h1>
                <p class="subtitle">
                    AI-система автоматической категоризации входящей почты 
                    <span class="stats-badge">v1.0</span>
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Если логотипа нет, показываем альтернативный заголовок
        st.markdown("""
        <div class="header-container">
            <div style="height: 60px; width: 60px; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); 
                     border-radius: 10px; margin-right: 20px; display: flex; align-items: center; justify-content: center;">
                <span style="color: white; font-size: 28px;">✉️</span>
            </div>
            <div>
                <h1 class="title-text">Классификатор электронных писем</h1>
                <p class="subtitle">
                    AI-система автоматической категоризации входящей почты 
                    <span class="stats-badge">v1.0</span>
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)


# --- Загрузка категорий ---
@st.cache_data
def load_categories_from_file():
    """Загружает категории из файла"""
    try:
        categories = {}
        with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if ':' in line:
                    category, keywords = line.strip().split(':', 1)
                    categories[category.strip()] = [
                        kw.strip() for kw in keywords.split(',') if kw.strip()
                    ]
        return categories
    except Exception as e:
        st.error(f"Ошибка загрузки категорий: {e}")
        return {}


# --- Загрузка существующих результатов ---
def load_latest_results():
    """Загружает последний CSV файл с результатами"""
    try:
        result_files = list(RESULTS_DIR.glob("mail_lens_results_*.csv"))
        if not result_files:
            # Ищем в корне data/ если нет в results/
            result_files = list(DATA_DIR.glob("mail_lens_results_*.csv"))
            if not result_files:
                return None, None

        latest_file = max(result_files, key=os.path.getctime)
        df = pd.read_csv(latest_file, encoding='utf-8-sig')
        return df, latest_file.name
    except Exception as e:
        st.warning(f"Не удалось загрузить результаты: {e}")
        return None, None


# --- Функция запуска классификации ---
def run_classification(uploaded_files=None):
    """Запускает процесс классификации"""
    try:
        if not CLASSIFIER_AVAILABLE:
            return False, "Классификатор не доступен"

        # Очищаем директорию input
        for file in INPUT_DIR.glob("*"):
            file.unlink()

        # Сохраняем загруженные файлы
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_path = INPUT_DIR / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

        # Загружаем категории
        categories = load_categories_from_file()
        if not categories:
            return False, "Не удалось загрузить категории"

        # Получаем список файлов для обработки
        email_files = list(INPUT_DIR.glob("*.eml"))
        if not email_files:
            return False, "Нет файлов для обработки"

        # Запускаем классификацию через импортированный модуль
        results = []
        for email_file in email_files:
            result = process_email_file(email_file, categories)
            if result:
                results.append(result)

        if not results:
            return False, "Не удалось обработать ни одного письма"

        # Сохраняем результаты
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = RESULTS_DIR / f"mail_lens_results_{timestamp}.csv"
        save_results_to_csv(results, output_file)

        return True, f"✅ Успешно обработано писем: {len(results)}\n📁 Результаты сохранены в: {output_file.name}"

    except Exception as e:
        return False, f"❌ Ошибка при классификации: {str(e)}"


# --- Отображение статистики ---
def display_statistics(df):
    """Отображает статистику по результатам"""
    if df is None or df.empty:
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_emails = len(df)
        st.metric("📧 Всего писем", total_emails)

    with col2:
        processed = df['processed'].sum() if 'processed' in df.columns else total_emails
        st.metric("✅ Обработано", processed)

    with col3:
        if 'confidence' in df.columns:
            avg_conf = df['confidence'].mean() * 100
            st.metric("🎯 Средняя уверенность", f"{avg_conf:.1f}%")

    with col4:
        if 'top_category' in df.columns:
            unique_cats = df['top_category'].nunique()
            st.metric("🏷️ Категорий использовано", unique_cats)


# --- Основной интерфейс ---

# Показываем заголовок с логотипом
show_header()

# Сайдбар для управления
with st.sidebar:
    st.header("⚙️ Управление")

    # Показываем текущие категории
    st.subheader("📂 Категории")
    categories = load_categories_from_file()
    if categories:
        st.success(f"Загружено категорий: {len(categories)}")
        with st.expander("👁️ Просмотр категорий"):
            for category, keywords in categories.items():
                st.markdown(f"**{category}**")
                st.caption(f"🔑 Ключевые слова: {', '.join(keywords[:3])}...")
    else:
        st.error("Категории не загружены")

    # Загрузка новых писем
    st.subheader("📤 Загрузка писем")
    uploaded_files = st.file_uploader(
        "Выберите .eml файлы",
        type=['eml'],
        accept_multiple_files=True,
        help="Загрузите один или несколько файлов в формате .eml"
    )

    if uploaded_files:
        st.info(f"📎 Загружено файлов: {len(uploaded_files)}")
        for file in uploaded_files:
            st.caption(f"• {file.name}")

    # Кнопка запуска классификации
    st.subheader("🚀 Классификация")
    classify_button = st.button(
        "Начать классификацию",
        type="primary",
        use_container_width=True,
        disabled=not uploaded_files or not CLASSIFIER_AVAILABLE
    )

    if classify_button:
        if not uploaded_files:
            st.warning("⚠️ Сначала загрузите письма")
        elif not CLASSIFIER_AVAILABLE:
            st.error("❌ Классификатор не доступен")
        else:
            with st.spinner("🔄 Идет обработка..."):
                success, message = run_classification(uploaded_files)
                if success:
                    st.success(message)
                    st.balloons()
                    st.rerun()
                else:
                    st.error(message)

    # Информация о системе
    st.markdown("---")
    st.subheader("ℹ️ О системе")
    st.write(f"**Версия Python:** {sys.version.split()[0]}")
    st.write(f"**Streamlit:** {st.__version__}")
    st.write(f"**Всего категорий:** {len(categories)}")

# Основная область - отображение результатов
st.header("📊 Результаты классификации")

# Загружаем и показываем последние результаты
df, filename = load_latest_results()

if df is not None and not df.empty:
    st.success(f"📁 Загружены результаты из: **{filename}**")

    # Отображаем статистику
    display_statistics(df)
    st.markdown("---")

    # Вкладки для разных представлений
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Все письма", "📈 Статистика", "🎯 Топ категории", "🔍 Детали"])

    with tab1:
        # Таблица всех писем
        display_df = df[[
            'filename', 'subject', 'top_category',
            'top_score', 'confidence', 'processed'
        ]].copy()

        # Форматируем confidence в проценты
        if 'confidence' in display_df.columns:
            display_df['confidence'] = display_df['confidence'].apply(
                lambda x: f"{float(x) * 100:.1f}%" if pd.notnull(x) else "N/A")

        # Сортируем по уверенности
        display_df = display_df.sort_values('top_score', ascending=False)

        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            column_config={
                "filename": "Файл",
                "subject": "Тема",
                "top_category": "Категория",
                "top_score": "Score",
                "confidence": "Уверенность",
                "processed": "Обработано"
            }
        )

    with tab2:
        # Статистика по категориям
        col1, col2 = st.columns(2)

        with col1:
            if 'top_category' in df.columns:
                category_stats = df['top_category'].value_counts()
                st.bar_chart(category_stats)

        with col2:
            # Круговая диаграмма
            if 'top_category' in df.columns:
                category_counts = df['top_category'].value_counts()
                chart_data = pd.DataFrame({
                    'category': category_counts.index,
                    'count': category_counts.values
                })
                st.dataframe(chart_data, use_container_width=True)

        # Распределение confidence
        st.subheader("📊 Распределение уверенности")
        if 'confidence' in df.columns:
            hist_values = np.histogram(df['confidence'].astype(float) * 100, bins=10, range=(0, 100))[0]
            st.bar_chart(hist_values)

    with tab3:
        # Детали по категориям
        selected_category = st.selectbox(
            "Выберите категорию для деталей",
            options=df['top_category'].unique() if 'top_category' in df.columns else []
        )

        if selected_category:
            category_emails = df[df['top_category'] == selected_category]
            if not category_emails.empty:
                st.write(f"📂 Писем в категории **'{selected_category}'**: {len(category_emails)}")

                for _, row in category_emails.iterrows():
                    with st.expander(f"{row['filename']} - {str(row['subject'])[:50]}..."):
                        st.write(f"**Тема:** {row['subject']}")
                        if 'confidence' in row:
                            st.write(f"**Уверенность:** {float(row['confidence']) * 100:.1f}%")
                        st.write(f"**Предпросмотр:** {str(row.get('body_preview', ''))[:200]}...")
            else:
                st.info("📭 Нет писем в выбранной категории")

    with tab4:
        # Подробная информация о конкретном письме
        if 'filename' in df.columns:
            selected_email = st.selectbox(
                "Выберите письмо для детального просмотра",
                options=df['filename'].tolist(),
                key="email_selector"
            )

            if selected_email:
                email_data = df[df['filename'] == selected_email].iloc[0]

                st.write(f"### 📄 {selected_email}")

                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Тема:** {email_data['subject']}")
                    st.write(f"**Основная категория:** {email_data['top_category']}")

                with col2:
                    if 'confidence' in email_data:
                        confidence_pct = float(email_data['confidence']) * 100
                        st.write(f"**Уверенность:** {confidence_pct:.1f}%")
                        st.progress(float(email_data['confidence']))

                # Показываем все предсказанные категории
                st.write("**🏷️ Все категории:**")
                categories_scores = []
                for i in range(1, 6):
                    cat_col = f'category_{i}'
                    score_col = f'score_{i}'
                    if cat_col in email_data and score_col in email_data:
                        categories_scores.append((
                            email_data[cat_col],
                            float(email_data[score_col])
                        ))

                for cat, score in categories_scores:
                    progress = min(score * 100, 100)
                    st.progress(score, text=f"{cat}: {score:.4f}")

                # Предпросмотр тела письма
                with st.expander("📝 Предпросмотр содержимого"):
                    st.text(email_data.get('body_preview', 'Нет данных'))

                # Ошибки если есть
                if 'error' in email_data and pd.notna(email_data['error']):
                    st.error(f"⚠️ Ошибка обработки: {email_data['error']}")

else:
    # Если результатов нет
    st.info("📭 Нет результатов классификации.")
    st.markdown("""
    ### 📌 Чтобы начать работу:
    1. **Загрузите .eml файлы** через панель слева
    2. **Нажмите кнопку "Начать классификацию"**
    3. **Результаты появятся здесь автоматически**

    ### 📁 Формат результатов:
    - Каждому письму будет присвоена основная категория
    - Показывается уверенность классификации
    - Результаты сохраняются в CSV файл
    """)

# Информация в подвале
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"🔄 Последнее обновление: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
with col2:
    st.caption(f"📁 Директория с данными: {DATA_DIR.resolve()}")
with col3:
    files_count = len(list(INPUT_DIR.glob('*.eml')))
    results_count = len(list(RESULTS_DIR.glob('*.csv')))
    st.caption(f"📊 Файлов: {files_count} | Результатов: {results_count}")