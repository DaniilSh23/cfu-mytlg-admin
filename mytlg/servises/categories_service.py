from mytlg.models import Categories
from django.core.exceptions import ObjectDoesNotExist
from cfu_mytlg_admin.settings import MY_LOGGER
import json
from mytlg.servises.channels_service import ChannelsService


class CategoriesService:

    @staticmethod
    def get_all_categories():
        return Categories.objects.all()

    @staticmethod
    def get_or_create(category_name: str, defaults: dict) -> tuple:
        theme_obj, theme_created = Categories.objects.get_or_create(category_name=category_name, defaults=defaults)
        return theme_obj, theme_created

    @staticmethod
    def create_category_from_json_data(json_data):
        category = json_data.get("category")
        category, created = Categories.objects.get_or_create(
            category_name=category.lower(),
            defaults={
                "category_name": category.lower(),
            }
        )
        MY_LOGGER.debug(f'Категория каналов {category.category_name!r} была {"создана" if created else "получена"}.')
        return category

    @staticmethod
    def convert_category_list_to_string():
        categories_qset = Categories.objects.all()
        all_categories_lst = [category.category_name for category in categories_qset]
        categories_str = '\n'.join([category for category in all_categories_lst])
        return categories_str

    @staticmethod
    def create_category_from_gpt_result(gpt_rslt, i_interest):
        if gpt_rslt == 'no_themes':
            MY_LOGGER.info(f'GPT не определил тем для интереса пользователя: {i_interest.get("interest")!r} '
                           f'и прислал {gpt_rslt!r}. Привязываем юзера к категории тест')
            gpt_rslt = 'общее 🆕'
            category, created = Categories.objects.get_or_create(
                category_name='тест',
                defaults={"category_name": "тест"}
            )
        else:
            MY_LOGGER.debug('Привязываем пользователя к категории и каналам')
            try:
                category = Categories.objects.get(category_name=gpt_rslt.lower())
            except ObjectDoesNotExist:
                MY_LOGGER.warning(f'В БД не найдена категория: {gpt_rslt!r}. '
                                  f'Привязывем по стандарту к категории "тест".')
                category, created = Categories.objects.get_or_create(
                    category_name='тест',
                    defaults={"category_name": "тест"}
                )
        return category, gpt_rslt

    @staticmethod
    def get_or_create_channels_from_json_file(request):
        print(request)
        for i_json_file in request.FILES.getlist("json_files"):

            i_file_dct = json.loads(i_json_file.read().decode('utf-8'))

            theme_obj, theme_created = CategoriesService.get_or_create(
                category_name=i_file_dct.get("category").lower(),
                defaults={"category_name": i_file_dct.get("category").lower()},
            )
            MY_LOGGER.debug(f'{"Создали" if theme_created else "Достали из БД"} тему {theme_obj}!')

            i_data = i_file_dct.get("data")
            ChannelsService.update_or_create_channels_from_data_file(i_data, theme_obj)