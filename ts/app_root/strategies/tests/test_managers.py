import json
from pathlib import Path
from typing import Union, List
from unittest import mock

import pytest
from django.conf import settings

from app_root.players.models import PlayerShipOffer
from app_root.players.utils_import import InitdataHelper
from app_root.servers.models import RunVersion, SQLDefinition, EndPoint
from app_root.servers.utils_import import SQLDefinitionHelper
from app_root.strategies.dumps import ts_dump
from app_root.strategies.managers import jobs_find, trains_find_match_with_job, find_job_sources
from app_root.strategies.utils import Strategy
from app_root.users.models import User
from core.tests.factory import AbstractFakeResp
from core.utils import convert_datetime, hash10


def prepare(initdata_filepath: Union[List[Path], Path]):
    user = User.objects.create_user(
        username='test', android_id='test', game_access_token='1', player_id='1'
    )
    version = RunVersion.objects.create(user_id=user.id, level_id=1)

    db_helper = SQLDefinitionHelper(version=version)
    instance = SQLDefinition.objects.create(
        version='206.013',
        checksum='077e2eff27bdd5cb079319c6d40f0916d9671b20',
        url='https://cdn.trainstation2.com/client-resources/client-data-206.013.sqlite',
        download_path=settings.DJANGO_PATH / 'fixtures' / '206.013.sqlite'
    )
    db_helper.read_sqlite(instance=instance)

    init_helper = InitdataHelper(version=version)
    if not isinstance(initdata_filepath, list):
        initdata_filepath = [initdata_filepath]

    for filepath in initdata_filepath:
        init_helper.parse_data(
            data=filepath.read_text(encoding='UTF-8')
        )

    EndPoint.objects.create(name=EndPoint.ENDPOINT_COMMAND_PROCESSING, name_hash=hash10(EndPoint.ENDPOINT_COMMAND_PROCESSING), url='a')

    return version


@pytest.mark.django_db
@pytest.mark.parametrize('init_filenames', [
    [
        'init_data/gaolious_2022.12.30-1.json',
        'init_data/gaolious_2022.12.30-2.json',
    ]
])
def test_ship_offer(multidb, init_filenames):
    ###########################################################################
    # prepare
    paths = [
        settings.DJANGO_PATH / 'fixtures' / path for path in init_filenames
    ]
    version = prepare(initdata_filepath=paths)

    assert version
    assert version.guild_id
    assert PlayerShipOffer.objects.count() == 1



@pytest.mark.django_db
@pytest.mark.parametrize('init_filenames', [
    [
        'strategies/contract_check/2_2.json',
        'strategies/contract_check/2_3.json',
    ]
])
def test_strategy(multidb, init_filenames):
    ###########################################################################
    # prepare
    class FakeResp(AbstractFakeResp):
        text = """{"Success":true,"RequestId":"0a645537-2b6d-4c99-81ef-d968877ca303","Time":"2023-01-23T12:43:06Z","Data":{"CollectionId":1,"Commands":[]}}"""

    paths = [
        settings.DJANGO_PATH / 'fixtures' / path for path in init_filenames
    ]
    version = prepare(initdata_filepath=paths)

    txt = paths[-1].read_text(encoding='utf-8')
    json_data = json.loads(txt, strict=False)
    now = convert_datetime(json_data['Time'])

    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now
        ts_dump(version=version)

        with mock.patch('app_root.mixins.CrawlingHelper.post') as post:
            post.side_effect = FakeResp
            strategy = Strategy(user_id=version.user_id)
            strategy.run()


@pytest.mark.django_db
@pytest.mark.parametrize('init_filename, event_count, union_count, story_count, side_count', [
    ('strategies/6/6_0.json', 0,  0, 3, 0),
    ('init_data/gaolious1_2022.12.29.json', 0,  0, 4, 0),
    ('init_data/gaolious_2022.12.30-1.json', 3, 4, 6, 5),
    ('init_data/gaolious_2023.01.09_contract.json', 0, 4, 4, 5),
    ('init_data/gaolious_2023.01.09_gifts.json', 0, 3, 4, 5),
    ('init_data/gaolious_2023.01.11_jobs.json', 3, 3, 4, 5),
    ('init_data/gaolious_2023.01.14_fulltest.json', 3, 4, 4, 5),
    ('init_data/gaolious_2023.01.14_idle_destinations.json', 3, 4, 4, 5),
    ('init_data/gaolious_2023.01.14_results.json', 3, 4, 4, 5),
    ('init_data/gaolious_2023.01.11_jobs.json', 3, 3, 4, 5),
])
def test_prepare_material(multidb, init_filename, event_count, union_count, story_count, side_count):
    ###########################################################################
    # prepare
    initdata_filepath = settings.DJANGO_PATH / 'fixtures' / init_filename

    version = prepare(initdata_filepath=initdata_filepath)

    jobs = list(jobs_find(version, event_jobs=True))
    assert len(jobs) == event_count, "event only"
    for job in jobs:
        trains = list(trains_find_match_with_job(version=version, job=job))
        assert trains

    jobs = list(jobs_find(version, union_jobs=True))
    assert len(jobs) == union_count, "union only"
    for job in jobs:
        trains = list(trains_find_match_with_job(version=version, job=job))
        assert trains

    jobs = list(jobs_find(version, story_jobs=True))
    assert len(jobs) == story_count, "story only"
    for job in jobs:
        trains = list(trains_find_match_with_job(version=version, job=job))
        assert trains

    jobs = list(jobs_find(version, side_jobs=True))
    assert len(jobs) == side_count, "side only"
    for job in jobs:
        trains = list(trains_find_match_with_job(version=version, job=job))
        assert trains


@pytest.mark.django_db
@pytest.mark.parametrize('init_filename, event_count, union_count, story_count, side_count', [
    ('strategies/6/6_0.json', 0,  0, 3, 0),
    ('init_data/gaolious1_2022.12.29.json', 0,  0, 4, 0),
    ('init_data/gaolious_2022.12.30-1.json', 3, 4, 6, 5),
    ('init_data/gaolious_2023.01.09_contract.json', 0, 4, 4, 5),
    ('init_data/gaolious_2023.01.09_gifts.json', 0, 3, 4, 5),
    ('init_data/gaolious_2023.01.11_jobs.json', 3, 3, 4, 5),
    ('init_data/gaolious_2023.01.14_fulltest.json', 3, 4, 4, 5),
    ('init_data/gaolious_2023.01.14_idle_destinations.json', 3, 4, 4, 5),
    ('init_data/gaolious_2023.01.14_results.json', 3, 4, 4, 5),
])
def test_find_job_materials(multidb, init_filename, event_count, union_count, story_count, side_count):
    ###########################################################################
    # prepare

    initdata_filepath = settings.DJANGO_PATH / 'fixtures' / init_filename

    version = prepare(initdata_filepath=initdata_filepath)

    txt = initdata_filepath.read_text(encoding='utf-8')
    json_data = json.loads(txt, strict=False)
    now = convert_datetime(json_data['Time'])

    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now

        jobs = list(jobs_find(version=version))

        materials = find_job_sources(version=version, jobs=jobs)

        assert materials
        assert len(materials) == len(jobs)
        for job_pk, possible_sources in materials.items():
            assert possible_sources, f"for job pk = {job_pk}"

@pytest.mark.django_db
@pytest.mark.parametrize('init_filename, event_count, union_count, story_count, side_count', [
    ('strategies/6/6_0.json', 0,  0, 3, 0),
    ('init_data/gaolious1_2022.12.29.json', 0,  0, 4, 0),
    ('init_data/gaolious_2022.12.30-1.json', 3, 4, 6, 5),
    ('init_data/gaolious_2023.01.09_contract.json', 0, 4, 4, 5),
    ('init_data/gaolious_2023.01.09_gifts.json', 0, 3, 4, 5),
    ('init_data/gaolious_2023.01.11_jobs.json', 3, 3, 4, 5),
    ('init_data/gaolious_2023.01.14_fulltest.json', 3, 4, 4, 5),
    ('init_data/gaolious_2023.01.14_idle_destinations.json', 3, 4, 4, 5),
    ('init_data/gaolious_2023.01.14_results.json', 3, 4, 4, 5),
])
def test_dump(multidb, init_filename, event_count, union_count, story_count, side_count):
    ###########################################################################
    # prepare
    initdata_filepath = settings.DJANGO_PATH / 'fixtures' / init_filename

    version = prepare(initdata_filepath=initdata_filepath)

    txt = initdata_filepath.read_text(encoding='utf-8')
    json_data = json.loads(txt, strict=False)
    now = convert_datetime(json_data['Time'])

    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now

        ts_dump(version=version)