from mytlg.models import FaqQuestion
from cfu_mytlg_admin.settings import MY_LOGGER


class FaqQuestionService:

    @staticmethod
    def get_all_faq_questions() -> list:
        try:
            faq_questions = FaqQuestion.objects.all()
            all_faq_questions = [{'question': faq_question.question, 'answer': faq_question.answer} for faq_question in
                                 faq_questions]
            MY_LOGGER.info('Все вопросы FaqQuestion получены')
            return all_faq_questions
        except Exception as e:
            MY_LOGGER.error(f'Не удалось получить все вопросы FaqQuestion: {e}')
            return []
