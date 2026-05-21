# -*- coding: utf-8, encoding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import requests
import re

# 1. 网页基础配置（设置为暗黑风、宽屏）
st.set_page_config(page_title="ShadowAgent - 潜意识沙盒", layout="wide")

st.title("🌙 ShadowAgent：荣格心理学潜意识沙盒")
st.caption("基于深度心理学与荣格八维理论的梦境与阴影特征追踪系统")

# 2. 初始化大模型客户端（这里换上你之前用的 DeepSeek 或 OpenAI 的 API）
# 建议在实际使用时把 base_url 和 api_key 替换成你的可用配置
client = OpenAI(
    api_key="sk-xbilnhagmoncwomzkxnxejkheobmubaawofrercuipbylbwq", 
    base_url="https://api.siliconflow.cn/v1"  # 或者是你之前用的中转地址
)

# 3. 注入灵魂的系统 Prompt（去塑料感，强化功能冲突）
SYSTEM_PROMPT = """
你是一名冷峻、敏锐、不讲废话的深层心理学大师。你精通荣格心理学、精神分析和荣格八维动力学。
不要用流水线报告的语气，不要说“第一、第二”这种无聊的废话。

请用充满洞察力、略带宿命感和穿透力的语言，直接剖析用户给出的梦境碎片。
你必须严格包含以下三个部分，并用 Markdown 的 `##` 作为分隔符：

## 👁️ 阴影与压抑的自白
[在这里直接指出梦境符号背后的真实恐惧、嫉妒、或者被社会化面具掩盖的欲望。撕开虚伪的安慰，用富有心理学美感的语言直接指出用户在逃避什么。]

## ⚙️ 荣格八维功能崩塌分析
[精准判定这场梦是哪些功能的冲突。例如：是不是主导功能 Ti 过度运转导致大脑烧毁，从而让劣势功能 Fe 变成梦里的追杀者？或者是 Ne 失去了控制，把现实焦虑无限放大？给出最底层的心理学功能解释。]

## 🌌 梦境视觉复原描述
[仅输出一段用来绘图的英文提示词，不要带任何中文解释，严格以下面的格式输出：
Surrealism painting, [英文描述梦境中最视觉震撼的画面], dark, symbolic, cinematic lighting, 8k]
"""

# 4. 绘图函数
def generate_dream_image(image_prompt, api_key):
    url = f"{BASE_URL}/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    # 使用硅基流动的 SDXL 绘图模型
    payload = {
        "model": "stabilityai/stable-diffusion-xl-base-1.0", 
        "prompt": image_prompt,
        "negative_prompt": "ugly, deformed, blurry, low quality, text, words",
        "image_size": "1024x1024",
        "batch_size": 1
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()["data"][0]["url"]
        else:
            st.error(f"绘图服务器返回错误: {response.text}")
    except Exception as e:
        st.error(f"绘图引擎连不上了: {e}")
    return None

# 5. 网页界面布局
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🔑 开发者凭据")
    st.session_state["SF_API_KEY"] = st.text_input(
        "输入你的硅基流动 API Key:", 
        value=st.session_state["SF_API_KEY"],
        type="password"
    )
    
    st.subheader("📁 潜意识档案")
    st.info("长期情结网络图谱（开发中...）")
    
    if st.button("✨ 载入昨夜的荒诞梦境模板"):
        st.session_state["dream_input"] = "被前女友/前男友追着说话，嘴巴扭曲。旁边还有健身房的肌肉女在发光的柜台上拉伸。感觉很累、很压抑。"

with col2:
    st.subheader("✍️ 投递你的梦境碎片")
    
    if "dream_input" not in st.session_state:
        st.session_state["dream_input"] = ""
        
    user_dream = st.text_area(
        "写下那些越轨的、残忍的、或者无法理解的画面：",
        value=st.session_state["dream_input"],
        height=180,
    )

    if st.button("👁️ 开始深层解析", type="primary"):
        if not st.session_state["SF_API_KEY"]:
            st.error("请先在左侧输入你的硅基流动 API Key！")
        elif not user_dream.strip():
            st.warning("潜意识是一片空白，请先输入文字。")
        else:
            analysis_placeholder = st.empty()
            with st.spinner("正在剥离你的显意识防御..."):
                try:
                    # 初始化客户端
                    client = OpenAI(api_key=st.session_state["SF_API_KEY"], base_url=BASE_URL)
                    
                    # 1. 呼叫大模型解梦
                    response = client.chat.completions.create(
                        model="deepseek-ai/DeepSeek-V3",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_dream}
                        ],
                        stream=False 
                    )
                    
                    full_text = response.choices[0].message.content
                    
                    # 2. 渲染心理学报告
                    analysis_placeholder.markdown(full_text)
                    
                    # 3. 🔍 【核心修复】使用正则表达式强行切分文本
                    # 匹配包含“梦境视觉复原”关键字的标题，不管它带不带括号或井号
                    match = re.search(r"##?\s*.*?梦境视觉复原.*?\n(.*)", full_text, re.DOTALL)
                    
                    if match:
                        image_prompt = match.group(1).strip()
                        # 清理可能残留的 markdown 标记
                        image_prompt = re.sub(r"```[a-zA-Z]*", "", image_prompt).replace("
```", "").strip()
                        
                        st.write("---")
                        st.subheader("🖼️ 梦境多模态视觉复原")
                        
                        with st.spinner("绘图智能体正在捕捉潜意识画面..."):
                            img_url = generate_dream_image(image_prompt, st.session_state["SF_API_KEY"])
                            if img_url:
                                st.image(img_url, caption="ShadowAgent 复原的梦境世界", use_container_width=True)
                            else:
                                st.warning("图片生成没成功，请查看上面的错误提示。")
                    else:
                        st.warning("未能自动解析出英文绘图提示词，请检查大模型的输出格式。")
                                
                except Exception as e:
                    st.error(f"解析失败: {e}")