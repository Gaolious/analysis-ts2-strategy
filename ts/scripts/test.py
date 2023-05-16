from unittest import mock

from app_root.servers.models import RunVersion
from app_root.strategies.dumps import ts_dump
from app_root.strategies.firestore import execute_firestore
from app_root.users.models import User


def dump(version_id: int = None):
    for user in User.objects.all():
        print(f"[dump for user : {user.username} - {user.android_id}]")
        queryset = RunVersion.objects.filter(user_id=user.id).order_by("-pk")
        if version_id:
            queryset = queryset.filter(id=version_id)
        version = queryset.first()
        if not version:
            continue

        with mock.patch("django.utils.timezone.now") as p:
            p.return_value = version.now
            ts_dump(version=version)


def run():
    # dump(13)
    rv = RunVersion.objects.filter(id=121).first()
    execute_firestore(rv)
    """
25/23/gaolious1/22.log

25/23/gaolious1/31.log
25/23/gaolious/15.log
25/23/gaolious2/25.log
25/23/gaolious2/52.log
25/23/gaolious/27.log
25/23/gaolious/56.log
26/00/gaolious/11.log
26/00/gaolious1/46.log
26/00/gaolious2/20.log
26/01/gaolious1/37.log
26/01/gaolious1/54.log
26/01/gaolious2/15.log
26/01/gaolious/28.log
26/02/gaolious1/22.log
26/02/gaolious/13.log
26/02/gaolious2/12.log
26/02/gaolious2/26.log
26/02/gaolious/24.log
26/02/gaolious/42.log    
    """
