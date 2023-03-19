import pytest
from django.contrib.auth import get_user_model

from core.models.utils import get_model_differs


@pytest.mark.django_db
def test_model_differs_equal_model(multidb):
    model = get_user_model()

    src = model.objects.create(username="src_name", email="a@gmail.com")

    dest = model.objects.filter(username=src.username).first()

    ret = get_model_differs(src, dest)

    assert ret == {}


@pytest.mark.django_db
def test_model_differs_different_model(multidb):
    model = get_user_model()

    src = model.objects.create(username="src_name", email="a@gmail.com")

    dest = model.objects.filter(username=src.username).first()
    dest.username = "test"

    ret = get_model_differs(src, dest)

    assert ret == {"username": ("src_name", "test")}
