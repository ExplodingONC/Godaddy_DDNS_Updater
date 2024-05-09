import os
from typing import Literal
from logger import TaskLogger
from dataclasses import dataclass

from logger import TaskLogger


RECORD_TYPE = Literal["A", "AAAA", "CNAME", "MX", "NS", "SOA", "SRV", "TXT"]


@dataclass
class DNSRecordQueryKey:
    name: str = ""
    type: RECORD_TYPE = "TXT"


@dataclass
class DNSRecord:
    id: str = ""
    domain: str = ""
    name: str = ""
    type: RECORD_TYPE = "TXT"
    value: str = ""
    ttl: int = 600
    comment: str = ""


class ProxyHelper:

    def __init__(self, task_logger: TaskLogger):
        self.logger = task_logger.getChild("Proxy")

    def set_proxy(self, proxy: str = "socks5://localhost:10808"):
        self.logger.warning("Setting proxy service...")
        os.environ["ALL_PROXY"] = proxy
        self.logger.warning(f"Proxy service set as \"{os.environ.get('ALL_PROXY')}\"!")

    def unset_proxy(self):
        self.logger.warning("Removing proxy service...")
        if os.environ.get("ALL_PROXY") is not None:
            os.environ.pop("ALL_PROXY")
        self.logger.warning("Proxy service removed!")
