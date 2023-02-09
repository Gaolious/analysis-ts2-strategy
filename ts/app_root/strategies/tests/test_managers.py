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
from app_root.strategies.commands import ShopPurchaseItem
from app_root.strategies.dumps import ts_dump
from app_root.strategies.managers import jobs_find, trains_find_match_with_job, jobs_find_sources, trains_max_capacity, \
    jobs_find_priority, daily_offer_get_slots, materials_find_redundancy
from app_root.strategies.utils import Strategy
from app_root.users.models import User
from core.tests.factory import AbstractFakeResp
from core.utils import convert_datetime, hash10


class FakeRunCommand(object):
    commands: List
    version: RunVersion
    def __init__(self, version, commands):
        self.commands = commands
        self.version = version

    def run(self):
        for cmd in self.commands:
            cmd.post_processing({})


@pytest.fixture(scope='function')
def fixture_send_commands():
    with mock.patch('app_root.strategies.utils.RunCommand') as patch:
        patch.side_effect = FakeRunCommand
        yield patch

def prepare(initdata_filepath: Union[List[Path], Path]):
    user = User.objects.create_user(
        username='test', android_id='test', game_access_token='1', player_id='1'
    )
    version = RunVersion.objects.create(user_id=user.id, level_id=1)

    db_helper = SQLDefinitionHelper(version=version)
    instance = SQLDefinition.objects.create(
        version='206.013',
        checksum='077e2eff27bdd5cb079319c6d40f0916d9671b20',
        # url='https://cdn.trainstation2.com/client-resources/client-data-206.013.sqlite',
        # download_path=settings.DJANGO_PATH / 'fixtures' / '206.013.sqlite'
        url='https://cdn.trainstation2.com/client-resources/client-data-207.003.sqlite',
        download_path=settings.DJANGO_PATH / 'fixtures' / '207.003.sqlite'
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

        for job in jobs_find(version=version):
            materials = jobs_find_sources(version=version, job=job)

            assert materials


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


@pytest.mark.django_db
@pytest.mark.parametrize('init_filename', [
    'strategies/6/6_0.json',
    'init_data/gaolious1_2022.12.29.json',
    'init_data/gaolious_2022.12.30-1.json',
    'init_data/gaolious_2023.01.09_contract.json',
    'init_data/gaolious_2023.01.09_gifts.json',
    'init_data/gaolious_2023.01.11_jobs.json',
    'init_data/gaolious_2023.01.14_fulltest.json',
    'init_data/gaolious_2023.01.14_idle_destinations.json',
    'init_data/gaolious_2023.01.14_results.json',
])
def test_available_max_capacity(multidb, init_filename):
    ###########################################################################
    # prepare
    initdata_filepath = settings.DJANGO_PATH / 'fixtures' / init_filename

    version = prepare(initdata_filepath=initdata_filepath)

    txt = initdata_filepath.read_text(encoding='utf-8')
    json_data = json.loads(txt, strict=False)
    now = convert_datetime(json_data['Time'])

    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now

        ret = trains_max_capacity(version=version, region=1)
        assert len(ret) >= 1


@pytest.mark.django_db
@pytest.mark.parametrize('init_filename', [
    # 'strategies/6/6_0.json',
    'init_data/gaolious1_2022.12.29.json',
    # 'init_data/gaolious_2022.12.30-1.json',
    # 'init_data/gaolious_2023.01.09_contract.json',
    # 'init_data/gaolious_2023.01.09_gifts.json',
    # 'init_data/gaolious_2023.01.11_jobs.json',
    # 'init_data/gaolious_2023.01.14_fulltest.json',
    # 'init_data/gaolious_2023.01.14_idle_destinations.json',
    # 'init_data/gaolious_2023.01.14_results.json',
    # 'init_data/gaolious_2023.02.05.json',
    # 'init_data/gaolious_2023.02.07.json',
])
def test_shop_purchase_item(multidb, init_filename, fixture_send_commands):
    ###########################################################################
    # prepare
    initdata_filepath = settings.DJANGO_PATH / 'fixtures' / init_filename

    version = prepare(initdata_filepath=initdata_filepath)

    txt = initdata_filepath.read_text(encoding='utf-8')
    json_data = json.loads(txt, strict=False)
    now = convert_datetime(json_data['Time'])

    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now
        cnt1, cnt2 = 0, 0
        daily_offer_items = daily_offer_get_slots(
            version=version,
            available_video=True,
            availble_gem=False,
            available_gold=False,
        )
        for offer_item in daily_offer_items:
            cmd = ShopPurchaseItem(version=version, offer_item=offer_item)
            cmd.post_processing({})
            cnt1 += 1

        daily_offer_items = daily_offer_get_slots(
            version=version,
            available_video=True,
            availble_gem=False,
            available_gold=False,
        )
        for offer_item in daily_offer_items:
            cmd = ShopPurchaseItem(version=version, offer_item=offer_item)
            cmd.post_processing({})
            cnt2 += 1

        assert cnt1 >= 0
        assert cnt2 == 0


@pytest.mark.django_db
@pytest.mark.parametrize('init_filename', [
    # 'strategies/6/6_0.json',
    # 'init_data/gaolious1_2022.12.29.json',
    # 'init_data/gaolious_2022.12.30-1.json',
    # 'init_data/gaolious_2023.01.09_contract.json',
    # 'init_data/gaolious_2023.01.09_gifts.json',
    # 'init_data/gaolious_2023.01.11_jobs.json',
    # 'init_data/gaolious_2023.01.14_fulltest.json',
    # 'init_data/gaolious_2023.01.14_idle_destinations.json',
    # 'init_data/gaolious_2023.01.14_results.json',
    # 'init_data/gaolious_2023.02.05.json',
    'init_data/gaolious_2023.02.07.json',
])
def test_job_prioirty(multidb, init_filename):
    ###########################################################################
    # prepare
    initdata_filepath = settings.DJANGO_PATH / 'fixtures' / init_filename

    version = prepare(initdata_filepath=initdata_filepath)

    txt = initdata_filepath.read_text(encoding='utf-8')
    json_data = json.loads(txt, strict=False)
    now = convert_datetime(json_data['Time'])

    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now
        jobs_find_priority(version=version)



@pytest.mark.django_db
@pytest.mark.parametrize('init_filename', [
    # 'strategies/6/6_0.json',
    # 'init_data/gaolious1_2022.12.29.json',
    # 'init_data/gaolious_2022.12.30-1.json',
    # 'init_data/gaolious_2023.01.09_contract.json',
    # 'init_data/gaolious_2023.01.09_gifts.json',
    # 'init_data/gaolious_2023.01.11_jobs.json',
    # 'init_data/gaolious_2023.01.14_fulltest.json',
    # 'init_data/gaolious_2023.01.14_idle_destinations.json',
    # 'init_data/gaolious_2023.01.14_results.json',
    # 'init_data/gaolious_2023.02.05.json',
    'init_data/gaolious_2023.02.07.json',
])
def test_materials_find_redundancy(multidb, init_filename):
    ###########################################################################
    # prepare
    initdata_filepath = settings.DJANGO_PATH / 'fixtures' / init_filename

    version = prepare(initdata_filepath=initdata_filepath)

    txt = initdata_filepath.read_text(encoding='utf-8')
    json_data = json.loads(txt, strict=False)
    now = convert_datetime(json_data['Time'])

    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now
