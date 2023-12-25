"""
Разные функции, которые нужно переиспользовать в коде.
"""


def account_json_data_formatter(account_json_data: dict):
    """
    Функция, которая вытаскивает только нужные данные из TlgAccounts.json_data и упаковывает их
    для корректного взаимодействия с приложухой аккаунтов.
    """
    return {
        "tlg_id": account_json_data.get("id"),
        "api_id": account_json_data.get("app_id"),
        "api_hash": account_json_data.get("app_hash"),
        "device_model": account_json_data.get("device"),
        "app_version": account_json_data.get("app_version"),
        "lang_code": account_json_data.get("lang_pack"),
        "system_lang_code": account_json_data.get("system_lang_pack"),
        "system_version": account_json_data.get("system_version"),
    }
