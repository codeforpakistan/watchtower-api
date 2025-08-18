from pydantic import BaseModel, HttpUrl
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum

class GovernmentLevel(str, Enum):
    federal = "federal"
    state = "state"
    local = "local"

class WebsiteBase(BaseModel):
    name: str
    url: HttpUrl
    government_level: GovernmentLevel
    agency_type: str

class WebsiteCreate(WebsiteBase):
    pass

class Website(WebsiteBase):
    id: UUID
    created_at: datetime
    last_scanned: Optional[datetime] = None

class WebsiteResponse(Website):
    pass