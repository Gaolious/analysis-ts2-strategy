from app_root.users.models import User
from core.utils import Logger


def run():
    init_data = [
        {'username': 'gaolious1', 'android_id': '57316822b8f2aa50'},
    ]

    for row in init_data:
        username = row.get('username', '')
        android_id = row.get('android_id', '')

        if not username or not android_id:
            continue

        if User.objects.filter(username=username).exists():
            continue

        User.objects.create_user(username=username, android_id=android_id)

        Logger.info(menu='gen_init', action='create user', username=username, android_id=android_id)