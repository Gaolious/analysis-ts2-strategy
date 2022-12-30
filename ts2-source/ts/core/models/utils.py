from decimal import Decimal
from typing import List, Dict, Type

from django.db import models, connections, transaction
from django.utils import timezone

from core.models.exceptions import InvalidTaskStatus


# def backup_objects(source_object, backup_model, deleted_by):
#     """
#         [Source Model] -> [Backup model]
#         model A의 [source_object]를 backup model A' 로 복사
#
#     :param source_object: src
#     :param backup_model: dest
#     :param deleted_by: log
#     :return:
#     """
#     data = {
#         field.attname: getattr(source_object, field.attname)
#         for field in source_object._meta.fields if hasattr(backup_model, field.attname)
#     }
#
#     backup_objects = []
#     backup_object = backup_model(**data)
#     backup_object.pk = None
#     backup_object.old_pk = source_object.pk
#     backup_object.archive_date = timezone.now()
#     backup_object.archive_user = deleted_by
#     backup_objects.append(backup_object)
#     backup_model.objects.bulk_create(backup_objects, 100)


# def restore_objects(queryset, source_model):
#     """
#         [Source Model] <- [Backup model]
#         backup model 의 Queryset을 source_model 으로 복사 후 삭제
#
#     :param queryset: Queryset (backup model)
#     :param source_model:
#     :return:
#     """
#     source_objects = []
#     for deleted_object in queryset:
#         data = {
#             field.attname: getattr(deleted_object, field.attname)
#             for field in deleted_object._meta.fields if hasattr(source_model, field.attname)
#         }
#         delete_attr_list = [
#             'archive_date', 'archive_user', 'archive_user_id',
#         ]
#         for attr in delete_attr_list:
#             if attr in data:
#                 del data[attr]
#
#         src_instance = source_model(**data)
#         src_instance.id = deleted_object.old_pk
#         source_objects.append(src_instance)
#
#     if source_model.objects.bulk_create(source_objects, 100):
#         queryset.delete()
#         return True
#     else:
#         return False

def get_model_differs(src, dest) -> Dict[str, tuple]:
    """
        src 기준 dest 모델과의 차이
    Args:
        src:
        dest:

    Returns:

    """
    def convert_python_value(instance, field_name):
        """
        python variable type 으로 변환

        Args:
            instance:
            field_name:

        Returns:

        """
        value = getattr(instance, field_name)

        src_field = instance._meta._forward_fields_map.get(field_name)
        if src_field:
            try:
                return src_field.get_prep_value(value)
            except:
                pass

        return None


    ret = {}

    for field in src._meta.fields:
        field_name = field.attname
        if field_name in ('id', 'pk', 'created', 'modified'):
            continue

        src_value = convert_python_value(instance=src, field_name=field_name)

        if hasattr(dest, field_name):
            dest_value = convert_python_value(instance=dest, field_name=field_name)

            is_equal = False
            if isinstance(dest_value, Decimal):
                try:
                    src_field = src._meta._forward_fields_map.get(field_name)

                    diff = abs(src_value - dest_value)
                    if diff < 0.1**src_field.decimal_places:
                        is_equal = True
                except:
                    pass
            elif src_value == dest_value:
                is_equal = True

            if not is_equal:
                ret.update({
                    field_name: (src_value, dest_value)
                })
        else:
            ret.update({
                field_name: (src_value, None)
            })

    return ret


# def chunk_queryset(queryset, chunk_size):
#
#     last_pk = None
#
#     while True:
#
#         inner_queryset = queryset.order_by('id')
#
#         if last_pk:
#             inner_queryset = inner_queryset.filter(id__gt=last_pk)
#
#         data_list = list(inner_queryset.all()[:chunk_size])
#
#         for row in data_list:
#             yield row
#
#         if len(data_list) < chunk_size:
#             break
#
#         last_pk = data_list[-1].id


# def chunk_list(data, chunk_size):
#     if not isinstance(data, list):
#         data = list(data)
#     for i in range(0, len(data), chunk_size):
#         yield data[i:i + chunk_size]


# def truncate_model(MODEL):
#
#     # allowed only specified model
#
#     allowed_model = {'buildings.titleinfo', 'buildings.basisoutlineinfo', 'buildings.exposepublicareainfo'}
#     try:
#         app_label = MODEL._meta.app_label or ''
#         model_name = MODEL._meta.model_name or ''
#
#         keyword = f'{app_label}.{model_name}'
#
#         if keyword in allowed_model:
#             db_alias = MODEL.objects.db
#             if db_alias in connections:
#                 with connections[db_alias].cursor() as cursor:
#                     cursor.execute(
#                         'TRUNCATE TABLE `{table}`'.format(table=MODEL._meta.db_table)
#                     )
#                     return True
#     except:
#         pass
#
#     return False


# def check_task_status(MODEL: Type[models.Model], pk: int) -> 'MODEL':
#     """
#         MODEL class의 pk를 row-level lock 상태로 load 후,
#
#         status 체크.
#
#     Args:
#         MODEL:
#         pk:
#
#     Returns:
#
#     """
#     db_alias = MODEL.objects.db
#     with transaction.atomic(using=db_alias):
#         version = MODEL.objects.filter(id=pk).select_for_update().first()
#
#         if version.is_processing_task:
#             raise InvalidTaskStatus(version.CHOICE_TASK_STATUS_QUEUED, version.task_status)
#
#         version.set_processing(save=True, update_fields=[])
#
#         return version