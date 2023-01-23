
# class BaseCommand(object):
#     """
#         BaseCommand
#     """
#     COMMAND = ''
#     helper: BaseCommandHelper
#     SLEEP_RANGE = (0.5, 1.5)
#     _start_datetime: datetime
#
#     def __init__(self, *, helper: BaseCommandHelper, **kwargs):
#         self.helper = helper
#
#     def get_parameters(self) -> dict:
#         return {}
#
#     def get_command(self):
#         self._start_datetime = self.helper.server_time.get_curr_datetime()
#
#         return {
#             'Command': self.COMMAND,
#             'Time': self.helper.server_time.get_curr_time_s(),
#             'Parameters': self.get_parameters()
#         }
#
#     def sleep(self):
#         self.helper._do_sleep(min_second=self.SLEEP_RANGE[0], max_second=self.SLEEP_RANGE[1])
#
#     def duration(self) -> int:
#         return 0
#
#     def end_datetime(self) -> datetime:
#         return self._start_datetime + timedelta(seconds=self.duration())
#
#     def __str__(self):
#         return f'''[{self.COMMAND}] / parameters: {self.get_parameters()}'''
#
#     def post_processing(self):
#         pass
#
###########################################################################
# Ship