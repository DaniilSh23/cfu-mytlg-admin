from django.core.management import BaseCommand
from loguru import logger

from mytlg.models import Themes, Channels, SubThemes


class Command(BaseCommand):
    """
    Команда для наполнения БД стандартными значениями
    """
    def handle(self, *args, **options):
        logger.info('Старт команды по наполнению БД!')

        # Создать записи о тематиках
        themes = {
            'Telegram'.lower(): (
                ('ChatGPT & Midjourney ', 'https://t.me/nomax'),
                ('Botcollection ', 'https://t.me/botcollection'),
                ('Каналы Telegram - каталог', 'https://t.me/chagram'),
                ('Каталог Telegram каналов, ботов ', 'https://t.me/openbusines'),
                ('Telegram Baza ', 'https://t.me/TBaza'),
                ('HowYour ', 'https://t.me/HowYour'),
            ),
            'Софт и приложения'.lower(): (
                ('📲 Easy APK  ', 'https://t.me/EasyAPK'),
                ('💎 MUST HAVE ', 'https://t.me/Alexey070315'),
                ('Bзлoмaнные приложения ', 'https://t.me/daker7'),
            ),
            'Маркетинг, PR, реклама'.lower(): (
                ('Семейка ботов', 'https://t.me/FamilyBots'),
                ('Клиент всегда прав', 'https://t.me/klientvp'),
                ('Сосисочная', 'https://t.me/joinchat/-pYpF2amrepmMTli'),
                ('кабачковая икра по акции', 'https://t.me/sale_caviar'),
            ),
            'Бизнес и стартапы'.lower(): (
                ('Книги на миллион | бизнес блог', 'https://t.me/ikniga'),
                ('ОПЕРШТАБ РЫБАКОВ ИГОРЬ', 'https://t.me/rybakovigor'),
                ('Трансформатор', 'https://t.me/TransformatorTV'),
                ('Стартап дня. Александр Горный.', 'https://t.me/startupoftheday'),
                ('СберБизнес', 'https://t.me/sberbusiness'),
            ),
            'Образование'.lower(): (
                ('!Finuniver', 'https://t.me/finuniverchan'),
                ('Вышка для своих', 'https://t.me/hse_live'),
                ('⚡️ITMOLNIA⚡️', 'https://t.me/itmolnia'),
                ('Университет «Синергия»', 'https://t.me/synergyunivers'),
            ),
            'Криптовалюты'.lower(): (
                ('CoinLLions', 'https://t.me/coinllions'),
                ('Криптограм 👾', 'https://t.me/cryptogram_ton'),
                ('Крипта головного мозга🤯🚀', 'https://t.me/crypto_mozgi'),
                ('Сигналы Криптовалюты', 'https://t.me/torgovlya_fyuchersy2'),
            ),
            'Технологии'.lower(): (
                ('Эксплойт ', 'https://t.me/exploitex'),
                ('Wylsacom Red ', 'https://t.me/Wylsared'),
                ('Не баг, а фича ', 'https://t.me/bugfeature'),
                ('ChatGPT 4.0 | Бот Канал ✳️ ', 'https://t.me/ChatGPT_Main'),
                ('Милорд ', 'https://t.me/+itM4B8KVXRIzNzdi'),
                ('1337: IT, ChatGPT, Midjourney ', 'https://t.me/chatgpt1337_artis'),
                ('concertzaal', 'https://t.me/concertzaal'),
            )
        }
        sub_themes = {
            'Технологии'.lower(): {
                'Python'.lower(): (
                    ('Python обучающий', 'https://t.me/pythonist24'),
                    ('Python Academy ', 'https://t.me/python_academy'),
                    ('Python Hacks', 'https://t.me/python_secrets'),
                    ('Python Community', 'https://t.me/Python_Community_ru'),
                ),
                'Frontend-разработка'.lower(): (
                    ('Простой HTML | Программирование', 'https://t.me/joinchat/ml4Q_yJfHtwwOGUy'),
                    ('Простой JavaScript | Программирование', 'https://t.me/joinchat/T1h1H8kGO0hhYjc6'),
                    ('Сайтодел | GitHub, CodePen, JavaScript, CSS, Figma', 'https://t.me/sitodel'),
                ),
                'Linux'.lower(): (
                    ('Linux для чайника', 'https://t.me/os_linux_ru'),
                    ('DevOps School | Linux, InfoSec, ИБ', 'https://t.me/devops_sc'),
                    ('Kali Linux', 'https://t.me/linuxkalii'),
                ),
            },
            'Образование'.lower(): {
                'Онлайн обучение'.lower(): (
                    ('GeekBrains', 'https://t.me/geekbrains_ru'),
                    ('Яндекс Практикум', 'https://t.me/yndx_practicum'),
                    ('Skillbox: образовательная платформа', 'https://t.me/skillboxru'),
                    ('Нетология', 'https://t.me/netology_ru'),
                    ('Лекторий', 'https://t.me/lektorium'),
                ),
                'Английский язык'.lower(): (
                    ('Fucking English | Английский 18+', 'https://t.me/fuckingenglish'),
                    ('Английский с нуля | Английский язык', 'https://t.me/EnglishBestChannel'),
                    ('УЧИЛКА АНГЛИЙСКОГО', 'https://t.me/englishmaria'),
                )
            }
        }
        for i_key, i_value in themes.items():
            i_theme, i_created = Themes.objects.get_or_create(
                theme_name=i_key,
                defaults={'theme_name': i_key}
            )
            logger.success(f'Тема {i_key!r} {"создана" if i_created else "уже есть"} в БД.')
            for j_ch_name, j_ch_lnk in i_value:
                ch_obj, j_created = Channels.objects.get_or_create(
                    channel_link=j_ch_lnk,
                    defaults={
                        "channel_name": j_ch_name,
                        "channel_link": j_ch_lnk,
                        "theme": i_theme,
                        'sub_theme': None,
                    }
                )
                logger.success(f'Канал {j_ch_lnk!r} {"создан" if j_created else "уже есть"} в БД.')

            # Достаём и записываем в БД подтемы
            i_sub_themes = sub_themes.get(i_key)
            if i_sub_themes:
                for k_key, k_val in i_sub_themes.items():
                    i_sub_theme, i_created = SubThemes.objects.get_or_create(
                        sub_theme_name=k_key,
                        defaults={'sub_theme_name': k_key}
                    )
                    logger.success(f'Подтема {k_key!r} {"создана" if i_created else "уже есть"} в БД.')
                    for k_ch_name, k_ch_lnk in k_val:
                        ch_obj, j_created = Channels.objects.get_or_create(
                            channel_link=k_ch_lnk,
                            defaults={
                                "channel_name": k_ch_name,
                                "channel_link": k_ch_lnk,
                                "sub_theme": i_sub_theme,
                                'theme': None,
                            }
                        )
                        logger.success(f'Канал {k_ch_lnk!r} {"создан" if j_created else "уже есть"} в БД.')

        logger.info('Окончание команды по наполнению БД!')
