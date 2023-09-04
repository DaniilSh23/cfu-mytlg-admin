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


def send_command_to_bot(command: str, bot_admin, session_file, disable_notification=True):
    """
    Отправка боту команды на старт или стоп аккаунта. Также шлём и файл сессии
    """
    # TODO: доработать так, чтобы при стопе аккаунта файл сессии не отправлять
    MY_LOGGER.info(f'Выполняем функцию для отправки команды боту: {command}.')
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument'
    data = {'chat_id': bot_admin, 'caption': command, 'disable_notification': disable_notification}
    with open(file=session_file, mode='rb') as file:
        file_name = session_file.split('/')[-1]
        files = {'document': (file_name, file)}
        MY_LOGGER.debug(f'Выполняем запрос на отправку команды боту, данные запроса: {data}')
        response = requests.post(url=url, data=data, files=files)  # Выполняем запрос на отправку сообщения с файлом

    if response.status_code != 200:  # Обработка неудачного запроса на отправку
        MY_LOGGER.error(f'Неудачная отправка команды боту.\n'
                        f'Запрос: url={url} | data={data}\n'
                        f'Ответ:{response.json()}')
        return
    MY_LOGGER.success(f'Успешная отправка команды боту.')


def send_message_by_bot(chat_id, text, disable_notification=False) -> bool | None:
    """
    Функция для отправки сообщений в телеграм от лица бота
    """
    MY_LOGGER.info(f'Вызвана функция для отправки от лица бота сообщений в телегу юзеру {chat_id!r}')
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': chat_id, 'text': text, 'disable_notification': disable_notification}
    MY_LOGGER.debug(f'Выполняем запрос на отправку сообщения от лица бота, данные запроса: {data}')
    response = requests.post(url=url, data=data)  # Выполняем запрос на отправку сообщения

    if response.status_code != 200:  # Обработка неудачного запроса на отправку
        MY_LOGGER.error(f'Неудачная отправка сообщения от лица бота.\n'
                        f'Запрос: url={url} | data={data}\n'
                        f'Ответ:{response.json()}')
        return
    MY_LOGGER.success(f'Успешная отправка сообщения от лица бота юзеру {chat_id!r}.')
    return True


def send_file_by_bot(chat_id, caption, file, file_name, disable_notification=False) -> bool | None:
    """
    Фукнция для отправки файла от лица бота.
    file - должен быть байтовым IO объектом.
    """
    MY_LOGGER.info(f'Вызвана функция для отправки от лица бота файла в телегу юзеру {chat_id!r}')
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument'
    data = {'chat_id': chat_id, 'caption': caption, 'disable_notification': disable_notification}
    # Телега принимает файлы в пар-ре document, в него кладём кортеж с именем, IO объектом файла и MIME типом
    files = {'document': (file_name, file, 'text/plain')}
    MY_LOGGER.debug(f'Выполняем запрос на отправку файла от лица бота, данные запроса: {data} | {files}')
    response = requests.post(url=url, data=data, files=files)

    if response.status_code != 200:
        MY_LOGGER.error(f'Неудачная отправка файла от лица бота.\n'
                        f'Запрос: url={url} | data={data} | files={files}\n'
                        f'Ответ:{response.json()}')
        return
    MY_LOGGER.success(f'Успешная отправка файла от лица бота юзеру {chat_id!r}.')
    return True


def bot_command_for_start_or_stop_account(instance, bot_admin, bot_command: str = 'start_acc'):
    """
    Функция для отправки боту команды на старт или стоп аккаунта
    """
    file_name = instance.session_file.path.split('/')[-1]
    command_msg = f'/{bot_command} {instance.pk} {file_name} {instance.proxy if bot_command == "start_acc" else ""}'
    send_command_to_bot(
        command=command_msg,
        bot_admin=bot_admin,
        session_file=instance.session_file.path,
    )
