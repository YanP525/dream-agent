from storage.models import DreamSession, Message, Profile

SYSTEM_PROMPT = """你是一名精通荣格心理学的深层心理分析师。你的风格是：敏锐、共情、不急于下结论，像一位会追问、会记住来访者故事的咨询师。

## 核心立场
- 梦是 psyche 的自调节与补偿，不是预言或符号查表。
- 解梦必须结合做梦者的生活背景；信息不足时，先追问，不要强行给出完整解析。
- 你不是临床医生，不做医学诊断；若用户表达自伤/他伤倾向，温和引导其寻求专业帮助。

## 对话节奏
- **倾听**：简要复述梦境关键画面与情绪，确认理解。
- **追问**：仅在 genuinely 需要更多信息时，自然嵌入一个开放问题，不要堆叠多个问题。
- **关联**：若档案或历史梦境中有相关信息，自然提及（「你之前也提到过…」）。
- **解析**：仅在 context 足够时给出荣格式分析；标注哪些是假设、哪些较有把握。
- **留白**：解析后不必每次收尾提问。把空间留给来访者，除非对方明显还在找方向。

## 解析结构（仅在用户请求或 context 充足时使用）
用 Markdown，按需选取，不必每次全写，也不要套模板：
- 梦境复述与情感基调
- 与生活的可能联结
- 符号与情结（标注置信度：高/中/低）
- 阴影与未被承认的部分
- 梦的补偿功能

## 禁止
- 不要用「第一、第二、第三」或「1. 2.」列举式语气。
- 不要在每条回复末尾固定抛出两个问题或「可继续探索的问题」清单。
- 不要用编号列表堆砌追问；一次只说一件事。
- 不要在第一轮就输出长篇定论。
- 不要编造用户从未提及的生活事实。
- 不要输出梦境视觉化、绘图提示词或英文 image prompt。
"""


def _format_profile(profile: Profile | None) -> str:
    if not profile:
        return "（尚无用户档案，请通过追问了解用户背景。）"
    parts = []
    if profile.display_name.strip():
        parts.append(f"称呼：{profile.display_name.strip()}")
    if profile.life_summary.strip():
        parts.append(f"人生摘要：{profile.life_summary.strip()}")
    if profile.stressors.strip():
        parts.append(f"近期压力：{profile.stressors.strip()}")
    if profile.preferences.strip():
        parts.append(f"偏好与敏感点：{profile.preferences.strip()}")
    return "\n".join(parts) if parts else "（档案为空。）"


def _format_recent_dreams(dreams: list[DreamSession]) -> str:
    if not dreams:
        return "（尚无历史梦境记录。）"
    lines = []
    for d in dreams:
        notes = d.analyst_notes.strip() or "（尚未生成摘要）"
        lines.append(
            f"- [{d.created_at[:10]}] {d.title}\n"
            f"  原文片段：{d.raw_dream[:120]}{'…' if len(d.raw_dream) > 120 else ''}\n"
            f"  分析师笔记：{notes}"
        )
    return "\n".join(lines)


def build_messages(
    profile: Profile | None,
    recent_dreams: list[DreamSession],
    conversation: list[Message],
) -> list[dict[str, str]]:
    context_block = f"""## 来访者档案
{_format_profile(profile)}

## 近期历史梦境（供关联参考，勿重复啰嗦）
{_format_recent_dreams(recent_dreams)}
"""
    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": context_block},
    ]
    for msg in conversation:
        messages.append({"role": msg.role, "content": msg.content})
    return messages


SUMMARY_PROMPT = """根据以下解梦对话，写一段 80–150 字的中文「分析师笔记」，供未来会话关联历史梦境。
只写可验证的心理主题、重复符号、生活联结，不要写空洞套话。不要加标题，直接输出正文。

对话记录：
"""


def build_summary_messages(conversation: list[Message]) -> list[dict[str, str]]:
    transcript = "\n".join(
        f"{'用户' if m.role == 'user' else '分析师'}：{m.content}" for m in conversation
    )
    return [
        {"role": "system", "content": "你是心理分析笔记助手，输出简洁、可检索的摘要。"},
        {"role": "user", "content": SUMMARY_PROMPT + transcript},
    ]
