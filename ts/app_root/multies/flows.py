from datetime import datetime
from queue import PriorityQueue

from app_root.servers.models import RunVersion

# INIT - CREATE VERSION
FLOWS_CREATE_RUN_VERSION = 100

# CHECK
FLOWS_CHECK_FACTORY = 201

# CACULATE JOB PRIORITY

# DISPATCH JOB

# DISPATCH DESTINATION

# PRODUCE PRODUCT IN FACTORY

#


class FlowMixin:
    curr_flow_id: int
    next_flow_id: int
    next_event_time: datetime
    queue: PriorityQueue
    version: RunVersion

    def __init__(self, version: RunVersion, queue: PriorityQueue, **kwargs):
        self.version = version
        self.queue = queue

    def run(self):
        pass


class InitCreateRunVersion:
    pass
