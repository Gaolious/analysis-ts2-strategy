import shutil
from unittest import mock

import pytest
from django.conf import settings

from app_root.servers.models import RunVersion, EndPoint, TSArticle, TSUserLevel, TSWarehouseLevel, TSFactory, \
    TSProduct, TSTrain, TSTrainLevel, TSRegion, TSLocation, TSDestination, TSJobLocation
from app_root.servers.utils_import import EndpointHelper, SQLDefinitionHelper, LoginHelper
from app_root.users.models import User
from core.tests.factory import AbstractFakeResp
from core.utils import hash10


@pytest.fixture(scope='function')
def fixture_crawling_get():
    with mock.patch('app_root.mixins.CrawlingHelper.get') as p:
        yield p


@pytest.fixture(scope='function')
def fixture_crawling_post():
    with mock.patch('app_root.mixins.CrawlingHelper.post') as p:
        yield p


@pytest.fixture(scope='function')
def fixture_download_file():
    with mock.patch('app_root.servers.utils_import.download_file') as p:
        yield p


@pytest.mark.django_db
@pytest.mark.parametrize('filename', [
    'gaolious1_2022.12.29.json',
])
def test_server_import_endpoint(multidb, filename, fixture_crawling_get, fixture_crawling_post):

    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'endpoints' / filename).read_text('utf-8')

    ###########################################################################
    # prepare
    user = User.objects.create_user(username='test', android_id='test')
    version = RunVersion.objects.create(user_id=user.id)

    fixture_crawling_get.return_value = FakeResp()

    helper = EndpointHelper(version=version)
    ###########################################################################
    # call function
    ret = helper.run()

    ###########################################################################
    # assert

    names = [
        'login', 'login_v2', 'payment', 'command_processing', 'command_processing_collection', 'support_url', 'definitions', 'start_game', 'login_restore_url', 'restore_decision_url', 'store_notification_token', 'update_device_id', 'impersonate_link', 'payments', 'leaderboard', 'firebase_auth_token', 'dwh_events', 'search_player', 'search_guild', 'search_guild_recommended', 'privacy', 'eula', 'localized_privacy', 'localized_eula', 'app_logs', 'applogs', 'firebase_db', 'payment_obfuscation_public_key', 'ts2feedback', 'facebook', 'twitter', 'forum', 'instagram', 'youtube', 'cdn_enpoint',
        EndPoint.ENDPOINT_INIT_DATA_URLS,
    ]
    for name in names:
        cnt = len(EndPoint.get_urls(name))

        assert cnt > 0, f"Not found for name='{name}'"


@pytest.mark.django_db
@pytest.mark.parametrize('filename, sqlite_filename', [
    ('gaolious1_2022.12.29.json', 'client-data-206.009.sqlite'),
])
def test_server_import_sql_definition(
        multidb, filename, sqlite_filename,
        fixture_crawling_get, fixture_crawling_post, fixture_download_file
):

    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'definition' / filename).read_text('utf-8')

    sqllite_filepath = settings.DJANGO_PATH / 'fixtures' / 'definition' / sqlite_filename

    def FakeDownload(download_filename, *args, **kwargs):
        path = download_filename.parent
        if not path.exists():
            path.mkdir(0o755, True, True)
        shutil.copy(sqllite_filepath, download_filename)
        return 1_000_000

    fixture_crawling_get.return_value = FakeResp()

    ###########################################################################
    # prepare
    user = User.objects.create_user(username='test', android_id='test', game_access_token='a', player_id='1')
    version = RunVersion.objects.create(user_id=user.id)
    EndPoint.objects.create(name=EndPoint.ENDPOINT_DEFINITION, name_hash=hash10(EndPoint.ENDPOINT_DEFINITION), url='a')

    fixture_crawling_get.return_value = FakeResp()
    fixture_download_file.side_effect = FakeDownload

    helper = SQLDefinitionHelper(version=version)
    ###########################################################################
    # call function
    ret = helper.run()

    ###########################################################################
    # assert
    models = [
        TSArticle,
        TSUserLevel,
        TSWarehouseLevel,
        TSFactory,
        TSProduct,
        TSTrain,
        TSTrainLevel,
        TSRegion,
        TSLocation,
        TSDestination,
        TSJobLocation,
    ]
    for model in models:
        assert model.objects.count() > 0


@pytest.mark.django_db
@pytest.mark.parametrize('remember_me_token, filename', [
    ('', 'gaolious1_2022.12.29_with_device_id.json'),
    ('a', 'gaolious1_2022.12.29_with_remember_token.json'),
    ('', 'gaolious_2022.12.30_with_device_id.json'),
    ('a', 'gaolious_2022.12.30_with_remember_token.json'),
])
def test_utils_login_helper(multidb, filename, remember_me_token, fixture_crawling_get, fixture_crawling_post):
    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'login' / filename).read_text('utf-8')

    ###########################################################################
    # prepare
    user = User.objects.create_user(username='test', android_id='test', remember_me_token=remember_me_token)
    version = RunVersion.objects.create(user_id=user.id)
    EndPoint.objects.create(name=EndPoint.ENDPOINT_LOGIN, name_hash=hash10(EndPoint.ENDPOINT_LOGIN), url='a')

    fixture_crawling_post.return_value = FakeResp()

    helper = LoginHelper(version=version)
    ###########################################################################
    # call function
    helper.run()

    ###########################################################################
    # assert
    user.refresh_from_db()
    assert user.player_id
    assert user.game_access_token
    assert user.authentication_token
    assert user.remember_me_token
    assert user.device_token
    assert user.support_url