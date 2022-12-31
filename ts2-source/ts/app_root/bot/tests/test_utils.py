from unittest import mock

import pytest
from django.conf import settings

from app_root.bot.utils_bot import Bot
from app_root.users.models import User

#
# @pytest.mark.django_db
# @pytest.mark.parametrize('filename', [
#     'gaolious1_2022.12.29.json',
# ])
# def test_steps(
#     multidb,
#     filename,
#     fixture_get_endpoints,
#     fixture_login_with_device_id,
#     fixture_login_with_remember_token,
#     fixture_get_init_data,
#     fixture_get_definition,
# ):
#     ###########################################################################
#     # prepare
#     user = User.objects.create_user(username='test', android_id='test')
#     fixture_get_endpoints.return_value = (settings.DJANGO_PATH / 'fixtures' / 'get_endpoints' / filename).read_text('utf-8')
#     fixture_login_with_device_id.return_value = (settings.DJANGO_PATH / 'fixtures' / 'login_with_device_id' / filename).read_text('utf-8')
#     fixture_login_with_remember_token.return_value = (settings.DJANGO_PATH / 'fixtures' / 'login_with_device_id' / filename).read_text('utf-8')
#     fixture_get_init_data.return_value = (settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')
#     fixture_get_definition.return_value = (settings.DJANGO_PATH / 'fixtures' / 'get_definition' / filename).read_text('utf-8')
#     bot = Bot(user.id)
#
#     ###########################################################################
#     # call function
#     bot.run_endpoints()
#
#     ###########################################################################
#     # assert
#     assert bot.time_offset
#     assert bot.endpoints
#     assert bot.init_data_urls
#
#     ###########################################################################
#     # call function
#     bot.run_login()
#
#     ###########################################################################
#     # assert
#     user.refresh_from_db()
#     assert user.player_id
#     assert user.game_access_token
#     assert user.authentication_token
#     assert user.remember_me_token
#     assert user.device_id
#     assert user.support_url
#
#
#     ###########################################################################
#     # call function
#     bot.load_init_data()
#
#     ###########################################################################
#     # assert
#
#
#     ###########################################################################
#     # call function
#     bot.load_init_data()
#
#     ###########################################################################
#     # assert
