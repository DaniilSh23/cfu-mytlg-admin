from django.core.management import BaseCommand
from loguru import logger

from mytlg.models import BotSettings, Categories


class Command(BaseCommand):
    """
    Команда для по установки настроек
    """

    def handle(self, *args, **options):
        logger.info('Старт команды по установке настроек и стандартных значений в БД')
        keys = {
            'bot_admins': '1978587604',
            'max_channels_per_acc': '45',
            'similarity_index_for_interests': '0.3',
            'prompt_for_interests_category': 'Ты ответственный помощник и твоя задача - это классификация интересов пользователей по '
                                             'определённым тематикам. На вход ты будешь получать данные с информацией для ответа пользователю - '
                                             'это список тематик (каждая тематика с новой строки) и запрос пользователя, который будет содержать '
                                             'формулировку его интереса. Твоя задача определить только одну тематику из переданного списка, '
                                             'которая с большей вероятностью подходит под интерес пользователя и написать в ответ только эту '
                                             'тематику и никакого больше текста в твоём ответе не должно быть. Не придумывай ничего от себя, '
                                             'выбирай тематику строго из того списка, который получил. Если интерес пользователя не подходит '
                                             'ни под одну из предоставленных тебе тематик, то пришли в ответ только фразу no_themes и никакого '
                                             'больше текста.',
            'prompt_for_text_reducing': 'Ты ответственный помощник и твоя задача - это создание краткого изложения '
                                        'переданного тебе текста. На вход ты будешь получать текст и тебе необходимо '
                                        'сократить его до 1-3 предложений. В сокращенном варианте тебе необходимо '
                                        'сохранить основной смысл, чтобы пользователь, который его прочтёт понял о чём '
                                        'идёт речь в тексте и смог принять решение интересно ли ему это или нет.'
                                        'Цель формирования сокращённого варианта текста - это не перегружать '
                                        'пользователя лишней информацией и в то же время передать основной смысл '
                                        'исходного текста. После прочтения сокращённого варианта пользователь должен '
                                        'принять решение стоит ли ему потратить время на ознакомление с оригинальным '
                                        'текстом или же нет.  В качестве своего ответа верни только сокращенный вариант '
                                        'текста и ничего более.',
        }
        for i_key, i_val in keys.items():
            _, i_created = BotSettings.objects.update_or_create(
                key=i_key,
                defaults={'key': i_key, 'value': i_val}
            )
            logger.success(f'Ключ {i_key} успешно {"создан" if i_created else "обновлён"} со значением {i_val}')
        category, created = Categories.objects.get_or_create(
            category_name='тест',
            defaults={'category_name': 'тест'}
        )
        logger.success(f'Категория {category!r} была {"создана" if created else "получена"}')

        logger.info('Окончание команды по установке настроек и стандартных значений в БД')
