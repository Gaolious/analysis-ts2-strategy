import shutil
from unittest import mock

import pytest
from django.conf import settings

from app_root.bot.models import Definition, Article, Factory, Product, Train, Destination, Region, Location, JobLocation
from app_root.bot.models import RunVersion
from app_root.bot.utils_definition import DefinitionHelper
from app_root.bot.utils_server_time import ServerTimeHelper
from app_root.users.models import User
from core.tests.factory import AbstractFakeResp


@pytest.fixture(scope='function')
def fixture_crawling_get():
    with mock.patch('app_root.bot.utils_definition.CrawlingHelper.get') as p:
        yield p


@pytest.fixture(scope='function')
def fixture_crawling_post():
    with mock.patch('app_root.bot.utils_definition.CrawlingHelper.post') as p:
        yield p


@pytest.fixture(scope='function')
def fixture_download_file():
    with mock.patch('app_root.bot.utils_definition.download_file') as p:
        yield p


@pytest.mark.django_db
@pytest.mark.parametrize('filename, sqlite_filename', [
    ('gaolious1_2022.12.29.json', 'client-data-206.009.sqlite'),
])
def test_utils_definition_helper(multidb, filename, sqlite_filename, fixture_crawling_get, fixture_crawling_post, fixture_download_file):
    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'definition' / filename).read_text('utf-8')
    sqllite_filepath = settings.DJANGO_PATH / 'fixtures' / 'definition' / sqlite_filename

    def FakeDownload(download_filename, *args, **kwargs):
        path = download_filename.parent
        if not path.exists():
            path.mkdir(0o755, True, True)
        shutil.copy(sqllite_filepath, download_filename)
        return 1_000_000

    ###########################################################################
    # prepare
    user = User.objects.create_user(username='test', android_id='test')
    version = RunVersion.objects.create(user_id=user.id)

    server_time = ServerTimeHelper()
    fixture_crawling_get.return_value = FakeResp()
    fixture_download_file.side_effect = FakeDownload

    bot = DefinitionHelper()
    ###########################################################################
    # call function
    bot.run(url='url', user=user, server_time=server_time, run_version=version)

    ###########################################################################
    # assert
    assert bot.instance
    assert Definition.objects.count() > 0
    assert Article.objects.count() > 0
    assert Factory.objects.count() > 0
    assert Product.objects.count() > 0
    assert Train.objects.count() > 0
    assert Destination.objects.count() > 0
    assert Region.objects.count() > 0
    assert Location.objects.count() > 0
    assert JobLocation.objects.count() > 0