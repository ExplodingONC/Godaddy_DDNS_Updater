import re
import ipaddress
import netifaces
from logger import TaskLogger


class Localhost:

    def __init__(self, task_logger: TaskLogger) -> None:
        self.logger = task_logger.getChild("Local")

    def get_ipv4_ip(self) -> ipaddress.IPv4Address:
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
        except Exception as e:
            self.logger.warning(f"Unable to get IPv4 IP from localhost:\n"
                                f"{e}")
            ipv4_addr = ipaddress.IPv4Address("127.0.0.1")
        return ipv4_addr
    
    def get_ipv6_ip(self) -> ipaddress.IPv6Address:
        # just find the first wired network interface
        wired_iface_regex = re.compile(r"en[op][0-9]s[0-9]", flags=re.IGNORECASE)
        interface: str = ""
        for interface_iter in netifaces.interfaces():
            if wired_iface_regex.match(str(interface_iter)):
                interface = str(interface_iter)
                break
        addrs = netifaces.ifaddresses(interface)
        try:
            ipv6_addr = ipaddress.IPv6Address(addrs[netifaces.AF_INET6][0]['addr'])
        except Exception as e:
            self.logger.warning(f"Unable to get IPv6 IP from localhost:\n"
                                f"{e}")
            ipv6_addr = ipaddress.IPv6Address("::1")
        return ipv6_addr