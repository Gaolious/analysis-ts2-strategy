# from unittest import mock
#
# import pytest
# from django.conf import settings
#
# from app_root.players.models import RunVersion, PlayerBuilding, PlayerDestination, PlayerGift
# from app_root.bots.utils_init_data import InitdataHelper
# from app_root.bots.utils_server_time import ServerTimeHelper
# from app_root.users.models import User
# from core.tests.factory import AbstractFakeResp
#
#
# @pytest.fixture(scope='function')
# def fixture_crawling_get():
#     with mock.patch('app_root.bot.utils_init_data.CrawlingHelper.get') as p:
#         yield p
#
#
# @pytest.fixture(scope='function')
# def fixture_crawling_post():
#     with mock.patch('app_root.bot.utils_init_data.CrawlingHelper.post') as p:
#         yield p
#
#
# @pytest.mark.django_db
# @pytest.mark.parametrize('filename, population, num_buildings, num_destination', [
#     (
#             'gaolious1_2022.12.29.json',
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