# from functools import cached_property
#
# from app_root.bots.models import RunVersion
#
#
# class BaseManager(object):
#     run_version_id: int
#
#     def __init__(self, run_version_id: int):
#         self.run_version_id = run_version_id
#
#     @cached_property
#     def version(self):
#         return RunVersion.objects.filter(id=self.run_version_id).first()
#
#
# class WarehouseManager(BaseManager):
#     pass
#
#
# class FactoryManager(BaseManager):
#     pass
#
#
# class TrainManager(BaseManager):
#     pass
#
#
# class JobManager(BaseManager):
#     pass
#
#
# class DestinationManager(BaseManager):
#     pass
#
#
# class GiftManager(BaseManager):
#
#     def has_gift(self):
#         pass