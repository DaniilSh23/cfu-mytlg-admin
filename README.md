# Веб-приложение для проекта "Мой телеграм"
Суть его в том, чтобы давать пользователям только самую необходимую информацию из тех источников, которые они для себя выберут.


### Значение в админке (настройки бота, модель BotSettings), которые необходимы для работы:
* Их можно установить командой ```python3 manage.py setkeys```
1. ```bot_admins``` - список через пробел Telegram ID админов бота 
2. ```max_channels_per_acc``` - макс. кол-во каналов, на которое может подписаться один аккаунт
3. ```similarity_index_for_interests``` - индекс сходства для интересов (пример: берём текст поста и, если векторное расстояние текста поста и интереса меньше этого индекса, то пост подходит под интерес пользователя)