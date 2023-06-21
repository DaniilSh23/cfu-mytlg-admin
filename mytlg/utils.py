from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse_lazy

from cfu_mytlg_admin.settings import MY_LOGGER
from mytlg.models import Channels, Themes


def make_form_with_channels(themes_pk, tlg_id):
    """
    Функция для формирования строки с HTML разметкой веб-формы с каналами для выбранных тематик.
    """
    MY_LOGGER.info(f'Запущена функция формирования HTML ответа с каналами на выбор в ответ на AJAX запрос')

    MY_LOGGER.debug(f'Итерируемся по списку PK тематик {themes_pk!r} и пробуем достать саму тематику из БД.')
    acordeon_body = ''
    for i_indx, i_theme_pk in enumerate(themes_pk):
        try:
            i_theme = Themes.objects.get(pk=int(i_theme_pk))
        except ObjectDoesNotExist:
            MY_LOGGER.warning(f'Не удалось найти тематику с PK={i_theme_pk}')
            return

        acordeon_body_head = f"""
            <div class="card accordion-item my-background">
                <h2 class="accordion-header" id="heading{i_indx + 1}">
                    <button type="button" class="accordion-button collapsed my-accordion-button" data-bs-toggle="collapse" 
                    data-bs-target="#accordion{i_indx + 1}" aria-expanded="true" 
                    aria-controls="accordion{i_indx + 1}">
                        {i_theme.theme_name}
                    </button>
                </h2>
                <div id="accordion{i_indx + 1}" class="accordion-collapse collapse" aria-labelledby="heading{i_indx + 1}" 
                data-bs-parent="#accordionExample" style="">
                    <div class="accordion-body">
                            <small class="text-light fw-semibold">Каналы для тематики {i_theme.theme_name}:</small>
                            <input type="text" value="{i_theme.pk}" name="theme_pk">
                            <div class="demo-inline-spacing mt-3">
        """
        acordeon_body_foot = f"""
                            </div>
                    </div>
                </div>
            </div>
        """
        acordeon_body = ''.join([
            acordeon_body,
            acordeon_body_head,
        ])

        MY_LOGGER.debug(f'Достаём фильтром каналы для тематики и создаём HTML разметку с ними.')
        channels_qset = Channels.objects.filter(theme=i_theme)
        for j_indx, j_ch in enumerate(channels_qset):
            acordeon_body_item = f"""
                <div class="list-group">
                    <label class="list-group-item my-label" for="channel-{j_ch.pk}">
                        <input class="form-check-input me-1 my-filling-fields" id="channel-{j_ch.pk}" name="selected_channel" type="checkbox" 
                        value="{j_ch.pk}">
                        <code>{j_ch.channel_name}</code> | <a href="{j_ch.channel_link}">{j_ch.channel_link}</a>
                    </label>
                </div>
            """
            acordeon_body = ''.join([
                acordeon_body,
                acordeon_body_item,
            ])
        acordeon_body = ''.join([
            acordeon_body,
            acordeon_body_foot,
        ])

    acordeon = f"""
    <div class="col-md mb-1 mb-md-0">
        <small class="text-light fw-semibold">Выберите каналы для тематик из раскрывающегося списка</small>
        <form onsubmit="showSpinner()" action="{reverse_lazy('mytlg:start_settings')}" method="post">
            <input class="my-filling-fields" type="hidden" id="tg-id-input" value="{tlg_id}" name="tlg_id">
            <div class="accordion mt-2 my-form-area" id="accordionExample">
                {acordeon_body}
            </div>
            <div class="mb-1 mt-3">
                <button type="submit" id="saveChannels" class="btn btn-info my-btn-clr">Сохранить каналы</button>
            </div>
        </form>
    </div>
    """
    return acordeon
