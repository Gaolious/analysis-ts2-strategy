import json
import subprocess
from pathlib import Path

from django.conf import settings

from app_root.players.models import PlayerJob, PlayerVisitedRegion
from app_root.players.utils_import import InitdataHelper
from app_root.servers.models import RunVersion, TSRegion
from core.utils import convert_number_as_int

projectId = 'trainstation-2-30223076'
apiKey = 'AIzaSyB_O_eamXZfqGmgHEksFKCpD4QEwciCBiM'
authDomain = f'{projectId}.firebaseapp.com'
databaseURL = f'https://{projectId}.firebaseio.com'
storageBucket = f'{projectId}.appspot.com'
appId = '1:389445276055:android:efbd60f62f7fb4bb'


def run_nodejs(version: RunVersion):
    config_path = version.get_account_path()

    node = Path('/usr/local/bin/node')
    node_path = Path('/usr/local/bin/node')
    if not node_path.exists():
        node_path = Path('/usr/bin/node')

    commands = [
        str(node_path),
        str(settings.SOURCE_PATH / 'ts-firestore' / 'dist' / 'index.js'),
        '--path={}'.format(config_path),
    ]
    cmd = ' '.join(commands)

    timeout = 30

    try:
        out = subprocess.check_output(
            cmd, shell=True, timeout=timeout
        )
    except subprocess.TimeoutExpired as e:
        print(str(e))
    except subprocess.CalledProcessError as e:
        stderr = "{}".format(e.stderr)[:500] if hasattr(e, 'stderr') else ''
        stdout = "{}".format(e.stdout)[:500] if hasattr(e, 'stdout') else ''
        output = "{}".format(e.output)[:500] if hasattr(e, 'output') else ''
        print(stderr, stdout, output)


def write_fireston_json(version: RunVersion):
    config = {
        'token': version.firebase_token,
        'guildId': version.guild_id,
        'firebaseConfig': {
            'apiKey': apiKey,
            'authDomain': authDomain,
            'projectId': projectId,
            'storageBucket': storageBucket,
            'databaseURL': databaseURL,
            'appId': appId,
        }
    }

    config_path = version.get_account_path()

    with open(config_path / 'firestore.json', 'wt') as fout:
        fout.write(json.dumps(config))


def read_fireston_json(version: RunVersion):
    config = {
        'token': version.firebase_token,
        'guildId': version.guild_id,
        'firebaseConfig': {
            'apiKey': apiKey,
            'authDomain': authDomain,
            'projectId': projectId,
            'storageBucket': storageBucket,
            'databaseURL': databaseURL,
            'appId': appId,
        }
    }

    config_path = version.get_account_path()
    jobs = config_path / 'guild_jobs.json'
    if jobs.exists():
        txt = jobs.read_text(encoding='utf-8')
        json_data = json.loads(txt, strict=False)

        bulk_list, _ = PlayerJob.create_instance(data=json_data, version_id=version.id)

        regions = list(TSRegion.objects.filter(content_category=1).order_by('level_from', 'ordering').all())
        regions_map = {
            r.id: idx for idx, r in enumerate(regions, 1)
        }
        max_region = 0
        for visited in PlayerVisitedRegion.objects.filter(version_id=version.id).all():
            max_region = max(max_region, regions_map.get(visited.region_id, 0))

        for instance in bulk_list:

            exists = PlayerJob.objects.filter(version_id=version.id, job_id=instance.job_id).first()
            if exists:
                continue

            instance : PlayerJob
            requirements = json.loads(instance.requirements)

            for idx, requirement in enumerate(requirements):
                _value = convert_number_as_int(requirement.get('Value'))
                _type = requirement.get('Type')

                if _type == 'relative_region':
                    _value = max_region + _value
                    requirements[idx]['Value'] = _value
                    requirements[idx]['Type'] = 'region'
            instance.requirements = json.dumps(requirements, separators=(',', ':')) if requirements else ''
            instance.save()
            print(f"added new guild job: {instance.job_id} / location id: {instance.job_location_id}")


def execute_firestore(version: RunVersion):

    if not version.guild_id:
        return

    write_fireston_json(version=version)

    run_nodejs(version=version, )

    read_fireston_json(version=version)