"""
Таски Celery для приложения posts.
"""
from celery import shared_task

from cfu_mytlg_admin.settings import MY_LOGGER
from posts.services.post_filter_service import PostFilters
from posts.services.post_service import PostService
from posts.services.text_process_service import TextProcessService


@shared_task
def raw_post_processing(channel_id: int, new_post_text: str, post_link: str):
    """
    Таск селери для обработки сырого поста, который прилетел из какого-либо канала.
    """
    MY_LOGGER.info('Запущен таск селери для обработки сырых постов (raw_post_processing).')

    # Обработка поста из кастомных каналов пользователей
    PostService.suitable_post_processing_from_users_list(
        post_text=new_post_text,
        channel_id=channel_id,
        post_link=post_link,
    )

    # Достать посты из БД с общей категорией для нового поста
    similar_posts = PostService.get_posts_with_similar_category(channel_id)
    if similar_posts is None:
        MY_LOGGER.warning('Неудачная обработка поста! Не удалось достать посты с общей категорией')
        return False

    # Если нет постов для сравнения
    if len(similar_posts) == 0:
        MY_LOGGER.debug('Нет постов для сравнения, сходимся на том, что новый пост уникален.')
        new_post_embedding = TextProcessService.make_embeddings(text=new_post_text)
        if not new_post_embedding:
            return False
        PostService.suitable_post_processing(channel_id=channel_id, embedding=new_post_embedding, post_link=post_link,
                                             post_text=new_post_text)
        return True

    # Выполнить фильтры постов (сейчас только проверка на дубли)
    MY_LOGGER.debug('Вызываем фильтры')
    filtration_rslt, post_filters_obj = PostFilters.get_filtration_result(new_post_text, similar_posts)

    # Проверяем результаты фильтров
    if all(filtration_rslt):
        MY_LOGGER.debug('Пост прошёл фильтры!')
        PostService.suitable_post_processing(channel_id=channel_id, embedding=post_filters_obj.new_post_embedding,
                                             post_link=post_link, post_text=new_post_text)
        return True
    else:
        MY_LOGGER.debug('Фильтры для поста не пройдены. Откидываем пост.')
        return False
