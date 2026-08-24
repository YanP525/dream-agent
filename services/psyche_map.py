import json
import re

from prompts.psyche_map import (
    build_extract_messages,
    build_rebuild_messages,
    _empty_map,
)
from services.llm import chat
from storage.models import DreamSession, Message, Profile
from storage.repository import get_messages, get_psyche_map, update_psyche_map


def psyche_map_is_empty(data: dict | None = None) -> bool:
    data = data if data is not None else get_psyche_map()
    if not data:
        return True
    if data.get("symbols") or data.get("complexes"):
        return False
    shadow = data.get("shadow") or {}
    animus = data.get("animus_anima") or {}
    return not shadow.get("current_theme") and not shadow.get("note") and not animus.get("note")


def _dream_messages_map(dreams: list[DreamSession]) -> dict[int, list[Message]]:
    return {d.id: get_messages(d.id) for d in dreams}


def _parse_map_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return _empty_map()
        data = json.loads(match.group())
    return _normalize_map(data)


def _normalize_map(data: dict) -> dict:
    base = _empty_map()
    if not isinstance(data, dict):
        return base

    symbols = data.get("symbols", [])
    if isinstance(symbols, list):
        cleaned = []
        for item in symbols[:8]:
            if not isinstance(item, dict) or not str(item.get("symbol", "")).strip():
                continue
            cleaned.append(
                {
                    "symbol": str(item.get("symbol", "")).strip(),
                    "personal_meaning": str(item.get("personal_meaning", "")).strip(),
                    "linked_themes": [
                        str(t).strip()
                        for t in (item.get("linked_themes") or [])
                        if str(t).strip()
                    ][:4],
                    "intensity": str(item.get("intensity", "中")).strip() or "中",
                }
            )
        base["symbols"] = cleaned

    for key, defaults in [
        ("shadow", {"current_theme": "", "movement": "不明", "note": ""}),
        ("animus_anima", {"polarity": "未显", "movement": "不明", "note": ""}),
    ]:
        block = data.get(key)
        if isinstance(block, dict):
            merged = defaults.copy()
            for field in defaults:
                value = str(block.get(field, "")).strip()
                if value:
                    merged[field] = value
            base[key] = merged

    complexes = data.get("complexes", [])
    if isinstance(complexes, list):
        base["complexes"] = [
            {
                "name": str(c.get("name", "")).strip(),
                "trigger": str(c.get("trigger", "")).strip(),
                "status": str(c.get("status", "活跃")).strip() or "活跃",
            }
            for c in complexes[:6]
            if isinstance(c, dict) and str(c.get("name", "")).strip()
        ]

    return base


def refresh_psyche_map(
    profile: Profile | None,
    dreams: list[DreamSession],
    latest_messages: list[Message] | None = None,
) -> dict:
    if not dreams and not latest_messages:
        update_psyche_map(_empty_map())
        return _empty_map()

    current = get_psyche_map()
    messages = build_extract_messages(profile, current, dreams, latest_messages)
    raw = chat(messages)
    new_map = _parse_map_json(raw)
    update_psyche_map(new_map)
    return new_map


def rebuild_psyche_map(profile: Profile | None, dreams: list[DreamSession]) -> dict:
    if not dreams:
        update_psyche_map(_empty_map())
        return _empty_map()

    dream_messages = _dream_messages_map(dreams)
    messages = build_rebuild_messages(profile, dreams, dream_messages)
    raw = chat(messages)
    new_map = _parse_map_json(raw)
    update_psyche_map(new_map)
    return new_map


def init_psyche_map_from_history(profile: Profile | None, dreams: list[DreamSession]) -> dict:
    """从全部历史梦境与对话记录初始化/重建潜意识地图。"""
    return rebuild_psyche_map(profile, dreams)
