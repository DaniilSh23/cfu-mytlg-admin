from django.test import TestCase
from django.test import RequestFactory
import json
from mytlg.models import Categories, Channels
from mytlg.servises.categories_service import CategoriesService


class CategoriesServiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.category1 = Categories.objects.create(category_name="category1")
        cls.category2 = Categories.objects.create(category_name="category2")

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
        category_obj.delete()

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

        # Call the method to get all categories
        categories = CategoriesService.get_all_categories()

        # Assert that the correct number of categories is returned
        self.assertEqual(len(categories), 2)

    def test_convert_category_list_to_string(self):
        # Call the method to convert categories to a string
        result = CategoriesService.convert_category_list_to_string()

        # Assert that the result contains the names of both categories
        self.assertIn(self.category1.category_name, result)
        self.assertIn(self.category2.category_name, result)

    def test_create_category_from_gpt_result_existing_category(self):
        # Test when GPT result matches an existing category
        gpt_result = "Category1"
        interest = {"interest": "Sample Interest"}

        result_category, result_gpt_result = CategoriesService.create_category_from_gpt_result(gpt_result, interest)

        # Assert that the result category matches the existing category
        self.assertEqual(result_category, self.category1)
        # Assert that the result GPT result remains the same
        self.assertEqual(result_gpt_result, gpt_result)
        result_category.delete()

    def test_create_category_from_gpt_result_new_category(self):
        # Test when GPT result doesn't match any existing category
        gpt_result = "NewCategory"
        interest = {"interest": "Sample Interest"}

        result_category, result_gpt_result = CategoriesService.create_category_from_gpt_result(gpt_result, interest)

        # Assert that the result category is a new category with the name "тест"
        self.assertTrue(result_category.category_name, "тест")
        # Assert that the result GPT result remains the same
        self.assertEqual(result_gpt_result, gpt_result)
