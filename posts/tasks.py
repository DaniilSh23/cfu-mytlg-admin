"""
Таски Celery для приложения posts.
"""
from celery import shared_task
from openai.error import RateLimitError

from cfu_mytlg_admin.settings import MY_LOGGER
from posts.services.post_filter_service import PostFilters
from posts.services.post_service import PostService


@shared_task
def raw_post_processing(ch_pk: int, new_post_text: str, post_link: str):
    """
    Таск селери для обработки сырого поста, который прилетел из какого-либо канала.
    """
    MY_LOGGER.info(f'Запущен таск селери для обработки сырых постов (raw_post_processing).')

    # Обработка поста из кастомных каналов пользователей
    PostService.suitable_post_processing_from_users_list(
        post_text=new_post_text,
        ch_pk=ch_pk,
        post_link=post_link,
    )

    # Достать посты из БД с общей категорией для нового поста
    similar_posts = PostService.get_posts_with_similar_category(ch_pk)
    if similar_posts is None:
        MY_LOGGER.warning(f'Неудачная обработка поста!')    # TODO: поправить лог
        return False

    # Если нет постов для сравнения
    if len(similar_posts) == 0:
        MY_LOGGER.debug(f'Нет постов для сравнения, сходимся на том, что новый пост уникален.')
        new_post_embedding = PostFilters.make_embedding(text=new_post_text)
        PostService.suitable_post_processing(ch_pk=ch_pk, embedding=new_post_embedding, post_link=post_link,
                                             post_text=new_post_text)
        return True

    # Выполнить фильтры постов (сейчас только проверка на дубли)
    MY_LOGGER.debug(f'Вызываем фильтры')
    try:
        post_filters_obj = PostFilters(
            new_post=new_post_text,
            old_posts=[(i_post.get("text"), i_post.get("embedding").split()) for i_post in similar_posts],
        )
        filtration_rslt = post_filters_obj.complete_filtering()
    except RateLimitError as err:
        MY_LOGGER.warning(f'Проблема с запросами к OpenAI, откидываем пост. Ошибка: {err.error}')
        return False
    except Exception as err:
        MY_LOGGER.error(f'Необрабатываемая проблема на этапе фильтрации поста и запросов к OpenAI. '
                        f'Пост будет отброшен. Ошибка: {err} | Текст поста: {new_post_text[:30]!r}...')
        return False

    # Проверяем результаты фильтров
    if all(filtration_rslt):
        MY_LOGGER.debug(f'Пост прошёл фильтры!')
        PostService.suitable_post_processing(ch_pk=ch_pk, embedding=post_filters_obj.new_post_embedding,
                                             post_link=post_link, post_text=new_post_text)
        return True
    else:
        MY_LOGGER.debug(f'Фильтры для поста не пройдены. Откидываем пост.')
        return False
