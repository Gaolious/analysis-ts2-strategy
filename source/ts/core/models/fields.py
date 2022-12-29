
from django.db import models
from django.utils.translation import gettext_lazy as _
import lzma


def decompress_data(s):
    """
    압축 해제

    Args:
        s:

    Returns:

    """
    if isinstance(s, (bytes, bytearray)):
        return lzma.decompress(s).decode('utf-8')
    return s


def compress_data(s):
    """
    압축

    Args:
        s:

    Returns:

    """
    if isinstance(s, str):
        return lzma.compress(s.encode('utf-8'))
    if isinstance(s, (bytes, bytearray)):
        return lzma.compress(s)
    return s


class CompressedTextField(models.BinaryField):
    description = _("LZMA Compressed Text for BinaryFields")
    empty_values = [None, b'']

    def get_prep_value(self, value):
        return compress_data(value)

    def from_db_value(self, value, *args, **kwargs):
        return self.to_python(value)

    def value_to_string(self, obj):
        return decompress_data(self.value_from_object(obj))

    def to_python(self, value):
        if value is not None:
            if type(value) in (bytes, bytearray):
                return decompress_data(value)
            else:
                return value
        return value


class FtcMoneyField(models.BigIntegerField):
    description = _("money field")


class FtcDateField(models.CharField):
    description = _("Date as String field")

    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs['max_length'] = 50
        super(FtcDateField, self).__init__(*args, **kwargs)

