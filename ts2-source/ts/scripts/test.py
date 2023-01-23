from unittest import mock

from app_root.servers.models import RunVersion
from app_root.strategies.dumps import ts_dump
from app_root.users.models import User


def dump():
    for user in User.objects.all():
        print(f"[dump for user : {user.username} - {user.android_id}]")

        version = RunVersion.objects.filter(user_id=user.id).order_by('-pk').first()
        if not version:
            continue

        # with mock.patch('django.utils.timezone.now') as p:
        #     p.return_value = version.init_server_1
        ts_dump(version=version)


def run():
    dump()
