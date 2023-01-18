from django.utils import timezone

from app_root.bots.utils_bot import Bot
from app_root.users.models import User


def run():
    now = timezone.now()
    for user in User.objects.all():
        if not user.is_active:
            continue
        if user.has_error:
            continue
        if user.next_event and user.next_event >= now:
            continue

        print(f"run for user : {user.android_id}")
        bot = Bot(user_id=user.id)
        bot.start_version()

        bot.run_endpoints()
        bot.run_login()
        bot.run_definition()
        bot.run_init_data()
        bot.run_leader_board_status()
        bot.run_command()

