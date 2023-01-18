from unittest import mock

import pytest
from django.conf import settings

from app_root.bots.models import RunVersion, DbDefinition
from app_root.bots.utils_definition import DefinitionHelper
from app_root.bots.utils_init_data import InitdataHelper
from app_root.bots.utils_server_time import ServerTimeHelper
from app_root.users.models import User
from core.tests.factory import AbstractFakeResp
from core.utils import convert_datetime


@pytest.fixture(scope='function')
def fixture_basis():
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

    # yield load_data
    #     helper = CommandHelper(
    #         run_version=version,
    #         url='',
    #         user=user,
    #         server_time=server_time
    #     )
    #     ###########################################################################
    #     # call function
    #     command = list(helper.command_send_train_to_destination())