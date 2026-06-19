
from dataclasses import dataclass, field
from typing import List


@dataclass
class ActivityInfo:

    manifest_xml: str = None
    activity_name: str = None
    is_alias: bool = False
    alias_for: str = None

    declared_intent_filters: bool = False
    intent_filters: List[str] = field(default_factory=list)
    is_ignored: bool = False