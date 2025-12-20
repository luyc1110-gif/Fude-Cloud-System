import streamlit as st

st.set_page_config(
    page_title="福德里社區管理系統",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🔥 莫蘭迪配色定義
COLORS = {
    "volunteer": "#9A8C98", # 煙燻紫
    "elderly": "#B5838D",   # 暮色粉
    "care": "#8E9775",      # 鼠尾草綠
    "bg": "#F8F9FA"         # 極淺灰底
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
[data-testid="stSidebar"] {{ display: none; }}
.stApp {{ background-color: {COLORS['bg']}; }}

.big-btn {{
    width: 100%;
    padding: 45px 20px;
    border-radius: 25px;
    text-align: center;
    background-color: white;
    box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    border: 1px solid rgba(0,0,0,0.05);
    transition: all 0.3s ease;
    margin-bottom: 15px;
}}
.big-btn:hover {{
    transform: translateY(-10px);
    box-shadow: 0 15px 40px rgba(0,0,0,0.1);
}}
.icon {{ font-size: 4rem; margin-bottom: 20px; display: block; }}
.btn-title {{ font-size: 1.8rem; font-weight: 900; margin-bottom: 10px; display: block; }}
.btn-desc {{ font-size: 0.95rem; color: #777; line-height: 1.6; display: block; }}

/* 莫蘭迪色系文字設定 */
.theme-vol {{ color: {COLORS['volunteer']}; }}
.theme-elder {{ color: {COLORS['elderly']}; }}
.theme-care {{ color: {COLORS['care']}; }}

div[data-testid="stButton"] > button {{
    border-radius: 50px !important;
    font-weight: 700 !important;
    padding: 10px 20px !important;
    border: 1.5px solid transparent !important;
}}
/* 莫蘭迪按鈕樣式 */
.st-vol button {{ background-color: {COLORS['volunteer']} !important; color: white !important; }}
.st-elder button {{ background-color: {COLORS['elderly']} !important; color: white !important; }}
.st-care button {{ background-color: {COLORS['care']} !important; color: white !important; }}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #444; margin-top: 20px;'>🏘️ 福德里社區管理中樞</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888; font-size: 1.2rem; margin-bottom: 40px;'>人文關懷．數位整合</p>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""<div class="big-btn"><span class="icon">💜</span><span class="btn-title theme-vol">志工管理</span><span class="btn-desc">時數統計與名冊維護</span></div>""", unsafe_allow_html=True)
    st.markdown('<div class="st-vol">', unsafe_allow_html=True)
    if st.button("點擊進入志工系統", use_container_width=True): st.switch_page("pages/1_volunteer.py")
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="big-btn"><span class="icon">👴</span><span class="btn-title theme-elder">長輩關懷</span><span class="btn-desc">據點報到與血壓追蹤</span></div>""", unsafe_allow_html=True)
    st.markdown('<div class="st-elder">', unsafe_allow_html=True)
    if st.button("點擊進入長輩系統", use_container_width=True): st.switch_page("pages/2_elderly.py")
    st.markdown('</div>', unsafe_allow_html=True)

with c3:
    st.markdown(f"""<div class="big-btn"><span class="icon">🏠</span><span class="btn-title theme-care">關懷戶系統</span><span class="btn-desc">弱勢名冊與物資發放</span></div>""", unsafe_allow_html=True)
    st.markdown('<div class="st-care">', unsafe_allow_html=True)
    if st.button("點擊進入關懷戶系統", use_container_width=True): st.switch_page("pages/3_care.py")
    st.markdown('</div>', unsafe_allow_html=True)
