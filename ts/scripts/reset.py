from app_root.servers.models import RunVersion
from app_root.users.models import User


def run(*args, **kwargs):
    for user in User.objects.all():
        if user.username not in args:
            continue
        if not user.is_active:
            continue
        if user.has_error:
            continue
        RunVersion.objects.create(user_id=user.id, level_id=1)