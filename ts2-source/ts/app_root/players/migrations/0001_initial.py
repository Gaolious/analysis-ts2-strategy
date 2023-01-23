# Generated by Django 4.1.4 on 2023-01-22 08:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('servers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlayerFactory',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('slot_count', models.IntegerField(verbose_name='slot count')),
                ('factory', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.tsfactory')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Factory',
                'verbose_name_plural': 'Player Factories',
            },
        ),
        migrations.CreateModel(
            name='PlayerJob',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('job_id', models.CharField(max_length=100, verbose_name='job id')),
                ('job_level', models.IntegerField(default=0, verbose_name='CraftTime')),
                ('sequence', models.IntegerField(default=0, null=True, verbose_name='Sequence')),
                ('job_type', models.IntegerField(default=0, verbose_name='JobType')),
                ('duration', models.IntegerField(default=0, verbose_name='Duration')),
                ('condition_multiplier', models.IntegerField(default=0, verbose_name='ConditionMultiplier')),
                ('reward_multiplier', models.IntegerField(default=0, verbose_name='RewardMultiplier')),
                ('required_amount', models.IntegerField(default=0, verbose_name='required_amount')),
                ('current_article_amount', models.IntegerField(default=0, verbose_name='CurrentArticleAmount')),
                ('reward', models.CharField(default='', max_length=255, verbose_name='reward')),
                ('bonus', models.CharField(default='', max_length=255, verbose_name='bonus')),
                ('expires_at', models.DateTimeField(default=None, null=True, verbose_name='ExpiresAt')),
                ('requirements', models.CharField(default='', max_length=255, verbose_name='reward')),
                ('unlock_at', models.DateTimeField(default=None, null=True, verbose_name='UnlocksAt')),
                ('collectable_from', models.DateTimeField(default=None, null=True, verbose_name='CollectableFrom')),
                ('completed_at', models.DateTimeField(default=None, null=True, verbose_name='CompletedAt')),
                ('job_location', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.tsjoblocation')),
                ('required_article', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.tsarticle')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Job',
                'verbose_name_plural': 'Player Jobs',
            },
        ),
        migrations.CreateModel(
            name='PlayerLeaderBoard',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('leader_board_id', models.CharField(default='', max_length=50, verbose_name='LeaderboardId')),
                ('leader_board_group_id', models.CharField(default='', max_length=50, verbose_name='LeaderboardGroupId')),
                ('player_job', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='players.playerjob')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Leader Board',
                'verbose_name_plural': 'Player Leader Boards',
            },
        ),
        migrations.CreateModel(
            name='PlayerWhistle',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('category', models.IntegerField(default=0, verbose_name='category')),
                ('position', models.IntegerField(default=0, verbose_name='position')),
                ('spawn_time', models.DateTimeField(blank=True, default=None, null=True, verbose_name='SpawnTime')),
                ('collectable_from', models.DateTimeField(blank=True, default=None, null=True, verbose_name='CollectableFrom')),
                ('is_for_video_reward', models.BooleanField(blank=True, default=None, null=True, verbose_name='IsForVideoReward')),
                ('expires_at', models.DateTimeField(blank=True, default=None, null=True, verbose_name='ExpiresAt')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Whistle',
                'verbose_name_plural': 'Player Whistles',
            },
        ),
        migrations.CreateModel(
            name='PlayerWhistleItem',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('value', models.IntegerField(default=0, verbose_name='value')),
                ('amount', models.IntegerField(default=0, verbose_name='amount')),
                ('article', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.tsarticle')),
                ('player_whistle', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='players.playerwhistle')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Whistle Item',
                'verbose_name_plural': 'Player Whistle Items',
            },
        ),
        migrations.CreateModel(
            name='PlayerWarehouse',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('amount', models.IntegerField(default=0, verbose_name='amount')),
                ('article', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.tsarticle')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Warehouse',
                'verbose_name_plural': 'Player Warehouses',
            },
        ),
        migrations.CreateModel(
            name='PlayerVisitedRegion',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('region', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.tsregion')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Visited Region',
                'verbose_name_plural': 'Player Visited Regions',
            },
        ),
        migrations.CreateModel(
            name='PlayerTrain',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('instance_id', models.IntegerField(default=0, verbose_name='instance_id')),
                ('region', models.IntegerField(blank=True, default=None, null=True, verbose_name='region')),
                ('has_route', models.BooleanField(blank=True, default=False, verbose_name='has route')),
                ('route_type', models.CharField(blank=True, default=None, max_length=20, null=True, verbose_name='route_type')),
                ('route_definition_id', models.IntegerField(blank=True, default=None, null=True, verbose_name='route_definition_id')),
                ('route_departure_time', models.DateTimeField(blank=True, default=None, null=True, verbose_name='route_departure_time')),
                ('route_arrival_time', models.DateTimeField(blank=True, default=None, null=True, verbose_name='route_arrival_time')),
                ('has_load', models.BooleanField(blank=True, default=False, verbose_name='has load')),
                ('load_amount', models.IntegerField(default=0, verbose_name='load amount')),
                ('level', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.tstrainlevel')),
                ('load', models.ForeignKey(db_constraint=False, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.tsarticle')),
                ('train', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.tstrain')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Train',
                'verbose_name_plural': 'Player Trains',
            },
        ),
        migrations.CreateModel(
            name='PlayerShipOffer',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('definition_id', models.IntegerField(null=True, verbose_name='definition_id')),
                ('conditions', models.CharField(default='', max_length=255, verbose_name='Conditions')),
                ('reward', models.CharField(default='', max_length=255, verbose_name='reward')),
                ('arrival_at', models.DateTimeField(null=True, verbose_name='ArrivalAt')),
                ('expire_at', models.DateTimeField(null=True, verbose_name='ExpireAt')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Ship Offer',
                'verbose_name_plural': 'Player Ship Offers',
            },
        ),
        migrations.CreateModel(
            name='PlayerQuest',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('milestone', models.IntegerField(default=0, verbose_name='Milestone')),
                ('progress', models.IntegerField(default=0, verbose_name='Progress')),
                ('job_location', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.tsjoblocation')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Quest',
                'verbose_name_plural': 'Player Quests',
            },
        ),
        migrations.CreateModel(
            name='PlayerMap',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('region_name', models.CharField(default='', max_length=20, verbose_name='region name')),
                ('spot_id', models.IntegerField(default=0, verbose_name='SpotId')),
                ('position_x', models.IntegerField(default=0, verbose_name='Position X')),
                ('position_y', models.IntegerField(default=0, verbose_name='Position Y')),
                ('connections', models.CharField(default='', max_length=50, verbose_name='connections')),
                ('is_resolved', models.BooleanField(default=False, verbose_name='IsResolved')),
                ('content', models.CharField(default='', max_length=255, verbose_name='region name')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Map',
                'verbose_name_plural': 'Player Maps',
            },
        ),
        migrations.CreateModel(
            name='PlayerLeaderBoardProgress',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('player_id', models.IntegerField(default=0, verbose_name='PlayerId')),
                ('avata_id', models.IntegerField(default=0, verbose_name='AvatarId')),
                ('firebase_uid', models.CharField(default='', max_length=50, verbose_name='FirebaseUid')),
                ('player_name', models.CharField(default='', max_length=50, verbose_name='player_name')),
                ('progress', models.IntegerField(default=0, verbose_name='progress')),
                ('position', models.IntegerField(default=0, verbose_name='position')),
                ('last_updated_at', models.DateTimeField(default=0, verbose_name='LastUpdatedAt')),
                ('reward_claimed', models.BooleanField(default=False, verbose_name='RewardClaimed')),
                ('rewards', models.CharField(default='', max_length=255, verbose_name='rewards')),
                ('leader_board', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='players.playerleaderboard')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Leader Board Progress',
                'verbose_name_plural': 'Player Leader Board Progresses',
            },
        ),
        migrations.CreateModel(
            name='PlayerGift',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('job_id', models.CharField(max_length=100, verbose_name='job id')),
                ('reward', models.CharField(default='', max_length=255, verbose_name='reward')),
                ('gift_type', models.IntegerField(default=0, verbose_name='gift_type')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Gift',
                'verbose_name_plural': 'Player Gifts',
            },
        ),
        migrations.CreateModel(
            name='PlayerFactoryProductOrder',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('index', models.IntegerField(default=0, verbose_name='index')),
                ('amount', models.IntegerField(default=0, verbose_name='amount')),
                ('craft_time', models.IntegerField(default=0, verbose_name='CraftTime')),
                ('finish_time', models.DateTimeField(default=None, null=True, verbose_name='FinishTime')),
                ('finishes_at', models.DateTimeField(default=None, null=True, verbose_name='FinishesAt')),
                ('article', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.tsarticle')),
                ('player_factory', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='players.playerfactory')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Factory Product Order',
                'verbose_name_plural': 'Player Factory Product Orders',
            },
        ),
        migrations.CreateModel(
            name='PlayerDestination',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('train_limit_count', models.IntegerField(null=True, verbose_name='train_limit_count')),
                ('train_limit_refresh_time', models.DateTimeField(null=True, verbose_name='train_limit_refresh_time')),
                ('train_limit_refresh_at', models.DateTimeField(null=True, verbose_name='train_limit_refresh_at')),
                ('multiplier', models.IntegerField(default='', null=True, verbose_name='multiplier')),
                ('definition', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.tsdestination')),
                ('location', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.tslocation')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Destination',
                'verbose_name_plural': 'Player Destination',
            },
        ),
        migrations.CreateModel(
            name='PlayerDailyReward',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('available_from', models.DateTimeField(blank=True, default=None, null=True, verbose_name='AvailableFrom')),
                ('expire_at', models.DateTimeField(blank=True, default=None, null=True, verbose_name='ExpireAt')),
                ('rewards', models.CharField(default='', max_length=255, verbose_name='Rewards')),
                ('pool_id', models.IntegerField(default=0, verbose_name='PoolId')),
                ('day', models.IntegerField(default=0, verbose_name='Day')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Daily Reward',
                'verbose_name_plural': 'Player Daily Rewards',
            },
        ),
        migrations.CreateModel(
            name='PlayerContractList',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('contract_list_id', models.IntegerField(default=0, verbose_name='contract list id')),
                ('available_to', models.DateTimeField(default=None, null=True, verbose_name='Available To')),
                ('next_replace_at', models.DateTimeField(default=None, null=True, verbose_name='Next Replace At')),
                ('next_video_replace_at', models.DateTimeField(default=None, null=True, verbose_name='Next Video Replace At')),
                ('next_video_rent_at', models.DateTimeField(default=None, null=True, verbose_name='Next Video Rent At')),
                ('next_video_speed_up_at', models.DateTimeField(default=None, null=True, verbose_name='Next Video SpeedUp At')),
                ('expires_at', models.DateTimeField(default=None, null=True, verbose_name='Expires At')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Contract List',
                'verbose_name_plural': 'Player Contract Lists',
            },
        ),
        migrations.CreateModel(
            name='PlayerContract',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('slot', models.IntegerField(default=0, verbose_name='slot')),
                ('conditions', models.CharField(default='', max_length=255, verbose_name='conditions')),
                ('reward', models.CharField(default='', max_length=255, verbose_name='reward')),
                ('usable_from', models.DateTimeField(default=None, null=True, verbose_name='UsableFrom')),
                ('available_from', models.DateTimeField(default=None, null=True, verbose_name='AvailableFrom')),
                ('available_to', models.DateTimeField(default=None, null=True, verbose_name='AvailableTo')),
                ('expires_at', models.DateTimeField(default=None, null=True, verbose_name='AvailableTo')),
                ('contract_list', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='players.playercontractlist')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Contract',
                'verbose_name_plural': 'Player Contracts',
            },
        ),
        migrations.CreateModel(
            name='PlayerBuilding',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('instance_id', models.IntegerField(null=True, verbose_name='instance id')),
                ('definition_id', models.IntegerField(null=True, verbose_name='instance id')),
                ('rotation', models.IntegerField(null=True, verbose_name='instance id')),
                ('level', models.IntegerField(null=True, verbose_name='instance id')),
                ('upgrade_task', models.CharField(default='', max_length=255, null=True, verbose_name='upgrade task')),
                ('parcel_number', models.IntegerField(default=None, null=True, verbose_name='parcel_number')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Building',
                'verbose_name_plural': 'Buildings',
            },
        ),
        migrations.CreateModel(
            name='PlayerAchievement',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, editable=False, verbose_name='created date')),
                ('modified', models.DateTimeField(blank=True, editable=False, verbose_name='modified date')),
                ('achievement', models.CharField(default='', max_length=255, verbose_name='achievement')),
                ('level', models.IntegerField(default=0, verbose_name='level')),
                ('progress', models.IntegerField(default=0, verbose_name='level')),
                ('version', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='servers.runversion')),
            ],
            options={
                'verbose_name': 'Player Achievement',
                'verbose_name_plural': 'Player Achievements',
            },
        ),
    ]
