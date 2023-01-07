from app_root.bot.models import RunVersion
from app_root.bot.utils_dump import RunVersionDump
from app_root.users.models import User

def dump():
    for user in User.objects.all():
        print(f"dump for user : {user.username} - {user.android_id}")

        version = RunVersion.objects.filter(user_id=user.id).order_by('-pk').first()
        if version:
            dumper = RunVersionDump(run_version_id=version.id)
            dumper.dump()


def run():
    dump()