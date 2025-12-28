import streamlit as st
import os
import base64

# =========================================================
# 0) 系統設定
# =========================================================
st.set_page_config(
    page_title="福德里社區管理系統",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded" 
)

# =========================================================
# 1) CSS 樣式 (V30.0 強力響應式修正版)
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

html, body, [class*="css"], div, p, span, li, ul {
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: #333333;
}

.stApp { background-color: #F0F2F5 !important; }
section[data-testid="stSidebar"] { background-color: #F0F2F5; border-right: none; }

/* 懸浮大卡片 */
.block-container {
    background-color: #FFFFFF;
    border-radius: 25px;
    padding: 3rem 4rem !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    margin-top: 2rem; margin-bottom: 2rem;
    max-width: 1100px !important;
}

/* 手機版調整：減少大卡片留白 */
@media (max-width: 1000px) {
    .block-container {
        padding: 2rem 1.5rem !important;
    }
}

/* 隱藏 Header */
header[data-testid="stHeader"] { background-color: transparent !important; }
header[data-testid="stHeader"] .decoration { display: none; }

/* 側邊欄按鈕 */
section[data-testid="stSidebar"] button {
    background-color: #FFFFFF !important; color: #555 !important;
    border: 1px solid transparent !important; box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
    border-radius: 25px !important; padding: 12px 0 !important;
    font-weight: 700 !important; width: 100%; margin-bottom: 10px !important;
    transition: all 0.3s;
}
section[data-testid="stSidebar"] button:hover {
    transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.1) !important;
    color: #000 !important; border: 1px solid #ddd !important;
}

/* 首頁標題 */
.hero-title {
    font-size: 2.5rem; font-weight: 900; color: #2c3e50;
    text-align: center; margin-bottom: 10px;
}
.hero-subtitle {
    font-size: 1.2rem; color: #7f8c8d; text-align: center; margin-bottom: 50px;
}

/* --- 🔥 核心修改區：服務卡片 (Service Box) --- */
.service-box {
    display: flex; 
    flex-direction: row; /* 預設：電腦版左右排列 */
    background-color: #F8F9FA; border-radius: 20px;
    padding: 0; margin-bottom: 30px; overflow: hidden;
    border: 1px solid #eee; transition: transform 0.3s;
    min-height: 250px; 
}
.service-box:hover {
    transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.08);
}

/* 圖片與內容預設值 (電腦版) */
.service-img {
    width: 40%;
    background-size: cover; background-position: center;
    display: flex; align-items: center; justify-content: center;
}
.service-content {
    width: 60%;
    padding: 30px;
    display: flex; flex-direction: column; justify-content: center;
}

/* --- 📱 強力手機版設定 (Breakpoint 拉大到 1000px) --- */
@media (max-width: 1000px) {
    .service-box {
        flex-direction: column !important; /* 🔥 強制變成上下排列 */
        height: auto !important;
    }
    .service-img {
        width: 100% !important;   /* 🔥 圖片寬度佔滿 */
        height: 250px !important; /* 🔥 固定高度，確保圖片夠大 */
        min-height: 250px !important;
    }
    .service-content {
        width: 100% !important;   /* 🔥 文字寬度佔滿 */
        padding: 25px !important;
    }
    .hero-title { font-size: 2rem !important; } /* 手機標題縮小 */
}

.service-title {
    font-size: 1.8rem; font-weight: 900; margin-bottom: 10px;
}
.service-desc {
    font-size: 1rem; color: #666; line-height: 1.6; margin-bottom: 15px;
}
.service-tag {
    display: inline-block; padding: 5px 12px; border-radius: 15px;
    font-size: 0.85rem; font-weight: bold; color: white; margin-right: 5px; margin-bottom: 5px;
}
.service-icon-placeholder { font-size: 5rem; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 輔助函式：圖片轉碼
# =========================================================
def get_image_as_base64(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

# =========================================================
# 3) 側邊欄與主畫面
# =========================================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#333; margin-bottom:20px;'>🚀 系統快速入口</h2>", unsafe_allow_html=True)
    if st.button("💜 進入 志工管理系統"): st.switch_page("pages/1_volunteer.py")
    if st.button("👴 進入 長輩關懷系統"): st.switch_page("pages/2_elderly.py")
    if st.button("🏠 進入 關懷戶系統"): st.switch_page("pages/3_care.py")
    st.markdown("---")
    st.markdown("<div style='text-align:center; color:#999; font-size:0.8rem; margin-top:20px;'>福德里辦公處 © 2025</div>", unsafe_allow_html=True)

st.markdown('<div class="hero-title">🏘️ 福德里 - 社區數位管理中樞</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">志工調度．長輩照護．弱勢關懷．一站整合</div>', unsafe_allow_html=True)
st.markdown("---")

services = [
    {
        "title": "志工管理系統",
        "desc": "整合志工排班、時數統計與榮譽名冊。透過數位化管理，讓志工服務歷程清晰可見，並能快速調度人力支援社區活動。",
        "tags": ["時數統計", "排班打卡", "榮譽名冊"],
        "color": "#4A148C",
        "icon": "💜",
        "img_file": "volunteer.jpg"
    },
    {
        "title": "長輩關懷系統",
        "desc": "針對社區長者提供據點報到、血壓健康追蹤與活動參與記錄。透過數據分析，主動關懷長輩健康狀況，落實在地安老。",
        "tags": ["據點報到", "血壓量測", "健康追蹤"],
        "color": "#EF6C00",
        "icon": "👴",
        "img_file": "elderly.jpg"
    },
    {
        "title": "關懷戶系統",
        "desc": "建立弱勢家庭數位名冊，記錄物資發放與訪視歷程。確保資源能精準送達需要的人手中，不遺漏任何一個角落。",
        "tags": ["弱勢名冊", "物資發放", "訪視紀錄"],
        "color": "#2E7D32",
        "icon": "🏠",
        "img_file": "care.jpg"
    }
]

for svc in services:
    img_html = f"""<div class="service-img" style="background-color: {svc['color']}15;"><div class="service-icon-placeholder">{svc['icon']}</div></div>"""
    
    if os.path.exists(svc['img_file']):
        img_b64 = get_image_as_base64(svc['img_file'])
        if img_b64:
            ext = svc['img_file'].split('.')[-1].lower()
            mime = "image/png" if ext == 'png' else "image/jpeg"
            img_html = f"""<div class="service-img" style="background-image: url('data:{mime};base64,{img_b64}');"></div>"""

    tags_html = "".join([f'<span class="service-tag" style="background-color:{svc["color"]}">{t}</span>' for t in svc['tags']])

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
