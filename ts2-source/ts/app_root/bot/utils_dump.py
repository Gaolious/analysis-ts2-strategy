from functools import cached_property

from app_root.bot.models import RunVersion, PlayerBuilding, PlayerDestination, PlayerFactory, PlayerFactoryProductOrder, \
    PlayerJob, PlayerWarehouse


class RunVersionDump():

    run_version_id: int

    def __init__(self, run_version_id):
        self.run_version_id = run_version_id

    @cached_property
    def version(self):
        return RunVersion.objects.filter(id=self.run_version_id).first()

    def _dump_player_info(self):
        s = f"""
######################################################
# Player Info : {self.version.player_id} / {self.version.player_name}
######################################################
    - Level / XP : {self.version.level} / {self.version.xp}
    - Key / Gold / Gem : {self.version.key} / {self.version.gold} / {self.version.gem}
    - Request Time : {self.version.init_data_request_datetime} 
    - Response Time : {self.version.init_data_response_datetime} 
    - Server Time : {self.version.init_data_server_datetime} 
"""
        print(s)

    def _dump_player_building(self):
        print('######################################################')
        for building in PlayerBuilding.objects.filter(version_id=self.run_version_id).order_by('instance_id').all():
            s = f"""    -  Player Building # {building.id} : #{building.instance_id} / #{building.definition_id} . Lv {building.level} / {building.upgrade_task}"""
            print(s)

    def _dump_destination(self):
        print('######################################################')
        print('# Destination')
        s = []
        for destination in PlayerDestination.objects.filter(version_id=self.run_version_id).order_by('location_id').all():
            s.append(f"""    -  location_id : {destination.location_id}""")
            s.append(f"""    -  definition_id : {destination.definition_id}""")
            s.append(f"""    -  train_limit_count : {destination.train_limit_count}""")
            s.append(f"""    -  train_limit_refresh_time : {destination.train_limit_refresh_time}""")
            s.append(f"""    -  train_limit_refresh_at : {destination.train_limit_refresh_at}""")

        print('\n'.join(s))

    def _dump_factory(self):
        print('######################################################')
        print('# Factory')
        s = []
        for factory in PlayerFactory.objects.filter(version_id=self.run_version_id).order_by('id').select_related('factory').all():
            s.append(f"""    -  #{factory.factory_id} {factory.factory}""")
            for order in PlayerFactoryProductOrder.objects.filter(player_factory_id=factory.id).select_related('article').order_by('index').all():
                if order.finish_time:
                    if order.finish_time <= self.version.init_data_server_datetime:
                        s.append(f'        -  #{order.index} / 완료 / {order.article}')
                    else:
                        remain = (order.finish_time - self.version.init_data_server_datetime).total_seconds()
                        s.append(f'        -  #{order.index} / 생성중 ({remain} 남음) / {order.article}')
                else:
                    s.append(f'        -  #{order.index} / 대기중 / {order.article}')

        print('\n'.join(s))

    def _dump_job(self):
        print('######################################################')
        print('# Job')
        s = []
        for job in PlayerJob.objects.filter(version_id=self.run_version_id).order_by('id').select_related('required_article', 'location').all():
            s.append(f"""    -  #{job.job_id}""")
            s.append(f"""       Location:{job.location}, level:{job.job_level}, sequence:{job.sequence}, job_type:{job.job_type}, duration:{job.duration}, condition_multiplier:{job.condition_multiplier}, reward_multiplier:{job.reward_multiplier}""")
            s.append(f"""       재료 : {job.required_article} : {job.required_amount-job.current_article_amount}개 남음 (총 {job.required_amount}개)""")
            s.append(f"""       보상 : {job.str_rewards}""")
            # s.append(f"""       bonus {job.bonus}""")
            s.append(f"""       조건 : {job.str_requirements}""")

        print('\n'.join(s))

    def _dump_warehouse(self):

        print('######################################################')
        print('# Job')
        s = []
        for wh in PlayerWarehouse.objects.filter(version_id=self.run_version_id).order_by('id').all():
            s.append(f"""    -  #{wh}""")

        print('\n'.join(s))

    def dump(self):

        self._dump_player_info()

        self._dump_player_building()
        self._dump_destination()
        self._dump_factory()
        self._dump_job()
        self._dump_warehouse()
