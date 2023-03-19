# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal
from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BaseModelMixin(models.Model):
    """
    PK mixin
    """

    id = models.BigAutoField(primary_key=True)

    class Meta:
        abstract = True

    # @classmethod
    # def dummy(cls, save=False, **kwargs):
    #     """
    #         더미 데이터 생성
    #     Args:
    #         save: DB 저장 여부
    #         **kwargs:
    #             keyword argument based field values
    #
    #     Returns:
    #         instance of this class
    #     """
    #     now = timezone.now().astimezone(settings.KST)
    #     attnames = set([f.attname for f in cls._meta.fields])
    #     error_fields = set(kwargs.keys()) - attnames
    #     if error_fields:
    #         assert 'Invalid Fields ', error_fields
    #
    #     for field in cls._meta.fields:
    #         if field.attname in {'id'}:
    #             continue
    #         if field.attname not in kwargs:
    #             # if field.blank:
    #             #     continue
    #             if isinstance(field, models.DateTimeField):
    #                 kwargs.update({field.attname: now})
    #             elif isinstance(field, models.DateField):
    #                 kwargs.update({field.attname: now.date()})
    #             elif isinstance(field, models.CharField):
    #                 kwargs.update({field.attname: '1'})
    #             elif isinstance(field, (models.BigIntegerField, models.IntegerField, models.ForeignKey)):
    #                 kwargs.update({field.attname: 1})
    #             elif isinstance(field, models.DecimalField):
    #                 kwargs.update({field.attname: Decimal('123.456789')})
    #             elif field.null is True:
    #                 kwargs.update({field.attname: None})
    #
    #     instance = cls(**kwargs)
    #     if save:
    #         instance.save()
    #     return instance


class TimeStampedMixin(models.Model):
    """
    row 생성일, 수정일 mixin
    """

    created = models.DateTimeField(_("created date"), blank=True, editable=False)
    modified = models.DateTimeField(_("modified date"), blank=True, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        now = timezone.now()
        if not self.created:
            self.created = now
            if "update_fields" in kwargs:
                kwargs["update_fields"].append("created")

        update_fields = kwargs.get("update_fields", None)
        if not update_fields:
            self.modified = now
        elif isinstance(update_fields, list) and "modified" not in update_fields:
            self.modified = now
            update_fields.append("modified")

        super(TimeStampedMixin, self).save(*args, **kwargs)


class ArchiveModelMixin(models.Model):
    """
    model 삭제시 archive
    """

    archive_date = models.DateTimeField(_("created date"), blank=True, editable=False)

    old_pk = models.BigIntegerField(
        _("old pk"), db_index=True, blank=False, editable=False
    )

    archive_user = models.ForeignKey(
        to=get_user_model(),
        on_delete=models.DO_NOTHING,
        related_name="+",
        null=True,
        blank=False,
        db_constraint=False,
        db_index=False,
    )

    class Meta:
        abstract = True


class TaskModelMixin(models.Model):
    """
    Async Task 모델 Mixin
    Task Status와 관련된 field 모음.
    """

    CHOICE_TASK_STATUS_QUEUED = 10  # push to MQ
    CHOICE_TASK_STATUS_PROGRESSING = 20  # pop from MQ
    CHOICE_TASK_STATUS_ERROR = 30  # something wrong...
    CHOICE_TASK_STATUS_COMPLETED = 40  # complete

    CHOICE_TASK_STATUS = (
        (CHOICE_TASK_STATUS_QUEUED, _("in queued")),
        (CHOICE_TASK_STATUS_PROGRESSING, _("in processing")),
        (CHOICE_TASK_STATUS_ERROR, _("error")),
        (CHOICE_TASK_STATUS_COMPLETED, _("completed")),
    )

    task_status = models.PositiveSmallIntegerField(
        _("status of crawling task"),
        choices=CHOICE_TASK_STATUS,
        default=CHOICE_TASK_STATUS_QUEUED,
    )
    queued_datetime = models.DateTimeField(
        _("queued datetime"), null=True, blank=True, default=None
    )
    processing_datetime = models.DateTimeField(
        _("processing datetime"), null=True, blank=True, default=None
    )
    error_datetime = models.DateTimeField(
        _("error datetime"), null=True, blank=True, default=None
    )
    completed_datetime = models.DateTimeField(
        _("completed datetime"), null=True, blank=True, default=None
    )

    def set_completed(self, save: bool, update_fields: List):
        self.task_status = self.CHOICE_TASK_STATUS_COMPLETED
        self.completed_datetime = timezone.now()

        # cache를 이용할 때는 queued, processing 데이터가 없음.
        if not self.queued_datetime:
            self.queued_datetime = self.completed_datetime
            update_fields.append("queued_datetime")

        if not self.processing_datetime:
            self.processing_datetime = self.completed_datetime
            update_fields.append("processing_datetime")

        if save:
            self.save(
                update_fields=update_fields + ["task_status", "completed_datetime"]
            )

    def set_error(self, save: bool, msg: str, update_fields: List):
        self.task_status = self.CHOICE_TASK_STATUS_ERROR
        self.error_datetime = timezone.now()

        # cache를 이용할 때는 queued, processing 데이터가 없음.
        if not self.queued_datetime:
            self.queued_datetime = self.error_datetime
            update_fields.append("queued_datetime")

        if not self.processing_datetime:
            self.processing_datetime = self.error_datetime
            update_fields.append("processing_datetime")

        if save:
            self.save(update_fields=update_fields + ["task_status", "error_datetime"])

    def set_processing(self, save: bool, update_fields: List):
        self.task_status = self.CHOICE_TASK_STATUS_PROGRESSING
        self.processing_datetime = timezone.now()

        if not self.queued_datetime:
            self.queued_datetime = self.processing_datetime
            update_fields.append("queued_datetime")

        if save:
            self.save(
                update_fields=update_fields + ["task_status", "processing_datetime"]
            )

    @property
    def is_queued_task(self):
        return self.task_status == self.CHOICE_TASK_STATUS_QUEUED

    @property
    def is_processing_task(self):
        return self.task_status == self.CHOICE_TASK_STATUS_PROGRESSING

    @property
    def is_error_task(self):
        return self.task_status == self.CHOICE_TASK_STATUS_ERROR

    @property
    def is_completed_task(self):
        return self.task_status == self.CHOICE_TASK_STATUS_COMPLETED

    @property
    def task_badge_class(self):
        if self.is_queued_task:
            return "bg-secondary"
        elif self.is_processing_task:
            return "bg-info"
        elif self.is_error_task:
            return "bg-danger"
        elif self.is_completed_task:
            return "bg-success"

    class Meta:
        abstract = True


# class CoordinateMixin(models.Model):
#
#     longitude = models.DecimalField(_('longitude'), max_digits=30, decimal_places=10, null=False, blank=True, default=Decimal('0.0'))
#     latitude = models.DecimalField(_('latitude'), max_digits=30, decimal_places=10, null=False, blank=True, default=Decimal('0.0'))
#
#     class Meta:
#         abstract = True
#
#     @property
#     def is_valid_coordinate(self) -> bool:
#         # 124 – 132, 33 – 43
#         if self.longitude and self.latitude and (124-1 <= self.longitude <= 132+1) and (33-1 <= self.latitude <= 43+1):
#             return True
#         return False
