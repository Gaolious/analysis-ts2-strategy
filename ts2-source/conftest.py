from unittest.mock import patch

from django.db import connections, transaction
from typing import Dict, Union

from django.test import Client
import pytest
from django.conf import settings

from app_root.bots.models import RunVersion, DbDefinition
from app_root.bots.utils_definition import DefinitionHelper
from app_root.users.models import User


HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
}

def request_helper(url: str, method: str, data: Union[Dict[str, str], str, None], is_ajax: bool, user, **kwargs):
    """

    :param user:
    :param url:
    :param method:
        GET
        POST
            parameter 와 함께
                data = {
                    'user_id': user_id,
                    'memo': '테스트 메모',
                }
                request_helper(url=url, method='POST', data=data, is_ajax=False, user=None, **headers )
    :param data:
    :param is_ajax:
    :param kwargs:
    :return:
    """
    c = Client()
    if user:
        c.force_login(user=user)
    method = method.lower()
    caller = getattr(c, method)

    if data and not isinstance(data, (dict, str)):
        data = {}

    """
    application/x-www-form-urlencoded
        - 'key=value & key=value'
    multipart/form-data 
        - binary data
        - RFC2388
    text/plain
    """

    if method == 'get':
        kwargs.update({
            'content_type':  'application/json; utf-8'
        })


    if is_ajax:
        kwargs.update({
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'
        })

    kwargs.setdefault('follow', False)
    kwargs.setdefault('secure', False)
    kwargs.setdefault('path', url)
    kwargs.setdefault('data', data)
    kwargs.setdefault('path', url)

    return caller(**kwargs)



# global fixture
def pytest_sessionstart(session):
    """
    to avoid
    https://pytest-django.readthedocs.io/en/latest/database.html#multi-db

    Args:
        session:

    Returns:

    """
    from django.test import TestCase
    TestCase.multi_db = True
    TestCase.databases = '__all__'


@pytest.fixture(scope='function')
def multidb():
    atomics = {}
    db_names = [k for k in connections]  # for multi db

    for db in db_names:
        atomics[db] = transaction.atomic(using=db)
        atomics[db].__enter__()

    yield atomics

    for db in reversed(db_names):
        transaction.set_rollback(True, using=db)
        atomics[db].__exit__(None, None, None)


@pytest.fixture(scope='session')
def req():
    return request_helper


@pytest.fixture(scope='session')
def chrome_header():
    def func():
        return HEADERS
    return func


@pytest.fixture(scope='function', autouse=True)
def http_connection_pool():
    with patch('urllib3.connectionpool.HTTPConnectionPool.urlopen') as mock:
        mock.side_effect = Exception('You should be mock the async task.')
        yield mock


@pytest.fixture(scope='function')
def fixture_version() -> RunVersion:
    ###########################################################################
    # prepare
    user = User.objects.create_user(username='test', android_id='test')
    version = RunVersion.objects.create(user_id=user.id)

    helper = DefinitionHelper()
    helper.instance = DbDefinition.objects.create(
        version='206.013',
        checksum='077e2eff27bdd5cb079319c6d40f0916d9671b20',
        url='https://cdn.trainstation2.com/client-resources/client-data-206.013.sqlite',
        download_path=settings.DJANGO_PATH / 'fixtures' / '206.013.sqlite'
    )
    helper.read_sqlite()
    yield version

