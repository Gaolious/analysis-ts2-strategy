from datetime import datetime
from queue import PriorityQueue
from typing import Dict

from app_root.multies.flows import FLOWS_CREATE_RUN_VERSION
from app_root.servers.models import RunVersion
from app_root.users.models import User

"""
    Union Dependency.
    
    Player Dependency.
    
    
    check_queue - priority queue
    command_queue - just queue
    
    for loop
        call `check_xxxx` functions
            return [
                (before_sleep, command, after_sleep),
            ]
    
    MessageQueue = {
        version_id: {
            last_dt,
            [commands]
        }
    }
"""


class Message:
    event_time: datetime
    flow_id: int
    version: RunVersion

    def __init__(self, *, version: RunVersion, event_time: datetime, flow_id: int):
        self.event_time = event_time
        self.flow_id = flow_id
        self.version = version

    def __lt__(self, other):
        l = (self.event_time, self.flow_id, self.version_id)
        r = (other.event_time, other.flow_id, other.version_id)

        return l < r


class MultiStrategy:
    users: Dict[int, User] = {}  # [user.id, User]
    queues: PriorityQueue

    MAPPING = {
        # FLOWS_CREATE_RUN_VERSION: create_run_version,
    }

    def __init__(self, queryset):
        self.users = {}
        self.queues = PriorityQueue()
        self.versions = {}

        for o in queryset.all():
            self.users.update({o.id: o})

    # def run(self):
