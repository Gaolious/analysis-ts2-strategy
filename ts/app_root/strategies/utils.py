import json
from datetime import datetime, timedelta
from typing import Iterator, Tuple, List, Optional, Dict

from django.conf import settings
from django.utils import timezone

from app_root.exceptions import TsRespInvalidOrExpiredSession
from app_root.players.models import PlayerWhistle, PlayerTrain, PlayerJob, PlayerContract
from app_root.players.utils_import import InitdataHelper, LeaderboardHelper
from app_root.servers.models import RunVersion
from app_root.servers.utils_import import EndpointHelper, LoginHelper, SQLDefinitionHelper
from app_root.strategies.commands import HeartBeat, RunCommand, BaseCommand, TrainUnloadCommand, StartGame, \
    DailyRewardClaimWithVideoCommand, GameSleep, GameWakeup, DailyRewardClaimCommand, CollectWhistle, \
    TrainSendToDestinationCommand, ShopBuyContainer, ShopPurchaseItem, TrainDispatchToJobCommand, ContractAcceptCommand, \
    FactoryCollectProductCommand
from app_root.strategies.dumps import ts_dump
from app_root.strategies.managers import jobs_find, trains_find, \
    daily_reward_get_reward, warehouse_can_add, warehouse_can_add_with_rewards, \
    daily_reward_get_next_event_time, trains_get_next_unload_event_time, \
    update_next_event_time, trains_max_capacity, destination_gold_find_iter, container_offer_find_iter, \
    warehouse_max_capacity, daily_offer_get_next_event_time, daily_offer_get_slots, \
    jobs_find_priority, jobs_check_warehouse, get_number_of_working_dispatchers, warehouse_countable, \
    warehouse_get_amount, article_find_product, article_find_contract, article_find_destination, \
    factory_find_product_orders, factory_find_player_factory, factory_find_possible_products
from app_root.utils import get_curr_server_str_datetime_s, get_curr_server_datetime

USE_CACHE = False


class Strategy(object):
    version: RunVersion
    user_id: int
    now: datetime
    train_job_amount_list: List[Tuple[PlayerTrain, PlayerJob, int]]

    def __init__(self, user_id):
        self.user_id = user_id
        self.version = None
        self.train_job_amount_list = []

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
            now = get_curr_server_datetime(version=instance)

            now_format = now.astimezone(settings.KST).strftime('%Y-%m-%d %H')
            srv_format = instance.login_server.astimezone(settings.KST).strftime('%Y-%m-%d %H')

            if now_format != srv_format:
                print(f"""[CreateVersion] Status=processing. passed over 1hour. start with new instance""")
                instance = RunVersion.objects.create(user_id=self.user_id, level_id=1)
                return instance

            if instance.next_event_datetime and instance.next_event_datetime > now:
                print(f"""[CreateVersion] Status=processing. waiting for next event. Next event time is[{instance.next_event_datetime.astimezone(settings.KST)}] / Now is {now.astimezone(settings.KST)}""")
                return None

            print(f"""[CreateVersion] Status=processing. start with previous instance""")
            return instance

        elif instance.is_completed_task:
            now = get_curr_server_datetime(version=instance)
            if instance.next_event_datetime and instance.next_event_datetime > now:
                print(f"""[CreateVersion] Status=Completed. waiting for next event. Next event time is[{instance.next_event_datetime.astimezone(settings.KST)}] / Now is {now.astimezone(settings.KST)}""")
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

    def _command_train_unload(self) -> Optional[datetime]:
        for train in trains_find(version=self.version, is_idle=True, has_load=True):
            if not warehouse_can_add(version=self.version, article_id=train.load_id, amount=train.load_amount):
                continue

            cmd = TrainUnloadCommand(version=self.version, train=train)
            self._send_commands(commands=[cmd])

        return trains_get_next_unload_event_time(version=self.version)

    def _command_daily_reward(self) -> Optional[datetime]:

        daily_reward = daily_reward_get_reward(version=self.version)
        if daily_reward:
            if daily_reward.can_claim_with_video:
                ret = warehouse_can_add_with_rewards(
                    version=self.version,
                    reward=daily_reward.get_today_rewards(),
                    multiply=2
                )

                if ret:
                    video_started_datetime_s = get_curr_server_str_datetime_s(version=self.version)
                    cmd = GameSleep(version=self.version, sleep_seconds=30)
                    self._send_commands(commands=[cmd])

                    cmd = GameWakeup(version=self.version)
                    self._send_commands(commands=[cmd])

                    cmd = DailyRewardClaimWithVideoCommand(
                        version=self.version,
                        reward=daily_reward,
                        video_started_datetime_s=video_started_datetime_s
                    )
                    self._send_commands(commands=[cmd])

            else:
                cmd = DailyRewardClaimCommand(version=self.version, reward=daily_reward)
                self._send_commands(commands=[cmd])

        return daily_reward_get_next_event_time(version=self.version)

    def _command_daily_offer(self) -> Optional[datetime]:
        daily_offer_items = daily_offer_get_slots(
            version=self.version,
            available_video=True,
            availble_gem=False,
            available_gold=False,
        )

        for offer_item in daily_offer_items:
            cmd = ShopPurchaseItem(version=self.version, offer_item=offer_item)
            self._send_commands(commands=[cmd])

        return daily_offer_get_next_event_time(version=self.version)

    def _command_whistle(self) -> Optional[datetime]:
        pass
        # for whistle in whistle_get_collectable_list(version=self.version):
        #     cmd = CollectWhistle(version=self.version, whistle=whistle)
        #     self._send_commands(commands=[cmd])
        #
        # return whistle_get_next_event_time(version=self.version)

    def _command_offer_container(self) -> Optional[datetime]:
        ret = None

        for offer in container_offer_find_iter(version=self.version, available_only=True):

            cmd_no = None
            cmd_list = []

            if offer.is_video_reward:
                cmd_no = self.version.command_no
                cmd = GameSleep(version=self.version, sleep_seconds=30)
                self._send_commands(commands=[cmd])

                cmd = GameWakeup(version=self.version)
                cmd_list.append(cmd)

            cmd = ShopBuyContainer(
                version=self.version,
                offer=offer,
                sleep_command_no=cmd_no,
            )
            cmd_list.append(cmd)
            self._send_commands(commands=cmd_list)

        for offer in container_offer_find_iter(version=self.version, available_only=False):
            container = offer.offer_container
            next_dt = offer.last_bought_at + timedelta(seconds=container.cooldown_duration)
            ret = update_next_event_time(previous=ret, event_time=next_dt)

        return ret

    def collectable_commands(self) -> Optional[datetime]:
        """

        """
        # todo: return next event time.
        ret: Optional[datetime] = None

        # daily reward
        next_dt = self._command_daily_reward()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        # daily offer
        next_dt = self._command_daily_offer()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        # train unload
        next_dt = self._command_train_unload()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        next_dt = self._command_whistle()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        # gift

        # ship

        # offer container
        next_dt = self._command_offer_container()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        return ret

    def _command_send_gold_destination(self) -> Optional[datetime]:
        ret = None
        for destination in destination_gold_find_iter(version=self.version):
            if destination.is_available(now=self.now):
                requirerments = destination.definition.requirements_to_dict
                possibles = []
                for train in trains_max_capacity(version=self.version, **requirerments):
                    if train.is_idle(now=self.now):
                        possibles.append(train)
                if possibles:
                    cmd = TrainSendToDestinationCommand(
                        version=self.version,
                        train=possibles[0],
                        dest=destination.definition,
                    )
                    self._send_commands(commands=[cmd])
            elif destination.train_limit_refresh_at and destination.train_limit_refresh_at > self.now:
                ret = update_next_event_time(previous=ret, event_time=destination.train_limit_refresh_at)

        return ret

    def _command_do_union_quest(self, train_job_amount_list):
        normal_workers, union_workers = get_number_of_working_dispatchers(version=self.version)
        max_normal_workers = self.version.dispatchers + 2
        max_union_workers = self.version.guild_dispatchers + 2

        for train, job, amount in train_job_amount_list:
            if union_workers >= max_union_workers:
                break
            train: PlayerTrain
            train.refresh_from_db()

            if train.is_working(now=self.now):
                continue
            if train.has_load:
                continue

            cmd = TrainDispatchToJobCommand(
                version=self.version,
                train=train,
                job=job,
                amount=amount,
            )
            self._send_commands(commands=[cmd])
            union_workers += 1

    def _command_prepare_ship_material(self) -> Optional[datetime]:
        """

        :return:
        """
        # warehouse_capacity = warehouse_max_capacity(version=self.version)
        # ship_materials = materials_find_from_ship(version=self.version)
        #
        # article_source_factory = article_find_all_article_and_factory(version=self.version)
        # article_source_destination = article_find_all_article_and_destination(version=self.version)
        # article_source_contract = article_find_all_article_and_contract(version=self.version)
        #
        # # ship
        #
        # # prepare materials
        # # redundancy_materials = materials_find_redundancy(version=self.version)
        pass

    def _command_collect_article_from_contract(self, article_id: int, amount: int, depth: int = 0) -> bool:
        if depth > 5:
            return False

        source_contract = article_find_contract(version=self.version, article_id=article_id)
        if not source_contract:
            return False

        contract_list = source_contract.get(article_id, [])
        for contract in contract_list:
            contract: PlayerContract

            has_amount = warehouse_get_amount(version=self.version, article_id=article_id)
            if amount <= has_amount:
                break

            condition = contract.conditions_to_article_dict
            if not condition:
                continue

            all_pass = []
            for required_article_id, required_article_amount in condition.items():
                required_article_amount = required_article_amount
                self._command_collect_article(article_id=required_article_id, amount=required_article_amount, depth=depth + 1)

                has_amount = warehouse_get_amount(version=self.version, article_id=required_article_id)
                if required_article_amount <= has_amount:
                    all_pass.append(True)
                else:
                    all_pass.append(False)

            if all_pass and all(all_pass):
                cmd = ContractAcceptCommand(version=self.version, contract=contract)
                self._send_commands(commands=[cmd])

        return True

    def _command_collect_article_from_destination(self, article_id: int, amount: int, depth: int = 0) -> bool:
        if depth > 5:
            return False

        normal_workers, union_workers = get_number_of_working_dispatchers(version=self.version)
        if normal_workers >= self.version.dispatchers + 2:
            return False

        source_destination = article_find_destination(version=self.version, article_id=article_id)

        if not source_destination:
            return False

        # requirerments = destination.definition.requirements_to_dict
        # possibles = []
        # for train in trains_max_capacity(version=self.version, **requirerments):
        #     if train.is_idle(now=self.now):
        #         possibles.append(train)
        # if possibles:
        #     cmd = TrainSendToDestinationCommand(
        #         version=self.version,
        #         train=possibles[0],
        #         dest=destination.definition,
        #     )
        #     self._send_commands(commands=[cmd])
        return True

    def _command_collect_article_from_factory(self, article_id: int, amount: int, depth: int = 0) -> bool:
        if depth > 5:
            return False

        source_factory = article_find_product(version=self.version, article_id=article_id)

        if not source_factory:
            return False

        products_list = source_factory.get(article_id, [])
        if not products_list:
            return False

        for product in products_list:
            found = True
            while found:
                found = False

                has_amount = warehouse_get_amount(version=self.version, article_id=article_id)
                if amount <= has_amount:
                    return True

                completed_orders, _, _ = factory_find_product_orders(
                    version=self.version,
                    factory_id=int(product.factory_id),
                    article_id=article_id,
                )

                for order in completed_orders:
                    found = True
                    cmd = FactoryCollectProductCommand(version=self.version, order=order)
                    self._send_commands(commands=[cmd])
                    break

        return True

    def _command_collect_article(self, article_id: int, amount: int, depth: int = 0):
        if depth > 5:
            return

        has_amount = warehouse_get_amount(version=self.version, article_id=article_id)
        if amount < has_amount:
            return

        if self._command_collect_article_from_destination(article_id=article_id, amount=amount, depth=depth + 1):
            return

        if self._command_collect_article_from_factory(article_id=article_id, amount=amount, depth=depth + 1):
            return

        if self._command_collect_article_from_contract(article_id=article_id, amount=amount, depth=depth + 1):
            return

    def _command_prepare_union_quest_materials(self) -> Optional[datetime]:
        warehouse_capacity = warehouse_max_capacity(version=self.version)
        warehouse_amount = warehouse_countable(version=self.version, basic=True, event=False, union=True)
        avg_count = warehouse_capacity // len(warehouse_amount)

        need_article: Dict[int, int] = {}

        for train, job, amount in self.train_job_amount_list:
            article_id = int(job.required_article_id)
            need_article.setdefault(article_id, 0)
            need_article[article_id] += amount

        for article_id, amount in need_article.items():
            need_amount = max(amount, avg_count)
            self._command_collect_article(article_id=article_id, amount=need_amount)

        return None

    def _command_prepare_factory(self) -> Optional[datetime]:
        for player_factory in factory_find_player_factory(version=self.version):
            if player_factory.factory.is_event:
                continue

            slot_count = player_factory.slot_count

            factory_product_list = []
            destination_product_list = []
            for product in factory_find_possible_products(version=self.version, player_factory=player_factory):
                ret = article_find_destination(version=self.version, article_id=product.article_id)
                destinations = ret.get(product.article_id, [])

                if destinations:
                    destination_product_list.append(product)
                else:
                    factory_product_list.append(product)

        pass

    def _command_prepare_redundancy(self) -> Optional[datetime]:
        pass

    def _command_prepare_population(self) -> Optional[datetime]:
        pass

    def update_union_progress(self, force: bool = False):
        if self.version.has_union and (force or abs((self.version.created - self.now).total_seconds()) > 10):
            for job in jobs_find(version=self.version, union_jobs=True):
                lb_helper = LeaderboardHelper(version=self.version, player_job_id=job.id, use_cache=USE_CACHE)
                lb_helper.run()

    def _command_dispatch_jobs(self) -> Optional[datetime]:
        if self.version.has_union:
            # union quest item
            self.train_job_amount_list = jobs_find_priority(version=self.version, with_warehouse_limit=False)

            if jobs_check_warehouse(version=self.version, train_job_amount_list=self.train_job_amount_list):
                self._command_do_union_quest(train_job_amount_list=self.train_job_amount_list)

        return None

    def _command_prepare_materials(self) -> Optional[datetime]:
        ret = None

        # Step 0. Ship
        # Step 1. contract. / union quest materials.
        # Step 2. Factory
        # Step 3. Redundancy
        # Step 4. Population

        next_dt = self._command_prepare_ship_material()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        next_dt = self._command_prepare_union_quest_materials()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        next_dt = self._command_prepare_factory()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        next_dt = self._command_prepare_redundancy()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        next_dt = self._command_prepare_population()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        return ret

    def dispatchers_commands(self) -> Optional[datetime]:
        ret: Optional[datetime] = None

        next_dt = self._command_send_gold_destination()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        next_dt = self._command_dispatch_jobs()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        # next_dt = self._command_prepare_materials()
        # ret = update_next_event_time(previous=ret, event_time=next_dt)
        return ret

    def on_finally(self) -> Optional[datetime]:
        ret = None

        for train in trains_find(version=self.version, is_idle=False):
            if train.route_arrival_time and train.route_arrival_time > self.now:
                ret = update_next_event_time(previous=ret, event_time=train.route_arrival_time)

        return ret

    def on_processing_status(self) -> Optional[datetime]:
        """

        """
        self.update_union_progress()

        ret: Optional[datetime] = None
        self._send_commands(commands=[HeartBeat(version=self.version)])

        # 2. collect
        next_dt = self.collectable_commands()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        next_dt = self.dispatchers_commands()
        ret = update_next_event_time(previous=ret, event_time=next_dt)

        # 3. assign job if
        # 4. prepare materials
        # 6. increase population
        return ret

    def _send_commands(self, commands: List[BaseCommand]):
        if not isinstance(commands, list):
            commands = [commands]
        cmd = RunCommand(version=self.version, commands=commands)
        cmd.run()

    def run(self):

        self.version = self.create_version()

        if not self.version:
            return

        try:
            ret = None
            self.now = get_curr_server_datetime(version=self.version)

            if self.version.is_queued_task:
                self.on_queued_status()
                self.version.set_processing(save=True, update_fields=[])

            if self.version.is_processing_task:
                next_dt = self.on_processing_status()
                ret = update_next_event_time(previous=ret, event_time=next_dt)

            next_dt = self.on_finally()
            ret = update_next_event_time(previous=ret, event_time=next_dt)

            self.version.next_event_datetime = ret
            self.version.save(
                update_fields=['next_event_datetime']
            )
        except TsRespInvalidOrExpiredSession as e:
            if self.version:
                now = get_curr_server_datetime(version=self.version)
                self.version.next_event_datetime = now + timedelta(minutes=10)
                self.version.set_completed(save=True, update_fields=[])

        except Exception as e:
            if self.version:
                self.version.set_error(save=True, msg=str(e), update_fields=[])
            raise e
