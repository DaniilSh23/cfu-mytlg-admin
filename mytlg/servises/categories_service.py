import json
from mytlg.models import Categories
from django.core.exceptions import ObjectDoesNotExist
from .channels_service import ChannelsService
from cfu_mytlg_admin.settings import MY_LOGGER


class CategoriesService:

    @staticmethod
    def get_all_categories():
        return Categories.objects.all()

    @staticmethod
    def get_or_create(category_name: str, defaults: dict) -> tuple:
        theme_obj, theme_created = Categories.objects.get_or_create(category_name=category_name, defaults=defaults)
        return theme_obj, theme_created

    @staticmethod
    def get_or_create_categories_from_json_file(request):
        for i_json_file in request.FILES.getlist("json_files"):
            i_file_dct = json.loads(i_json_file.read().decode('utf-8'))
            # theme_obj, theme_created = Categories.objects.get_or_create(
            theme_obj, theme_created = CategoriesService.get_or_create(
                category_name=i_file_dct.get("category").lower(),
                defaults={"category_name": i_file_dct.get("category").lower()},
            )
            MY_LOGGER.debug(f'{"Создали" if theme_created else "Достали из БД"} тему {theme_obj}!')

            i_data = i_file_dct.get("data")
            ChannelsService.update_or_create_channels_from_data_file(i_data, theme_obj)


