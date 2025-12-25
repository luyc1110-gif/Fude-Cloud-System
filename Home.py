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
# 1) CSS 魔術：強制亮色 + 卡片設計 + 修復按鈕覆蓋
# =========================================================
st.markdown("""
<style>
/* 🔥 1. 網頁背景色 */
.stApp {
    background-color: #F0F2F5 !important;
    color: #333333 !important;
}

/* 隱藏預設側邊欄 */
[data-testid="stSidebar"] { display: none; }
.block-container { padding-top: 2rem; max-width: 1200px; }

/* --- 🔥 2. 卡片容器設定 --- */
div[data-testid="column"] {
    background-color: #FFFFFF; /* 卡片白底 */
    border-radius: 20px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    border: 1px solid #eee;
    padding: 0px !important;
    overflow: hidden;
    transition: transform 0.3s, box-shadow 0.3s;
    position: relative; /* 讓絕對定位的按鈕可以對齊這裡 */
    height: 100%;
    display: flex;         /* 確保內容垂直排列 */
    flex-direction: column; 
}

/* 滑鼠移過去浮起來 */
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
    flex-shrink: 0; /* 確保圖片不會被壓縮 */
}
.card-img-box img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

/* --- 文字與按鈕區域 --- */
.card-content {
    padding: 25px 20px 40px 20px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    flex-grow: 1; /* 讓文字區填滿剩下空間 */
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
    margin-bottom: 20px;
}

/* --- 這是那個「置中的黑色按鈕 (偽裝)」樣式 --- */
.card-btn {
    background-color: #212121;
    color: white !important;
    padding: 10px 30px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 1.1rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    display: inline-block;
    margin-top: auto; /* 把按鈕推到底部 */
}

/* --- 🔥🔥🔥 [關鍵修正] 透明按鈕覆蓋術 (強力版) 🔥🔥🔥 --- */

/* 1. 針對按鈕的外框 (Wrapper) */
div[data-testid="column"] .stButton {
    position: absolute !important; /* 強制浮動 */
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    z-index: 99 !important; /* 確保在最上層 */
    margin: 0 !important;
    padding: 0 !important;
    display: block !important;
}

/* 2. 針對按鈕本體 (Button) */
div[data-testid="column"] .stButton button {
    width: 100% !important;
    height: 100% !important;
    opacity: 0 !important; /* 變成透明 */
    border: none !important;
    cursor: pointer !important;
    background-color: transparent !important;
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

systems = [
    {
        "title": "志工管理系統",
        "desc": "志工打卡・時數統計<br>榮譽與名冊管理",
        "img_file": "cover_volunteer.jpg",  
        "icon": "💜", 
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

cols = st.columns(3)

for i, col in enumerate(cols):
    sys = systems[i]
    with col:
        # 1. 圖片
        if os.path.exists(sys["img_file"]):
            st.image(sys["img_file"], use_container_width=True)
        else:
            st.markdown(f"""
            <div class="card-img-box" style="background-color: {sys['color']}15;">
                <span style="font-size: 5rem;">{sys['icon']}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # 2. 內容 + 偽裝按鈕
        st.markdown(f"""
        <div class="card-content">
            <div class="card-title" style="color: {sys['color']}">{sys['title']}</div>
            <div class="card-desc">{sys['desc']}</div>
            <div class="card-btn">進入系統</div>
        </div>
        """, unsafe_allow_html=True)

        # 3. 真實按鈕 (透明覆蓋)
        # 這裡把按鈕文字改成空白 " "，避免 btn_0 露餡
        if st.button(" ", key=f"btn_{i}"):
            st.switch_page(sys['link'])

st.markdown("---")
st.markdown("<div style='text-align: center; color: #aaa; margin-top: 20px;'>福德里辦公處 © 2025 • 數位化服務</div>", unsafe_allow_html=True)
