import requests
from dataclasses import dataclass
from logger import TaskLogger
from .utils import RECORD_TYPE, DNSRecord
from .abstract_api import AbstractDNSConfig, AbstractDNSApi


@dataclass
class GodaddyDNSConfig(AbstractDNSConfig):
    handler_class: AbstractDNSApi = None
    use_proxy: bool = True
    key: str = ""
    secret: str = ""


class GodaddyDNSApi(AbstractDNSApi):
    
    def __init__(self, config: GodaddyDNSConfig, task_logger: TaskLogger):
        super().__init__(config, task_logger)
        self.key: str = config.key
        self.secret: str = config.secret
        self.headers: dict = {"Accept": "application/json",
                              "Content-Type": "application/json",
                              "Authorization": f"sso-key {self.key}:{self.secret}"}

    def get_record(self, name: str, type: RECORD_TYPE) -> DNSRecord:
        uri = (f"https://api.godaddy.com/v1/domains/{self.domain}/"
               f"records/{type}/{name}")
        response = requests.get(url=uri,
                                headers=self.headers,
                                timeout=self.timeout)
        try:
            if response.status_code == 200:
                self.logger.info(f"Succeeded to get {type} record for {name}")
                response_json = response.json()
                self.logger.debug(response_json)
                if len(response_json) > 0:
                    result = response_json[0]
                    return DNSRecord(domain=self.domain, name=name, type=type,
                                     value=result["data"],
                                     ttl=result["ttl"])
                else:
                    self.logger.warning(f"No {type} record is found for {name}")
                    return None
            else:
                self.logger.warning(f"Failed to fetch {type} record for {name}:\n"
                                    f"Status Code: {response.status_code}\n"
                                    f"Json Content: {response.json()}")
                return None
        except Exception as e:
            self.logger.warning(f"Failed to fetch {type} record for {name}:\n"
                                f"Status Code: {response.status_code}\n"
                                f"Json Content: {response.json()}\n"
                                f"Exception: {e}")
            return None

    def set_record(self, record: DNSRecord) -> bool:
        uri = (f"https://api.godaddy.com/v1/domains/{self.domain}/"
               f"records/{record.type}/{record.name}")
        payload = [{"data": record.value, "ttl": record.ttl}]
        response = requests.put(url=uri,
                                headers=self.headers,
                                json=payload,
                                timeout=self.timeout)
        try:
            if response.status_code == 200:
                return True
            else:
                self.logger.warning(f"Failed to set {record.type} record for {record.name} as {record.value}:\n"
                                    f"Status Code: {response.status_code}\n"
                                    f"Json Content: {response.json()}")
                return False
        except Exception as e:
            self.logger.warning(f"Failed to set {record.type} record for {record.name} as {record.value}:\n"
                                f"Status Code: {response.status_code}\n"
                                f"Json Content: {response.json()}\n"
                                f"Exception: {e}")
            return False
        
    def delete_record(self, name: str, type: RECORD_TYPE) -> bool:
        uri = (f"https://api.godaddy.com/v1/"
               f"domains/{self.domain}/"
               f"records/{type}/{name}")
        response = requests.delete(url=uri,
                                   headers=self.headers,
                                   timeout=self.timeout)
        try:
            if response.status_code == 204:
                self.logger.info(f"Succeeded to delete {type} record for {name}")
                return True
            else:
                self.logger.warning(f"Failed to delete {type} record for {name}:\n"
                                    f"Status Code: {response.status_code}\n"
                                    f"Json Content: {response.json()}")
                return False
        except Exception as e:
            self.logger.warning(f"Failed to delete {type} record for {name}:\n"
                                f"Status Code: {response.status_code}\n"
                                f"Json Content: {response.json()}\n"
                                f"Exception: {e}")
            return False
