import datetime
import json
from decimal import Decimal
from functools import cached_property
from typing import List, Tuple, Dict

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models.mixins import BaseModelMixin, TimeStampedMixin, TaskModelMixin
from core.utils import convert_time, convert_datetime


