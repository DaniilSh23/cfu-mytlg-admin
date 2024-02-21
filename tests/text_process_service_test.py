from django.test import TestCase
from langchain import FAISS
from langchain.embeddings import OpenAIEmbeddings
import openai
from langchain.text_splitter import CharacterTextSplitter
from mytlg.servises.bot_settings_service import BotSettingsService
from mytlg.servises.interests_service import InterestsService
from unittest.mock import Mock
from posts.services.text_process_service import TextProcessService
from mytlg.models import BotUser, Categories
from user_interface.models import Interests


class TextProcessServiceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.bot_user = BotUser.objects.create(
            tlg_id="123456789",
            tlg_username="user_name",
            language_code="ru",
        )

        cls.category = Categories.objects.create(category_name="test")
        cls.interest1 = Interests.objects.create(bot_user=cls.bot_user, is_active=True, interest_type='main',
                                                 category_id=cls.category.id)
        cls.interest2 = Interests.objects.create(bot_user=cls.bot_user, is_active=True, interest_type='main',
                                                 category_id=cls.category.id)
        cls.text_process_service = TextProcessService()
        cls.bot_settings_service = BotSettingsService
        interest_obj_lst = [cls.interest1, cls.interest2]
        interest_lst = InterestsService.create_interests_list_for_gpt_processing(interest_obj_lst)
        cls.index_db = cls.text_process_service.make_index_db_from_embeddings(interest_lst)

    def test_make_index_db_from_embeddings(self):
        # Mock the OpenAIEmbeddings object
        #self.text_process_service.embeddings.embed_text = Mock(return_value=[0.1, 0.2, 0.3])

        # Mock the BotSettingsService to return a known value
        self.bot_settings_service.get_bot_settings_by_key = Mock(return_value=0.5)

        self.assertIsInstance(self.index_db, FAISS)  # Check if an FAISS object is returned
        #self.assertEqual(len(self.index_db.text_embeddings), 2)  # Check if the number of embeddings matches the input list
        #self.assertEqual(self.index_db.embedding, self.text_process_service.embeddings)  # Check if the embeddings match the provided OpenAIEmbeddings object

    def test_filter_relevant_pieces_by_vector_distance(self):
        # Create a list of relevant pieces with scores
        relevant_pieces = [("piece1", 0.1), ("piece2", 0.6), ("piece3", 0.2)]

        # Set the similarity_index_for_interests to 0.5
        self.text_process_service.similarity_index_for_interests = 0.5

        filtered_rel_pieces = self.text_process_service.filter_relevant_pieces_by_vector_distance(relevant_pieces)

        # Only the piece with a score less than 0.5 should remain
        self.assertEqual(len(filtered_rel_pieces), 2)
        self.assertTrue(("piece1", 0.1) in filtered_rel_pieces)
        self.assertTrue(("piece3", 0.2) in filtered_rel_pieces)

    def test_get_relevant_pieces_by_embeddings(self):
        # Mock the FAISS object

        self.index_db.similarity_search_with_score_by_vector = Mock(return_value=[("relevant_piece", 0.3)])

        post = Mock(embedding="0.1 0.2 0.3")

        relevant_pieces = self.text_process_service.get_relevant_pieces_by_embeddings(self.index_db, post)

        self.assertEqual(relevant_pieces, [("relevant_piece", 0.3)])  # Check if the relevant piece is returned

