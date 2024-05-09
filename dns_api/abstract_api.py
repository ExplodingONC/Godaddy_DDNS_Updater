from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass
from logger import TaskLogger
from .utils import RECORD_TYPE, DNSRecord


@dataclass
class AbstractDNSConfig:
    handler_class: AbstractDNSApi = None
    use_proxy: bool = False
    domain: str = ""
    timeout: float = 10

    def dict(self):
        return self.__dict__


class AbstractDNSApi:

    def __init__(self, config: AbstractDNSConfig, task_logger: TaskLogger):
        self.domain = config.domain
        self.timeout = config.timeout
        self.logger = task_logger.getChild("API")

    @abstractmethod
    def list_all_records(self) -> list[DNSRecord]:
        pass

    @abstractmethod
    def get_record(self, name: str, type: RECORD_TYPE) -> DNSRecord:
        pass

    @abstractmethod
    def set_record(self, record: DNSRecord) -> bool:
        pass

    @abstractmethod
    def delete_record(self, name: str, type: RECORD_TYPE) -> bool:
        pass
