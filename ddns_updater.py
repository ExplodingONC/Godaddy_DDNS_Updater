import os
import re
import time
import random
import paramiko
import ipaddress
import traceback
from typing import Union
import netifaces

from godaddy_api import GodaddyApi, RECORD_TYPE
from logger import DDNS_logger
from configs import api_domain, router_username, router_password


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

    def __init__(self, name: str, type: RECORD_TYPE, domain: str = DEFAULT_DOMAIN, router: bool = False) -> None:
        self.api_handler = GodaddyApi()
        self.use_router_addr = router
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

    @staticmethod
    def get_router_ip() -> tuple[ipaddress.IPv4Address, ipaddress.IPv4Address]:
        # For Asus routers with SSH enabled
        wan_ip = real_ip = "0.0.0.0"
        try:
            with paramiko.SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
                ssh.connect(hostname="router.asus.com", port=22,
                            username=router_username, password=router_password)
                _, _stdout, _stderr = ssh.exec_command("nvram get wan0_ipaddr")
                wan_ip =  _stdout.read().decode().strip() or wan_ip
                _, _stdout, _stderr = ssh.exec_command("nvram get wan0_realip_ip")
                real_ip =  _stdout.read().decode().strip() or real_ip
        except Exception as e:
            DDNS_logger.warning(f"Unable to get WAN IP from router:\n"
                                f"{e}")
        return ipaddress.IPv4Address(wan_ip), ipaddress.IPv4Address(real_ip)

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

    def remove_dns_record(self):
        self.api_handler.delete_record(name=self.record_name,
                                       type=self.record_type,
                                       domain=self.domain)
        self.fetch_dns_record()

    def update_dns_record(self):

        # force fetching DNS record from Godaddy
        if not self.record or not self.force_fetch_counter:
            self.fetch_dns_record()
            self.force_fetch_counter = random.randint(*self.FORCE_FETCH_RAND_INTERVAL)

        # get local running IP addresses
        if not self.use_router_addr:
            # get local running IP addresses
            current_ipv4, current_ipv6 = self.get_local_ip()
            DDNS_logger.info(f"Local IPv4 address is {current_ipv4} "
                            f"({'is' if current_ipv4.is_private else 'not'} private)")
            DDNS_logger.info(f"Local IPv6 address is {current_ipv6} "
                            f"({'is' if current_ipv6.is_private else 'not'} private)")
            # update DNS records if needed
            if self.record_type == "A":
                if str(current_ipv4) != self.record.get("data"):
                    DDNS_logger.warning(f"DDNS update for IPv4 is needed...")
                    self.push_dns_record(data=str(current_ipv4))
                else:
                    DDNS_logger.info(f"DDNS for IPv4 is up to date...")
            if self.record_type == "AAAA" and not current_ipv6.is_private:
                # usually IPv6 address is public... I hope...
                if str(current_ipv6) != self.record.get("data"):
                    DDNS_logger.warning(f"DDNS update for IPv6 is needed...")
                    self.push_dns_record(data=str(current_ipv6))
                else:
                    DDNS_logger.info(f"DDNS for IPv6 is up to date...")
        else:
            # get router WAN IP addresses
            current_router_ipv4, current_real_ipv4 = self.get_router_ip()
            DDNS_logger.info(f"Router IPv4 address is {current_router_ipv4} "
                            f"({'is' if current_router_ipv4.is_private else 'not'} private)")
            DDNS_logger.info(f"Public IPv4 address is {current_real_ipv4} "
                            f"({'is' if current_real_ipv4.is_private else 'not'} private)")
            # update DNS records if needed
            if self.record_type == "A":
                if current_router_ipv4 != current_real_ipv4:
                    # that means we don't have a public IPv4 address
                    DDNS_logger.info(f"DDNS for IPv4 is unavailable due to NAT address...")
                    if self.record.get("data"):
                        self.remove_dns_record()
                elif not current_real_ipv4.is_private:
                    # otherwise we have a valid public IPV4 address
                    if str(current_real_ipv4) != self.record.get("data"):
                        DDNS_logger.warning(f"DDNS update for IPv4 is needed...")
                        self.push_dns_record(data=str(current_real_ipv4))
                    else:
                        DDNS_logger.info(f"DDNS for IPv4 is up to date...")


def main():
    # count fails
    fail_count: int = 0
    # do DDNS monitoring and updates
    try:
        if USE_PROXY:
            set_proxy()
        home_updater_4 = DDNSUpdater(name="home-server", type="A", router=True)
        home_updater_6 = DDNSUpdater(name="home-server", type="AAAA", router=False)
        while True:
            try:
                home_updater_4.update_dns_record()
                home_updater_6.update_dns_record()
                time_sleep = random.randint(30, 60) + fail_count
                time.sleep(time_sleep)
            except Exception as e:
                fail_count += 1
                DDNS_logger.warning(f"DDNS update attempt # {fail_count} failed: {e}")
                if fail_count >= 100:
                    raise RuntimeError from e
            else:
                fail_count = 0
    except:
        DDNS_logger.error(f"\n\n{traceback.format_exc()}")
    finally:
        if USE_PROXY:
            unset_proxy()


if __name__ == "__main__":
    main()
