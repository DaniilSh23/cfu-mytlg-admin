from typing import List

import requests

from cfu_mytlg_admin.settings import MY_LOGGER, BOT_TOKEN


def send_gpt_interests_proc_rslt_to_tlg(gpt_rslts: List, tlg_id):
    """
    Отправка результатов обработки интересов через модель GPT юзеру в телеграм
    """
    msg_txt = '📌 Вот, какие темы мне удалось подобрать по Вашим интересам:\n\n'
    for i_theme in gpt_rslts:
        msg_txt = ''.join([msg_txt, f'🔹 {i_theme}\n'])

    MY_LOGGER.info(f'Запущена функция для отправки в телеграм подобранных тем пользователя.')
    send_rslt = requests.post(
        url=f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
        data={
            'chat_id': tlg_id,
            'text': msg_txt,
        }
    )
    if send_rslt.status_code == 200:
        MY_LOGGER.success('Успешная отправка подобранных тем пользователю в телеграм')
    else:
        MY_LOGGER.warning(f'Не удалось отправить пользователю в телеграм подобранные темы: {send_rslt.text}')


def send_err_msg_for_user_to_telegram(err_msg, tlg_id):
    """
    Отправка сообщения об ошибке пользователю в телеграм.
    """
    msg_txt = '⚠️ Возникла проблема:\n\n'
    msg_txt = ''.join([msg_txt, f'❕ {err_msg}\n'])

    MY_LOGGER.info(f'Запущена функция для отправки в телеграм подобранных тем пользователя.')
    send_rslt = requests.post(
        url=f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
        data={
            'chat_id': tlg_id,
            'text': msg_txt,
        }
    )
    if send_rslt.status_code == 200:
        MY_LOGGER.success('Успешная отправка ошибки пользователю в телеграм')
    else:
        MY_LOGGER.warning(f'Не удалось отправить текст ошибки пользователю в телеграм: {send_rslt.text}')


def send_command_to_bot(command: str):
    """
    Отправка боту команды на выполнение каких-либо действий
    """
    # TODO: дописать функцию, логи о результатах отправки тоже тут
    return True
    MY_LOGGER.info(f'Выполняем функцию для отпавки команды на остановку аккаунтов из-за истекших подписок.')
    bot_admin = BotSettings.objects.get(key='bot_admin').value
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': bot_admin, 'text': f'{command_msg}', 'disable_notification': True}
    MY_LOGGER.debug(f'Выполняем запрос на отправку команды боту для отключения каналов по истекшим подпискам')
    response = requests.post(url=url, data=data)  # Выполняем запрос на отправку сообщения

    if response.status_code != 200:  # Обработка неудачного запроса на отправку
        MY_LOGGER.error(f'Неудачная отправка команды на остановку аккаунтов из-за истекших подписок.\n'
                        f'Запрос: url={url} | data={data}\n'
                        f'Ответ:{response.json()}')
        return
    MY_LOGGER.success(f'Успешная отправка команды на остановку аккаунтов из-за истекших подписок.')
