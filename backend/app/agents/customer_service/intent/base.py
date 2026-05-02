from __future__ import annotations

from enum import Enum


class Intent(str, Enum):
    TICKET = "ticket"
    PRODUCT = "product"
    GENERAL = "general"
