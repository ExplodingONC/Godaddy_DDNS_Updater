import ipaddress
import paramiko
from logger import TaskLogger


class AsusRouter:

    def __init__(self, task_logger: TaskLogger, username: str, password: str = "", timeout: float = 5) -> None:
        self.logger = task_logger.getChild("Local")
        self.hostname: str = "router.asus.com"
        self.port: int = 22
        self.username: str = username
        self.password: str = password
        self.timeout: float = timeout
     
    def get_wan_ip(self) -> ipaddress.IPv4Address:
            # For Asus routers with SSH enabled
            wan_ip = real_ip = "0.0.0.0"
            try:
                with paramiko.SSHClient() as ssh:
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
                    ssh.connect(hostname=self.hostname, port=self.port,
                                username=self.username, password=self.password,
                                timeout=self.timeout, auth_timeout=self.timeout, banner_timeout=self.timeout)
                    _, _stdout, _stderr = ssh.exec_command("nvram get wan0_ipaddr")
                    wan_ip =  _stdout.read().decode().strip() or wan_ip
            except Exception as e:
                self.logger.warning(f"Unable to get WAN IP from router:\n"
                                    f"{e}")
            return ipaddress.IPv4Address(wan_ip)
    
    def get_real_ip(self) -> ipaddress.IPv4Address:
            # For Asus routers with SSH enabled
            wan_ip = real_ip = "0.0.0.0"
            try:
                with paramiko.SSHClient() as ssh:
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
                    ssh.connect(hostname=self.hostname, port=self.port,
                                username=self.username, password=self.password,
                                timeout=self.timeout, auth_timeout=self.timeout, banner_timeout=self.timeout)
                    _, _stdout, _stderr = ssh.exec_command("nvram get wan0_realip_ip")
                    real_ip =  _stdout.read().decode().strip() or real_ip
            except Exception as e:
                self.logger.warning(f"Unable to get WAN IP from router:\n"
                                    f"{e}")
            return ipaddress.IPv4Address(real_ip)
    