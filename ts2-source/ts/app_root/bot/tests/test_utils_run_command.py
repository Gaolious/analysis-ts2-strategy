import json
from unittest import mock

import pytest
from django.conf import settings
from django.utils import timezone

from app_root.bot.models import RunVersion, Location, Definition
from app_root.bot.utils_definition import DefinitionHelper
from app_root.bot.utils_init_data import InitdataHelper
from app_root.bot.utils_run_command import CommandHelper
from app_root.bot.utils_server_time import ServerTimeHelper
from app_root.users.models import User
from core.tests.factory import AbstractFakeResp
from core.utils import convert_datetime


@pytest.fixture(scope='function')
def fixture_crawling_get():
    with mock.patch('app_root.bot.utils_run_command.CrawlingHelper.get') as p:
        yield p

        
@pytest.fixture(scope='function')
def fixture_crawling_post():
    with mock.patch('app_root.bot.utils_run_command.CrawlingHelper.post') as p:
        yield p


@pytest.mark.django_db
@pytest.mark.parametrize('filename', [
    'gaolious_2023.01.11_jobs.json',  # 기차에 싣고 온 데이터 존재.
])
def test_utils_collect_from_train_command(multidb, filename, fixture_crawling_get):
    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')

    ###########################################################################
    # prepare
    now = timezone.now()
    user = User.objects.create_user(username='test', android_id='test')
    version = RunVersion.objects.create(user_id=user.id)

    helper = DefinitionHelper()
    helper.instance = Definition.objects.create(
        version='206.013',
        checksum='077e2eff27bdd5cb079319c6d40f0916d9671b20',
        url='https://cdn.trainstation2.com/client-resources/client-data-206.013.sqlite',
        download_path=settings.DJANGO_PATH / 'fixtures' / '206.013.sqlite'
    )
    helper.read_sqlite()
    fixture_crawling_get.return_value = FakeResp()

    server_time = ServerTimeHelper()

    bot = InitdataHelper()
    bot.run(url='url', user=user, server_time=server_time, run_version=version)
    helper = CommandHelper(
        run_version=version,
        url='',
        user=user,
        server_time=server_time
    )

    ###########################################################################
    # call function
    command = helper._command_collect_from_train()

    ###########################################################################
    # assert
    assert command
    for cmd in command:
        assert cmd.COMMAND == 'Train:Unload'

    user.refresh_from_db()
    version.refresh_from_db()


@pytest.mark.django_db
@pytest.mark.parametrize('filename', [
    'gaolious_2023.01.09_gifts.json',  # gift 존재
])
def test_utils_collect_from_gift(multidb, filename, fixture_crawling_get):
    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')
    ###########################################################################
    # prepare
    now = timezone.now()
    user = User.objects.create_user(username='test', android_id='test')
    version = RunVersion.objects.create(user_id=user.id)

    helper = DefinitionHelper()
    helper.instance = Definition.objects.create(
        version='206.013',
        checksum='077e2eff27bdd5cb079319c6d40f0916d9671b20',
        url='https://cdn.trainstation2.com/client-resources/client-data-206.013.sqlite',
        download_path=settings.DJANGO_PATH / 'fixtures' / '206.013.sqlite'
    )
    helper.read_sqlite()
    fixture_crawling_get.return_value = FakeResp()

    server_time = ServerTimeHelper()

    bot = InitdataHelper()
    bot.run(url='url', user=user, server_time=server_time, run_version=version)
    helper = CommandHelper(
        run_version=version,
        url='',
        user=user,
        server_time=server_time
    )

    ###########################################################################
    # call function
    command = helper._command_collect_from_gift()

    ###########################################################################
    # assert
    assert command
    for cmd in command:
        assert cmd.COMMAND == 'Gift:Claim'
        assert cmd.str_time
        assert cmd.job_id
    user.refresh_from_db()
    version.refresh_from_db()


@pytest.mark.django_db
@pytest.mark.parametrize('filename', [
    'gaolious_2022.12.30-2.json',  # working dispatchers == 0
])
def test_utils_send_train_destination(multidb, filename, fixture_crawling_get):
    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')

    ###########################################################################
    # prepare
    now = timezone.now()
    user = User.objects.create_user(username='test', android_id='test')
    version = RunVersion.objects.create(user_id=user.id)

    helper = DefinitionHelper()
    helper.instance = Definition.objects.create(
        version='206.013',
        checksum='077e2eff27bdd5cb079319c6d40f0916d9671b20',
        url='https://cdn.trainstation2.com/client-resources/client-data-206.013.sqlite',
        download_path=settings.DJANGO_PATH / 'fixtures' / '206.013.sqlite'
    )
    helper.read_sqlite()
    fixture_crawling_get.return_value = FakeResp()

    server_time = ServerTimeHelper()

    bot = InitdataHelper()
    bot.run(url='url', user=user, server_time=server_time, run_version=version)
    helper = CommandHelper(
        run_version=version,
        url='',
        user=user,
        server_time=server_time
    )
    ###########################################################################
    # call function
    command = helper.command_send_train_to_destination()

    ###########################################################################
    # assert
    assert helper.number_of_working_dispatchers == 0
    # for cmd in command:
    #     assert cmd.COMMAND == 'Gift:Claim'
    #     assert cmd.str_time
    #     assert cmd.job_id
    user.refresh_from_db()
    version.refresh_from_db()

@pytest.mark.django_db
@pytest.mark.parametrize('filename', [
    'gaolious_2023.01.14_fulltest.json',
])
def test_utils_send_train_destination_idle_destination(multidb, filename, fixture_crawling_get):
    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')

    ###########################################################################
    # prepare
    user = User.objects.create_user(username='test', android_id='test')
    version = RunVersion.objects.create(user_id=user.id)

    helper = DefinitionHelper()
    helper.instance = Definition.objects.create(
        version='206.013',
        checksum='077e2eff27bdd5cb079319c6d40f0916d9671b20',
        url='https://cdn.trainstation2.com/client-resources/client-data-206.013.sqlite',
        download_path=settings.DJANGO_PATH / 'fixtures' / '206.013.sqlite'
    )
    helper.read_sqlite()

    fake = FakeResp()
    fixture_crawling_get.return_value = fake

    now = convert_datetime(fake.json()['Time'])
    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now
        server_time = ServerTimeHelper()

        bot = InitdataHelper()
        bot.run(url='url', user=user, server_time=server_time, run_version=version)

        helper = CommandHelper(
            run_version=version,
            url='',
            user=user,
            server_time=server_time
        )
        ###########################################################################
        # call function
        command = list(helper.command_send_train_to_destination())

    ###########################################################################
    # assert
    assert helper.number_of_working_dispatchers == 0
    for cmd in command:
        assert cmd.COMMAND == 'Train:DispatchToDestination'
    user.refresh_from_db()
    version.refresh_from_db()


@pytest.mark.django_db
@pytest.mark.parametrize('filename', [
    # 'gaolious_2023.01.14_fulltest.json',
    'gaolious_2023.01.11_jobs.json',
])
def test_utils_prepare_materials(multidb, filename, fixture_crawling_get):
    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')

    ###########################################################################
    # prepare
    user = User.objects.create_user(username='test', android_id='test')
    version = RunVersion.objects.create(user_id=user.id)

    helper = DefinitionHelper()
    helper.instance = Definition.objects.create(
        version='206.013',
        checksum='077e2eff27bdd5cb079319c6d40f0916d9671b20',
        url='https://cdn.trainstation2.com/client-resources/client-data-206.013.sqlite',
        download_path=settings.DJANGO_PATH / 'fixtures' / '206.013.sqlite'
    )
    helper.read_sqlite()

    fake = FakeResp()
    fixture_crawling_get.return_value = fake

    now = convert_datetime(fake.json()['Time'])
    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now
        server_time = ServerTimeHelper()

        bot = InitdataHelper()
        bot.run(url='url', user=user, server_time=server_time, run_version=version)

        helper = CommandHelper(
            run_version=version,
            url='',
            user=user,
            server_time=server_time
        )
        ###########################################################################
        # call function
        command = list(helper.command_prepare_materials())

    ###########################################################################
    # assert
    assert helper.number_of_working_dispatchers == 0
    for cmd in command:
        assert cmd.COMMAND == 'Train:DispatchToDestination'

    user.refresh_from_db()
    version.refresh_from_db()



@pytest.mark.django_db
@pytest.mark.parametrize('filename', [
    # 'gaolious_2023.01.14_fulltest.json',
    'gaolious_2023.01.11_jobs.json',
])
def test_utils_run_command(multidb, filename, fixture_crawling_get, fixture_crawling_post):
    class FakeResp(AbstractFakeResp):
        text = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')

    class FakeResp2(AbstractFakeResp):
        text = """{"Success":true,"RequestId":"b496033d-84d2-4861-b263-58c7166c0da1","Time":"2023-01-12T02:58:32Z"}"""

    ###########################################################################
    # prepare
    user = User.objects.create_user(username='test', android_id='test')
    version = RunVersion.objects.create(user_id=user.id)

    helper = DefinitionHelper()
    helper.instance = Definition.objects.create(
        version='206.013',
        checksum='077e2eff27bdd5cb079319c6d40f0916d9671b20',
        url='https://cdn.trainstation2.com/client-resources/client-data-206.013.sqlite',
        download_path=settings.DJANGO_PATH / 'fixtures' / '206.013.sqlite'
    )
    helper.read_sqlite()

    fake = FakeResp()
    fixture_crawling_get.return_value = fake
    fixture_crawling_post.return_value = FakeResp2()

    now = convert_datetime(fake.json()['Time'])
    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now
        server_time = ServerTimeHelper()

        bot = InitdataHelper()
        bot.run(url='url', user=user, server_time=server_time, run_version=version)

        helper = CommandHelper(
            run_version=version,
            url='',
            user=user,
            server_time=server_time
        )
        ###########################################################################
        # call function
        helper.run()

    ###########################################################################
    # assert

    user.refresh_from_db()
    version.refresh_from_db()