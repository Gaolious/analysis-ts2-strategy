from typing import Optional, Dict, List

from app_root.players.models import PlayerAchievement, PlayerJob, PlayerQuest, PlayerContractList, PlayerTrain, \
    PlayerFactory, PlayerBuilding, PlayerCompetition, PlayerGift, PlayerCityLoopTask, PlayerCityLoopParcel, \
    PlayerWhistleItem
from app_root.servers.mixins import RARITY_LEGENDARY, RARITY_EPIC, RARITY_RARE, RARITY_COMMON
from app_root.servers.models import RunVersion, TSAchievement, TSMilestone, TSTrainUpgrade, TSFactory, TSArticle
from datetime import datetime, timedelta

from app_root.strategies.commands import GameSleep, send_commands, GameWakeup, DailyRewardClaimWithVideoCommand, \
    DailyRewardClaimCommand, ShopPurchaseItem, TrainUnloadCommand, ShopBuyContainer, CollectAchievementCommand, \
    JobCollectCommand, RegionQuestCommand, LevelUpCommand, ContractListRefreshCommand, TrainUpgradeCommand, \
    FactoryAcquireCommand, CollectGiftCommand, CityLoopBuildingUpgradeCommand, CityLoopBuildingReplaceCommand, \
    CityLoopBuildingReplaceInstantlyCommand, CollectWhistle
from app_root.strategies.data_types import Material, MaterialStrategy
from app_root.strategies.managers import daily_reward_get_reward, warehouse_can_add_with_rewards, \
    daily_reward_get_next_event_time, daily_offer_get_slots, daily_offer_get_next_event_time, trains_find, \
    warehouse_can_add, trains_get_next_unload_event_time, container_offer_find_iter, update_next_event_time, jobs_find, \
    find_xp, trains_get_upgrade_material, warehouse_get_amount, whistle_get_collectable_list, \
    whistle_get_next_event_time, competition_union_group
from app_root.strategies.strategy_materials import expand_material_strategy
from app_root.utils import get_curr_server_str_datetime_s, get_remain_time


def collect_daily_reward(version: RunVersion) -> datetime:
    """
    Daily Reward (일일 보상. 5일간 연속 로그인시 보상)

    :param version:
    :return:
    """
    print(f"# [Strategy Process] - Collect Daily Reward")

    daily_reward = daily_reward_get_reward(version=version)
    if daily_reward:
        if daily_reward.can_claim_with_video:
            ret = warehouse_can_add_with_rewards(
                version=version,
                reward=daily_reward.get_today_rewards(),
                multiply=2
            )

            if ret:
                video_started_datetime_s = get_curr_server_str_datetime_s(version=version)
                cmd = GameSleep(version=version, sleep_seconds=30)
                send_commands(commands=cmd)

                cmd = GameWakeup(version=version)
                send_commands(commands=cmd)

                cmd = DailyRewardClaimWithVideoCommand(
                    version=version,
                    reward=daily_reward,
                    video_started_datetime_s=video_started_datetime_s
                )
                send_commands(commands=cmd)

        else:
            cmd = DailyRewardClaimCommand(version=version, reward=daily_reward)
            send_commands(commands=cmd)

    return daily_reward_get_next_event_time(version=version)


def collect_daily_offer(version: RunVersion) -> datetime:
    """
    Daily Offer (일일 reward)

    video 보기 전용 only

    :param version:
    :return:
    """
    print(f"# [Strategy Process] - Collect Daily Offer")

    daily_offer_items = daily_offer_get_slots(
        version=version,
        available_video=True,
        availble_gem=False,
        available_gold=False,
    )

    for offer_item in daily_offer_items:
        cmd = ShopPurchaseItem(version=version, offer_item=offer_item)
        send_commands(commands=cmd)

    return daily_offer_get_next_event_time(version=version)


def collect_train_unload(version: RunVersion) -> datetime:
    print(f"# [Strategy Process] - Collect Train Load")

    for train in trains_find(version=version, has_load=True):
        if not warehouse_can_add(version=version, article_id=train.load_id, amount=train.load_amount):
            continue

        cmd = TrainUnloadCommand(version=version, train=train)
        send_commands(commands=cmd)

    return trains_get_next_unload_event_time(version=version)


def collect_whistle(version: RunVersion) -> datetime:
    print(f"# [Strategy Process] - Collect Whistle")

    for whistle in whistle_get_collectable_list(version=version):
        reward = []
        articles_str = []
        for row in PlayerWhistleItem.objects.filter(player_whistle=whistle, item_id=8).all():
            reward.append({'Id': row.item_id, 'Value': row.value, 'Amount': row.amount})
            article = TSArticle.objects.filter(id=row.value).first()
            articles_str.append(
                f'''[{article.id}|{article.name}:{row.amount}]'''
            )

        print(f'''      => rewards : {','.join(articles_str)}''')
        if warehouse_can_add_with_rewards(version=version, reward=reward):
            print(f'''      => Can Add Rewards - Try Collect''')
            cmd = CollectWhistle(version=version, whistle=whistle)
            send_commands(commands=cmd)
        else:
            print(f'''      => Not enough warehouse | PASS''')

    return whistle_get_next_event_time(version=version)


def collect_gift(version: RunVersion):
    print(f"# [Strategy Process] - Collect gift")

    competition_list = competition_union_group(version=version)

    if len(competition_list) > 0:
        print(f"  - Now Collectible Gift")
        for gift in PlayerGift.objects.filter(version_id=version.id).all():
            cmd = CollectGiftCommand(version=version, gift=gift)
            send_commands(commands=cmd)
    else:
        print(f"  - Now Not Collectible Gift")


def collect_offer_container(version: RunVersion) -> datetime:
    ret = None
    print(f"# [Strategy Process] - Collect Offer Container")

    for offer in container_offer_find_iter(version=version, available_only=True):
        offer.refresh_from_db()
        cmd_no = None
        cmd_list = []
        if not offer.is_available(now=version.now):
            continue
            
        if offer.is_video_reward:
            cmd_no = version.command_no
            cmd = GameSleep(version=version, sleep_seconds=30)
            send_commands(commands=cmd)

            cmd = GameWakeup(version=version)
            cmd_list.append(cmd)

        cmd = ShopBuyContainer(
            version=version,
            offer=offer,
            sleep_command_no=cmd_no,
        )
        cmd_list.append(cmd)
        print(f"""    - Container Offer Before : OfferId={offer.offer_container_id} | last_bought_at={offer.last_bought_at} | count={offer.count}""")
        send_commands(commands=cmd_list)
        offer.refresh_from_db()
        print(f"""    - Container Offer After : OfferId={offer.offer_container_id} | last_bought_at={offer.last_bought_at} | count={offer.count}""")

    for offer in container_offer_find_iter(version=version, available_only=False):
        container = offer.offer_container
        next_dt = offer.last_bought_at + timedelta(seconds=container.cooldown_duration)
        if version.now < next_dt:
            ret = update_next_event_time(previous=ret, event_time=next_dt)

    return ret


def strategy_collect_reward_commands(version: RunVersion) -> datetime:
    """

    :param version:
    :return:
    """
    # todo: return next event time.
    ret: Optional[datetime] = None

    # daily reward
    next_dt = collect_daily_reward(version=version)
    ret = update_next_event_time(previous=ret, event_time=next_dt)

    # daily offer
    next_dt = collect_daily_offer(version=version)
    ret = update_next_event_time(previous=ret, event_time=next_dt)

    # train unload
    next_dt = collect_train_unload(version=version)
    ret = update_next_event_time(previous=ret, event_time=next_dt)

    # next_dt = collect_whistle(version=version)
    # ret = update_next_event_time(previous=ret, event_time=next_dt)

    # gift
    next_dt = collect_gift(version=version)
    ret = update_next_event_time(previous=ret, event_time=next_dt)

    # ship

    strategy_collect_achievement_commands(version=version)

    # offer container
    next_dt = collect_offer_container(version=version)
    ret = update_next_event_time(previous=ret, event_time=next_dt)

    check_levelup(version=version)

    check_expired_contracts(version=version)

    ret = update_next_event_time(previous=ret, event_time=next_dt)

    return ret


def strategy_collect_achievement_commands(version: RunVersion):
    print(f"# [Strategy Process] - Collect Achievement")

    achievements_dict: Dict[str, TSAchievement] = {
        o.name: o for o in TSAchievement.objects.all()
    }
    for achievement in PlayerAchievement.objects.filter(version_id=version.id).all():
        achievement_name = achievement.achievement
        level = achievement.level
        progress = achievement.progress

        instance = achievements_dict[achievement_name]
        if instance and instance.is_collectable(level=level, progress=progress):
            reward_article_id, reward_article_amount = instance.get_reward(level=level)

            cmd = GameSleep(version=version, sleep_seconds=30)
            send_commands(commands=cmd)

            cmd_list = [
                GameWakeup(version=version),
                CollectAchievementCommand(
                    version=version,
                    achievement=achievement,
                    reward_article_id=reward_article_id,
                    reward_article_amount=reward_article_amount,
                )
            ]

            send_commands(cmd_list)


def collect_job_complete(version: RunVersion):
    print(f"# [Strategy Process] - Collect Job Complete")
    job_collections = [
        jobs_find(version=version, story_jobs=True, expired_jobs=False),
        jobs_find(version=version, side_jobs=True, expired_jobs=False),
    ]
    for job_list in job_collections:
        for job in job_list:
            job: PlayerJob

            if not job.is_completed(version.now):
                print(f"""    - {job} | is not completed: Now[{version.now}]""")
                continue
            if not job.is_collectable(version.now):
                print(f"""    - {job} | is not collectable: Now[{version.now}]""")
                continue

            quest = PlayerQuest.objects.filter(version_id=version.id, job_location_id=job.job_location_id).first()
            milestone = None
            curr_milestone = '-'
            curr_progress = '-'
            required_progress = '-'

            if quest:
                milestone = TSMilestone.objects.filter(job_location_id=job.job_location_id, milestone=quest.milestone).first()
                curr_milestone = quest.milestone
                curr_progress = quest.progress

            if milestone:
                required_progress = milestone.milestone_progress

            print(f"""    - {job} | Try Collect[milestone:{curr_milestone} / progress:{curr_progress} / required:{required_progress}""")

            cmd = JobCollectCommand(version=version, job=job)
            send_commands(cmd)

            if quest and milestone and quest.progress >= milestone.milestone_progress and not milestone.force_region_collect:
                cmd = RegionQuestCommand(version=version, job=job)
                send_commands(cmd)


def check_levelup(version: RunVersion):
    print(f"# [Strategy Process] - Collect Level Up")

    if find_xp(version) >= version.level.xp:
        cmd = LevelUpCommand(version=version)
        send_commands(cmd)


def check_expired_contracts(version: RunVersion):
    print(f"# [Strategy Process] - Refresh Expired Contracts")

    for contract_list in PlayerContractList.objects.filter(version_id=version.id).all():
        if contract_list.expires_at and contract_list.is_expired(version.now) and contract_list.contract_list_id != 1:
            cmd = ContractListRefreshCommand(version=version, contract_list=contract_list)
            send_commands(cmd)


def check_upgrade_train(version: RunVersion):
    print(f"# [Strategy Process] - Upgrade Train")
    gold_article_id = 3
    legend_parts_id = 9
    epic_parts_id = 8
    rare_parts_id = 7
    common_parts_id = 6
    guild_parts_id = 5

    target_train: Dict[int, Dict[int, List[PlayerTrain]]] = {}
    for train in trains_find(version=version):
        if train.level_id >= train.train.max_level:
            continue

        rarity = train.train.rarity  # 일반 / 레어 / 에픽 / 전설
        region = train.get_region()

        if region not in target_train:
            target_train.update({region: {}})

        if rarity not in target_train[region]:
            target_train[region].update({rarity: []})
        target_train[region][rarity].append(train)

    for region in target_train:
        for rarity in target_train[region]:
            target_train[region][rarity].sort(key=lambda o: o.capacity(), reverse=True)

    region_list = sorted(target_train.keys(), reverse=True)

    for region in region_list:
        rarity_list = [RARITY_LEGENDARY, RARITY_EPIC, RARITY_RARE, RARITY_COMMON]
        rarity_article_ids = [legend_parts_id, epic_parts_id, rare_parts_id, common_parts_id]

        for rarity, rarity_article_id in zip(rarity_list, rarity_article_ids):

            train_list = target_train[region].get(rarity, [])
            if not train_list:
                continue

            train: PlayerTrain = train_list.pop(0)
            is_satisfied_rarity_article = False
            while train_list:
                train.refresh_from_db()
                if train.level_id >= train.train.max_level:
                    del train_list[0]
                    continue

                train_upgrade = trains_get_upgrade_material(version=version, train=train)
                if not train_upgrade:
                    break

                condition = {
                    article_id: (warehouse_get_amount(version=version, article_id=article_id), amount)
                    for article_id, amount in train_upgrade.price_to_dict.items()
                }

                satisfied = {article_id: a >= b for article_id, (a, b) in condition.items()}
                is_satisfied_rarity_article = satisfied[rarity_article_id]

                if all(satisfied.values()):
                    cmd = TrainUpgradeCommand(
                        version=version,
                        train=train,
                        upgrade=train_upgrade,
                    )
                    send_commands(commands=cmd)
                    # do upgrade
                    continue
                else:
                    break

            if train_list and is_satisfied_rarity_article:
                return
            else:
                continue


def check_factory(version: RunVersion):
    """
    Factory:AcquireFactory

    :param version:
    :return:
    """
    print(f"# [Strategy Process] - Check Factory")

    for factory in TSFactory.objects.filter(type=1, level_from__lte=version.level_id).all():
        player_factory = PlayerFactory.objects.filter(version_id=version.id, factory_id=factory.id).first()
        if player_factory:
            continue

        cmd = FactoryAcquireCommand(version=version, factory=factory)
        send_commands(cmd)


def _remove_task_from_building(version: RunVersion, task: PlayerCityLoopTask, building: PlayerBuilding) -> bool:
    if task.next_replace_at and task.next_replace_at < version.now:
        print(f"  - Try Replace now.")
        cmd = CityLoopBuildingReplaceCommand(version=version, building=building)
        send_commands(cmd)
        return True

    elif task.next_video_replace_at and task.next_video_replace_at < version.now:
        print(f"  - Try Replace with video now.")
        cmd = GameSleep(version=version, sleep_seconds=30)
        send_commands(commands=cmd)

        cmd_list = [
            GameWakeup(version=version),
            CityLoopBuildingReplaceInstantlyCommand(version=version, building=building)
        ]
        send_commands(commands=cmd_list)
        return True

    print(f"  - Can't Replace Task. All Busy now.")
    return False


def check_building(version: RunVersion) -> PlayerBuilding:
    print(f"# [Strategy Process] - Check Building")
    task = PlayerCityLoopTask.objects.filter(version_id=version.id).first()
    # parcels = list(PlayerCityLoopParcel.objects.filter(version_id=version.id).values_list('parcel', flat=True))
    if task:
        for curr_try in range(3):
            upgrade_list = []
            task.refresh_from_db()

            for bld in PlayerBuilding.objects.filter(version_id=version.id, parcel_number__gt=0, level__lt=150).all():
                upgrade_list.append(bld)

            if not upgrade_list:
                return None

            upgrade_list.sort(key=lambda x: (x.level, x.upgrade_task), reverse=True)
            target = upgrade_list[0]
            cancelable_list = [o for o in upgrade_list[1:] if o.upgrade_task]

            next_replace_at = get_remain_time(version=version, finish_at=task.next_replace_at)
            next_video_replace_at = get_remain_time(version=version, finish_at=task.next_video_replace_at)
            print(f"  - Task NextReplace At: {next_replace_at} / NextVideoReplace At: {next_video_replace_at}")
            print(f"  - [Try {curr_try}] Target : {target}")
            for cancel in cancelable_list:
                print(f"  - [Try {curr_try}] Candidate : {cancel}")

            if target.upgrade_task:

                if target.available_from and target.available_from > version.now:
                    dt = get_remain_time(version=version, finish_at=target.available_from)
                    print(f"  - [Try {curr_try}] Target is not Available. remain: {dt} | PASS")
                    return None

                condition = {
                    article_id: (warehouse_get_amount(version=version, article_id=article_id), amount)
                    for article_id, amount in target.requirements_to_dict.items()
                }
                satisfied = {article_id: a >= b for article_id, (a, b) in condition.items()}
                satisfied_for_city_plans = {
                    a: b for a, b in satisfied.items() if a in (10, 11, 12)  # blue, yellow, red city plans
                }

                if all(satisfied.values()):
                    print(f"  - [Try {curr_try}] Try Upgrade")
                    cmd = CityLoopBuildingUpgradeCommand(version=version, building=target)
                    send_commands(cmd)
                else:
                    if satisfied_for_city_plans and all(satisfied_for_city_plans.values()):
                        print(f"  - [Try {curr_try}] Target is not enough normal city plan & city plan | PASS")
                        return target
                    else:
                        print(f"  - [Try {curr_try}] Target is not enough city plan - Remove Task. | PASS")
                        if _remove_task_from_building(version=version, task=task, building=target):
                            continue
                return None

            elif len(cancelable_list) > 0:
                available_list = [o for o in cancelable_list if o.available_from and o.available_from < version.now]
                if not available_list:
                    print(f"  - [Try {curr_try}] cancelable list is empty. all busy now. | PASS")
                    return None
                cancel_target = available_list[-1]

                if _remove_task_from_building(version=version, task=task, building=cancel_target):
                    continue
                else:
                    return None



    """
    UpgradeTaskNextReplaceAt,
    UpgradeTaskNextVideoReplaceAt 
    
    추가 필요.
    
     
    초기상태

"UpgradeTaskNextReplaceAt": "2023-02-24T03:36:49Z",
"UpgradeTaskNextVideoReplaceAt": "2023-02-23T13:26:10Z",
{"InstanceId": 1,"DefinitionId": 100,"Rotation": 0,"Level": 6},
{"UpgradeTask": {"AvailableFrom": "2023-02-23T23:36:50Z","RequiredArticles": [{"Id": 12,"Amount": 7},{"Id": 10,"Amount": 6},{"Id": 232,"Amount": 20}]},"InstanceId": 2,"DefinitionId": 102,"ParcelNumber": 2,"Rotation": 0,"Level": 7},
{"UpgradeTask": {"AvailableFrom": "2023-02-23T00:16:10Z","RequiredArticles": [{"Id": 11,"Amount": 12},{"Id": 107,"Amount": 9}]},"InstanceId": 3,"DefinitionId": 104,"ParcelNumber": 3,"Rotation": 0,"Level": 6},
{"InstanceId": 4,"DefinitionId": 109,"Rotation": 0,"Level": 6},
{"UpgradeTask": {"AvailableFrom": "2023-02-23T23:51:27Z","RequiredArticles": [{"Id": 11,"Amount": 6},{"Id": 10,"Amount": 7},{"Id": 104,"Amount": 22}]},"InstanceId": 5,"DefinitionId": 106,"ParcelNumber": 5,"Rotation": 0,"Level": 10},
{"UpgradeTask": {"AvailableFrom": "2023-02-23T23:50:04Z","RequiredArticles": [{"Id": 102,"Amount": 14},{"Id": 107,"Amount": 8}]},"InstanceId": 6,"DefinitionId": 101,"ParcelNumber": 1,"Rotation": 0,"Level": 8},
{"InstanceId": 7,"DefinitionId": 103,"ParcelNumber": 4,"Rotation": 0,"Level": 7},
{"InstanceId": 8,"DefinitionId": 105,"Rotation": 0,"Level": 6},
{"InstanceId": 9,"DefinitionId": 107,"Rotation": 0,"Level": 5},
{"InstanceId": 10,"DefinitionId": 14,"Rotation": 0,"Level": 1}


    지우기. 1회(광고 X)
{"Id":2,"Time":"2023-02-24T05:06:29Z","Commands":[{"Command":"CityLoop:Building:UpgradeTask:Replace","Time":"2023-02-24T05:06:29Z","Parameters":{"BuildingId":3}}],"Transactional":false}
{"Success":true,"RequestId":"1f23af25-3b5e-412e-9deb-242e2481adca","Time":"2023-02-24T05:06:32Z","Data":{"CollectionId":2,"Commands":[
    {"Command":"CityLoop:Building:UpgradeTask","Data":{"BuildingId":7,"UpgradeTask":{"AvailableFrom":"2023-02-24T05:06:32Z","RequiredArticles":[{"Id":12,"Amount":7},{"Id":10,"Amount":6},{"Id":107,"Amount":7}]}}}]}}

    업그레이드
{"Id":3,"Time":"2023-02-24T05:07:01Z","Commands":[{"Command":"CityLoop:Building:Upgrade","Time":"2023-02-24T05:07:01Z","Parameters":{"BuildingId":6,"UsesAutoCollect":false}}],"Transactional":false}
{"Success":true,"RequestId":"97d8bc1c-8258-422d-b754-4b81c1500a1d","Time":"2023-02-24T05:07:03Z","Data":{"CollectionId":3,"Commands":[{"Command":"CityLoop:Building:UpgradeTask","Data":{"BuildingId":3,"UpgradeTask":{"AvailableFrom":"2023-02-24T05:19:03Z","RequiredArticles":[{"Id":12,"Amount":13},{"Id":232,"Amount":25}]}}},{"Command":"Population:Update","Data":{"Population":{"LastCalculatedCount":59,"LastCalculatedAt":"2023-02-24T05:07:01Z"}}},{"Command":"Achievement:Change","Data":{"Achievement":{"AchievementId":"city_task","Level":2,"Progress":53}}}]}}


{"Id":4,"Time":"2023-02-24T05:07:09Z","Commands":[{"Command":"Game:Sleep","Time":"2023-02-24T05:07:09Z","Parameters":{},"Debug":{"CollectionsInQueue":0,"CollectionsInQueueIds":""}}],"Transactional":false}
{"Success":true,"RequestId":"c7c7f345-1c00-41da-8806-418164764019","Time":"2023-02-24T05:07:47Z","Data":{"CollectionId":4,"Commands":[]}}


{"Id":5,"Time":"2023-02-24T05:07:49Z","Commands":[{"Command":"Game:WakeUp","Time":"2023-02-24T05:07:09Z","Parameters":{}},{"Command":"CityLoop:Building:UpgradeTask:ReplaceInstantly","Time":"2023-02-24T05:07:46Z","Parameters":{"BuildingId":2,"ArticleId":16}}],"Transactional":false}
{"Success":true,"RequestId":"01d6522a-f9f6-404a-be19-5ac0ab2d7740","Time":"2023-02-24T05:07:50Z","Data":{"CollectionId":5,"Commands":[{"Command":"CityLoop:Building:UpgradeTask","Data":{"BuildingId":6,"UpgradeTask":{"AvailableFrom":"2023-02-24T05:07:50Z","RequiredArticles":[{"Id":10,"Amount":14},{"Id":107,"Amount":10}]}}}]}}



"UpgradeTaskNextReplaceAt": "2023-02-24T09:06:29Z",
"UpgradeTaskNextVideoReplaceAt": "2023-02-24T06:07:46Z",


{"InstanceId": 1,"DefinitionId": 100,"Rotation": 0,"Level": 6},
{"InstanceId": 2,"DefinitionId": 102,"ParcelNumber": 2,"Rotation": 0,"Level": 7},
{"UpgradeTask": {"AvailableFrom": "2023-02-24T05:19:03Z","RequiredArticles": [{"Id": 12,"Amount": 13},{"Id": 232,"Amount": 25}]},"InstanceId": 3,"DefinitionId": 104,"ParcelNumber": 3,"Rotation": 0,"Level": 6},
{"InstanceId": 4,"DefinitionId": 109,"Rotation": 0,"Level": 6},
{"UpgradeTask": {"AvailableFrom": "2023-02-23T23:51:27Z","RequiredArticles": [{"Id": 11,"Amount": 6},{"Id": 10,"Amount": 7},{"Id": 104,"Amount": 22}]},"InstanceId": 5,"DefinitionId": 106,"ParcelNumber": 5,"Rotation": 0,"Level": 10},
{"UpgradeTask": {"AvailableFrom": "2023-02-24T05:07:50Z","RequiredArticles": [{"Id": 10,"Amount": 14},{"Id": 107,"Amount": 10}]},"InstanceId": 6,"DefinitionId": 101,"ParcelNumber": 1,"Rotation": 0,"Level": 9},
{"UpgradeTask": {"AvailableFrom": "2023-02-24T05:06:32Z","RequiredArticles": [{"Id": 12,"Amount": 7},{"Id": 10,"Amount": 6},{"Id": 107,"Amount": 7}]},"InstanceId": 7,"DefinitionId": 103,"ParcelNumber": 4,"Rotation": 0,"Level": 7},
{"InstanceId": 8,"DefinitionId": 105,"Rotation": 0,"Level": 6},
{"InstanceId": 9,"DefinitionId": 107,"Rotation": 0,"Level": 5},
{"InstanceId": 10,"DefinitionId": 14,"Rotation": 0,"Level": 1}



{"Id":2,"Time":"2023-02-24T05:00:59Z","Commands":[{"Command":"CityLoop:Building:Move:ToStash","Time":"2023-02-24T05:00:57Z","Parameters":{"BuildingId":7}}],"Transactional":false}
{"Success":true,"RequestId":"9d42cb19-f2f5-4cd2-8167-eee026d5c021","Time":"2023-02-24T05:01:02Z","Data":{"CollectionId":2,"Commands":[{"Command":"Population:Update","Data":{"Population":{"LastCalculatedCount":47,"LastCalculatedAt":"2023-02-24T05:00:57Z"}}}]}}

24 14:01:11 | T: 3039 | I | SSL_AsyncWrite  | POST /api/v2/command-processing/run-collection HTTP/1.1
PXFD-Request-Id: 781b7555-ec45-4577-a1a0-9166ada5dfae
PXFD-Retry-No: 0
PXFD-Sent-At: 2023-02-24T05:01:10.658Z
PXFD-Client-Information: {"Store":"google_play","Version":"2.7.0.4123","Language":"ko"}
PXFD-Client-Version: 2.7.0.4123
PXFD-Device-Token: 0cbd8657b85587591462e728d4129ab0
PXFD-Game-Access-Token: be034580-530e-5105-97d2-ec1acba9d147
PXFD-Player-Id: 76408422
Content-Type: application/json
Content-Length: 191
Host: game.trainstation2.com
Accept-Encoding: gzip, deflate


{"Id":3,"Time":"2023-02-24T05:01:10Z","Commands":[{"Command":"CityLoop:Building:Move:FromStash","Time":"2023-02-24T05:01:09Z","Parameters":{"Parcel":4,"BuildingId":7}}],"Transactional":false}
24 14:01:11 | T: 3044 | I | IO.Mem.Write    | {"Success":true,"RequestId":"781b7555-ec45-4577-a1a0-9166ada5dfae","Time":"2023-02-24T05:01:11Z","Data":{"CollectionId":3,"Commands":[
{"Command":"Population:Update","Data":{"Population":{"LastCalculatedCount":58,"LastCalculatedAt":"2023-02-24T05:01:09Z"}}}]}}

    """