from dataclasses import dataclass, field

@dataclass
class SecurityConfig:
    allowed_domains: list[str] = field(default_factory=list)
    disallowed_domains: list[str] = field(default_factory=list)