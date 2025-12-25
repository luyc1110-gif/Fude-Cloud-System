import streamlit as st
import os

# =========================================================
# 0) 頁面設定
# =========================================================
st.set_page_config(
    page_title="福德里社區管理系統",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# 1) CSS 魔術：強制亮色模式 + 卡片按鈕
# =========================================================
st.markdown("""
<style>
/* 🔥🔥🔥 關鍵修正：強制將背景設為亮色，忽略系統深色模式 🔥🔥🔥 */
.stApp {
    background-color: #F0F2F5 !important;
    color: #333333 !important;
}

/* 隱藏預設側邊欄 */
[data-testid="stSidebar"] { display: none; }
.block-container { padding-top: 2rem; max-width: 1200px; }

/* --- 卡片容器樣式 --- */
div[data-testid="column"] {
    background-color: white; /* 卡片本身是白色 */
    border-radius: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    border: 1px solid #eee;
    padding: 0px !important;
    overflow: hidden;
    transition: transform 0.3s, box-shadow 0.3s;
    position: relative;
    height: 100%;
}

div[data-testid="column"]:hover {
    transform: translateY(-8px);
    box-shadow: 0 15px 30px rgba(0,0,0,0.12);
    border-color: #ddd;
}

/* --- 圖片區域 --- */
.card-img-box {
    width: 100%;
    height: 200px;
    background-color: #f0f0f0;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}
.card-img-box img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

/* --- 文字內容區域 --- */
.card-content {
    padding: 25px 20px 40px 20px;
    text-align: center;
}
.card-title {
    font-size: 1.5rem;
    font-weight: 900;
    margin-bottom: 10px;
}
.card-desc {
    font-size: 1rem;
    color: #666;
    line-height: 1.5;
}

/* --- 透明按鈕覆蓋術 --- */
div[data-testid="column"] [data-testid="stButton"] {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 10;
    margin: 0;
}
div[data-testid="column"] [data-testid="stButton"] button {
    width: 100%;
    height: 100%;
    opacity: 0;
    border: none;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 標題區
# =========================================================
st.markdown("<h1 style='text-align: center; color: #333; margin-bottom: 10px;'>🏘️ 福德里 - 社區數位管理中樞</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 1.2rem; margin-bottom: 40px;'>志工調度．長輩照護．弱勢關懷．一站整合</p>", unsafe_allow_html=True)

# =========================================================
# 3) 三大系統入口 (卡片區)
# =========================================================

# 定義三個系統的資訊
systems = [
    {
        "title": "志工管理系統",
        "desc": "志工打卡・時數統計<br>榮譽與名冊管理",
        "img_file": "cover_volunteer.jpg",  # 請確認您的圖片檔名
        "icon": "💜", # 如果沒圖片時顯示的替代 icon
        "link": "pages/1_volunteer.py",
        "color": "#4A148C"
    },
    {
        "title": "長輩關懷系統",
        "desc": "據點報到・血壓量測<br>健康數據追蹤",
        "img_file": "cover_elderly.jpg",
        "icon": "👴",
        "link": "pages/2_elderly.py",
        "color": "#E65100"
    },
    {
        "title": "關懷戶系統",
        "desc": "弱勢家戶名冊・物資發放<br>訪視紀錄 (建置中)",
        "img_file": "cover_care.jpg",
        "icon": "🏠",
        "link": "pages/3_care.py",
        "color": "#00695C"
    }
]

# 建立三欄
cols = st.columns(3)

# 迴圈生成卡片
for i, col in enumerate(cols):
    sys = systems[i]
    with col:
        # 1. 顯示圖片 (如果有檔案就顯示圖片，沒有就顯示漂亮色塊+Icon)
        if os.path.exists(sys["img_file"]):
            st.image(sys["img_file"], use_container_width=True)
        else:
            # 沒圖片時的替代方案：顯示色塊與Icon
            st.markdown(f"""
            <div class="card-img-box" style="background-color: {sys['color']}15;">
                <span style="font-size: 5rem;">{sys['icon']}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # 2. 顯示文字內容
        st.markdown(f"""
        <div class="card-content">
            <div class="card-title" style="color: {sys['color']}">{sys['title']}</div>
            <div class="card-desc">{sys['desc']}</div>
        </div>
        """, unsafe_allow_html=True)

        # 3. 放置一個「透明的巨大按鈕」在最上層
        # 因為 CSS 設定，這個按鈕會自動拉伸蓋住整張卡片
        if st.button(f"進入 {sys['title']}", key=f"btn_{i}"):
            st.switch_page(sys['link'])

st.markdown("---")
st.markdown("<div style='text-align: center; color: #aaa; margin-top: 20px;'>福德里辦公處 © 2025 • 數位化服務</div>", unsafe_allow_html=True)
