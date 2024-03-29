from app_root.strategies.utils import Strategy
from app_root.users.models import User


def run(*args, **kwargs):
    for user in User.objects.all():
        if user.username not in args:
            continue
        if not user.is_active:
            continue
        if user.has_error:
            continue

        print(f"run for user : {user.username} - {user.android_id}")
        strategy = Strategy(user_id=user.id)
        strategy.run()
