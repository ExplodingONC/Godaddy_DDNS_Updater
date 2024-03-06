from typing import Literal
import requests
import json

from logger import DDNS_logger
from configs import api_key, api_secret, api_domain


RECORD_TYPE = Literal["A", "AAAA", "CNAME", "MX", "NS", "SOA", "SRV", "TXT"]


class GodaddyApi:

    timeout: float = 30

    key: str = api_key
    secret: str = api_secret
    headers: dict = {"Accept": "application/json",
                     "Content-Type": "application/json",
                     "Authorization": f"sso-key {key}:{secret}"}
    DOMAIN: str = api_domain

    def get_record(self, name: str, type: RECORD_TYPE,
                   domain: str = DOMAIN) -> dict:
        uri = f"https://api.godaddy.com/v1/domains/{domain}/records/{type}/{name}"
        response = requests.get(url=uri,
                                headers=self.headers,
                                timeout=self.timeout)
        try:
            if response.status_code == 200:
                if len(response.json()) > 0:
                    response_json = response.json()[0]
                else:
                    response_json = {"message": "Record not found."}
                DDNS_logger.info(response_json)
                return response_json
            else:
                DDNS_logger.warning(f"Failed to fetch {type} record for {name}:\n"
                                    f"Status Code: {response.status_code}\n"
                                    f"Json Content: {response.json()}")
                return {}
        except Exception as e:
            DDNS_logger.warning(f"Failed to fetch {type} record for {name}:\n"
                                f"Status Code: {response.status_code}\n"
                                f"Json Content: {response.json()}\n"
                                f"Exception: {e}")
            return {}

    def set_record(self, name: str, type: RECORD_TYPE,
                   data: str, ttl: int = 600,
                   domain: str = DOMAIN) -> bool:
        uri = f"https://api.godaddy.com/v1/domains/{domain}/records/{type}/{name}"
        payload = [{"data": data, "ttl": ttl}]
        response = requests.put(url=uri,
                                headers=self.headers,
                                json=payload,
                                timeout=self.timeout)
        try:
            if response.status_code == 200:
                return True
            else:
                DDNS_logger.warning(response.json())
                return False
        except:
            DDNS_logger.warning(response.json())
            return False
        
    def delete_record(self, name: str, type: RECORD_TYPE,
                      domain: str = DOMAIN) -> bool:
        uri = f"https://api.godaddy.com/v1/domains/{domain}/records/{type}/{name}"
        response = requests.delete(url=uri,
                                   headers=self.headers,
                                   timeout=self.timeout)
        try:
            if response.status_code == 204:
                return True
            else:
                DDNS_logger.warning(response.json())
                return False
        except:
            DDNS_logger.warning(response.json())
            return False
