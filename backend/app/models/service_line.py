from typing import Literal

from pydantic import BaseModel

ServiceLineKey = Literal["training", "consulting", "retainer", "certification", "other"]


class ServiceLine(BaseModel):
    id: str
    key: ServiceLineKey
    label: str
    description: str
