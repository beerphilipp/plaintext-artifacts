
from dataclasses import dataclass, field

@dataclass
class FastbotConfig:

    config: dict = field(default_factory=dict)