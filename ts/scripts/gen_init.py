from app_root.users.models import User
from core.utils import Logger


def run():
    init_data = [
        {"username": "gaolious1", "android_id": "fdc47e06bac1ab54"},
        {"username": "gaolious2", "android_id": "c01764740b8f2f49"},
        {"username": "gaolious", "android_id": "346c03d6d4042d74"},
    ]

    for row in init_data:
        username = row.get("username", "")
        android_id = row.get("android_id", "")

        if not username or not android_id:
            continue

        if User.objects.filter(username=username).exists():
            continue

        User.objects.create_user(**row)

        Logger.info(
            menu="gen_init",
            action="create user",
            username=username,
            android_id=android_id,
        )
