import time
import random
import traceback
from copy import deepcopy
from typing import Literal
from dataclasses import dataclass

from logger import TaskLogger

from local_utils import Localhost, AsusRouter
from local_utils.router_cfg import router_username, router_password

from dns_api import RECORD_TYPE, AbstractDNSApi, AbstractDNSConfig
from dns_api.utils import ProxyHelper, DNSRecord, DNSRecordQueryKey


RECORD_SOURCE = Literal["local", "router"]


@dataclass
class DDNSTaskConfig:
    name: str = "www"
    type: RECORD_TYPE = "AAAA"
    source: RECORD_SOURCE = "local"


@dataclass
class DDNSTaskBoard:
    local_record: DNSRecord
    remote_record: DNSRecord
    config: DDNSTaskConfig


class DDNSTask:

    # This is just for some randomness, some proxy service 
    # seems to be not very happy with a constant interval network traffic...
    FORCE_FETCH_RAND_INTERVAL: tuple[int, int] = (40, 80)

    task_configs: list[DDNSTaskConfig]

    def __init__(self, api_config: AbstractDNSConfig, task_configs: list[DDNSTaskConfig]) -> None:
        self.domain: str = api_config.domain
        self.task_name = (api_config.handler_class.__name__.rstrip("DNSApi")
                          + "@\"" + api_config.domain + "\"")
        self.logger = TaskLogger(name=self.task_name)
        self.logger.warning(f"DDNS task <{self.task_name}> created!")

        self.use_proxy: bool = api_config.use_proxy
        self.proxy_helper = ProxyHelper(task_logger=self.logger)
        self.api_handler: AbstractDNSApi = api_config.handler_class(api_config, task_logger=self.logger)
        self.local_handler: Localhost = Localhost(task_logger=self.logger)
        self.router_handler: AsusRouter = AsusRouter(task_logger=self.logger,
                                                     username=router_username,
                                                     password=router_password)

        self.task_configs = task_configs
        self.tasks: list[DDNSTaskBoard] = []
        for task_config in self.task_configs:
            record_args = {"domain": self.domain, "name": task_config.name, "type": task_config.type}
            self.tasks.append(DDNSTaskBoard(local_record=DNSRecord(**record_args),
                                            remote_record=DNSRecord(**record_args),
                                            config=task_config))

        self.force_fetch_counter: int = 0

    def fetch_dns_record(self, task_board: DDNSTaskBoard):
        task_board.remote_record = self.api_handler.get_record(name=task_board.config.name,
                                                               type=task_board.config.type)

    def push_dns_record(self, task_board: DDNSTaskBoard):
        self.api_handler.set_record(record=task_board.local_record)
        self.fetch_dns_record(task_board)

    def remove_dns_record(self, task_board: DDNSTaskBoard):
        self.api_handler.delete_record(name=task_board.config.name,
                                       type=task_board.config.type)
        self.fetch_dns_record(task_board)


    def main(self):

        # force fetching DNS record from DNS API
        if not self.force_fetch_counter:
            for task in self.tasks:
                self.fetch_dns_record(task_board=task)
            self.force_fetch_counter = random.randint(*self.FORCE_FETCH_RAND_INTERVAL)

        # iter through all tasks (different target records)
        for task in self.tasks:

            if task.config.source == "local":

                if task.config.type == "A":
                    # get local running IP addresses
                    current_ipv4 = self.local_handler.get_ipv4_ip()
                    task.local_record.value = str(current_ipv4)
                    self.logger.info(f"Local IPv4 address is {current_ipv4} "
                                    f"({'is' if current_ipv4.is_private else 'not'} private)")
                    # update DNS records if needed
                    if not current_ipv4.is_private:
                        if task.remote_record is None or str(current_ipv4) != task.remote_record.value:
                            self.logger.warning(f"DDNS update for IPv4 is needed...")
                            self.push_dns_record(task_board=task)
                        else:
                            self.logger.info(f"DDNS for IPv4 is up to date...")

                elif task.config.type == "AAAA":
                    # get local running IP addresses
                    current_ipv6 = self.local_handler.get_ipv6_ip()
                    task.local_record.value = str(current_ipv6)
                    self.logger.info(f"Local IPv6 address is {current_ipv6} "
                                    f"({'is' if current_ipv6.is_private else 'not'} private)")
                    # update DNS records if needed
                    if not current_ipv6.is_private:
                        if task.remote_record is None or str(current_ipv6) != task.remote_record.value:
                            self.logger.warning(f"DDNS update for IPv6 is needed...")
                            self.push_dns_record(task_board=task)
                        else:
                            self.logger.info(f"DDNS for IPv6 is up to date...")

            elif task.config.source == "router":

                if task.config.type == "A":
                    # get router running IP addresses
                    current_wan_ipv4 = self.router_handler.get_wan_ip()
                    current_real_ipv4 = self.router_handler.get_real_ip()
                    task.local_record.value = str(current_real_ipv4)
                    self.logger.info(f"Router IPv4 address is {current_wan_ipv4} "
                                    f"({'is' if current_wan_ipv4.is_private else 'not'} private)")
                    self.logger.info(f"Public IPv4 address is {current_real_ipv4} "
                                    f"({'is' if current_real_ipv4.is_private else 'not'} private)")
                    # check if the IP address is useable
                    if current_wan_ipv4 != current_real_ipv4:
                        # that means we don't have a public IPv4 address
                        self.logger.info(f"DDNS for IPv4 is unavailable due to NAT address...")
                        if task.remote_record and task.remote_record.value:
                            self.remove_dns_record(task)
                    elif current_real_ipv4.is_private:
                        self.logger.info(f"DDNS for IPv4 is unavailable due to terrible NAT condition...")
                        if task.remote_record and task.remote_record.value:
                            self.remove_dns_record(task)
                    else:
                        # otherwise we have a valid public IPV4 address
                        if task.remote_record is None or str(current_real_ipv4) != task.remote_record.value:
                            self.logger.warning(f"DDNS update for router IPv4 is needed...")
                            self.push_dns_record(task_board=task)
                        else:
                            self.logger.info(f"DDNS for router IPv4 is up to date...")
                            
                elif task.config.type == "AAAA":
                    # get local running IP addresses
                    self.logger.warning(f"Router IPv6 address should not be put into DDNS!")


    def run(self):

        # do DDNS monitoring and updates
        try:
            if self.use_proxy:
                self.proxy_helper.set_proxy()

            while True:
                try:
                    self.main()
                    time_sleep = random.randint(60, 120)
                    time.sleep(time_sleep)
                except Exception as e:
                    self.logger.warning(f"DDNS update attempt failed: {e}")
                    self.logger.error(f"\n\n{traceback.format_exc()}")
        except:
            self.logger.error(f"\n\n{traceback.format_exc()}")

        finally:
            if self.use_proxy:
                self.proxy_helper.unset_proxy()
