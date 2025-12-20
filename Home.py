import streamlit as st

# 頁面設定
st.set_page_config(
    page_title="福德里社區管理系統",
    page_icon="🏘️",
    layout="wide", # 🔥 改成寬版，容納三個卡片
    initial_sidebar_state="collapsed"
)

# CSS 美化
st.markdown("""
<style>
[data-testid="stSidebar"] { display: none; }
.block-container { padding-top: 3rem; max-width: 1200px; }

/* 大卡片按鈕樣式 */
.big-btn {
    width: 100%;
    padding: 40px 20px;
    border-radius: 25px;
    text-align: center;
    background-color: white;
    box-shadow: 0 10px 25px rgba(0,0,0,0.08);
    border: 3px solid white;
    cursor: default; /* 純展示用，點擊靠下方的 button */
    margin-bottom: 15px;
    height: 100%;
    transition: transform 0.3s;
}
.big-btn:hover {
    transform: translateY(-5px);
}

.icon { font-size: 5rem; margin-bottom: 15px; display: block; }
.btn-title { font-size: 1.8rem; font-weight: 900; margin-bottom: 10px; display: block; }
.btn-desc { font-size: 1rem; color: #666; font-weight: 500; display: block; }

/* 志工系統配色 */
.theme-vol { color: #4A148C; }
.border-vol:hover { border-color: #4A148C; box-shadow: 0 15px 35px rgba(74, 20, 140, 0.15); }

/* 長輩系統配色 */
.theme-elder { color: #E65100; }
.border-elder:hover { border-color: #E65100; box-shadow: 0 15px 35px rgba(230, 81, 0, 0.15); }

/* 關懷戶系統配色 */
.theme-care { color: #00695C; }
.border-care:hover { border-color: #00695C; box-shadow: 0 15px 35px rgba(0, 105, 92, 0.15); }

/* 按鈕微調 */
div[data-testid="stButton"] > button {
    border-radius: 50px !important;
    font-weight: 900 !important;
    font-size: 1.2rem !important;
    padding: 15px 0 !important;
    border-width: 2px !important;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

# 標題區
st.markdown("<h1 style='text-align: center; color: #333; margin-bottom: 10px;'>🏘️ 福德里 - 社區數位管理中樞</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 1.2rem; margin-bottom: 50px;'>志工調度．長輩照護．弱勢關懷．一站整合</p>", unsafe_allow_html=True)

# 三欄版面
c1, c2, c3 = st.columns(3)

# 1. 志工系統
with c1:
    st.markdown("""
    <div class="big-btn border-vol">
        <span class="icon">💜</span>
        <span class="btn-title theme-vol">志工管理系統</span>
        <span class="btn-desc">志工打卡、時數統計<br>榮譽與名冊管理</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("進入【志工系統】", use_container_width=True):
        st.switch_page("pages/1_志工管理.py")

# 2. 長輩系統
with c2:
    st.markdown("""
    <div class="big-btn border-elder">
        <span class="icon">👴</span>
        <span class="btn-title theme-elder">長輩關懷系統</span>
        <span class="btn-desc">據點報到、血壓量測<br>健康數據追蹤</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("進入【長輩系統】", use_container_width=True):
        st.switch_page("pages/2_長輩管理.py")

# 3. 關懷戶系統 (預留)
with c3:
    st.markdown("""
    <div class="big-btn border-care">
        <span class="icon">🏠</span>
        <span class="btn-title theme-care">關懷戶系統</span>
        <span class="btn-desc">弱勢家戶名冊、物資發放<br>訪視紀錄 (建置中)</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("進入【關懷戶系統】", use_container_width=True):
        st.switch_page("pages/3_關懷戶管理.py")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #aaa; margin-top: 20px;'>福德里辦公處 © 2025 • 數位化服務</div>", unsafe_allow_html=True)
