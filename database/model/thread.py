from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Thread:
    id: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None