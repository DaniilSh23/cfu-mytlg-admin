from django.test import TestCase
from django.urls import reverse_lazy
from bs4 import BeautifulSoup

from mytlg.models import Themes


class StartSettingsViewTestCase(TestCase):
    """
    Тесты для стартовой страницы с настройками.
    """

    @classmethod
    def setUpClass(cls):
        """
        Устанавливаем значения для всех тестов
        """
        cls.themes = [Themes.objects.create(theme_name=theme_name)
                      for theme_name in ('тематика для теста 1', 'тематика для теста 2')]

    @classmethod
    def tearDownClass(cls):
        """
        Удаляем значения, установленные только для тестов
        """
        [theme.delete() for theme in cls.themes]

    def test_inputs_checkbox_in_page(self):
        """
        Проверка, что теги input с type="checkbox" присутствуют на странице.
        """
        response = self.client.get(reverse_lazy('mytlg:start_settings'))
        self.assertEqual(response.status_code, 200, msg=f'Получен статус код, отличные от 200: {response.status_code}')
        soup = BeautifulSoup(response.content, 'html.parser')
        inputs = soup.findAll('input')
        checkboxes = [i_input for i_input in inputs
                      if "type" in i_input.attrs and i_input["type"] == "checkbox"
                      and 'id' in i_input.attrs and i_input['id'].startswith('theme-')]
        self.assertTrue(len(checkboxes) > 0)
