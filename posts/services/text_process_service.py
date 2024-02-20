from langchain import FAISS
from langchain.embeddings import OpenAIEmbeddings
import requests
from langchain.text_splitter import CharacterTextSplitter

from mytlg.exceptions.custom_exceptions import OpenaiException
from mytlg.servises.bot_settings_service import BotSettingsService

from cfu_mytlg_admin.settings import MY_LOGGER, OPEN_AI_SERVICE_HOST, OPEN_AI_APP_TOKEN


class TextProcessService:
    similarity_index_for_interests = float(
        BotSettingsService.get_bot_settings_by_key(key='similarity_index_for_interests'))
    headers_for_gpt = {
        'Authorization': f"Bearer {OPEN_AI_APP_TOKEN}"
    }
    token_data = {"token": OPEN_AI_APP_TOKEN}
    embeddings = OpenAIEmbeddings()

    @staticmethod
    def get_gpt_answer(prompt: str, query: str, base_text='', temp=0.1):
        data = {
            "prompt": prompt,
            "query": query,
            "base_text": base_text,
            "temp": temp
        }
        response = requests.post(url=f'{OPEN_AI_SERVICE_HOST}get-gpt-answer/',
                                 json=data | TextProcessService.token_data,     # Добавлен токен в тело запроса
                                 headers=TextProcessService.headers_for_gpt)
        if response.status_code == 200 and response.json().get('success'):
            return response.json().get('answer')
        else:
            MY_LOGGER.warning(f'Ошибка при запросе к приложению для опен аи {response.status_code}, {response}')
            raise OpenaiException(message=f'Неудачный запрос к языковой модели GPT! '
                                          f'STATUS_CODE == {response.status_code} | DESCRIPTION == {response.text}')

    @staticmethod
    def make_embeddings(text: str):
        data = {
            "text": text
        }
        response = requests.post(url=f'{OPEN_AI_SERVICE_HOST}make-embeddings/',
                                 json=data | TextProcessService.token_data,     # Добавлен токен в тело запроса
                                 headers=TextProcessService.headers_for_gpt)
        if response.status_code == 200 and response.json().get('success'):
            return response.json().get('embeddings')
        else:
            MY_LOGGER.warning(
                f'Ошибка при запросе к приложению для опен аи для формирования эмбеддингов: {response.status_code} | '
                f'{response.text}')
            raise OpenaiException(message=f'Неудачный запрос при формировании эмбеддингов! '
                                          f'STATUS_CODE == {response.status_code} | DESCRIPTION == {response.text}')

    def make_index_db_from_embeddings(self, interest_lst):
        index_db = FAISS.from_embeddings(text_embeddings=interest_lst, embedding=self.embeddings)
        return index_db

    def filter_relevant_pieces_by_vector_distance(self, relevant_pieces):
        filtered_rel_pieces = list(
            filter(lambda piece: piece[1] < self.similarity_index_for_interests, relevant_pieces))
        return filtered_rel_pieces

    @staticmethod
    def get_relevant_pieces_by_embeddings(index_db, post):
        relevant_pieces = index_db.similarity_search_with_score_by_vector(
            embedding=[float(i_emb) for i_emb in post.embedding.split()],
            k=1,
        )
        return relevant_pieces

    @staticmethod
    def relevant_text_preparation(base_text: str, query: str) -> str | None:
        """
        Подготовка текста, перед запросом к модели OpenAI
        base_text - базовый текст, база знаний или иное, на чем модель должно базировать свой ответ
        query - запрос пользователя, под который в base_text нужно найти более релевантные куски текста
        """
        MY_LOGGER.info('Запуск функции подготовки текста для запроса к модели OpenAI')

        # Разбиваем текст на чанки
        text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=0)
        text_chunks = text_splitter.split_text(base_text)

        # Создадим индексную базу векторов по данному тексту (переведом текст в цифры, чтобы его понял комп)
        embeddings = TextProcessService.embeddings
        index_db = FAISS.from_texts(text_chunks, embeddings)

        # Отбираем более релевантные куски базового текста (base_text), согласно запросу (query)
        relevant_pieces = index_db.similarity_search_with_score(query, k=4)  # Достаём куски с Евклидовым расстоянием
        filtered_rel_pieces = [i_rel_p for i_rel_p in relevant_pieces if
                               i_rel_p[1] < 0.3]  # Фильтруем все, что ниже 0.3
        if len(filtered_rel_pieces) < 1:  # Выходим, если куски очень далеки от схожести
            MY_LOGGER.warning(f'Не найдено релевантных кусков для запроса: {query!r}')
            return

        # Отдаём склеенную через \n строку с релевантными кусками
        return '\n'.join([i_rel_p[0].page_content for i_rel_p in filtered_rel_pieces])

    # TODO: эта функция и функция ниже требуют рефакторинга. У них есть лишь незначительные отличия и надо их объединить
    @staticmethod
    def ask_the_gpt(system, query, base_text, temp=0):
        """
        Функция для того, чтобы отправить запрос к модели GPT и получить ответ.
        system - инструкция для модели GPT
        query - запрос пользователя
        base_text - текст, на котором модель должна базировать свой ответ
        temp - (значение от 0 до 1) чем выше, тем более творчески будет ответ модели, то есть она будет додумывать что-то.
        """
        answer = TextProcessService.get_gpt_answer(prompt=system,
                                                   query=f"Запрос пользователя: \n{query}",
                                                   base_text=base_text,
                                                   temp=temp)
        return answer  # возвращает ответ

    @staticmethod
    def gpt_text_reduction(prompt, text, temp=0.3):
        """
        Функция для сокращения текста, через модель GPT.
        prompt - промпт для модели
        text - текст, который надо сократить
        """
        answer = TextProcessService.get_gpt_answer(prompt,
                                                   query=f"Текст, который надо сократить:\n\n{text}",
                                                   base_text='',
                                                   temp=temp)
        return answer  # возвращает ответ

    @staticmethod
    def gpt_text_language_detection_and_translate(prompt, text, user_language_code, temp):
        """
        Функция для определения языка текста и при необходимости перевода текста на язык пользователя, через модель GPT.
        prompt - промпт для модели
        text - текст, который надо исследовать и перевести
        """
        answer = TextProcessService.get_gpt_answer(prompt,
                                                   query=f'user_language_code={user_language_code}.\n\n{text}',
                                                   base_text='',
                                                   temp=temp)
        return answer  # возвращает ответ

    @staticmethod
    def check_post_text_sentence_quantity_and_reduce_if_need(post_text: str, prompt: str,
                                                             sentence_quantity_limit: int) -> str:
        """
        Функция для проверки количества предложений в тексте поста.
        """
        post_sentence_quantity = len(post_text.split('.'))
        if post_sentence_quantity <= sentence_quantity_limit:
            return post_text
        else:
            return TextProcessService.gpt_text_reduction(prompt, text=post_text)
