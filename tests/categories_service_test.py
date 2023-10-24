from django.test import TestCase
from django.test import RequestFactory
import json
from mytlg.models import Categories, Channels
from mytlg.servises.categories_service import CategoriesService


class CategoriesServiceTest(TestCase):

    def test_get_or_create(self):
        # Test the get_or_create method
        category_name = "Test Category"
        defaults = {"category_name": category_name}
        category_obj, created = CategoriesService.get_or_create(category_name, defaults)

        # Assert that the category object is created
        self.assertTrue(created)
        self.assertEqual(category_obj.category_name, category_name)

        # Call the get_or_create method again with the same data
        category_obj, created = CategoriesService.get_or_create(category_name, defaults)

        # Assert that the category object is not created the second time
        self.assertFalse(created)
        self.assertEqual(category_obj.category_name, category_name)

    # TODO вернуться к этому тесту после рефакторнига
    # def test_get_or_create_categories_from_json_file(self):
    #     # Create a JSON file content to simulate the request.FILES data
    #     request = RequestFactory().post('/')
    #     json_data = [
    #         {"category": "Category1"},
    #         {"category": "Category2"},
    #     ]
    #
    #
    #     request._FILES = {"json_files": [json.dumps(item).encode("utf-8") for item in json_data]}
    #
    #     # Call the method to get or create categories from the JSON file
    #     CategoriesService.get_or_create_categories_from_json_file(request)
    #
    #     # Assert that the categories and associated channels are created
    #     self.assertEqual(Categories.objects.count(), 2)
    #     self.assertEqual(Channels.objects.count(), 0)  # You can add channels if needed

    def test_get_all_categories(self):
        # Create some categories for testing
        Categories.objects.create(category_name="Category1")
        Categories.objects.create(category_name="Category2")

        # Call the method to get all categories
        categories = CategoriesService.get_all_categories()

        # Assert that the correct number of categories is returned
        self.assertEqual(len(categories), 2)
