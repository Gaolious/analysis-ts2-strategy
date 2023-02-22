import json
import shutil
from pathlib import Path
from typing import Union, List
from unittest import mock

import pytest
from django.conf import settings
from django.utils import timezone

from app_root.players.models import PlayerShipOffer, PlayerFactory, PlayerFactoryProductOrder
from app_root.players.utils_import import InitdataHelper
from app_root.servers.models import RunVersion, SQLDefinition, EndPoint, TSProduct
from app_root.servers.utils_import import SQLDefinitionHelper
from app_root.strategies.commands import ShopPurchaseItem
from app_root.strategies.dumps import ts_dump, ts_dump_factory
from app_root.strategies.managers import jobs_find, trains_find_match_with_job, trains_max_capacity, \
    jobs_find_union_priority, daily_offer_get_slots, factory_order_product, factory_collect_product
from app_root.strategies.utils import Strategy
from app_root.users.models import User
from app_root.utils import get_curr_server_str_datetime_s
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

        # for job in jobs_find(version=version):
        #     materials = jobs_find_sources(version=version, job=job)
        #
        #     assert materials


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
        jobs_find_union_priority(version=version)


def convert_text(txt: str):
    data = json.loads(txt, strict=False)
    t = timezone.now().isoformat(sep='T', timespec='seconds').replace('+00:00', 'Z')
    data.update({
        'Time': t
    })

    return json.dumps(data, separators=(',', ':'))


@pytest.fixture(scope='function')
def fixture_endpoint():
    with mock.patch('app_root.strategies.utils.EndpointHelper.get') as patch:
        patch.return_value = convert_text(
            (settings.DJANGO_PATH / 'fixtures' / 'endpoints' / 'gaolious1_2022.12.29.json').read_text('utf-8')
        )
        yield patch


@pytest.fixture(scope='function')
def fixture_login():
    with mock.patch('app_root.strategies.utils.LoginHelper.post') as patch:
        patch.return_value = convert_text(
            (settings.DJANGO_PATH / 'fixtures' / 'login' / 'gaolious1_2022.12.29_with_device_id.json').read_text('utf-8')
        )
        yield patch


@pytest.fixture(scope='function')
def fixture_definition():

    sqllite_filepath = settings.DJANGO_PATH / 'fixtures' / '207.004.sqlite'

    def FakeDownload(instance, *args, **kwargs):
        download_filename = Path(instance.download_path)
        shutil.copy(sqllite_filepath, download_filename)
        return 1_000_000

    with mock.patch('app_root.strategies.utils.SQLDefinitionHelper.get') as patch:
        patch.return_value = convert_text(
            (settings.DJANGO_PATH / 'fixtures' / 'definition' / 'gaolious1_2022.12.29.json').read_text('utf-8')
        )

        with mock.patch('app_root.strategies.utils.SQLDefinitionHelper.download_data') as dn:
            dn.side_effect = FakeDownload
            yield dn

@pytest.fixture(scope='function')
def fixture_init_20230207():
    filename = 'gaolious_2023.02.07.json'
    with mock.patch('app_root.strategies.utils.InitdataHelper.get') as patch:
        patch.side_effect = [
            convert_text((settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')),
            '{}',
        ]
        yield patch

@pytest.fixture(scope='function')
def fixture_init_20230210():
    filename = 'gaolious_2023.02.10.json'
    with mock.patch('app_root.strategies.utils.InitdataHelper.get') as patch:
        patch.side_effect = [
            convert_text((settings.DJANGO_PATH / 'fixtures' / 'init_data' / filename).read_text('utf-8')),
            '{}',
        ]
        yield patch


@pytest.fixture(scope='function')
def fixture_leader_board():
    with mock.patch('app_root.strategies.utils.LeaderboardHelper.run') as patch:
        yield patch


@pytest.fixture(scope='function')
def fixture_start_game():
    with mock.patch('app_root.strategies.utils.StartGame.run') as patch:
        yield patch


class FakeRunCommand(object):
    commands: List
    version: RunVersion
    def __init__(self, version, commands):
        self.commands = commands
        self.version = version

    def run(self):
        for cmd in self.commands:
            print(f"* FakeCmd : {cmd.COMMAND} {cmd.get_parameters()}")
            cmd.post_processing({})


@pytest.fixture(scope='function')
def fixture_send_commands():
    with mock.patch('app_root.strategies.commands.RunCommand') as patch:
        patch.side_effect = FakeRunCommand
        yield patch


@pytest.fixture(scope='function')
def fixture_sleep():
    with mock.patch('app_root.strategies.commands.sleep') as patch:
        yield patch


@pytest.fixture(scope='function')
def fixture_use_cache():
    with mock.patch('app_root.strategies.utils.USE_CACHE', True) as patch:
        yield patch

@pytest.mark.django_db
@pytest.mark.parametrize('user_name, run_version_id', [
    ('gaolious', 13)
])
def test_materials_find_redundancy(
        multidb,
        user_name, run_version_id,
        fixture_send_commands, fixture_sleep, fixture_use_cache,
):
    ###########################################################################
    # prepare
    user = User.objects.create_user(
        username=user_name, android_id='test', game_access_token='1', player_id='1'
    )
    version = RunVersion.objects.create(id=run_version_id, user_id=user.id, level_id=1)
    initdata_filepath = version.get_account_path() / 'startgame_post.txt'
    txt = initdata_filepath.read_text(encoding='utf-8')
    json_data = json.loads(txt, strict=False)
    now = convert_datetime(json_data['Time'])

    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now
        s = Strategy(user.id)
        s.run()


@pytest.mark.django_db
@pytest.mark.parametrize('user_name, run_version_id', [
    ('gaolious1', 3),
    # ('gaolious', 34),  # 가능 상태
])
def test_prepare_contract(
        multidb,
        user_name, run_version_id,
        fixture_send_commands, fixture_sleep, fixture_use_cache,
):
    ###########################################################################
    # prepare
    user = User.objects.create_user(
        username=user_name, android_id='test', game_access_token='1', player_id='1'
    )
    version = RunVersion.objects.create(id=run_version_id, user_id=user.id, level_id=1)
    initdata_filepath = version.get_account_path() / 'startgame_post.txt'
    txt = initdata_filepath.read_text(encoding='utf-8')
    json_data = json.loads(txt, strict=False)
    now = convert_datetime(json_data['Time'])
    version.now = now
    version.save()

    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now
        s = Strategy(user.id)
        s.run()



@pytest.mark.django_db
@pytest.mark.parametrize('user_name, run_version_id', [
    ('gaolious1', 2),  # 약 1분정도 남은 상태.
    # ('gaolious', 34),  # 가능 상태
])
def test_factory_order_product(
        multidb,
        user_name, run_version_id,
        fixture_send_commands, fixture_sleep, fixture_use_cache,
):
    ###########################################################################
    # prepare
    user = User.objects.create_user(
        username=user_name, android_id='test', game_access_token='1', player_id='1'
    )
    version = RunVersion.objects.create(id=run_version_id, user_id=user.id, level_id=1)
    initdata_filepath = version.get_account_path() / 'startgame_post.txt'
    txt = initdata_filepath.read_text(encoding='utf-8')
    json_data = json.loads(txt, strict=False)
    now = convert_datetime(json_data['Time'])
    version.now = now
    version.save()

    with mock.patch('django.utils.timezone.now') as p:
        p.return_value = now
        s = Strategy(user.id)
        s.run()
        prod = TSProduct.objects.filter(article_id=224).first()
        order_list = list(
            PlayerFactoryProductOrder.objects.filter(player_factory__factory_id=prod.factory_id).order_by('index').all()
        )
        before = ts_dump_factory(version=version, factory_id=prod.factory_id)
        print("[INIT]")
        print("\n".join(before))

        for order in order_list:
            order.refresh_from_db()
            factory_collect_product(version=version, order=order)
            after1 = ts_dump_factory(version=version, factory_id=order.player_factory.factory_id)
            print("[After Collect]")
            print("\n".join(after1))

            factory_order_product(version=version, product=prod)
            after2 = ts_dump_factory(version=version, factory_id=order.player_factory.factory_id)
            print("[After add]")
            print("\n".join(after2))




"""
        "Quests": [
          {
            "JobLocationId": 150,
            "Milestone": 1,
            "Progress": 1
          },
          {
            "JobLocationId": 152,
            "Milestone": 2,
            "Progress": 2
          },
          {
            "JobLocationId": 159,
            "Milestone": 3,
            "Progress": 3
          },
          {
            "JobLocationId": 160,
            "Milestone": 4,
            "Progress": 4
          },
          {
            "JobLocationId": 161,
            "Milestone": 1,
            "Progress": 1
          },
          {
            "JobLocationId": 162,
            "Milestone": 1,
            "Progress": 1
          }

        "Jobs": [
          {
            "Id": "0a2fedfb-2e98-4370-9c84-56d1d2f0e6ec",
            "JobLocationId": 158,
            "JobLevel": 1,
            "Sequence": 0,
            "Reward": {"Items": [{"Id": 8,"Value": 4,"Amount": 25},{"Id": 8,"Value": 1,"Amount": 10},{"Id": 8,"Value": 3,"Amount": 30}]
          },
          {
            "Id": "e16445d3-92e1-4ab0-b595-0d20b3cab242",
            "JobLocationId": 161,
            "JobLevel": 2,
            "Sequence": 0,
            "Reward": {"Items": [{"Id": 8,"Value": 4,"Amount": 25},{"Id": 8,"Value": 1,"Amount": 15}]
            "UnlocksAt": "2023-02-21T07:48:05Z"
          },
          {
            "Id": "f2ce8345-c891-4144-a9ca-e9cb7a2d331f",
            "JobLocationId": 162,
            "JobLevel": 2,
            "Sequence": 0,
            "JobType": 8,
            "Duration": 30,
            "ConditionMultiplier": 1,
            "RewardMultiplier": 1,
            "RequiredArticle": {"Id": 101,"Amount": 60},
            "CurrentArticleAmount": 52,
            "Reward": {
              "Items": [{"Id": 8,"Value": 4,"Amount": 25},{"Id": 8,"Value": 1,"Amount": 15}]
            },
            "Bonus": {
              "Reward": {
                "Items": []
              }
            },
            "Requirements": [
              {
                "Type": "region",
                "Value": 1
              }
            ],
            "UnlocksAt": "2023-02-21T08:15:51Z"
          }
        ],          

"""