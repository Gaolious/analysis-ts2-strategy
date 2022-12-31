from app_root.bot.utils_bot import Bot
from app_root.users.models import User


def run():
    for user in User.objects.all():
        print(f"run for user : {user.android_id}")
        bot = Bot(user_id=user.id)
        bot.start_version()

        bot.run_endpoints()
        bot.run_login()
        bot.run_definition()
        bot.run_init_data()
