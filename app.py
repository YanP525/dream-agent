# -*- coding: utf-8 -*-
import streamlit as st

from config import API_KEY, RECENT_DREAMS_LIMIT
from prompts.analyst import build_messages, build_summary_messages
from services.llm import chat
from services.psyche_map import (
    init_psyche_map_from_history,
    psyche_map_is_empty,
    rebuild_psyche_map,
    refresh_psyche_map,
)
from storage.database import init_db
from storage.repository import (
    add_message,
    create_dream,
    delete_dream,
    get_dream,
    get_messages,
    get_profile,
    get_psyche_map,
    get_recent_dreams,
    list_dreams,
    profile_is_complete,
    update_dream_notes,
    upsert_profile,
)

st.set_page_config(page_title="ShadowAgent - 潜意识沙盒", layout="wide")

init_db()

if not API_KEY:
    st.error("未找到 API 密钥。请在项目根目录创建 `.env` 并设置 `SILICONFLOW_API_KEY`。")
    st.stop()


def _text_area_height(value: str, min_px: int = 72, max_px: int = 360) -> int:
    text = value or ""
    lines = 0
    for line in text.split("\n") or [""]:
        lines += max(1, (len(line) + 26) // 27)
    lines = max(lines, 3)
    return min(max(lines * 24 + 20, min_px), max_px)


def _init_session_state() -> None:
    defaults = {
        "dream_id": None,
        "messages": [],
        "awaiting_reply": False,
        "pending_delete_id": None,
        "psyche_map_bootstrapped": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _load_dream(dream_id: int) -> None:
    st.session_state.dream_id = dream_id
    st.session_state.messages = [
        {"role": m.role, "content": m.content} for m in get_messages(dream_id)
    ]
    st.session_state.awaiting_reply = False
    st.session_state.pending_delete_id = None


def _start_new_dream() -> None:
    st.session_state.dream_id = None
    st.session_state.messages = []
    st.session_state.awaiting_reply = False
    st.session_state.pending_delete_id = None


def _delete_dream_record(dream_id: int) -> None:
    delete_dream(dream_id)
    if st.session_state.dream_id == dream_id:
        _start_new_dream()
    else:
        st.session_state.pending_delete_id = None
    profile = get_profile()
    dreams = list_dreams()
    try:
        rebuild_psyche_map(profile, dreams)
    except Exception:
        pass


def _update_psyche_map(latest_messages=None) -> None:
    profile = get_profile()
    dreams = list_dreams()
    refresh_psyche_map(profile, dreams, latest_messages)


def _maybe_init_psyche_map() -> None:
    if st.session_state.psyche_map_bootstrapped:
        return

    dreams = list_dreams()
    if not dreams or not psyche_map_is_empty():
        st.session_state.psyche_map_bootstrapped = True
        return

    total_msgs = sum(len(get_messages(d.id)) for d in dreams)
    if total_msgs < 2:
        st.session_state.psyche_map_bootstrapped = True
        return

    with st.spinner("正在从已有对话初始化潜意识地图…"):
        try:
            init_psyche_map_from_history(get_profile(), dreams)
        except Exception as e:
            st.sidebar.error(f"地图初始化失败: {e}")
            st.session_state.psyche_map_bootstrapped = True
            return

    st.session_state.psyche_map_bootstrapped = True
    st.rerun()


def _movement_color(movement: str) -> str:
    mapping = {
        "整合": "#4ade80",
        "浮现": "#fbbf24",
        "对峙": "#f87171",
        "压抑": "#94a3b8",
        "投射": "#c084fc",
        "退行": "#fb923c",
        "对抗": "#f87171",
        "不明": "#64748b",
    }
    return mapping.get(movement, "#64748b")


def _render_psyche_map() -> None:
    st.subheader("🗺️ 潜意识地图")
    psyche_map = get_psyche_map()

    shadow = psyche_map.get("shadow", {})
    animus = psyche_map.get("animus_anima", {})
    symbols = psyche_map.get("symbols", [])
    complexes = psyche_map.get("complexes", [])

    if not symbols and not shadow.get("current_theme") and not complexes:
        st.caption("对话后会自动更新意象、阴影与阿尼姆斯/阿尼玛状态。")
        dreams = list_dreams()
        if dreams and sum(len(get_messages(d.id)) for d in dreams) >= 2:
            if st.button("从已有对话初始化", use_container_width=True):
                with st.spinner("正在读取历史对话…"):
                    try:
                        init_psyche_map_from_history(get_profile(), dreams)
                        st.session_state.psyche_map_bootstrapped = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"初始化失败: {e}")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🌑 阴影**")
        theme = shadow.get("current_theme") or "尚未浮现"
        movement = shadow.get("movement", "不明")
        color = _movement_color(movement)
        st.markdown(
            f"<span style='color:{color};font-weight:600'>{movement}</span> · {theme}",
            unsafe_allow_html=True,
        )
        if shadow.get("note"):
            st.caption(shadow["note"])

    with col2:
        st.markdown("**⚡ 阿尼姆斯 / 阿尼玛**")
        polarity = animus.get("polarity", "未显")
        movement = animus.get("movement", "不明")
        color = _movement_color(movement)
        st.markdown(
            f"<span style='color:{color};font-weight:600'>{movement}</span> · {polarity}",
            unsafe_allow_html=True,
        )
        if animus.get("note"):
            st.caption(animus["note"])

    if symbols:
        st.markdown("**🔮 意象对应**")
        for item in symbols:
            themes = " · ".join(item.get("linked_themes", []))
            theme_part = f"（{themes}）" if themes else ""
            st.markdown(
                f"**{item.get('symbol', '')}** · {item.get('intensity', '中')}"
                f"{theme_part}  \n{item.get('personal_meaning', '')}"
            )

    if complexes:
        st.markdown("**🧵 情结**")
        for c in complexes:
            st.markdown(
                f"**{c.get('name', '')}** · {c.get('status', '活跃')}  \n"
                f"触发：{c.get('trigger', '—')}"
            )


def _render_sidebar() -> None:
    st.subheader("📁 潜意识档案")
    profile = get_profile()

    with st.expander("个人档案", expanded=not profile_is_complete(profile)):
        display_name = st.text_input(
            "称呼（可选）",
            value=profile.display_name if profile else "",
        )
        life_summary_value = profile.life_summary if profile else ""
        life_summary = st.text_area(
            "人生背景摘要",
            value=life_summary_value,
            placeholder="例如：28岁，设计师，近期在考虑换工作…",
            height=_text_area_height(life_summary_value),
        )
        stressors_value = profile.stressors if profile else ""
        stressors = st.text_area(
            "近期压力与关注",
            value=stressors_value,
            placeholder="例如：与前伴侣未完成的对话、睡眠不好…",
            height=_text_area_height(stressors_value),
        )
        preferences_value = profile.preferences if profile else ""
        preferences = st.text_area(
            "解析偏好（可选）",
            value=preferences_value,
            placeholder="例如：不要太玄学，多联系现实",
            height=_text_area_height(preferences_value, min_px=60, max_px=200),
        )
        if st.button("保存档案", use_container_width=True):
            upsert_profile(display_name, life_summary, stressors, preferences)
            st.success("档案已更新")
            st.rerun()

    if profile and profile_is_complete(profile):
        st.caption("档案已载入，分析师会结合你的背景对话。")

    st.divider()
    _render_psyche_map()

    st.divider()
    st.subheader("🌙 梦境记录")

    if st.button("＋ 新梦境", type="primary", use_container_width=True):
        _start_new_dream()
        st.rerun()

    dreams = list_dreams()
    if not dreams:
        st.info("还没有历史记录。在右侧输入梦境开始。")
    else:
        for dream in dreams:
            is_active = st.session_state.dream_id == dream.id
            is_pending_delete = st.session_state.pending_delete_id == dream.id
            label = f"{'▸ ' if is_active else ''}{dream.title}"
            col_open, col_del = st.columns([5, 1])
            with col_open:
                if st.button(label, key=f"dream_{dream.id}", use_container_width=True):
                    _load_dream(dream.id)
                    st.rerun()
            with col_del:
                if st.button("🗑", key=f"del_{dream.id}", help="删除这条记忆"):
                    st.session_state.pending_delete_id = dream.id
                    st.rerun()

            if is_pending_delete:
                st.warning(f"确认删除「{dream.title}」？")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("确认", key=f"confirm_del_{dream.id}", type="primary"):
                        _delete_dream_record(dream.id)
                        st.rerun()
                with c2:
                    if st.button("取消", key=f"cancel_del_{dream.id}"):
                        st.session_state.pending_delete_id = None
                        st.rerun()

    if st.session_state.dream_id:
        st.divider()
        if st.button("✓ 结束本次解析", use_container_width=True):
            _finalize_session()


def _finalize_session() -> None:
    dream_id = st.session_state.dream_id
    if not dream_id:
        return
    messages = get_messages(dream_id)
    if len(messages) < 2:
        st.sidebar.warning("对话太短，暂无法生成摘要。")
        return
    with st.spinner("正在沉淀本次解析笔记…"):
        try:
            summary = chat(build_summary_messages(messages))
            update_dream_notes(dream_id, summary.strip())
            _update_psyche_map(messages)
            st.sidebar.success("已保存分析师笔记，潜意识地图已更新。")
        except Exception as e:
            st.sidebar.error(f"摘要生成失败: {e}")


def _queue_user_message(user_text: str) -> None:
    user_text = user_text.strip()
    if not user_text:
        return

    if st.session_state.dream_id is None:
        dream = create_dream(raw_dream=user_text)
        st.session_state.dream_id = dream.id

    dream_id = st.session_state.dream_id
    add_message(dream_id, "user", user_text)
    st.session_state.messages.append({"role": "user", "content": user_text})
    st.session_state.awaiting_reply = True


def _generate_assistant_reply() -> None:
    dream_id = st.session_state.dream_id
    if not dream_id:
        st.session_state.awaiting_reply = False
        return

    profile = get_profile()
    recent = get_recent_dreams(limit=RECENT_DREAMS_LIMIT, exclude_id=dream_id)
    db_messages = get_messages(dream_id)
    llm_messages = build_messages(profile, recent, db_messages)

    with st.chat_message("assistant"):
        try:
            with st.spinner("分析师在思考…"):
                reply = chat(llm_messages)
        except Exception as e:
            st.error(f"解析失败: {e}")
            st.session_state.awaiting_reply = False
            return
        st.markdown(reply)

    add_message(dream_id, "assistant", reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.awaiting_reply = False

    try:
        with st.spinner("更新潜意识地图…"):
            _update_psyche_map(get_messages(dream_id))
    except Exception:
        pass
    st.rerun()


def _render_chat() -> None:
    st.title("🌙 ShadowAgent：荣格心理学潜意识沙盒")
    st.caption("基于深度心理学的梦境对话 · 会追问、会记住、会关联你的历史")

    if st.session_state.dream_id:
        dream = get_dream(st.session_state.dream_id)
        if dream:
            st.markdown(f"**当前梦境：** {dream.title}")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.awaiting_reply:
        _generate_assistant_reply()

    if not st.session_state.messages and not st.session_state.awaiting_reply:
        st.info(
            "写下你的梦境——越具体越好。分析师会先倾听和追问，"
            "结合你的档案与历史梦境再给出解析。"
        )

    user_input = st.chat_input("描述梦境，或回答分析师的追问…")
    if user_input:
        _queue_user_message(user_input)
        st.rerun()


_init_session_state()
_maybe_init_psyche_map()

col_side, col_main = st.columns([1, 2.2], gap="large")

with col_side:
    _render_sidebar()

with col_main:
    _render_chat()
