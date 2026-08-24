import json

from storage.models import DreamSession, Message, Profile

EXTRACT_PROMPT = """你是荣格心理学档案员。根据对话与既有地图，输出更新后的「潜意识地图」JSON。

只基于对话中实际出现的内容，不要臆造。若信息不足，保留旧地图或留空数组。

严格只输出 JSON，不要 markdown 代码块，不要解释。格式：
{
  "symbols": [
    {
      "symbol": "意象名称",
      "personal_meaning": "对该来访者的个人意义",
      "linked_themes": ["主题1", "主题2"],
      "intensity": "低|中|高"
    }
  ],
  "shadow": {
    "current_theme": "当前阴影主题，无则空字符串",
    "movement": "状态变化，如：压抑|浮现|对峙|整合|不明",
    "note": "一句说明"
  },
  "animus_anima": {
    "polarity": "阿尼姆斯|阿尼玛|未显|双性",
    "movement": "状态变化，如：投射|退行|整合|对抗|不明",
    "note": "一句说明"
  },
  "complexes": [
    {
      "name": "情结名称",
      "trigger": "触发场景",
      "status": "活跃|松动|休眠"
    }
  ]
}

规则：
- symbols 最多 8 条，按重要性保留；重复意象合并而非重复列出
- movement 字段描述「变化趋势」，不是诊断结论
- 用中文填写所有字段
"""


def _format_dream_transcripts(
    dreams: list[DreamSession],
    dream_messages: dict[int, list[Message]] | None = None,
) -> str:
    if not dreams:
        return "（暂无梦境）"
    blocks = []
    for d in dreams:
        lines = [
            f"[{d.created_at[:10]}] {d.title}",
            f"原文：{d.raw_dream}",
        ]
        if d.analyst_notes.strip():
            lines.append(f"笔记：{d.analyst_notes}")
        msgs = (dream_messages or {}).get(d.id, [])
        if msgs:
            lines.append("对话记录：")
            for m in msgs:
                role = "用户" if m.role == "user" else "分析师"
                lines.append(f"{role}：{m.content}")
        blocks.append("\n".join(lines))
    return "\n\n---\n\n".join(blocks)


def build_extract_messages(
    profile: Profile | None,
    current_map: dict,
    dreams: list[DreamSession],
    latest_messages: list[Message] | None = None,
    dream_messages: dict[int, list[Message]] | None = None,
) -> list[dict[str, str]]:
    profile_text = ""
    if profile:
        parts = []
        if profile.display_name.strip():
            parts.append(f"称呼：{profile.display_name}")
        if profile.life_summary.strip():
            parts.append(f"背景：{profile.life_summary}")
        if profile.stressors.strip():
            parts.append(f"压力：{profile.stressors}")
        profile_text = "\n".join(parts) or "（无档案）"
    else:
        profile_text = "（无档案）"

    dreams_text = _format_dream_transcripts(dreams, dream_messages)

    latest_text = "（无新对话）"
    if latest_messages:
        latest_text = "\n".join(
            f"{'用户' if m.role == 'user' else '分析师'}：{m.content}"
            for m in latest_messages[-8:]
        )

    user_content = f"""## 来访者档案
{profile_text}

## 当前潜意识地图
{json.dumps(current_map, ensure_ascii=False, indent=2)}

## 历史梦境摘要
{dreams_text}

## 最新对话（重点参考）
{latest_text}

请输出更新后的完整 JSON。"""

    return [
        {"role": "system", "content": EXTRACT_PROMPT},
        {"role": "user", "content": user_content},
    ]


def build_rebuild_messages(
    profile: Profile | None,
    dreams: list[DreamSession],
    dream_messages: dict[int, list[Message]] | None = None,
) -> list[dict[str, str]]:
    return build_extract_messages(
        profile, _empty_map(), dreams, None, dream_messages
    )


def _empty_map() -> dict:
    return {
        "symbols": [],
        "shadow": {"current_theme": "", "movement": "不明", "note": ""},
        "animus_anima": {"polarity": "未显", "movement": "不明", "note": ""},
        "complexes": [],
    }
