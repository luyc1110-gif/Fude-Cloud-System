import streamlit as st
import os

# =========================================================
# 0) 系統設定
# =========================================================
st.set_page_config(
    page_title="福德里社區管理系統",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded" # 預設展開側邊欄以便導航
)

# =========================================================
# 1) CSS 樣式 (首頁專用視覺)
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

/* 全域字體 */
html, body, [class*="css"], div, p, span, li, ul {
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: #333333;
}

/* 背景色設定 */
.stApp {
    background-color: #F0F2F5 !important;
}

/* 側邊欄樣式 */
section[data-testid="stSidebar"] {
    background-color: #F0F2F5;
    border-right: none;
}

/* 🔥 主內容區：懸浮大卡片 */
.block-container {
    background-color: #FFFFFF;
    border-radius: 25px;
    padding: 3rem 4rem !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    margin-top: 2rem;
    margin-bottom: 2rem;
    max-width: 1100px !important;
}

/* 隱藏預設 Header (讓畫面更乾淨) */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}
header[data-testid="stHeader"] .decoration {
    display: none;
}

/* --- 側邊欄導航按鈕 (膠囊風格) --- */
section[data-testid="stSidebar"] button {
    background-color: #FFFFFF !important;
    color: #555 !important;
    border: 1px solid transparent !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
    border-radius: 25px !important;
    padding: 12px 0 !important;
    font-weight: 700 !important;
    width: 100%;
    margin-bottom: 10px !important;
    transition: all 0.3s;
}
section[data-testid="stSidebar"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.1) !important;
    color: #000 !important;
    border: 1px solid #ddd !important;
}

/* --- 首頁內容區塊樣式 --- */
.hero-title {
    font-size: 2.5rem;
    font-weight: 900;
    color: #2c3e50;
    text-align: center;
    margin-bottom: 10px;
}
.hero-subtitle {
    font-size: 1.2rem;
    color: #7f8c8d;
    text-align: center;
    margin-bottom: 50px;
}

/* 服務介紹區塊 (Service Section) */
.service-box {
    display: flex;
    align-items: center;
    background-color: #F8F9FA;
    border-radius: 20px;
    padding: 0;
    margin-bottom: 30px;
    overflow: hidden;
    border: 1px solid #eee;
    transition: transform 0.3s;
}
.service-box:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.08);
}

/* 圖片區域 */
.service-img {
    width: 40%;
    height: 250px;
    display: flex;
    align-items: center;
    justify-content: center;
    background-size: cover;
    background-position: center;
}

/* 若無圖片時的圖示替代區 */
.service-icon-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 5rem;
}

/* 文字內容區域 */
.service-content {
    width: 60%;
    padding: 30px;
}
.service-title {
    font-size: 1.8rem;
    font-weight: 900;
    margin-bottom: 10px;
}
.service-desc {
    font-size: 1rem;
    color: #666;
    line-height: 1.6;
    margin-bottom: 15px;
}
.service-tag {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 15px;
    font-size: 0.85rem;
    font-weight: bold;
    color: white;
    margin-right: 5px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 側邊欄導航 (Navigation)
# =========================================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#333; margin-bottom:20px;'>🚀 系統快速入口</h2>", unsafe_allow_html=True)
    
    # 按鈕 1: 志工
    if st.button("💜 進入 志工管理系統"):
        st.switch_page("pages/1_volunteer.py")
    
    # 按鈕 2: 長輩
    if st.button("👴 進入 長輩關懷系統"):
        st.switch_page("pages/2_elderly.py")
        
    # 按鈕 3: 關懷戶
    if st.button("🏠 進入 關懷戶系統"):
        st.switch_page("pages/3_care.py")

    st.markdown("---")
    st.markdown("<div style='text-align:center; color:#999; font-size:0.8rem; margin-top:20px;'>福德里辦公處 © 2025</div>", unsafe_allow_html=True)

# =========================================================
# 3) 主畫面內容 (Landing Page)
# =========================================================

# 標題區
st.markdown('<div class="hero-title">🏘️ 福德里 - 社區數位管理中樞</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">志工調度．長輩照護．弱勢關懷．一站整合</div>', unsafe_allow_html=True)

st.markdown("---")

# 定義三大區塊的內容
# 💡 提示：您可以將照片檔案放在同目錄下，並將檔名填入 'img_file'
services = [
    {
        "title": "志工管理系統",
        "desc": "整合志工排班、時數統計與榮譽名冊。透過數位化管理，讓志工服務歷程清晰可見，並能快速調度人力支援社區活動。",
        "tags": ["時數統計", "排班打卡", "榮譽名冊"],
        "color": "#4A148C", # 紫色
        "icon": "💜",
        "img_file": "volunteer.jpg" # 若有照片請改此檔名
    },
    {
        "title": "長輩關懷系統",
        "desc": "針對社區長者提供據點報到、血壓健康追蹤與活動參與記錄。透過數據分析，主動關懷長輩健康狀況，落實在地安老。",
        "tags": ["據點報到", "血壓量測", "健康追蹤"],
        "color": "#EF6C00", # 橙色
        "icon": "👴",
        "img_file": "elderly.jpg"
    },
    {
        "title": "關懷戶系統",
        "desc": "建立弱勢家庭數位名冊，記錄物資發放與訪視歷程。確保資源能精準送達需要的人手中，不遺漏任何一個角落。",
        "tags": ["弱勢名冊", "物資發放", "訪視紀錄"],
        "color": "#2E7D32", # 綠色
        "icon": "🏠",
        "img_file": "care.jpg"
    }
]

# 迴圈產生三個區塊
for svc in services:
    # 判斷是否有圖片，若無則顯示色塊+Icon
    if os.path.exists(svc['img_file']):
        img_html = f"""<div class="service-img" style="background-image: url('{svc['img_file']}');"></div>"""
    else:
        img_html = f"""
        <div class="service-img" style="background-color: {svc['color']}15;">
            <div class="service-icon-placeholder">{svc['icon']}</div>
        </div>
        """
    
    # 產生標籤 HTML
    tags_html = "".join([f'<span class="service-tag" style="background-color:{svc["color"]}">{t}</span>' for t in svc['tags']])

    # 渲染 HTML 結構
    st.markdown(f"""
    <div class="service-box">
        {img_html}
        <div class="service-content">
            <div class="service-title" style="color: {svc['color']}">{svc['title']}</div>
            <div class="service-desc">{svc['desc']}</div>
            <div>{tags_html}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
