import openai
from langchain import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter

from cfu_mytlg_admin.settings import MY_LOGGER


def relevant_text_preparation(base_text: str, query: str) -> str | None:
    """
    Подготовка текста, перед запросом к модели OpenAI
    base_text - базовый текст, база знаний или иное, на чем модель должно базировать свой ответ
    query - запрос пользователя, под который в base_text нужно найти более релевантные куски текста
    """
    MY_LOGGER.info(f'Запуск функции подготовки текста для запроса к модели OpenAI')

    # Разбиваем текст на чанки
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=0)
    text_chunks = text_splitter.split_text(base_text)

    # Создадим индексную базу векторов по данному тексту (переведом текст в цифры, чтобы его понял комп)
    embeddings = OpenAIEmbeddings()
    index_db = FAISS.from_texts(text_chunks, embeddings)

    # Отбираем более релевантные куски базового текста (base_text), согласно запросу (query)
    relevant_pieces = index_db.similarity_search_with_score(query, k=4)     # Достаём куски с Евклидовым расстоянием
    filtered_rel_pieces = [i_rel_p for i_rel_p in relevant_pieces if i_rel_p[1] < 0.3]  # Фильтруем все, что ниже 0.3
    if len(filtered_rel_pieces) < 1:    # Выходим, если куски очень далеки от схожести
        MY_LOGGER.warning(f'Не найдено релевантных кусков для запроса: {query!r}')
        return

    # Отдаём склеенную через \n строку с релевантными кусками
    return '\n'.join([i_rel_p[0].page_content for i_rel_p in filtered_rel_pieces])


# TODO: эта функция и функция ниже требуют рефакторинга. У них есть лишь незначительные отличия и надо их объединить
def ask_the_gpt(system, query, base_text, temp=0):
    """
    Функция для того, чтобы отправить запрос к модели GPT и получить ответ.
    system - инструкция для модели GPT
    query - запрос пользователя
    base_text - текст, на котором модель должна базировать свой ответ
    temp - (значение от 0 до 1) чем выше, тем более творчески будет ответ модели, то есть она будет додумывать что-то.
    """
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Данные с информацией для ответа пользователю: {base_text}\n\n"
                                    f"Запрос пользователя: \n{query}"}
    ]
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=temp
        )
    except openai.error.ServiceUnavailableError as err:
        MY_LOGGER.error(f'Серверы OpenAI перегружены или недоступны. {err}')
        return False
    answer = completion.choices[0].message.content
    return answer  # возвращает ответ


def gpt_text_reduction(prompt, text, temp=0.3):
    """
    Функция для сокращения текста, через модель GPT.
    prompt - промпт для модели
    text - текст, который надо сократить
    """
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Текст, который надо сократить:\n\n{text}"}
    ]
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=temp
        )
    except openai.error.ServiceUnavailableError as err:
        MY_LOGGER.error(f'Серверы OpenAI перегружены или недоступны. {err}')
        return False
    answer = completion.choices[0].message.content
    return answer  # возвращает ответ
