import datetime
import json
from functools import cached_property
from typing import List, Tuple, Dict, Optional, Type

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from app_root.servers.mixins import CHOICE_RARITY, CHOICE_ERA, ContentCategoryMixin
from core.models.mixins import BaseModelMixin, TimeStampedMixin, TaskModelMixin
from core.utils import convert_time, convert_datetime


class Union(BaseModelMixin, TimeStampedMixin, TaskModelMixin):
    class Meta:
        verbose_name = "Union"
        verbose_name_plural = "Unions"
