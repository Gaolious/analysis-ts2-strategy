from app_root.servers.models import RunVersion
from app_root.users.models import User


def run(*args, **kwargs):
    for user in User.objects.all():
        if user.username not in args:
            continue
        user.is_active = False
        user.has_error = True
        user.save()
