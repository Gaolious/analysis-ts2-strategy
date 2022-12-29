from app_root.bot.utils import Bot


def run():
    bot = Bot(user_id=1)
    end_points = bot.run_endpoints()
    login = bot.run_login()
    bot.load_init_data()

