"""
Таски Celery для приложения posts.
"""
from celery import shared_task

from cfu_mytlg_admin.settings import MY_LOGGER
from posts.services.post_filter_service import PostFilters
from posts.services.post_service import PostService


@shared_task
def raw_post_processing(ch_pk: int, new_post_text: str, post_link: str):
    """
    Таск селери для обработки сырого поста, который прилетел из какого-либо канала.
    """
    MY_LOGGER.info('Запущен таск селери для обработки сырых постов (raw_post_processing).')

    # Обработка поста из кастомных каналов пользователей
    PostService.suitable_post_processing_from_users_list(
        post_text=new_post_text,
        ch_pk=ch_pk,
        post_link=post_link,
    )

    # Достать посты из БД с общей категорией для нового поста
    similar_posts = PostService.get_posts_with_similar_category(ch_pk)
    if similar_posts is None:
        MY_LOGGER.warning('Неудачная обработка поста!')    # TODO: поправить лог
        return False

    # Если нет постов для сравнения
    if len(similar_posts) == 0:
        MY_LOGGER.debug('Нет постов для сравнения, сходимся на том, что новый пост уникален.')
        new_post_embedding = PostFilters.make_embedding(text=new_post_text)
        PostService.suitable_post_processing(ch_pk=ch_pk, embedding=new_post_embedding, post_link=post_link,
                                             post_text=new_post_text)
        return True

    # Выполнить фильтры постов (сейчас только проверка на дубли)
    MY_LOGGER.debug('Вызываем фильтры')
    filtration_rslt, post_filters_obj = PostFilters.get_filtration_result(new_post_text, similar_posts)

    # Проверяем результаты фильтров
    if all(filtration_rslt):
        MY_LOGGER.debug('Пост прошёл фильтры!')
        PostService.suitable_post_processing(ch_pk=ch_pk, embedding=post_filters_obj.new_post_embedding,
                                             post_link=post_link, post_text=new_post_text)
        return True
    else:
        MY_LOGGER.debug('Фильтры для поста не пройдены. Откидываем пост.')
        return False
