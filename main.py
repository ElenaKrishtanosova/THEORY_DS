import streamlit as st
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

def show_registration_form():
    """Показывает форму регистрации и возвращает имя пользователя"""
    # Логотип и заголовок регистрации
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("images/image_innowise2.png", width=200)
    with col2:
        st.markdown("## 👤 Регистрация")
        st.markdown("Введите ваше имя для начала тестирования:")
    
    with st.form("registration_form"):
        user_name = st.text_input("Ваше имя:", key="user_name_input")
        submitted = st.form_submit_button("Начать тестирование")
        
        if submitted and user_name.strip():
            st.session_state['user_name'] = user_name.strip()
            st.success(f"Добро пожаловать, {user_name.strip()}!")
            st.rerun()
        elif submitted and not user_name.strip():
            st.error("Пожалуйста, введите ваше имя.")
    
    return None

def get_user_results_content(user_name: str) -> str:
    """Возвращает содержимое результатов пользователя из session_state"""
    if 'user_results' not in st.session_state:
        st.session_state['user_results'] = ""
    return st.session_state['user_results']

def save_wrong_answers(user_name: str, section_name: str, subsection_name: str, 
                      questions: List[Dict], user_answers: List[Dict], 
                      pdf_links: List[str] = None):
    """Сохраняет неправильные ответы в session_state"""
    # Инициализируем результаты в session_state если их нет
    if 'user_results' not in st.session_state:
        st.session_state['user_results'] = ""
    
    # Собираем неправильные ответы и считаем статистику
    wrong_answers = []
    total_questions = len(questions)
    correct_answers = 0
    
    for i, (question, user_answer) in enumerate(zip(questions, user_answers)):
        if user_answer is None:
            continue
            
        is_wrong = False
        if question['question_type'] == 'single_choice':
            if user_answer.get('answer') != question['correct_answer']:
                is_wrong = True
        elif question['question_type'] in ['multiple_choice', 'multi_choice']:
            if set(user_answer.get('answer', [])) != set(question.get('correct_answers', [])):
                is_wrong = True
        
        if is_wrong:
            # Получаем текст ответа пользователя
            user_answer_text = ""
            if question['question_type'] == 'single_choice':
                user_choice = user_answer.get('answer')
                if user_choice is not None:
                    user_answer_text = question['options'][user_choice]
                else:
                    user_answer_text = "Не выбрано"
            elif question['question_type'] in ['multiple_choice', 'multi_choice']:
                user_choices = user_answer.get('answer', [])
                if user_choices:
                    user_answer_text = ', '.join([question['options'][i] for i in user_choices])
                else:
                    user_answer_text = "Не выбрано"
            
            wrong_answers.append({
                'question_number': i + 1,
                'question_text': question['question_text'],
                'user_answer_text': user_answer_text
            })
        else:
            correct_answers += 1
    
    # Вычисляем процент правильных ответов
    correct_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # Формируем текст для записи
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    result_text = f"""
{'='*60}
Результаты тестирования - {user_name}
Дата: {timestamp}
Раздел: {section_name}
Подраздел: {subsection_name}

📊 Статистика:
Правильных ответов: {correct_answers}/{total_questions} ({correct_percentage:.1f}%)

"""
    
    if wrong_answers:
        result_text += "Неправильные ответы:\n"
    else:
        result_text += "✅ Все ответы правильные!\n"
    
    for wrong in wrong_answers:
        result_text += f"""
Вопрос {wrong['question_number']}: {wrong['question_text']}
Ваш неправильный ответ: {wrong['user_answer_text']}
"""
    
    if pdf_links:
        result_text += f"""
Ссылки на материалы для изучения:
"""
        for i, link in enumerate(pdf_links, 1):
            result_text += f"{i}. {link}\n"
    
    result_text += f"\n{'='*60}\n"
    
    # Добавляем к существующим результатам в session_state
    st.session_state['user_results'] += result_text
    st.success(f"📝 Результаты сохранены в память приложения")

def load_quiz_data(file_path: str) -> Optional[Dict[str, Any]]:
    """Загружает данные теста из JSON файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def load_quiz_data_with_subsections(section_prefix: str, tab_number: int) -> tuple[Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]]]:
    """Загружает данные теста, проверяя наличие подразделов"""
    import glob
    import os
    
    # Сначала пытаемся загрузить основной файл
    main_file = f"quiz_data/{section_prefix}_{tab_number}.json"
    main_data = load_quiz_data(main_file)
    
    if main_data is not None:
        return main_data, None
    
    # Если основной файл не найден, ищем подразделы
    pattern = f"quiz_data/{section_prefix}_{tab_number}.*.json"
    subsection_files = sorted(glob.glob(pattern))
    
    if subsection_files:
        subsection_data = []
        for file_path in subsection_files:
            data = load_quiz_data(file_path)
            if data is not None:
                subsection_data.append(data)
        
        if subsection_data:
            return None, subsection_data
    
    return None, None

def render_question(question: Dict[str, Any], question_key: str) -> Dict[str, Any]:
    """Отображает вопрос и возвращает ответ пользователя"""
    st.write(f"**Вопрос {question['question_id']}:** {question['question_text']}")
    
    if question['question_type'] == 'single_choice':
        options = question['options']
        answer = st.radio(
            "Выберите правильный ответ:",
            options,
            key=f"{question_key}_radio",
            label_visibility="collapsed"
        )
        return {"type": "single_choice", "answer": options.index(answer) if answer else None}
    
    elif question['question_type'] in ['multiple_choice', 'multi_choice']:
        options = question['options']
        selected = st.multiselect(
            "Выберите правильные ответы:",
            options,
            key=f"{question_key}_multiselect"
        )
        return {"type": "multiple_choice", "answer": [options.index(opt) for opt in selected]}
    
    elif question['question_type'] == 'free_text':
        answer = st.text_area(
            "Введите ваш ответ:",
            key=f"{question_key}_text"
        )
        return {"type": "free_text", "answer": answer}
    
    return {"type": "unknown", "answer": None}

def calculate_score(user_answers: List[Dict], questions: List[Dict]) -> tuple:
    """Вычисляет количество правильных ответов"""
    correct = 0
    total = len(questions)
    
    for i, (user_answer, question) in enumerate(zip(user_answers, questions)):
        if user_answer is None:
            continue
            
        if question['question_type'] == 'single_choice':
            if user_answer.get('answer') == question['correct_answer']:
                correct += 1
        elif question['question_type'] in ['multiple_choice', 'multi_choice']:
            # Для множественного выбора нужно проверить все правильные ответы
            if 'correct_answers' in question:
                if set(user_answer.get('answer', [])) == set(question['correct_answers']):
                    correct += 1
    
    return correct, total

def main():
    st.set_page_config(
        page_title="Тестирование знаний по ML",
        page_icon="images/favicon.ico",
        layout="wide"
    )
    
    # Проверка регистрации
    if 'user_name' not in st.session_state:
        show_registration_form()
        return
    
    # Sidebar для выбора раздела
    with st.sidebar:
        # Логотип в sidebar
        st.image("images/image_innowise.png", width=200)
        st.markdown("---")
        st.header("🌿 Выбор раздела")
        
        # Словарь разделов
        sections = {
            "Theory DS - 0": "Fundamentals and prerequisites",
            "Theory DS - 1.1": "Classic supervised algorithms", 
            "Theory DS - 1.2": "Classic unsupervised algorithms",
            "Theory DS - 2.1": "Behind the scene"
        }
        
        selected_section = st.selectbox(
            "Выберите раздел:",
            list(sections.keys()),
            index=1,  # По умолчанию выбран Theory DS - 1.1
            format_func=lambda x: f"{x}: {sections[x]}"
        )
        
        st.markdown("---")
        st.markdown(f"**Пользователь:** {st.session_state['user_name']}")
        st.markdown(f"**Текущий раздел:** {selected_section}")
        st.markdown(f"**Описание:** {sections[selected_section]}")
        
        # Кнопка для просмотра результатов
        if st.button("📊 Просмотреть мои результаты"):
            results_content = get_user_results_content(st.session_state['user_name'])
            if results_content:
                st.text_area("Ваши результаты:", results_content, height=400)
            else:
                st.info("У вас пока нет результатов тестирования.")
        
        # Кнопка для скачивания результатов
        results_content = get_user_results_content(st.session_state['user_name'])
        if results_content:
            st.download_button(
                label="📥 Скачать файл с результатами",
                data=results_content,
                file_name=f"{st.session_state['user_name']}_results.txt",
                mime="text/plain"
            )
    
    # Логотип по центру
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("images/image_innowise1.png", width=300)
    
    # Заголовок раздела
    st.markdown(f"## Section quiz - {selected_section}: {sections[selected_section]}")
    
    st.markdown("---")
    
    # Динамические названия вкладок для каждого раздела
    tab_configs = {
        "Theory DS - 0": [
            "1. Fundamentals",
            "2. Prerequisites",
            "3. Basic concepts",
            "4. Mathematical foundations",
            "5. Statistics basics",
            "6. Probability theory",
            "7. Linear algebra",
            "8. Calculus",
            "9. Optimization",
            "10. Data preprocessing",
            "11. Feature engineering",
            "12. Model evaluation",
            "13. Overfitting basics"
        ],
        "Theory DS - 1.1": [
            "1. Basic understanding",
            "2. Linear models", 
            "3. Decision Trees",
            "4. KNN",
            "5. LDA/QDA",
            "6. Dimensionality reduction",
            "7. Regularisation",
            "8. ML metrics",
            "9. Validation"
        ],
        "Theory DS - 1.2": [
            "1. Unsupervised problems",
            "2. Clusterisation",
            "3. K-Means",
            "4. Hierarchical Clusterisation",
            "5. DBSCAN",
            "6. HDBSCAN",
            "7. GMM",
            "8. Dimensionality reduction",
            "9. PCA",
            "10. t-SNE",
            "11. UMAP",
            "12. Concept of auto-encoders",
            "13. Anomaly detection"
        ],
        "Theory DS - 2.1": [
            "1. Behind the scenes",
            "2. Model internals",
            "3. Algorithm details",
            "4. Implementation specifics",
            "5. Performance optimization",
            "6. Memory management",
            "7. Computational complexity",
            "8. Scalability issues",
            "9. Advanced techniques",
            "10. Research frontiers",
            "11. Industry practices",
            "12. Best practices",
            "13. Common pitfalls"
        ]
    }
    
    # Получаем названия вкладок для выбранного раздела
    tab_names = tab_configs.get(selected_section, [
        "1. Section 1",
        "2. Section 2",
        "3. Section 3",
        "4. Section 4",
        "5. Section 5",
        "6. Section 6",
        "7. Section 7",
        "8. Section 8",
        "9. Section 9",
        "10. Section 10",
        "11. Section 11",
        "12. Section 12",
        "13. Section 13"
    ])
    
    # Создаем вкладки
    tabs = st.tabs(tab_names)
    
    # Обрабатываем каждую вкладку
    for i, tab in enumerate(tabs):
        with tab:
            # Формируем путь к файлу в зависимости от выбранного раздела
            section_mapping = {
                "Theory DS - 0": "theory_ds_0",
                "Theory DS - 1.1": "theory_ds_1.1",
                "Theory DS - 1.2": "theory_ds_1.2",
                "Theory DS - 2.1": "theory_ds_2.1"
            }
            section_prefix = section_mapping.get(selected_section, "theory_ds_1.1")
            
            # Универсальная загрузка данных с поддержкой подразделов
            quiz_data, quiz_data_list = load_quiz_data_with_subsections(section_prefix, i+1)
            
            # Если нет ни основного файла, ни подразделов
            if quiz_data is None and quiz_data_list is None:
                st.info(f"📝 Данные для раздела {i+1} пока не загружены.")
                continue
            
            # Если есть подразделы, обрабатываем их
            if quiz_data_list is not None:
                for sub_idx, quiz_data in enumerate(quiz_data_list):
                    if quiz_data is None:
                        continue
                        
                    # Используем quiz_title как название подраздела
                    subsection_name = quiz_data.get('quiz_title', f'Подраздел {sub_idx+1}')
                    st.markdown(f"### {subsection_name}")
                    
                    # Инициализируем состояние для ответов
                    answer_key = f'answers_{i}_{sub_idx}'
                    if answer_key not in st.session_state:
                        st.session_state[answer_key] = [None] * len(quiz_data['questions'])
                    
                    # Отображаем вопросы
                    for j, question in enumerate(quiz_data['questions']):
                        question_key = f"tab_{i}_{sub_idx}_question_{j}"
                        user_answer = render_question(question, question_key)
                        st.session_state[answer_key][j] = user_answer
                        st.markdown("---")
                    
                    # Кнопка Apply для каждого подраздела
                    if st.button(f"Проверить ответы - {subsection_name}", key=f"apply_{i}_{sub_idx}"):
                        if f'show_results_{i}_{sub_idx}' not in st.session_state:
                            st.session_state[f'show_results_{i}_{sub_idx}'] = True
                    
                    # Показываем результаты после нажатия кнопки
                    if st.session_state.get(f'show_results_{i}_{sub_idx}', False):
                        st.markdown(f"#### 📊 Результаты - {subsection_name}:")
                        
                        correct, total = calculate_score(st.session_state[answer_key], quiz_data['questions'])
                        score_percent = (correct / total * 100) if total > 0 else 0
                        
                        st.metric("Правильных ответов", f"{correct}/{total} ({score_percent:.1f}%)")
                        
                        st.markdown("#### 📝 Детальные результаты:")
                        
                        for j, (question, user_answer) in enumerate(zip(quiz_data['questions'], st.session_state[answer_key])):
                            st.markdown(f"**Вопрос {j+1}:**")
                            
                            if question['question_type'] == 'single_choice':
                                user_choice = user_answer.get('answer')
                                correct_choice = question['correct_answer']
                                
                                if user_choice == correct_choice:
                                    st.success(f"✅ Правильно! Ваш ответ: {question['options'][user_choice]}")
                                else:
                                    user_answer_text = question['options'][user_choice] if user_choice is not None else 'Не выбрано'
                                    correct_answer_text = question['options'][correct_choice]
                                    st.error(f"❌ Неправильно. Ваш ответ: {user_answer_text}")
                                    st.success(f"✅ Правильный ответ: {correct_answer_text}")
                                
                                st.info(f"💡 **Объяснение:** {question['explanation']}")
                            
                            elif question['question_type'] in ['multiple_choice', 'multi_choice']:
                                user_choices = user_answer.get('answer', [])
                                correct_choices = question.get('correct_answers', [])
                                
                                if set(user_choices) == set(correct_choices):
                                    st.success(f"✅ Правильно! Ваши ответы: {', '.join([question['options'][i] for i in user_choices])}")
                                else:
                                    user_answers_text = ', '.join([question['options'][i] for i in user_choices]) if user_choices else 'Не выбрано'
                                    correct_answers_text = ', '.join([question['options'][i] for i in correct_choices])
                                    st.error(f"❌ Неправильно. Ваши ответы: {user_answers_text}")
                                    st.success(f"✅ Правильные ответы: {correct_answers_text}")
                                
                                st.info(f"💡 **Объяснение:** {question['explanation']}")
                            
                            st.markdown("---")
                        
                        # Сохраняем неправильные ответы
                        if score_percent < 100:  # Только если есть ошибки
                            pdf_links = quiz_data.get('pdf_links', [])
                            save_wrong_answers(
                                st.session_state['user_name'],
                                selected_section,
                                subsection_name,
                                quiz_data['questions'],
                                st.session_state[answer_key],
                                pdf_links
                            )
                        
                        # Показываем ссылки на PDF материалы
                        if 'pdf_links' in quiz_data and quiz_data['pdf_links']:
                            st.markdown("### 📚 Материалы для изучения:")
                            
                            # Показываем ссылки только если есть ошибки или по запросу
                            if score_percent < 100:  # Если есть ошибки
                                st.info("💡 У вас есть ошибки. Рекомендуем изучить дополнительные материалы:")
                                
                                for j, link in enumerate(quiz_data['pdf_links']):
                                    st.link_button(
                                        f"📄 Материал {j+1}",
                                        link
                                    )
                            else:
                                # Если все правильно, показываем ссылки по запросу
                                if st.button("📚 Показать материалы для изучения", key=f"show_materials_{i}_{sub_idx}"):
                                    st.info("📖 Дополнительные материалы по теме:")
                                    
                                    for j, link in enumerate(quiz_data['pdf_links']):
                                        st.link_button(
                                            f"📄 Материал {j+1}",
                                            link
                                        )
                        
                        # Кнопка для скрытия результатов
                        if st.button("Скрыть результаты", key=f"hide_{i}_{sub_idx}"):
                            st.session_state[f'show_results_{i}_{sub_idx}'] = False
                            st.rerun()
                    
                    st.markdown("---")
            
            # Если есть основной файл, обрабатываем его как обычно
            elif quiz_data is not None:
                
                # Отображаем заголовок теста
                st.header(quiz_data['quiz_title'])
                
                # Инициализируем состояние для ответов
                if f'answers_{i}' not in st.session_state:
                    st.session_state[f'answers_{i}'] = [None] * len(quiz_data['questions'])
                
                # Отображаем вопросы
                for j, question in enumerate(quiz_data['questions']):
                    question_key = f"tab_{i}_question_{j}"
                    user_answer = render_question(question, question_key)
                    st.session_state[f'answers_{i}'][j] = user_answer
                    st.markdown("---")
                
                # Кнопка Apply
                if st.button(f"Проверить ответы", key=f"apply_{i}"):
                    if f'show_results_{i}' not in st.session_state:
                        st.session_state[f'show_results_{i}'] = True
                
                # Показываем результаты после нажатия кнопки
                if st.session_state.get(f'show_results_{i}', False):
                    st.markdown("### 📊 Результаты:")
                    
                    correct, total = calculate_score(st.session_state[f'answers_{i}'], quiz_data['questions'])
                    score_percent = (correct / total * 100) if total > 0 else 0
                    
                    st.metric("Правильных ответов", f"{correct}/{total} ({score_percent:.1f}%)")
                    
                    st.markdown("### 📝 Детальные результаты:")
                    
                    for j, (question, user_answer) in enumerate(zip(quiz_data['questions'], st.session_state[f'answers_{i}'])):
                        st.markdown(f"**Вопрос {j+1}:**")
                        
                        if question['question_type'] == 'single_choice':
                            user_choice = user_answer.get('answer')
                            correct_choice = question['correct_answer']
                            
                            if user_choice == correct_choice:
                                st.success(f"✅ Правильно! Ваш ответ: {question['options'][user_choice]}")
                            else:
                                user_answer_text = question['options'][user_choice] if user_choice is not None else 'Не выбрано'
                                correct_answer_text = question['options'][correct_choice]
                                st.error(f"❌ Неправильно. Ваш ответ: {user_answer_text}")
                                st.success(f"✅ Правильный ответ: {correct_answer_text}")
                            
                            st.info(f"💡 **Объяснение:** {question['explanation']}")
                        
                        elif question['question_type'] in ['multiple_choice', 'multi_choice']:
                            user_choices = user_answer.get('answer', [])
                            correct_choices = question.get('correct_answers', [])
                            
                            if set(user_choices) == set(correct_choices):
                                st.success(f"✅ Правильно! Ваши ответы: {', '.join([question['options'][i] for i in user_choices])}")
                            else:
                                user_answers_text = ', '.join([question['options'][i] for i in user_choices]) if user_choices else 'Не выбрано'
                                correct_answers_text = ', '.join([question['options'][i] for i in correct_choices])
                                st.error(f"❌ Неправильно. Ваши ответы: {user_answers_text}")
                                st.success(f"✅ Правильные ответы: {correct_answers_text}")
                            
                            st.info(f"💡 **Объяснение:** {question['explanation']}")
                        
                        st.markdown("---")
                    
                    # Сохраняем неправильные ответы
                    if score_percent < 100:  # Только если есть ошибки
                        pdf_links = quiz_data.get('pdf_links', [])
                        save_wrong_answers(
                            st.session_state['user_name'],
                            selected_section,
                            quiz_data['quiz_title'],
                            quiz_data['questions'],
                            st.session_state[f'answers_{i}'],
                            pdf_links
                        )
                    
                    # Показываем ссылки на PDF материалы
                    if 'pdf_links' in quiz_data and quiz_data['pdf_links']:
                        st.markdown("### 📚 Материалы для изучения:")
                        
                        # Показываем ссылки только если есть ошибки или по запросу
                        if score_percent < 100:  # Если есть ошибки
                            st.info("💡 У вас есть ошибки. Рекомендуем изучить дополнительные материалы:")
                            
                            for j, link in enumerate(quiz_data['pdf_links']):
                                st.link_button(
                                    f"📄 Материал {j+1}",
                                    link
                                )
                        else:
                            # Если все правильно, показываем ссылки по запросу
                            if st.button("📚 Показать материалы для изучения", key=f"show_materials_{i}"):
                                st.info("📖 Дополнительные материалы по теме:")
                                
                                for j, link in enumerate(quiz_data['pdf_links']):
                                    st.link_button(
                                        f"📄 Материал {j+1}",
                                        link
                                    )
                    
                    # Кнопка для скрытия результатов
                    if st.button("Скрыть результаты", key=f"hide_{i}"):
                        st.session_state[f'show_results_{i}'] = False
                        st.rerun()
    
    # Футер с логотипом
    st.markdown("---")
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("images/image_innowise.png", width=100)
        st.markdown("*Разработано командой Innowise*")


if __name__ == "__main__":
    main()
