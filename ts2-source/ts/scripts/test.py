from app_root.bot.utils import Bot


def run():
    bot = Bot(user_id=1)
    bot.start_version()

    bot.run_endpoints()
    bot.run_login()
    bot.run_definition()
    bot.run_init_data()

