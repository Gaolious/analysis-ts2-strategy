from datetime import timedelta

from django.utils import timezone

from app_root.players.models import (
    PlayerBuilding,
    PlayerDestination,
    PlayerFactory,
    PlayerFactoryProductOrder,
    PlayerJob,
    PlayerContractList,
    PlayerContract,
    PlayerGift,
    PlayerLeaderBoard,
    PlayerLeaderBoardProgress,
    PlayerTrain,
    PlayerWarehouse,
    PlayerWhistle,
    PlayerWhistleItem,
    PlayerAchievement,
    PlayerDailyReward,
    PlayerMap,
    PlayerQuest,
    PlayerVisitedRegion,
    PlayerShipOffer,
    PlayerCompetition,
    PlayerUnlockedContent,
    PlayerDailyOfferContainer,
    PlayerDailyOffer,
    PlayerDailyOfferItem,
    PlayerCityLoopParcel,
    PlayerCityLoopTask,
)
from app_root.servers.models import RunVersion


def run(*args, **kwargs):
    now = timezone.now() - timedelta(days=3)
    version_id_list = list(
        RunVersion.objects.filter(created__lte=now)
        .order_by("id")
        .values_list("id", flat=True)
    )

    MODEL_LIST = [
        PlayerBuilding,
        PlayerDestination,
        PlayerFactory,
        PlayerFactoryProductOrder,
        PlayerJob,
        PlayerContractList,
        PlayerContract,
        PlayerGift,
        PlayerLeaderBoard,
        PlayerLeaderBoardProgress,
        PlayerTrain,
        PlayerWarehouse,
        PlayerWhistle,
        PlayerWhistleItem,
        PlayerAchievement,
        PlayerDailyReward,
        PlayerMap,
        PlayerQuest,
        PlayerVisitedRegion,
        PlayerShipOffer,
        PlayerCompetition,
        PlayerUnlockedContent,
        PlayerDailyOfferContainer,
        PlayerDailyOffer,
        PlayerDailyOfferItem,
        PlayerCityLoopParcel,
        PlayerCityLoopTask,
    ]
    for version_id in version_id_list:
        for model in MODEL_LIST:
            print(f"{version_id} - {model}")
            model.objects.filter(version_id=version_id).delete()
        RunVersion.objects.filter(id=version_id).delete()
