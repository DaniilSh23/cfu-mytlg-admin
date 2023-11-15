"""
Фильтры новых постов.
"""
from langchain import FAISS
from langchain.embeddings import OpenAIEmbeddings
import openai
from cfu_mytlg_admin.settings import MY_LOGGER


class PostFilters:
    """
    Класс с фильтрами для постов
    """

    # TODO: эту поебень перенести в бизнес-логику, я дял примера пока тут оставлю
    # post_filters_obj = PostFilters(
    #     new_post=update.text,
    #     old_posts=[(i_post.get("text"), i_post.get("embedding").split()) for i_post in posts_lst],
    # )
    # filtration_rslt = await post_filters_obj.complete_filtering()

    def __init__(self, new_post, old_posts):
        self.new_post = new_post
        self.new_post_embedding = None
        self.old_posts = old_posts
        self.filtration_result = []
        self.rel_old_post = None

    def __str__(self):
        return (f"new_post = {self.new_post}\nfiltration_result = {self.filtration_result}\n"
                f"rel_old_post = {self.rel_old_post}")

    def complete_filtering(self):
        """
        Полная фильтрация новостного поста, с применением всех фильтров
        """
        self.duplicate_filter()
        return self.filtration_result

    def duplicate_filter(self):
        """
        Фильтр дублирующихся новостных постов
        """
        find_rslt = self.find_similar_post()
        if not find_rslt:
            check_gpt_rslt = self.check_duplicate_by_gpt()
            MY_LOGGER.debug(f'Ответ GPT на поиск дублей: {check_gpt_rslt!r} | '
                            f'да - посты одинаковые по смыслу, нет - разные')
            if check_gpt_rslt.lower() == 'да':
                self.filtration_result.append(False)
            elif check_gpt_rslt.lower() == 'нет':
                self.filtration_result.append(True)
            else:
                MY_LOGGER.warning(f'Несмотря на все инструкции ChatGPT вернул дичь в ответ на проверку дублей постов.'
                                  f'Ответ ChatGPT {check_gpt_rslt!r}. Считаем, что новость не прошла проверку на дубли')
                self.filtration_result.append(False)

    def find_similar_post(self) -> bool | None:
        """
        Поиск похожего поста. Это необходимо для фильтрации дублирующих новостей.
        Вернёт True, если релевантный кусок не найден и None, если релевантный кусок найден.
        """
        MY_LOGGER.debug(f'Получаем объект эмбеддингов от OpenAI')
        embeddings = OpenAIEmbeddings(max_retries=2)  # добавил кол-во попыток запросов к OpenAI

        # Пилим эмбеддинги для нового поста
        MY_LOGGER.debug(f'Пилим эмбеддинги для нового поста')
        MY_LOGGER.debug(f'НОВЫЙ ПОСТ -- {self.new_post}')
        self.new_post_embedding = embeddings.embed_query(self.new_post)

        # Делаем индексную базу из старых кусков текста
        MY_LOGGER.debug(f'Делаем индексную базу из старых кусков текста')
        index_db = FAISS.from_embeddings(text_embeddings=self.old_posts, embedding=embeddings)

        # Поиск релевантных кусков текста, имея на входе уже готовые векторы
        MY_LOGGER.debug(f'Поиск релевантных кусков текста из уже имеющихся векторов')
        relevant_piece = index_db.similarity_search_with_score_by_vector(embedding=self.new_post_embedding, k=1)[0]

        if relevant_piece[1] > 0.3:
            MY_LOGGER.warning(f'Не найдено похожих новостных постов.')
            self.filtration_result.append(True)
            return True
        self.rel_old_post = relevant_piece[0].page_content
        MY_LOGGER.debug(f'Найден релевантный кусок: {self.rel_old_post}')

    def check_duplicate_by_gpt(self, temp=0):
        """
        Функция для того, чтобы проверить через GPT дублируют ли по смыслу друг друга два поста.
        temp - (значение от 0 до 1) чем выше, тем более творчески будет ответ модели, то есть она будет додумывать что-то.
        """
        system = "Ты занимаешься фильтрацией контента и твоя задача наиболее точно определить дублируют ли друг " \
                 "друга по смыслу два новостных поста: старый и новый." \
                 "Проанализируй смысл двух переданных тебе текстов новостных постов и реши говорится ли в этих " \
                 "постах об одном и том же или в них заложен разный смысл. Если тексты новостных постов" \
                 " имеют одинаковый смысл, то в ответ пришли слово 'да' и ничего больше. Если же" \
                 " в текстах новостных постов заложен разный смысл, то в ответ пришли слово 'нет' и ничего больше."
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Текст старого новостного поста: {self.rel_old_post}\n\n"
                                        f"Текст нового новостного поста: \n{self.new_post}"}
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
        return answer

    @staticmethod
    def make_embedding(text):
        """
        Метод для создания эмбеддингов для текста
        """
        MY_LOGGER.debug(f'Вызван метод для создания эмбеддингов к тексту')
        embeddings = OpenAIEmbeddings(max_retries=2)
        text_embedding = embeddings.embed_query(text)
        return text_embedding
