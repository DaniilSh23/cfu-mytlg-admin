from langchain import FAISS
from langchain.embeddings import OpenAIEmbeddings
from mytlg.servises.bot_settings_service import BotSettingsService
from cfu_mytlg_admin.settings import MY_LOGGER


class TextProcessService:
    def __init__(self):
        self.similarity_index_for_interests = float(
            BotSettingsService.get_bot_settings_by_key(key='similarity_index_for_interests'))

    @staticmethod
    def make_index_db_from_embeddings(interest_lst):
        embeddings = OpenAIEmbeddings()
        index_db = FAISS.from_embeddings(text_embeddings=interest_lst, embedding=embeddings)
        return index_db

    @staticmethod
    def get_relevant_pieces_by_embeddings(index_db, post):
        relevant_pieces = index_db.similarity_search_with_score_by_vector(
            embedding=[float(i_emb) for i_emb in post.embedding.split()],
            k=1,
        )
        return relevant_pieces

    def filter_relevant_pieces_by_vector_distance(self, relevant_pieces):
        filtered_rel_pieces = list(
            filter(lambda piece: piece[1] < self.similarity_index_for_interests, relevant_pieces))
        return filtered_rel_pieces
