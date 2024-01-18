import os
import re
import time
import random
import ipaddress
import traceback
from typing import Union
import netifaces

from godaddy_api import GodaddyApi, RECORD_TYPE
from logger import DDNS_logger
from configs import api_domain


# config if you use proxy service
USE_PROXY = True

def set_proxy(proxy: str = "socks5://localhost:10808"):
    DDNS_logger.warning("Setting proxy service...")
    os.environ["ALL_PROXY"] = proxy
    DDNS_logger.warning(f"Proxy service set as \"{os.environ.get('ALL_PROXY')}\"!")

def unset_proxy():
    DDNS_logger.warning("Removing proxy service...")
    if os.environ.get("ALL_PROXY") is not None:
        os.environ.pop("ALL_PROXY")
    DDNS_logger.warning("Proxy service removed!")


class DDNSUpdater:

    DEFAULT_DOMAIN: str = api_domain

    # This is just for some randomness, some proxy service 
    # seems to be not very happy with a constant interval network traffic...
    FORCE_FETCH_RAND_INTERVAL: tuple[int, int] = (40, 80)

    def __init__(self, name: str, type: RECORD_TYPE, domain: str = DEFAULT_DOMAIN) -> None:
        self.api_handler = GodaddyApi()
        self.domain: str = domain
        self.record: dict = {}
        self.record_name: str = name
        self.record_type: RECORD_TYPE = type
        self.force_fetch_counter: int = random.randint(*self.FORCE_FETCH_RAND_INTERVAL)

    @staticmethod
    def get_local_ip() -> tuple[ipaddress.IPv4Address, ipaddress.IPv6Address]:
        # just find the first wired network interface
        wired_iface_regex = re.compile(r"en[op][0-9]s[0-9]", flags=re.IGNORECASE)
        interface: str = ""
        for interface_iter in netifaces.interfaces():
            if wired_iface_regex.match(str(interface_iter)):
                interface = str(interface_iter)
                break
        addrs = netifaces.ifaddresses(interface)
        try:
            ipv4_addr = ipaddress.IPv4Address(addrs[netifaces.AF_INET][0]['addr'])
        except:
            ipv4_addr = ipaddress.IPv4Address("127.0.0.1")
        try:
            ipv6_addr = ipaddress.IPv6Address(addrs[netifaces.AF_INET6][0]['addr'])
        except:
            ipv6_addr = ipaddress.IPv6Address("::1")
        return ipv4_addr, ipv6_addr

    def fetch_dns_record(self):
        self.record = self.api_handler.get_record(name=self.record_name,
                                                  type=self.record_type,
                                                  domain=self.domain)

    def push_dns_record(self, data: str):
        self.api_handler.set_record(name=self.record_name,
                                    type=self.record_type,
                                    domain=self.domain,
                                    data=data)
        self.fetch_dns_record()

    def update_dns_record(self):
        if not self.record or not self.force_fetch_counter:
            self.fetch_dns_record()
            self.force_fetch_counter = random.randint(*self.FORCE_FETCH_RAND_INTERVAL)
        current_ipv4, current_ipv6 = self.get_local_ip()
        DDNS_logger.info(f"Local IPv4 address is {current_ipv4} "
                         f"({'is' if current_ipv4.is_private else 'not'} private)")
        DDNS_logger.info(f"Local IPv6 address is {current_ipv6} "
                         f"({'is' if current_ipv6.is_private else 'not'} private)")
        if self.record_type == "A" and not current_ipv4.is_private:
            if str(current_ipv4) != self.record.get("data"):
                DDNS_logger.warning(f"DDNS update for IPv4 is needed...")
                self.push_dns_record(data=str(current_ipv4))
            else:
                DDNS_logger.info(f"DDNS for IPv4 is up to date...")
        if self.record_type == "AAAA" and not current_ipv6.is_private:
            if str(current_ipv6) != self.record.get("data"):
                DDNS_logger.warning(f"DDNS update for IPv6 is needed...")
                self.push_dns_record(data=str(current_ipv6))
            else:
                DDNS_logger.info(f"DDNS for IPv6 is up to date...")


def main():
    # do DDNS monitoring and updates
    try:
        if USE_PROXY:
            set_proxy()
        www_updater = DDNSUpdater(name="www", type="CNAME")
        www_updater.fetch_dns_record()
        home_updater = DDNSUpdater(name="home-server", type="AAAA")
        home_updater.fetch_dns_record()
        while True:
            home_updater.update_dns_record()
            time_sleep = random.randint(30, 60)
            time.sleep(time_sleep)
    except:
        DDNS_logger.error(f"\n\n{traceback.format_exc()}")
    finally:
        if USE_PROXY:
            unset_proxy()


if __name__ == "__main__":
    main()
