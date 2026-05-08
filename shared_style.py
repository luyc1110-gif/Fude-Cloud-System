"""
shared_style.py ── 福德里社區管理系統共用樣式
=====================================================
所有子頁面只需 import 並呼叫 apply_base_style()，
即可套用一致的版型基底。各頁面只需傳入自己的主色。

使用方式：
    from shared_style import apply_base_style
    apply_base_style(primary="#4A148C", accent="#7B1FA2")
"""

import streamlit as st


# ── 各系統預設主題色 ──────────────────────────────
THEMES = {
    "volunteer": {"primary": "#4A148C", "accent": "#7B1FA2"},
    "elderly":   {"primary": "#EF6C00", "accent": "#FFA726"},
    "care":      {"primary": "#4A4E69", "accent": "#8E9775"},
    "home":      {"primary": "#4A148C", "accent": "#7B1FA2"},
}


def apply_base_style(
    primary: str = "#4A148C",
    accent:  str = "#7B1FA2",
    bg_main: str = "#F0F2F5",
    text:    str = "#212121",
) -> None:
    """
    套用全站共用 CSS 基底樣式。
    呼叫時請放在 st.set_page_config() 之後、任何其他 st.markdown() 之前。
    """
    st.markdown(f"""
<style>
/* ═══════════════════════════════════════════════
   FUDE 社區系統 ── 共用基底樣式 v1.0
   Primary : {primary}
   Accent  : {accent}
═══════════════════════════════════════════════ */

@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

/* 1. 全站字型 */
html, body, [class*="css"], div, p, span, li, ul {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
}}
[data-testid="stWidgetLabel"] p, label p, .stMarkdown p {{
    color: {text} !important;
}}

/* 2. 整體背景 */
.stApp {{ background-color: {bg_main} !important; }}

/* 3. 側邊欄 */
section[data-testid="stSidebar"] {{
    background-color: {bg_main};
    border-right: none;
    min-width: 200px !important;
    max-width: 230px !important;
}}

/* 4. 主內容白卡片 */
.block-container {{
    background-color: #FFFFFF;
    border-radius: 25px;
    padding: 3rem 3rem !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    margin-top: 2rem;
    margin-bottom: 2rem;
    max-width: 95% !important;
}}

/* 5. 頂部 header 透明化 */
header[data-testid="stHeader"] {{
    display: block !important;
    background-color: transparent !important;
}}
header[data-testid="stHeader"] .decoration {{ display: none; }}

/* 6. 側邊欄按鈕 */
section[data-testid="stSidebar"] button {{
    background-color: #FFFFFF !important;
    color: #666666 !important;
    border: 1px solid transparent !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    border-radius: 25px !important;
    padding: 10px 15px !important;
    font-weight: 700 !important;
    width: 100%;
    margin-bottom: 8px !important;
    transition: all 0.2s;
}}
section[data-testid="stSidebar"] button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
    color: {primary} !important;
}}

/* 7. 目前選中頁面指示器 */
.nav-active {{
    background: linear-gradient(135deg, {primary}, {accent});
    color: white !important;
    padding: 12px 0;
    text-align: center;
    border-radius: 25px;
    font-weight: 900;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    margin-bottom: 12px;
    cursor: default;
}}

/* 8. 輸入框 & 下拉選單 */
div[data-baseweb="select"] > div,
.stTextInput input,
.stDateInput input,
.stNumberInput input,
.stTimeInput input {{
    background-color: #FFFFFF !important;
    border: 2px solid #E0E0E0 !important;
    border-radius: 12px !important;
    color: {text} !important;
    -webkit-text-fill-color: {text} !important;
}}
div[role="listbox"], ul[data-baseweb="menu"], li[role="option"] {{
    background-color: #FFFFFF !important;
    color: {text} !important;
}}
li[role="option"]:hover {{ background-color: {primary}18 !important; }}

/* 多選標籤 */
span[data-baseweb="tag"] {{ background-color: {primary} !important; }}
span[data-baseweb="tag"] span {{ color: #FFFFFF !important; font-weight: bold !important; }}
span[data-baseweb="tag"] svg {{ fill: #FFFFFF !important; }}

/* 9. 主要按鈕 */
button[kind="primary"],
div[data-testid="stFormSubmitButton"] > button,
.stButton > button[kind="primary"] {{
    background-color: {primary} !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px 20px !important;
    font-weight: 900 !important;
}}
button[kind="primary"]:hover,
div[data-testid="stFormSubmitButton"] > button:hover {{
    background-color: {accent} !important;
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}}
button[kind="primary"] *, div[data-testid="stFormSubmitButton"] > button * {{
    color: #FFFFFF !important;
}}

/* 10. 日期選單明亮主題 */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="calendar"] {{
    background-color: #FFFFFF !important;
}}
div[data-baseweb="calendar"] *, div[data-baseweb="popover"] * {{
    color: {text} !important;
    fill: {text} !important;
}}
div[data-baseweb="calendar"] button[aria-selected="true"] {{
    background-color: {primary} !important;
    border-radius: 8px !important;
}}
div[data-baseweb="calendar"] button[aria-selected="true"] * {{
    color: #FFFFFF !important;
}}
div[data-baseweb="calendar"] button:hover {{
    background-color: {primary}22 !important;
    border-radius: 8px !important;
}}

/* 11. checkbox & label 文字 */
.stCheckbox label, .stCheckbox span {{
    color: {text} !important;
}}
label, .stTextInput label, .stSelectbox label,
.stDateInput label, .stNumberInput label,
[data-testid="stWidgetLabel"] {{
    color: {text} !important;
}}

/* 12. 時間輸入修正 */
div[data-testid="stTimeInput"] input,
div[data-testid="stTimeInput"] * {{
    color: {text} !important;
    -webkit-text-fill-color: {text} !important;
    opacity: 1 !important;
}}

/* 13. 響應式折行 (平板適配) */
@media (max-width: 1200px) {{
    .block-container {{
        padding: 1.5rem 1rem !important;
        max-width: 100% !important;
    }}
    div[data-testid="stHorizontalBlock"] {{
        flex-wrap: wrap !important;
    }}
    div[data-testid="column"] {{
        min-width: 260px !important;
        width: auto !important;
        flex: 1 1 auto !important;
        margin-bottom: 1rem !important;
    }}
}}
</style>
""", unsafe_allow_html=True)


def sidebar_footer(year: int = 2026, label: str = "福德里辦公處") -> None:
    """側邊欄底部版權標示（選用）"""
    st.markdown(
        f"<div style='text-align:center; color:#999; font-size:0.8rem; margin-top:20px;'>"
        f"{label} © {year}</div>",
        unsafe_allow_html=True,
    )
