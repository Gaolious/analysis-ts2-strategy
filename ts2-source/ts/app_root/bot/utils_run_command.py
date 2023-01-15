import json
import random
import uuid
from hashlib import md5
from typing import List, Iterator, Dict

from django.conf import settings

from app_root.bot.mixins_command import TrainUnloadCommand, BaseCommand, CollectGiftCommand, \
    TrainSendToDestinationCommand, \
    BaseCommandHelper, CollectJobReward, CollectWhistle
from app_root.bot.utils_request import CrawlingHelper
from core.utils import Logger

LOGGING_MENU = 'utils_run_command'


class CommandHelper(BaseCommandHelper):

    def _command_collect_from_train(self) -> Iterator[TrainUnloadCommand]:
        """
            기차에서 수집할게 있는가 ?
        """
        for train in self.find_trains_iter():
            if train.has_load:
                yield TrainUnloadCommand(helper=self, train=train)

    def _command_collect_from_gift(self) -> Iterator[CollectGiftCommand]:
        """
            수집할 gift가 있는가 ?

        :return:
        """
        """
            POST /api/v2/command-processing/run-collection HTTP/1.1
            PXFD-Request-Id: fceb920f-c2e5-4179-b7b9-61ae49f75270
            PXFD-Retry-No: 0
            PXFD-Sent-At: 2023-01-09T02:37:59.667Z
            PXFD-Client-Information: {"Store":"google_play","Version":"2.6.2.4023","Language":"en"}
            PXFD-Client-Version: 2.6.2.4023
            PXFD-Device-Token: 662461905988ab8a7fade82221cce64b
            PXFD-Game-Access-Token: 2af7f36d-1392-59f4-841b-5207bbc735ec
            PXFD-Player-Id: 61561146
            Content-Type: application/json
            Content-Length: 187
            Host: game.trainstation2.com
            Accept-Encoding: gzip, deflate
            
            {
                "Id":2,
                "Time":"2023-01-09T02:37:59Z",
                "Commands":[
                    {
                        "Command":"Gift:Claim",
                        "Time":"2023-01-09T02:37:59Z",
                        "Parameters":{
                            "Id":"8295a2de-d048-4228-ac02-e3d36c2d3b4a"
                        }
                    }
                ],
                "Transactional":false
            }        
        """
        for gift in self.find_gift_iter():
            if gift.job_id:
                yield CollectGiftCommand(helper=self, gift=gift)

    def _command_collect_from_event_jobs(self) -> Iterator[CollectJobReward]:
        for job in self.find_jobs(event_jobs=True, collectable_jobs=True):
            print(job.job_id, job.str_requirements)
            print("completed : ", job.collectable_from, job.completed_at, job.str_rewards)
            if job.is_collectable(init_data_server_datetime=self.run_version.init_data_server_datetime):
                yield CollectJobReward(helper=self, job=job)

    def _command_collect_from_whistle(self) -> Iterator[CollectWhistle]:
        """
{'buffer': 'POST /api/v2/command-processing/run-collection HTTP/1.1\r\nPXFD-Request-Id: 06ec734c-466b-4c2b-a1c1-37352444b819\r\nPXFD-Retry-No: 0\r\nPXFD-Sent-At: 2023-01-12T02:14:44.124Z\r\nPXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"ko"}\r\nPXFD-Client-Version: 2.6.3.4068\r\nPXFD-Device-Token: 662461905988ab8a7fade82221cce64b\r\nPXFD-Game-Access-Token: 80e1e3c6-28f8-5d50-8047-a9284469d1ef\r\nPXFD-Player-Id: 61561146\r\nContent-Type: application/json\r\nContent-Length: 175\r\nHost: game.trainstation2.com\r\nAccept-Encoding: gzip, deflate\r\n\r\n'}

{'buffer': '{"Id":10,"Time":"2023-01-12T02:14:44Z","Commands":[{"Command":"Whistle:Collect","Time":"2023-01-12T02:14:43Z","Parameters":{"Category":1,"Position":1}}],"Transactional":false}'}

{"Success":true,"RequestId":"06ec734c-466b-4c2b-a1c1-37352444b819","Time":"2023-01-12T02:14:44Z","Data":{"CollectionId":10,"Commands":[{"Command":"Whistle:Spawn","Data":{"Whistle":{"Category":1,"Position":1,"SpawnTime":"2023-01-12T02:20:43Z","CollectableFrom":"2023-01-12T02:20:43Z","Reward":{"Items":[{"Id":8,"Value":103,"Amount":4}]},"IsForVideoReward":false}}},{"Command":"Achievement:Change","Data":{"Achievement":{"AchievementId":"whistle_tap","Level":5,"Progress":16413}}}]}}
        :return:
        """

        for whistle in self.find_whistle():
            if whistle.is_collectable(init_data_server_datetime=self.run_version.init_data_server_datetime):
                yield CollectWhistle(helper=self, whistle=whistle)

    def command_send_train_to_destination(self) -> Iterator[TrainSendToDestinationCommand]:
        """

        """
        Logger.info(
            menu=LOGGING_MENU, action='command_send_train_to_destination',
            num_total_dispatchers=self.number_of_total_dispatchers,
            num_work_dispatchers=self.number_of_working_dispatchers,
            num_idle_dispatchers=self.number_of_idle_dispatchers,
            num_gold_destinations=len(self._gold_destinations),
        )

        if self.number_of_working_dispatchers == 0:

            cmd_list = []

            self.train_reset_reserve()

            for dest in self.find_gold_destination_iter(only_available=True):
                possible_region = dest.definition.get_region_requirements()
                possible_rarity = dest.definition.get_rarity_requirements()
                param = {}
                if possible_region:
                    param.update({'possible_region_id_list': possible_region})
                if possible_rarity:
                    param.update({'possible_rarity_list': possible_rarity})

                trains = list(self.find_trains_iter(**param))
                trains.sort(key=lambda x: x.capacity, reverse=True)

                train = trains[0] if len(trains) > 0 else None
                if train and train.is_idle(self.run_version.init_data_server_datetime):
                    cmd_list.append((dest, train))
                    self.train_reserve(train)

            if 0 < len(cmd_list) == self.get_gold_destination_count():
                for dest, train in cmd_list:
                    yield TrainSendToDestinationCommand(
                        helper=self,
                        train=train,
                        dest=dest.definition
                    )

    def command_prepare_materials_for_event_job(self):
        pass

    def command_prepare_materials_for_union_job(self):
        pass

    def command_prepare_materials_for_redundancy(self):
        pass

    def command_prepare_materials(self):
        print("event")
        for job in self.find_jobs(event_jobs=True):
            print(job.job_id, job.str_requirements)

        print("union")
        for job in self.find_jobs(union_jobs=True):
            print(job.job_id, job.str_requirements, job.str_rewards)

    def command_collect(self):
        for cmd in self._command_collect_from_gift():
            print(cmd)
            cmd.sleep()
            self._send_run_collection(url=self.url, commands=[cmd])

        for cmd in self._command_collect_from_event_jobs():
            print(cmd)
            cmd.sleep()
            self._send_run_collection(url=self.url, commands=[cmd])

        for cmd in self._command_collect_from_train():
            print(cmd)
            cmd.sleep()
            self._send_run_collection(url=self.url, commands=[cmd])

        for cmd in self._command_collect_from_whistle():
            print(cmd)
            cmd.sleep()
            self._send_run_collection(url=self.url, commands=[cmd])

    def command_dispatch_job(self):
        pass

    def run(self):
        self.command_collect()

    def check_response(self, data):
        data = json.loads(data, strict=False)
        if data.get('Success') is not True:
            print(data)
            raise Exception(str(data))

    def start_game(self, start_url):
        """

        :param start_url:
        :return:
        """

        client_info = {
            "Store": str(settings.CLIENT_INFORMATION_STORE),
            "Version": str(settings.CLIENT_INFORMATION_VERSION),
            "Language": str(settings.CLIENT_INFORMATION_LANGUAGE),
        }

        headers = {
            'PXFD-Request-Id': str(uuid.uuid4()),  # 'ed52b756-8c2f-4878-a5c0-5d249c36e0d3',
            'PXFD-Retry-No': '0',
            'PXFD-Sent-At': self.server_time.get_curr_time(),
            'PXFD-Client-Information': json.dumps(client_info, separators=(',', ':')),
            'PXFD-Client-Version': str(settings.CLIENT_INFORMATION_VERSION),
            'PXFD-Device-Token': md5(self.user.android_id.encode('utf-8')).hexdigest(),
            'PXFD-Game-Access-Token': str(self.user.game_access_token),
            'PXFD-Player-Id': str(self.user.player_id),
            'Accept-Encoding': 'gzip, deflate',
        }
        Logger.info(menu=LOGGING_MENU, action='start_game', msg='before request', url=start_url)
        resp = CrawlingHelper.post(
            url=start_url,
            headers=headers,
            payload={},
            cookies={},
            params={},
        )
        resp_status_code = resp.status_code
        resp_body = resp.content.decode('utf-8')
        resp_headers = {k: v for k, v in resp.headers.items()}
        resp_cookies = {k: v for k, v in resp.cookies.items()}

        Logger.info(
            menu=LOGGING_MENU, action='start_game', msg='after request',
            status_code=str(resp_status_code),
            body=str(resp_body),
            headers=str(resp_headers),
            cookies=str(resp_cookies),
        )

        self.check_response(resp_body)

        return resp_body


    def update_device_id(self, update_device_id_url):
        """
    POST /api/v2/authentication/update-device-id HTTP/1.1
    PXFD-Request-Id: f15d13a4-72a7-4762-89ed-4ff628ea015d
    PXFD-Retry-No: 0
    PXFD-Sent-At: 2023-01-14T10:27:23.000Z
    PXFD-Client-Information: {"Store":"google_play","Version":"2.6.3.4068","Language":"en"}
    PXFD-Client-Version: 2.6.3.4068
    PXFD-Device-Token: 662461905988ab8a7fade82221cce64b
    PXFD-Game-Access-Token: d2a6ba7d-6e06-523a-9be7-03d58aaf654e
    PXFD-Player-Id: 61561146
    Content-Type: application/json
    Content-Length: 4192
    Host: game.trainstation2.com
    Accept-Encoding: gzip, deflate\r\n\r\n'}

14 19:27:23 | T:10131 | I | SSL_AsyncWrite  | buffer :
    {
        "RememberMeToken":"eyJlcGsiOnsia3R5IjoiRUMiLCJjcnYiOiJQLTM4NCIsIngiOiJ3RjBLYkJQNTVqeWtKX1RBNW9sN1hfbVlYSEV3em1NWG5ZZlkyb3A4Xzk3a0RHWkNFdHZ3dEtFTnZMTTJNOEp2IiwieSI6ImF4LUF4N3NpeVBzLXdDQXBMT09EN2FYVFdyS1BMdmNNSC1rcFZjX3JEeWQxV2RBMVR2TjN1bG9LMnZ2czFzOVQifSwiYWxnIjoiRUNESC1FUytBMjU2S1ciLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiemlwIjoiREVGIn0.6lZeo-_LGuEQRz9B6HzpNVibJcnN_sQEw4O0kWitRW8erxIOuqPnI3AvsKfx7JpB6EmYgsJKTpTyKzHHMqry_TezmnKAePan.7-TThtN7RzBG21lt-E4nPQ.jtH1OmvWwiborTX3EVUlerA41LURCSYLNTUtA5ppbC5uWnKoqaaUH_wUnZQYbh-DQyLlMy-9ziP7T7v_9hcF0IEEMAUpfuzlf-BY037UJ9DGsS3JpmFHKbkVw11wsoL88geCYm5hZIRBIwkyGjS40eMdmic-iDQwPV4MvB0EjDOX-sufAB0vrrMlp0UtfWVUjK7TxQnXrMjH6N78PR_yWym14zhz_gDzKd0EV0qRGGtueP0-yC76djBcgQO5-3zp86XSDg4nsRAkOH3hxtqKplGkg_pazPyS8g2aJp8FLDuNGCp7s8ylDMgLK75eNsnOseZ_0NP352r6G3Ztbua4wxvAirfdovJ8SQtbed7oRcmlSZFkpojOP4KPoxUPN621gPvRSF8YhjiHdBztRo_MoB5fMUaNVelhRXxsAa1FjgZKusKcgmc4lXN0QvsFMk9B8poPdwbwAmx2tISWV_F1v_oMbX0lF8j2GqFxZr0tJAI8DGoz4aX9QPN3inx4kYWnT_tsN03Ywvsy_HD5VFTtL5xqccYcFkHEDVIOaOQSulbFThi7dshPK0RZeU0DqsVj9f3YiBBQ0quu8BT5xIBRGZmn46uUUK80nUq9RHJybe0-gTN6QBy4-ertlqBVh8rNeV58bx8jN5Uet9jFifEQJoVNXgaKVDcqc53ZLxL5dKKBTYBvWH15NtzuZuPB9qrRGYCpU72vuiM_JTti0jAJ16cAdnc3KjFmoqrn3fI2W0qW-0BvGikjnNMZGeEHHatS4KeEA2rJOuk4dapQuExo8rCynB47_lQxa7D-SzzQggHsoGeArrmm-4P7YD6Wkm6zpM82OKRg0ystrOubDPMKsuI9ofqV_VYlXdseONRkx99fvTdGUJZ3xGgVoNq5iALCPsTiPTAb1vnZ2o_zQ0iMPONwTuBq8dHZILsHzX_mUnV-urB4Ltm2XMmgYhgz5Fp6d9f6cK2VeM6DEv1IRnfF9dxrovGVHpKw3ck82MfiZC1wSpVr-hfb4lRpWCgRw88sXk8k14kiW7YQMdr1e-y99fqfKE6T4MTCh1cfhi8yEXBlTShpJvt1O9oP0d1OnZBuploe3f7xns_o-9GqUpcgLfkbqFlX40TiB0GbciXKCowzbZrmbYztStl3leB4WeawtEvVQnmAC-rjVO_sraUYW1T9BpZyQSTJqrdzSi4w5MpgDxS8uFXXHq0g_7IhbIUiKj3SqfAy59rxSa1A-E5z1N8cVrVuySxwTa5qgFbu3UYGnAO5xxa9nyyb_Z1xGN83xx59Luqg7mwtBpDDdlvEIZCR52SG3p77xTyq5OlxEtD5INyNqLOLFGAusAvw02lb7zx94L-gr-zNluWhekKAoV7-SU9F0xxSuupST_9Q6_iFMgk8B6Vw0CVoWnPpZubeDb9r9cbaixpFZ3bGFZfblc5JEfri0FSX81uoJiG1ByURJL_Vzh9_ljznI_hSkWkm3sKm6B5g9P8Qk_7dFs_UYu5EYa8k84KWNHXuCQiWChBzs6G4P5MTTFj_pCCX_vYbC-BeKYriUY_kFjGj97ss32Osdnx80XJVsK9piAasgkYuULfX6bTxDYAra3GgqDdenGPs0BhkcVy1QvR0ABKCZrFPJ5bvKB6VevMKoKOk-b_9z5gkLqC64F2HUm3FFvM6h00C6abo0lYstVa3TGhIbuYq7CRnFzgLL0GkPuobAYBO6IkHDdKZ0UMNEUGl8uSYeXoSTFvjb8e0-RYAVUWOJproFW1IPmfuW1i6m_KVJlaH7EY0cplg9uA8rZk48fPR8c6nB-uUXVCSfeeGdr_E-9iIK6X9UQYMF2MTSE-O5LUQhImi07WSmi0o4Im3NOoQ5N5QUd-DQhKHu-ImjcAO2PXe1kEtvoo0tkop7Ev_V1AkcZeuQXcO87HqC-ruuTdU8Bi__rg19Vrrk1QbqKSvdixwLbMsn1tpgnA1cAsJY-HhaSprGHUj_mFrTGOxkOvhJ5rLLRbd7uf88vy3sHoAZKLStn41s7-EK1ozacCoqg3z29S_HT0Q5yg26-M5IaX4GK9FPYRnLNenBlDR4wIxMFyJ83pQj38RMmunDqkqIlmvlnMs3ozZnaTdLl32mOPg0yqiXS5NUnR-sP7W6-myzwv27Ze6tOE_mDWmJdMAMLfWzS5UP_tP3viPRsRxAaOMLHSrKI49tE4FVxeiJ0IT8ud5hUV5vmfx2q0fb6BfOZOFiYIIQFEq1g0_BuU_IGUaKSjhWX1fuk8Ccc01B0Wr9tTVR7h-2bSdXpIp26S103QSOj-Ladix6eKPRLR-eJA0GvrFfgyIwfFQvHKttpSun8vqW7rh6KSuKoozG4ycj6WTQ8bUpwJrFAk_acO_3aT5GshzwF9QmRCrzPzTCv-tmxeuzTgRW82TFEATlYHhI8pZLGebcoeemI6nfVMspBkf7fV_P7gcndo-VlzBq5F3v_XhWqBK7OXSubhJn94ZcqyEJN5w5mWcvBQ0bLLFJS6lruVY3C82--4e7Ccpe07jRvXHCPHYbThyCpngDL5oNdRfeulvuOpDHG_5KnthfakDdooq0BLYt52Swlj5QyMOPiZ3_1ro_aYAnZVs78xCkZAdo3RBF8pjkrq-_69Fs47fWtvunK39_boGNxlJvU5WhCA8Uxs7KP5lYdBroHpdEI4cFu7e2IkUgEgPDFG2I5xf8qnr4FlwG_ci6RzQqQiEzQrCirHYMsFf9lpiG6BXQX9UdYZza_smULIBKmiDT6_MA4jOXyk9Y771fF4ysv7_boJGvWeTz0mc7w__R8eSgVnQj7KPA8PWDSvhGkZUvVWG6--CusWHSqQ-uXRN6FKotvlge9zMADVRGvXr4cjjb2GXKfm9lFp8oTPjnZjHUr8FZUG6M3D3nAZrecIaH2fs9fgiqWKPyw4yO7zIsHFec6cgM8ubjCH-BOKFvy30nNUsxbKZGKb3K3mKFtdgNLEZjKOKtskOkYUGKvl68mDmCeg4lRCN_WIynU840IezfpPM2aS6a3RpbsqFFvnwpkWstmvezvEaiNLQUpoh9qpopUQwMH6IAvCNO0Mm2ONioipvG8kM35sxunH0NZTlattSIkUYrY7a8-ByTffzPEBE5aeO540lsrWDQTgSJDq-fGkCDuTmiurhm4YNhFPPNIm2CUEdfIF5RuCf9EhamORVdKduFaRC4dm_vK0_8Nv3Lt7qpWf9QMwu6Jr1bNhRhypqy912DrwuYrOUYOW2pdB70pCS5tWR37R6deoCBq7PxZd8H5q0z3HkVjlKt22IqoVsMxX4QXxVLMBs4yz32-yAqH_ufpqEqDiyLkzSKWu2pVGGSIjqCDEj1eZJofTYomQj9vjBvxEHJ3_84E1SQ8TiQlUcDXoWHMPT6MSwG7wbAng8ACJ3XLBjXKF74cH95o9YGp3VKLuQLPHswxC37Z1vcKRHiq-27A1IyYVNe3mqnW7zhabY_igE4I_Ab9Eryef4VAIL3KEx_spq3_OMkZnRVquEZuqWAuRZq7bTuUH0djIlcwdCGU5cUYSkqjm25fQbgGE23oI6vJMdXLe6X3GQC8zfdm8Fl8srDzexP--rC-SQ6vmomLUBRSNwLMDvWy2sstLgi7LgWD-6uiVsvSdf-EGAKb3wueZPJ3tw5Kn1zsnE.NUNhomePwwwKZyd5YjxP88my7vMqOz__hWNixMSflkA",
        "DeviceId":"662461905988ab8a7fade82221cce64b"
    }

        :return:
        """

        client_info = {
            "Store": str(settings.CLIENT_INFORMATION_STORE),
            "Version": str(settings.CLIENT_INFORMATION_VERSION),
            "Language": str(settings.CLIENT_INFORMATION_LANGUAGE),
        }

        headers = {
            'PXFD-Request-Id': str(uuid.uuid4()),  # 'ed52b756-8c2f-4878-a5c0-5d249c36e0d3',
            'PXFD-Retry-No': '0',
            'PXFD-Sent-At': self.server_time.get_curr_time(),
            'PXFD-Client-Information': json.dumps(client_info, separators=(',', ':')),
            'PXFD-Client-Version': str(settings.CLIENT_INFORMATION_VERSION),
            'PXFD-Device-Token': md5(self.user.android_id.encode('utf-8')).hexdigest(),
            'PXFD-Game-Access-Token': str(self.user.game_access_token),
            'PXFD-Player-Id': str(self.user.player_id),
            'Accept-Encoding': 'gzip, deflate',
        }
        payload = {
            "RememberMeToken": self.user.remember_me_token,
            "DeviceId": headers['PXFD-Device-Token']
        }
        Logger.info(menu=LOGGING_MENU, action='update_device_id', msg='before request', url=update_device_id_url)
        resp = CrawlingHelper.post(
            url=update_device_id_url,
            headers=headers,
            payload=json.dumps(payload, separators=(',', ':')),
            cookies={},
            params={},
        )
        resp_status_code = resp.status_code
        resp_body = resp.content.decode('utf-8')
        resp_headers = {k: v for k, v in resp.headers.items()}
        resp_cookies = {k: v for k, v in resp.cookies.items()}

        Logger.info(
            menu=LOGGING_MENU, action='update_device_id', msg='after request',
            status_code=str(resp_status_code),
            body=str(resp_body),
            headers=str(resp_headers),
            cookies=str(resp_cookies),
        )

        self.check_response(resp_body)

        return resp_body

    def _send_run_collection(self, *, url: str, commands: List[BaseCommand]):
        """
        send command

        :param url:
        :param android_id:
        :param sent_at:
        :param game_access_token:
        :param player_id:
        :param commands:
        :return:
        """
        client_info = {
            "Store": str(settings.CLIENT_INFORMATION_STORE),
            "Version": str(settings.CLIENT_INFORMATION_VERSION),
            "Language": str(settings.CLIENT_INFORMATION_LANGUAGE),
        }

        headers = {
            'PXFD-Request-Id': str(uuid.uuid4()),  # 'ed52b756-8c2f-4878-a5c0-5d249c36e0d3',
            'PXFD-Retry-No': '0',
            'PXFD-Sent-At': self.server_time.get_curr_time(),
            'PXFD-Client-Information': json.dumps(client_info, separators=(',', ':')),
            'PXFD-Client-Version': str(settings.CLIENT_INFORMATION_VERSION),
            'PXFD-Device-Token': md5(self.user.android_id.encode('utf-8')).hexdigest(),
            'PXFD-Game-Access-Token': str(self.user.game_access_token),
            'PXFD-Player-Id': str(self.user.player_id),
            'Accept-Encoding': 'gzip, deflate',
        }
        payload = {
            'Id': self._command_id,
            'Time': self.server_time.get_curr_time_ymdhis(),
            'Commands': [c.get_command() for c in commands],
            'Transactional': False,
        }
        self._command_id += 1

        Logger.info(menu=LOGGING_MENU, action='send_run_collection', msg='before request', url=url, payload=payload)
        resp = CrawlingHelper.post(
            url=url,
            headers=headers,
            payload=json.dumps(payload, separators=(',', ':')),
            cookies={},
            params={},
        )
        resp_status_code = resp.status_code
        resp_body = resp.content.decode('utf-8')
        resp_headers = {k: v for k, v in resp.headers.items()}
        resp_cookies = {k: v for k, v in resp.cookies.items()}

        Logger.info(
            menu=LOGGING_MENU, action='send_run_collection', msg='after request',
            status_code=str(resp_status_code),
            body=str(resp_body),
            headers=str(resp_headers),
            cookies=str(resp_cookies),
        )

        self.check_response(resp_body)

        return resp_body


# 계약서
# {
#     "Id":8,
#     "Time":"2023-01-07T05:19:42Z",
#     "Commands":[
#         {
#             "Command":"Contract:Activate",
#             "Time":"2023-01-07T05:19:41Z",
#             "Parameters":{
#                 "ContractListId":100001,
#                 "Slot":20
#             }
#         }
#     ],
#     "Transactional":false
# }
#
#
#
# 기차에서 수집
# {'buffer': '{"Id":2,"Time":"2023-01-11T01:01:45Z","Commands":[{"Command":"Train:Unload","Time":"2023-01-11T01:01:44Z","Parameters":{"TrainId":10}},{"Command":"Train:Unload","Time":"2023-01-11T01:01:44Z","Parameters":{"TrainId":27}},{"Command":"Train:Unload","Time":"2023-01-11T01:01:45Z","Parameters":{"TrainId":9}}],"Transactional":false}'}
#
# 공장에서 상품 수집 (연속, 2번째, 3번째 순서대로)
# {'buffer': '{"Id":3,"Time":"2023-01-11T01:02:19Z","Commands":[{"Command":"Factory:CollectProduct","Time":"2023-01-11T01:02:17Z","Parameters":{"FactoryId":1,"Index":1}},{"Command":"Factory:CollectProduct","Time":"2023-01-11T01:02:18Z","Parameters":{"FactoryId":1,"Index":1}}],"Transactional":false}'}
#
# 기차에서 수집
# {'buffer': '{"Id":4,"Time":"2023-01-11T01:02:25Z","Commands":[{"Command":"Train:Unload","Time":"2023-01-11T01:02:25Z","Parameters":{"TrainId":93}},{"Command":"Train:Unload","Time":"2023-01-11T01:02:25Z","Parameters":{"TrainId":106}}],"Transactional":false}'}
#
# 기차에서 수집
# {'buffer': '{"Id":5,"Time":"2023-01-11T01:02:28Z","Commands":[{"Command":"Train:Unload","Time":"2023-01-11T01:02:25Z","Parameters":{"TrainId":144}},{"Command":"Train:Unload","Time":"2023-01-11T01:02:26Z","Parameters":{"TrainId":91}},{"Command":"Game:Heartbeat","Time":"2023-01-11T01:02:27Z","Parameters":{}}],"Transactional":false}'}
#
# {'buffer': '{"Id":6,"Time":"2023-01-11T01:02:31Z","Commands":[{"Command":"Job:Collect","Time":"2023-01-11T01:02:30Z","Parameters":{"JobLocationId":6003}}],"Transactional":false}'}
#
# {'buffer': '{"Id":7,"Time":"2023-01-11T01:02:34Z","Commands":[{"Command":"Job:Collect","Time":"2023-01-11T01:02:33Z","Parameters":{"JobLocationId":6004}}],"Transactional":false}'}
#
# {'buffer': '{"Id":8,"Time":"2023-01-11T01:02:46Z","Commands":[{"Command":"Factory:CollectProduct","Time":"2023-01-11T01:02:45Z","Parameters":{"FactoryId":6000,"Index":0}},{"Command":"Factory:OrderProduct","Time":"2023-01-11T01:02:46Z","Parameters":{"FactoryId":6000,"ArticleId":6007}}],"Transactional":false}'}
#
# 이벤트 기차 보내기
#     -  #37f82655-895e-4ec6-9749-11322e171bf4
#        Location:[Region6001:AUTO009], level:3, sequence:0, job_type:4, duration:3600, condition_multiplier:1, reward_multiplier:1
#        재료 : [auto_article_car_wheel/이벤트] : 170개 남음 (총 170개)
#        보상 : [auto_article_key/이벤트]-32개 [article_event_point/기본]-32개 [article_xp/기본]-660개
#        조건 : 4 지역 & ELECTRON
# {'buffer': '{"Id":9,"Time":"2023-01-11T01:02:55Z","Commands":[{"Command":"Train:DispatchToJob","Time":"2023-01-11T01:02:55Z","Parameters":{"UniqueId":"37f82655-895e-4ec6-9749-11322e171bf4","TrainId":91,"JobLocationId":6005,"Load":{"Id":6005,"Amount":40}}}],"Transactional":false}'}
#
# 이벤트 기차 보내기
#     -  #711aa850-4b42-40cd-b061-641be439be3f
#        Location:[Region6001:AUTO008], level:3, sequence:0, job_type:4, duration:3600, condition_multiplier:1, reward_multiplier:1
#        재료 : [auto_article_electric_engine/이벤트] : 360개 남음 (총 360개)
#        보상 : [auto_article_key/이벤트]-32개 [article_event_point/기본]-32개 [article_xp/기본]-1701개
#        조건 : 4 지역
# {'buffer': '{"Id":10,"Time":"2023-01-11T01:03:04Z","Commands":[{"Command":"Train:DispatchToJob","Time":"2023-01-11T01:03:01Z","Parameters":{"UniqueId":"711aa850-4b42-40cd-b061-641be439be3f","TrainId":144,"JobLocationId":6003,"Load":{"Id":6007,"Amount":45}}},{"Command":"Train:DispatchToJob","Time":"2023-01-11T01:03:03Z","Parameters":{"UniqueId":"711aa850-4b42-40cd-b061-641be439be3f","TrainId":106,"JobLocationId":6003,"Load":{"Id":6007,"Amount":44}}}],"Transactional":false}'}
#
# {'buffer': '{"Id":11,"Time":"2023-01-11T01:03:07Z","Commands":[{"Command":"Train:DispatchToJob","Time":"2023-01-11T01:03:05Z","Parameters":{"UniqueId":"711aa850-4b42-40cd-b061-641be439be3f","TrainId":93,"JobLocationId":6003,"Load":{"Id":6007,"Amount":40}}}],"Transactional":false}'}
#
# 이벤트 기차 보내기
#     -  #80806395-b6e8-40e2-92de-b6c0c3d3bb45
#        Location:[Region6001:AUTO007], level:4, sequence:0, job_type:4, duration:3600, condition_multiplier:1, reward_multiplier:1
#        재료 : [article_adhesive/기본] : 190개 남음 (총 190개)
#        보상 : [auto_article_key/이벤트]-31개 [article_event_point/기본]-31개 [article_xp/기본]-685개
#        조건 : 3 지역 & DIESEL
# {'buffer': '{"Id":12,"Time":"2023-01-11T01:03:13Z","Commands":[{"Command":"Train:DispatchToJob","Time":"2023-01-11T01:03:11Z","Parameters":{"UniqueId":"80806395-b6e8-40e2-92de-b6c0c3d3bb45","TrainId":82,"JobLocationId":6004,"Load":{"Id":115,"Amount":80}}},{"Command":"Train:DispatchToJob","Time":"2023-01-11T01:03:12Z","Parameters":{"UniqueId":"80806395-b6e8-40e2-92de-b6c0c3d3bb45","TrainId":77,"JobLocationId":6004,"Load":{"Id":115,"Amount":30}}}],"Transactional":false}'}
#
# {'buffer': '{"Id":13,"Time":"2023-01-11T01:03:19Z","Commands":[{"Command":"Train:DispatchToJob","Time":"2023-01-11T01:03:17Z","Parameters":{"UniqueId":"80806395-b6e8-40e2-92de-b6c0c3d3bb45","TrainId":81,"JobLocationId":6004,"Load":{"Id":115,"Amount":30}}}],"Transactional":false}'}
#
# {'buffer': '{"Id":14,"Time":"2023-01-11T01:03:25Z","Commands":[{"Command":"Factory:OrderProduct","Time":"2023-01-11T01:03:24Z","Parameters":{"FactoryId":5,"ArticleId":115}},{"Command":"Factory:CollectProduct","Time":"2023-01-11T01:03:25Z","Parameters":{"FactoryId":5,"Index":4}}],"Transactional":false}'}
#
# {'buffer': '{"Id":15,"Time":"2023-01-11T01:03:28Z","Commands":[{"Command":"Factory:CollectProduct","Time":"2023-01-11T01:03:26Z","Parameters":{"FactoryId":5,"Index":4}},{"Command":"Game:Heartbeat","Time":"2023-01-11T01:03:28Z","Parameters":{}}],"Transactional":false}'}
#
# 광고 보기
# {'buffer': '{"Id":16,"Time":"2023-01-11T01:03:51Z","Commands":[{"Command":"Game:Sleep","Time":"2023-01-11T01:03:51Z","Parameters":{},"Debug":{"CollectionsInQueue":0,"CollectionsInQueueIds":""}}],"Transactional":false}'}
#
# 광고 보고 고용하기
# {'buffer': '{"Id":17,"Time":"2023-01-11T01:04:34Z","Commands":[{"Command":"Game:WakeUp","Time":"2023-01-11T01:03:51Z","Parameters":{}},{"Command":"TemporaryDispatcher:Hire","Time":"2023-01-11T01:04:31Z","Parameters":{"DefinitionId":3}}],"Transactional":false}'}
#
# {'buffer': '{"Id":18,"Time":"2023-01-11T01:04:46Z","Commands":[{"Command":"Train:DispatchToDestination","Time":"2023-01-11T01:04:46Z","Parameters":{"TrainId":129,"DestinationId":408}}],"Transactional":false}'}
#
# 광고 보고 이벤트 수집
# {'buffer': '{"Id":20,"Time":"2023-01-11T01:05:40Z","Commands":[{"Command":"Game:WakeUp","Time":"2023-01-11T01:04:59Z","Parameters":{}},{"Command":"Milestone:CollectWithVideoReward","Time":"2023-01-11T01:05:37Z","Parameters":{"MilestoneId":6000}}],"Transactional":false}'}
#
# """
