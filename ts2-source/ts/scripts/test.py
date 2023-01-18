from app_root.bots.models import RunVersion, DbDefinition
from app_root.bots.utils_definition import DefinitionHelper
from app_root.bots.utils_dump import RunVersionDump
from app_root.users.models import User

def dump():
    for user in User.objects.all():
        print(f"dump for user : {user.username} - {user.android_id}")

        version = RunVersion.objects.filter(user_id=user.id).order_by('-pk').first()
        if version:
            dumper = RunVersionDump(run_version_id=version.id)
            dumper.dump()

def test_run_command():
    for user in User.objects.all():
        print(f"run command for user : {user.username} - {user.android_id}")

        version = RunVersion.objects.filter(user_id=user.id).order_by('-pk').first()
        # CollectFromTrainCommandHelper(1)

def run():
    # dump()
    helper = DefinitionHelper()
    helper.instance = DbDefinition.objects.order_by('-pk').first()
    helper.read_sqlite()