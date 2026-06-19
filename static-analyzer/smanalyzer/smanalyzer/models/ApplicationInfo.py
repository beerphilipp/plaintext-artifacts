from dataclasses import dataclass, field
from typing import List
from smanalyzer.models.ActivityInfo import ActivityInfo

@dataclass
class ApplicationInfo:
    
    apk_path: str = None
    package_name: str = None
    target_sdk: int = None
    uses_cleartext_traffic: bool = None
    has_network_security_config: bool = None
    network_security_config: str = None

    network_security_config_file: str = None

    mixed_content_calls: dict[str, list[str]] = field(default_factory=dict)

    start_time: str = None
    end_time: str = None
    exception: bool = False
    version_name: str = None