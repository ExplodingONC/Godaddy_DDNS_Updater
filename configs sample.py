"""

Rename this file to "configs.py", and input your own infomations and tasks

"""


from dns_api import AbstractDNSConfig, AbstractDNSApi
from dns_api import GodaddyDNSConfig, GodaddyDNSApi
from dns_api import CloudflareDNSConfig, CloudflareDNSApi
from ddns_task import DDNSTaskConfig


config_list: list[AbstractDNSConfig] = [
    # list of DNS targets (zones, which is a set of records for a certain domain)
    # each dict is config for one target
    {
        "api": CloudflareDNSConfig(
            handler_class=CloudflareDNSApi,
            use_proxy=False,
            domain="example.com",
            token="example_token",
            zone_id="example_zone_id"
        ),
        "task": [
            # list of tasks (get IP from where and set to which record)
            # each object is one task
            DDNSTaskConfig(
                name="example",
                type="AAAA",
                source="local"
            ),
            DDNSTaskConfig(
                name="example",
                type="A",
                source="router"
            ),
        ]
    },
    {
        "api": GodaddyDNSConfig(
            handler_class=GodaddyDNSApi,
            use_proxy=True,
            domain="example.com",
            key="example_key",
            secret="example_secret"
        ),
        "task": [
            # list of tasks (get IP from where and set to which record)
            # each object is one task
            DDNSTaskConfig(
                name="example",
                type="AAAA",
                source="local"
            ),
            DDNSTaskConfig(
                name="example",
                type="A",
                source="router"
            ),
        ]
    }
]
