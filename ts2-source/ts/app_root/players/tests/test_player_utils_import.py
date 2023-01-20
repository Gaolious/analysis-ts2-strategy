import shutil
from unittest import mock

import pytest
from django.conf import settings

from app_root.players.utils_import import InitdataHelper
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
    'gaolious_2022.12.30-1.json',
    'gaolious_2022.12.30-2.json',
    'gaolious_2023.01.09_contract.json',
    'gaolious_2023.01.09_gifts.json',
    'gaolious_2023.01.11_jobs.json',
    'gaolious_2023.01.14_fulltest.json',
    'gaolious_2023.01.14_idle_destinations.json',
    'gaolious_2023.01.14_results.json',
    'levelup.json',
    'whistle.json',
])
def test_utils_initdata_helper(multidb, filename, fixture_crawling_get, fixture_crawling_post):
    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')

    ###########################################################################
    # prepare
    user = User.objects.create_user(username='test', android_id='test', game_access_token='1', player_id='1')
    version = RunVersion.objects.create(user_id=user.id)
    EndPoint.objects.create(name=EndPoint.ENDPOINT_INIT_DATA_URLS, name_hash=hash10(EndPoint.ENDPOINT_INIT_DATA_URLS), url='a')

    fixture_crawling_get.return_value = FakeResp()

    helper = InitdataHelper(version=version)
    ###########################################################################
    # call function
    helper.run()

    ###########################################################################
    # assert
    user.refresh_from_db()

#
# @pytest.mark.django_db
# @pytest.mark.parametrize('filename, population, num_buildings, num_destination', [
#     (
#
#             25,  # population
#             8,  # num buildings
#             0,  # num destination
#     ),
#     (
#             'gaolious_2022.12.30-1.json',
#             33066,  # population
#             32,  # num buildings
#             4,  # num destination
#     )
# ])
# def test_utils_init_data_helper(
#         multidb,
#         filename,
#         fixture_crawling_get, fixture_crawling_post,
#         population, num_buildings, num_destination
# ):
#     class FakeResp(AbstractFakeResp):
#         text = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')
#
#     ###########################################################################
#     # prepare
#     user = User.objects.create_user(username='test', android_id='test')
#     version = RunVersion.objects.create(user_id=user.id)
#
#     server_time = ServerTimeHelper()
#     fixture_crawling_get.return_value = FakeResp()
#
#     bot = InitdataHelper()
#
#     ###########################################################################
#     # call function
#     bot.run(url='url', user=user, server_time=server_time, run_version=version)
#
#     ###########################################################################
#     # assert
#     user.refresh_from_db()
#     version.refresh_from_db()
#
#     # assert _parse_init_city_loop
#     assert version.population == population
#     # assert population
#     assert PlayerBuilding.objects.count() == num_buildings
#     assert PlayerDestination.objects.count() == num_destination
#
#
# @pytest.mark.django_db
# @pytest.mark.parametrize('filename', [
#     'gaolious_2022.12.30-2.json',  # legacy - ship 관련 정보.
# ])
# def test_utils_legacy_helper(multidb, filename, fixture_crawling_get, fixture_crawling_post):
#     class FakeResp(AbstractFakeResp):
#         text = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')
#
#     ###########################################################################
#     # prepare
#     user = User.objects.create_user(username='test', android_id='test')
#     version = RunVersion.objects.create(user_id=user.id)
#
#     server_time = ServerTimeHelper()
#     fixture_crawling_get.return_value = FakeResp()
#
#     bot = InitdataHelper()
#
#     ###########################################################################
#     # call function
#     bot.run(url='url', user=user, server_time=server_time, run_version=version)
#
#     ###########################################################################
#     # assert
#     user.refresh_from_db()
#     version.refresh_from_db()
#
# # player gift 관련
#
# @pytest.mark.django_db
# @pytest.mark.parametrize('filename', [
#     'gaolious_2023.01.09_gifts.json',  # legacy - ship 관련 정보.
# ])
# def test_utils_init_data_gifts(multidb, filename, fixture_crawling_get, fixture_crawling_post):
#     class FakeResp(AbstractFakeResp):
#         text = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')
#
#     ###########################################################################
#     # prepare
#     user = User.objects.create_user(username='test', android_id='test')
#     version = RunVersion.objects.create(user_id=user.id)
#
#     server_time = ServerTimeHelper()
#     fixture_crawling_get.return_value = FakeResp()
#
#     bot = InitdataHelper()
#
#     ###########################################################################
#     # call function
#     bot.run(url='url', user=user, server_time=server_time, run_version=version)
#
#     ###########################################################################
#     # assert
#     user.refresh_from_db()
#     version.refresh_from_db()
#     assert PlayerGift.objects.count() > 0
#
# @pytest.mark.django_db
# @pytest.mark.parametrize('filename', [
#     'gaolious_2023.01.09_contract.json',  # legacy - ship 관련 정보.
# ])
# def test_utils_init_data_contract(multidb, filename, fixture_crawling_get, fixture_crawling_post):
#     class FakeResp(AbstractFakeResp):
#         text = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')
#
#     ###########################################################################
#     # prepare
#     user = User.objects.create_user(username='test', android_id='test')
#     version = RunVersion.objects.create(user_id=user.id)
#
#     server_time = ServerTimeHelper()
#     fixture_crawling_get.return_value = FakeResp()
#
#     bot = InitdataHelper()
#
#     ###########################################################################
#     # call function
#     bot.run(url='url', user=user, server_time=server_time, run_version=version)
#
#     ###########################################################################
#     # assert
#     user.refresh_from_db()
#     version.refresh_from_db()
#
#
# @pytest.mark.django_db
# @pytest.mark.parametrize('filename', [
#     'gaolious_2023.01.11_jobs.json',  # legacy - ship 관련 정보.
# ])
# def test_utils_init_data_contract(multidb, filename, fixture_crawling_get, fixture_crawling_post):
#     class FakeResp(AbstractFakeResp):
#         text = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')
#
#     ###########################################################################
#     # prepare
#     user = User.objects.create_user(username='test', android_id='test')
#     version = RunVersion.objects.create(user_id=user.id)
#
#     server_time = ServerTimeHelper()
#     fixture_crawling_get.return_value = FakeResp()
#
#     bot = InitdataHelper()
#
#     ###########################################################################
#     # call function
#     bot.run(url='url', user=user, server_time=server_time, run_version=version)
#
#     ###########################################################################
#     # assert
#     user.refresh_from_db()
#     version.refresh_from_db()
#
#
# @pytest.mark.django_db
# @pytest.mark.parametrize('filename', [
#     'levelup.json',  # legacy - ship 관련 정보.
# ])
# def test_utils_init_data_levelup(multidb, filename, fixture_crawling_get, fixture_crawling_post):
#     class FakeResp(AbstractFakeResp):
#         text = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')
#
#     ###########################################################################
#     # prepare
#     user = User.objects.create_user(username='test', android_id='test')
#     version = RunVersion.objects.create(user_id=user.id)
#
#     server_time = ServerTimeHelper()
#     fixture_crawling_get.return_value = FakeResp()
#
#     bot = InitdataHelper()
#
#     ###########################################################################
#     # call function
#     bot.run(url='url', user=user, server_time=server_time, run_version=version)
#
#     ###########################################################################
#     # assert
#     user.refresh_from_db()
#     version.refresh_from_db()