from dataclasses import dataclass
from typing import Literal

MessageRole = Literal["user", "assistant"]
DreamStatus = Literal["exploring", "analyzed", "archived"]


@dataclass
class Profile:
    id: int
    display_name: str
    life_summary: str
    stressors: str
    preferences: str
    psyche_map: str
    updated_at: str


@dataclass
class DreamSession:
    id: int
    title: str
    raw_dream: str
    status: DreamStatus
    analyst_notes: str
    created_at: str
    updated_at: str


@dataclass
class Message:
    id: int
    dream_id: int
    role: MessageRole
    content: str
    created_at: str
