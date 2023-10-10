from mytlg.models import Categories
from django.core.exceptions import ObjectDoesNotExist


class CategoriesService:

    @staticmethod
    def get_all_categories():
        return Categories.objects.all()

    @staticmethod
    def get_or_create(category_name: str, defaults: dict) -> tuple:
        theme_obj, theme_created = Categories.objects.get_or_create(category_name, defaults)
        return theme_obj, theme_created

