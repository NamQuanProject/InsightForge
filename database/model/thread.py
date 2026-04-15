from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Thread:
    id: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

    def to_dict(self):
        return {
            k: v for k, v in asdict(self).items()
            if v is not None
        }