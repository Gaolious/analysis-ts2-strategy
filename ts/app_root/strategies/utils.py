from datetime import datetime, timedelta
from typing import List, Optional, Dict

from django.conf import settings
from django.utils import timezone

from app_root.exceptions import TsRespInvalidOrExpiredSession
from app_root.players.utils_import import InitdataHelper, LeaderboardHelper
from app_root.servers.models import RunVersion
from app_root.servers.utils_import import EndpointHelper, LoginHelper, SQLDefinitionHelper
from app_root.strategies.commands import HeartBeat, StartGame, send_commands
from app_root.strategies.data_types import JobPriority, ArticleSource, Material, \
    FactoryStrategy, MaterialStrategy
from app_root.strategies.dumps import ts_dump
from app_root.strategies.managers import jobs_find, trains_find, \
    update_next_event_time, jobs_find_union_priority, \
    jobs_check_warehouse, warehouse_get_amount, article_find_contract, factory_find_product_orders, \
    factory_find_player_factory, jobs_find_priority, jobs_find_locked_job_location_ids
from app_root.strategies.strategy_collect_rewards import strategy_collect_reward_commands, collect_job_complete
from app_root.strategies.strategy_materials import get_ship_materials, build_article_sources, build_factory_strategy, \
    get_destination_materials, get_factory_materials, command_collect_materials_if_possible, \
    command_collect_factory_product_redundancy, command_factory_strategy, expand_material_strategy, \
    command_material_strategy, command_ship_trade
from app_root.strategies.strategy_union_quest import strategy_dispatching_gold_destinations, dispatching_job
from app_root.utils import get_curr_server_datetime

USE_CACHE = False


class Strategy(object):
    version: RunVersion
    user_id: int
    union_job_dispatching_priority: List[JobPriority]
    job_dispatching_priority: List[JobPriority]

    # contract_material_manager: ContractMaterialStrategy
    article_source: Dict[int, ArticleSource]

    ship_material: Material
    union_job_material: Material
    job_material: Material
    destination_material: Material
    factory_material: Material

    factory_strategy: Dict[int, FactoryStrategy]

    def __init__(self, user_id):
        self.user_id = user_id
        self.version = None
        self.union_job_dispatching_priority = []
        self.job_dispatching_priority = []
        self.article_source = {}
        self.ship_material = Material()
        self.union_job_material = Material()
        self.job_material = Material()
        self.factory_strategy = {}
        self.destination_strategy = {}

    def create_version(self):
        instance = RunVersion.objects.filter(user_id=self.user_id).order_by('-pk').first()

        if not instance:
            print(f"""[CreateVersion] Not Exist - start with new instance""")
            instance = RunVersion.objects.create(user_id=self.user_id, level_id=1)
            return instance

        elif instance.is_queued_task:
            print(f"""[CreateVersion] Status=Queued. start with previous instance""")
            # do next something...
            return instance

        elif instance.is_error_task:
            version_list = RunVersion.objects.filter(user_id=self.user_id).order_by('-pk').all()[:5]
            for v in version_list:
                if not v.is_error_task:
                    instance = RunVersion.objects.create(user_id=self.user_id, level_id=1)
                    return instance

            print(f"""[CreateVersion] Status=Error. Stop""")
            # do nothing.
            return None

        elif instance.is_processing_task:
            now = timezone.now()

            now_format = now.astimezone(settings.KST).strftime('%Y-%m-%d %H')
            srv_format = instance.login_server.astimezone(settings.KST).strftime('%Y-%m-%d %H')

            if now_format != srv_format:
                print(f"""[CreateVersion] Status=processing. passed over 1hour. start with new instance""")
                instance = RunVersion.objects.create(user_id=self.user_id, level_id=1)
                return instance

            if instance.next_event_datetime and instance.next_event_datetime > now:
                print(
                    f"""[CreateVersion] Status=processing. waiting for next event. Next event time is[{instance.next_event_datetime.astimezone(settings.KST)}] / Now is {now.astimezone(settings.KST)}""")
                return None

            print(f"""[CreateVersion] Status=processing. start with previous instance""")
            return instance

        elif instance.is_completed_task:
            now = timezone.now()
            if instance.next_event_datetime and instance.next_event_datetime > now:
                print(
                    f"""[CreateVersion] Status=Completed. waiting for next event. Next event time is[{instance.next_event_datetime.astimezone(settings.KST)}] / Now is {now.astimezone(settings.KST)}""")
                # do nothing.
                return None
            else:
                # do newly
                print(f"""[CreateVersion] Status=Completed. start with new instance""")
                instance = RunVersion.objects.create(user_id=self.user_id, level_id=1)
                return instance
        else:
            return None

        return instance

    def on_queued_status(self):
        ep_helper = EndpointHelper(version=self.version, use_cache=USE_CACHE)
        ep_helper.run()

        login_helper = LoginHelper(version=self.version, use_cache=USE_CACHE)
        login_helper.run()

        sd_helper = SQLDefinitionHelper(version=self.version, use_cache=USE_CACHE)
        sd_helper.run()

        init_helper = InitdataHelper(version=self.version, use_cache=USE_CACHE)
        init_helper.run()

        sg = StartGame(version=self.version, use_cache=USE_CACHE)
        sg.run()

        self.update_union_progress(True)

        ts_dump(version=self.version)

    def dump_material(self, title: str, material: Material):
        ret = []
        ret.append(f'# [Prepare Condition] - {title}')
        ret.append('-'*80)
        article = 'Article'
        amount = 'Req'
        has = 'Has'
        more = 'More'
        dest='dest'
        factory='factory'
        contract='contract'
        ret.append(f'''       {article:20s}|{amount:4s}|{has:4s}|{more:4s}|{dest:8s}|{factory:8s}|{contract:8s}''')

        for article_id, amount in material.items():
            article = self.article_source[article_id].article
            has = warehouse_get_amount(version=self.version, article_id=article_id)
            more = max( 0, amount - has)
            destinations = len(self.article_source[article_id].destinations)
            products = len(self.article_source[article_id].products)
            contracts = len(self.article_source[article_id].contracts)
            ret.append(f'''   #{article.id:7d}|{article.name[:15]:15s}|{amount:4d}|{has:4d}|{more:4d}|{destinations:8d}|{products:8d}|{contracts:8d}''')
        ret.append('')
        print('\n'.join(ret))

    def dump_factory_strategies(self):
        ret = []
        for factory_id, strategy in self.factory_strategy.items():
            ret.append(f'# [Strategy Factory] - {strategy.player_factory.factory} / Slot: {strategy.player_factory.slot_count}')
            ret.append('-'*80)
            article = 'Article'
            required = '요구'
            waiting = '대기'
            processing = '진행'
            completed = '완료'
            amount = '수량'
            ret.append(f'''   {article:23s}  {amount:2s} |{required:2s}|{waiting:2s}|{processing:2s}|{completed:2s}''')

            for product in strategy.factory_only_products:
                article_id = int(product.article_id)
                amount = product.article_amount
                article = self.article_source[article_id].article

                required = strategy.strategy_article_count.get(article_id, 0)
                waiting = strategy.waiting_article_count.get(article_id, 0)
                processing = strategy.processing_article_count.get(article_id, 0)
                completed = strategy.completed_article_count.get(article_id, 0)

                ret.append(f'''   #{article.id:7d}|{article.name[:15]:15s}[{amount:4d}]|{required:4d}|{waiting:4d}|{processing:4d}|{completed:4d}''')
        ret.append('')
        print('\n'.join(ret))

    def dump_job_priority(self, title, job_priority):
        ret = []

        ret.append(f"""# [Job Priority] - {title}""")
        ret.append("-" * 80)
        jobs = {}
        trains = {}
        for priority in job_priority:
            if priority.job.id not in jobs:
                jobs.update({priority.job.id: priority.job})
            if priority.job.id not in trains:
                trains.update({priority.job.id: []})
            trains[priority.job.id].append(priority)

        for job_id, job in jobs.items():
            ret.append(f" + job: {job}")
            for priority in trains.get(job_id, []):
                train = priority.train
                instance_id = f'{train.instance_id:3d}'
                capacity = f'{priority.amount}/{train.capacity()}'
                era = f'{train.train.get_era_display():2s}'
                rarity = f'{train.train.get_rarity_display():2s}'
                name = f'{train.train.asset_name:27s}'
                ret.append(f'    Id:{instance_id} / amount:{capacity:6s} / era:{era} / rarity:{rarity} / name:{name} ')
        ret.append('')
        print('\n'.join(ret))

    def update_union_progress(self, force: bool = False):
        now = timezone.now()
        if self.version.has_union and (force or abs((self.version.created - now).total_seconds()) > 10):
            for job in jobs_find(version=self.version, union_jobs=True):
                lb_helper = LeaderboardHelper(version=self.version, player_job_id=job.id, use_cache=USE_CACHE)
                lb_helper.run()

    def _command_union_job(self) -> Optional[datetime]:
        if self.version.has_union:
            print(f"# [Strategy Process] - Union Job")

            # union quest item
            self.union_job_dispatching_priority = jobs_find_union_priority(version=self.version, with_warehouse_limit=False)
            self.dump_job_priority('Without resource', self.union_job_dispatching_priority)

            if jobs_check_warehouse(version=self.version, job_priority=self.union_job_dispatching_priority):
                dispatching_job(version=self.version, job_priority=self.union_job_dispatching_priority)
            else:
                temporary_train_job_amount_list = jobs_find_union_priority(version=self.version, with_warehouse_limit=True)
                self.dump_job_priority('out of resource.', temporary_train_job_amount_list)
                dispatching_job(version=self.version, job_priority=temporary_train_job_amount_list)

        return None

    def _command_basic_job(self) -> Optional[datetime]:
        if not self.version.has_union and self.version.level_id < 26:
            print(f"# [Strategy Process] - Story/Side Job")

            # union quest item
            completed_job_location_id, processing_job_location_id, locked_job_location_id = jobs_find_locked_job_location_ids(version=self.version)

            self.job_dispatching_priority = jobs_find_priority(
                version=self.version,
                locked_job_location_id=processing_job_location_id | locked_job_location_id,
                with_warehouse_limit=False
            )
            self.dump_job_priority('Without resource', self.job_dispatching_priority)

            if jobs_check_warehouse(version=self.version, job_priority=self.job_dispatching_priority):
                dispatching_job(version=self.version, job_priority=self.job_dispatching_priority)
            else:
                if self.job_dispatching_priority:
                    self.job_material.clear()
                    for instance in self.job_dispatching_priority:
                        article_id = int(instance.job.required_article_id)
                        article_amount = int(instance.amount)
                        self.job_material.add(article_id=article_id, amount=int(article_amount))

                    self.dump_material(title="Step 1-2. Basic Quest 재료", material=self.job_material)
                    strategy = MaterialStrategy()
                    expand_material_strategy(
                        version=self.version,
                        requires=self.job_material,
                        article_source=self.article_source,
                        strategy=strategy,
                    )

                    command_material_strategy(
                        version=self.version,
                        strategy=strategy
                    )
                temporary_train_job_amount_list = jobs_find_priority(
                    version=self.version,
                    locked_job_location_id=locked_job_location_id,
                    with_warehouse_limit=True
                )
                self.dump_job_priority('out of resource.', temporary_train_job_amount_list)
                dispatching_job(version=self.version, job_priority=temporary_train_job_amount_list)

        return None

    def on_finally(self) -> Optional[datetime]:
        ret = None

        for train in trains_find(version=self.version, is_idle=False):
            if train.route_arrival_time and train.route_arrival_time > self.version.now:
                ret = update_next_event_time(previous=ret, event_time=train.route_arrival_time)

        for player_factory in factory_find_player_factory(version=self.version):

            completed, processing, waiting = factory_find_product_orders(version=self.version, factory_id=player_factory.factory_id)
            if processing:
                if processing[0].finishes_at and processing[0].finishes_at > self.version.now:
                    ret = update_next_event_time(previous=ret, event_time=processing[0].finishes_at)

        for key, contract_list in article_find_contract(version=self.version, available_only=False).items():
            for contract in contract_list:
                if contract.usable_from and contract.usable_from > self.version.now:
                    ret = update_next_event_time(previous=ret, event_time=contract.usable_from)

        return ret

    def on_processing_status(self) -> Optional[datetime]:
        """

        """
        self.update_union_progress()

        ret: Optional[datetime] = None
        send_commands(HeartBeat(version=self.version))

        # 2. collect
        next_dt = strategy_collect_reward_commands(version=self.version)
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        next_dt = collect_job_complete(version=self.version)
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        next_dt = strategy_dispatching_gold_destinations(version=self.version)
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        next_dt = self._command_union_job()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        next_dt = self._command_basic_job()
        ret = update_next_event_time(previous=ret, event_time=next_dt)
        """
            Queue 형태
            
            Factory[ 1 ~ 6 ] - need product list
            destination [ 1 ~ 6 ] - need article list 
            
            step 1. union Quest.
                - contract material - required.
                    - short? add to factory, destination
                        - loop. in factory - required material & available to add
                            - add to factory, destination, ...
            step 2. 
        """
        self.ship_material = get_ship_materials(version=self.version)
        self.dump_material(title='Step 0. Ship 재료 (Pass)', material=self.ship_material)
        strategy = MaterialStrategy()
        command_ship_trade(
            version=self.version,
            requires=self.ship_material,
            article_source=self.article_source,
            strategy=strategy,
        )

        # Step 1. contract. / union quest materials.
        if self.union_job_dispatching_priority:
            self.union_job_material.clear()
            for instance in self.union_job_dispatching_priority:
                article_id = int(instance.job.required_article_id)
                article_amount = int(instance.amount)
                self.union_job_material.add(article_id=article_id, amount=int(article_amount))

            self.dump_material(title="Step 1-1. Union Quest 재료", material=self.union_job_material)
            strategy = MaterialStrategy()
            expand_material_strategy(
                version=self.version,
                requires=self.union_job_material,
                article_source=self.article_source,
                strategy=strategy,
            )
            command_material_strategy(
                version=self.version,
                strategy=strategy
            )

        # command_collect_materials_if_possible(
        #     version=self.version,
        #     requires=self.job_material,
        #     article_source=self.article_source
        # )

        # Step 2. Destination 여분 재료 채우기
        self.destination_material = get_destination_materials(version=self.version)
        self.dump_material(title="Destination(Redundancy)", material=self.destination_material)
        command_collect_materials_if_possible(
            version=self.version,
            requires=self.destination_material,
            article_source=self.article_source
        )

        print("Step 2. 공장 제품중 창고 부족분 채우기.")
        # Step 2. 공장 제품중 창고 부족분 채우기.
        command_collect_factory_product_redundancy(
            version=self.version,
            factory_strategy_dict=self.factory_strategy,
            article_source=self.article_source
        )

        # Step 2. Factory 여분 재료 채우기
        self.factory_material = get_factory_materials(version=self.version, factory_strategy_dict=self.factory_strategy)
        self.dump_material(title="Factory(Redundancy)", material=self.factory_material)
        command_collect_materials_if_possible(
            version=self.version,
            requires=self.factory_material,
            article_source=self.article_source
        )
        command_factory_strategy(
            version=self.version,
            factory_strategy_dict=self.factory_strategy,
            article_source=self.article_source
        )

        return ret

    def run(self):

        self.version = self.create_version()

        if not self.version:
            return

        try:
            ret = None
            if self.version.is_queued_task:
                self.on_queued_status()
                self.version.set_processing(save=True, update_fields=[])

            # build_possible_location(version=self.version)
            self.article_source = build_article_sources(version=self.version)
            self.factory_strategy = build_factory_strategy(version=self.version)
            self.dump_factory_strategies()

            if self.version.is_processing_task:
                next_dt = self.on_processing_status()
                ret = update_next_event_time(previous=ret, event_time=next_dt)

            next_dt = self.on_finally()
            ret = update_next_event_time(previous=ret, event_time=next_dt)

            self.version.next_event_datetime = ret
            self.version.save(
                update_fields=['next_event_datetime']
            )
            ts_dump(version=self.version)

        except TsRespInvalidOrExpiredSession as e:
            if self.version:
                now = get_curr_server_datetime(version=self.version)
                self.version.next_event_datetime = now + timedelta(minutes=10)
                self.version.set_completed(save=True, update_fields=[])

        except Exception as e:
            if self.version:
                self.version.set_error(save=True, msg=str(e), update_fields=[])
            raise e

