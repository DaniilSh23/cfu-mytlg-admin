import io
import json

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.db.models.options import Options

from cfu_mytlg_admin.settings import MY_LOGGER


class ExportAsJSONMixin:
    """
    Миксин для админки, даёт экшн для экспорта каналов в JSON
    """
    def export_json(self, request: HttpRequest, queryset: QuerySet):
        """
        Метод для экспортирования данных БД в JSON файл.
        """
        MY_LOGGER.info('Вызван метод админки для экспорта каналов в JSON')

        meta: Options = self.model._meta    # Берём meta у модели, от туда достанем потом названия полей
        field_names = ('pk', 'channel_name', 'channel_link', 'is_ready')

        # Запишем результат в ответ
        rslt_dct = dict(data=[])
        for i_obj in queryset:  # Идём по всем объектам в QuerySet
            i_obj_dct = dict()
            for i_field in field_names:
                i_obj_dct[i_field] = getattr(i_obj, i_field)
            rslt_dct['data'].append(i_obj_dct)

        # Дампим словарь в файл(респонс) как json
        json_io = io.StringIO()
        json.dump(obj=rslt_dct, fp=json_io, indent=4, ensure_ascii=False)

        # Подготовим объект, в который будут выводится данные - это будет HttpResponse
        response = HttpResponse(json_io.getvalue(), content_type='application/json')    # В объект сразу запишем заголовок content_type
        response['Content-Disposition'] = f'attachment; filename="{meta.verbose_name_plural}--export.json"'    # Дадим название файлу
        return response

    export_json.short_description = 'Экспорт в JSON'  # short_description - позволяет указать описание для action
