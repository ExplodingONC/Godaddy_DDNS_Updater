import requests
from dataclasses import dataclass
from logger import TaskLogger
from .utils import RECORD_TYPE, DNSRecord
from .abstract_api import AbstractDNSConfig, AbstractDNSApi


@dataclass
class CloudflareDNSConfig(AbstractDNSConfig):
    handler_class: AbstractDNSApi = None
    token: str = ""
    zone_id: str = ""


class CloudflareDNSApi(AbstractDNSApi):
    
    def __init__(self, config: CloudflareDNSConfig, task_logger: TaskLogger):
        super().__init__(config, task_logger)
        self.token: str = config.token
        self.zone_id: str = config.zone_id
        self.headers: dict = {"Accept": "application/json",
                              "Content-Type": "application/json",
                              "Authorization": f"Bearer {self.token}"}

    def get_record(self, name: str, type: RECORD_TYPE) -> DNSRecord:
        full_name = name + "." + self.domain
        uri = (f"https://api.cloudflare.com/client/v4/"
               f"zones/{self.zone_id}/"
               f"dns_records?name={full_name}&type={type}")
        response = requests.get(url=uri,
                                headers=self.headers,
                                timeout=self.timeout)
        try:
            if response.status_code == 200 and response.json()["success"]:
                self.logger.info(f"Succeeded to get {type} record for {name}")
                response_json = response.json()
                self.logger.debug(response_json)
                if len(response_json["result"]) > 0:
                    result = response_json["result"][0]
                    return DNSRecord(domain=self.domain, name=name, type=type,
                                     id=result["id"],
                                     value=result["content"],
                                     ttl=result["ttl"],
                                     comment=result["comment"])
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
        record_to_update = self.get_record(record.name, record.type)
        if record_to_update and record_to_update.id:
            # if the record already exists
            uri = (f"https://api.cloudflare.com/client/v4/"
                   f"zones/{self.zone_id}/"
                   f"dns_records/{record_to_update.id}")
            payload = {"name": record.name, "type": record.type,
                       "content": record.value, "ttl": record.ttl}
            response = requests.patch(url=uri,
                                      headers=self.headers,
                                      json=payload,
                                      timeout=self.timeout)
        else:
            # if the record does not exist
            uri = (f"https://api.cloudflare.com/client/v4/"
                   f"zones/{self.zone_id}/"
                   f"dns_records")
            payload = {"name": record.name, "type": record.type,
                       "content": record.value, "ttl": record.ttl,
                       "proxied": False}
            response = requests.post(url=uri,
                                     headers=self.headers,
                                     json=payload,
                                     timeout=self.timeout)
        try:
            if response.status_code == 200 and response.json()["success"]:
                self.logger.info(f"Succeeded to set {record.type} record for {record.name} as {record.value}")
                self.logger.debug(response.json())
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
        record_to_delete = self.get_record(name, type)
        if not record_to_delete or not record_to_delete.id:
            self.logger.warning(f"Failed to delete {type} record for {name}: Not existed")
            return False
        
        uri = (f"https://api.cloudflare.com/client/v4/"
               f"zones/{self.zone_id}/"
               f"dns_records/{record_to_delete.id}")
        response = requests.delete(url=uri,
                                   headers=self.headers,
                                   timeout=self.timeout)
        try:
            if response.status_code == 200 and response.json()["success"]:
                self.logger.info(f"Succeeded to delete {type} record for {name}")
                self.logger.debug(response.json())
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
