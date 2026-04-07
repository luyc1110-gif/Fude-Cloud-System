import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
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
# 1) CSS 樣式 (V31.0 數據儀表板版)
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

html, body, [class*="css"], div, p, span, li, ul {
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
}

.stApp { background-color: #F0F2F5 !important; }
section[data-testid="stSidebar"] { 
    background-color: #F0F2F5; 
    border-right: none; 
}

.block-container {
    background-color: #FFFFFF;
    border-radius: 25px;
    padding: 3rem 4rem !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    margin-top: 2rem; margin-bottom: 2rem;
    max-width: 1100px !important;
}

@media (max-width: 1000px) {
    .block-container { padding: 2rem 1.5rem !important; }
}

header[data-testid="stHeader"] { background-color: transparent !important; }
header[data-testid="stHeader"] .decoration { display: none; }

section[data-testid="stSidebar"] button {
    background-color: #FFFFFF !important;
    color: #666666 !important;
    border: 1px solid transparent !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    border-radius: 25px !important;
    padding: 10px 15px !important; /* 👈 把左右留白加回來 */
    font-weight: 700 !important;
    width: 100%;
    margin-bottom: 8px !important;
    transition: all 0.2s;
}
section[data-testid="stSidebar"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.1) !important;
    color: #4A148C !important;   /* ← 改成固定紫色 */
    border: 1px solid var(--color-border-secondary) !important;
}

.hero-title {
    font-size: 2.5rem; font-weight: 900;
    color: #212121;              /* ← 改成固定深色 */
    text-align: center; margin-bottom: 10px;
}
.hero-subtitle {
    font-size: 1.2rem;
    color: #666666;              /* ← 改成固定灰色 */
    text-align: center; margin-bottom: 50px;
}

.service-box {
    display: flex; flex-direction: row;
    background-color: #FFFFFF;   /* ← var(--color-background-secondary) 換掉 */
    border-radius: 20px; padding: 0; margin-bottom: 30px;
    overflow: hidden; border: 0.5px solid #E0E0E0; /* ← var(--color-border-tertiary) 換掉 */
    transition: transform 0.3s; min-height: 250px;
}
.service-box:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.08);
}
.service-img {
    width: 40%;
    background-size: cover; background-position: center;
    display: flex; align-items: center; justify-content: center;
}
.service-content {
    width: 60%; padding: 30px;
    display: flex; flex-direction: column; justify-content: center;
}

@media (max-width: 1000px) {
    .service-box { flex-direction: column !important; height: auto !important; }
    .service-img { width: 100% !important; height: 200px !important; min-height: 200px !important; }
    .service-content { width: 100% !important; padding: 25px !important; }
    .hero-title { font-size: 2rem !important; }
}

.service-title { font-size: 1.8rem; font-weight: 900; margin-bottom: 10px; }
.service-desc { font-size: 1rem; color: #666666; line-height: 1.6; margin-bottom: 15px; }
.service-icon-placeholder { font-size: 5rem; }

.stats-row { display: flex; gap: 15px; flex-wrap: wrap; margin-top: 10px; }
.stat-item {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 10px; padding: 8px 15px;
    font-size: 0.9rem; color: #666666;
    font-weight: 500; display: flex; align-items: center; gap: 8px;
}
.stat-item b { color: #212121; font-size: 1.1rem; margin-left: 5px; }
/* ── 輸入框、選單 ── */
div[data-baseweb="select"] > div,
.stTextInput input,
.stDateInput input,
.stNumberInput input,
.stTimeInput input {
    background-color: #FFFFFF !important;
    border: 2px solid #E0E0E0 !important;
    border-radius: 12px !important;
    color: #212121 !important;
}

/* 下拉選單選項 */
div[role="listbox"], ul[data-baseweb="menu"], li[role="option"] {
    background-color: #FFFFFF !important;
    color: #212121 !important;
}
li[role="option"]:hover { background-color: #F3E5F5 !important; }

/* checkbox 文字 */
.stCheckbox label, .stCheckbox span {
    color: #212121 !important;
}

/* label / caption 文字 */
label, .stTextInput label, .stSelectbox label,
.stDateInput label, .stNumberInput label,
[data-testid="stWidgetLabel"] {
    color: #212121 !important;
}

/* 確認新增按鈕 */
div[data-testid="stFormSubmitButton"] > button,
.stButton > button {
    background-color: #4A148C !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 900 !important;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 邏輯處理：資料庫讀取與計算 (Supabase 版)
# =========================================================
@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def calculate_age(dob_str):
    try:
        b_date = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        today = date.today()
        return today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
    except: return 0

def check_is_fully_retired(row):
    roles = [
        ('祥和_加入日期', '祥和_退出日期'), 
        ('據點週二_加入日期', '據點週二_退出日期'), 
        ('據點週三_加入日期', '據點週三_退出日期'), 
        ('環保_加入日期', '環保_退出日期')
    ]
    has_any = False 
    is_active = False 
    
    for join_col, exit_col in roles:
        join_val = str(row.get(join_col, '')).strip()
        if join_val and join_val != 'nan':
            has_any = True
            exit_val = str(row.get(exit_col, '')).strip()
            if not exit_val or exit_val == 'nan': 
                is_active = True
    
    if not has_any: return False 
    return not is_active

def calculate_year_hours(logs_df):
    try:
        cur_year = datetime.now().year
        logs_df['dt'] = pd.to_datetime(logs_df['日期'] + ' ' + logs_df['時間'], errors='coerce')
        logs_df = logs_df.dropna(subset=['dt'])
        year_logs = logs_df[logs_df['dt'].dt.year == cur_year].sort_values(['姓名', 'dt'])
        
        total_seconds = 0
        for (name, d), group in year_logs.groupby(['姓名', '日期']):
            actions = group['動作'].tolist()
            times = group['dt'].tolist()
            i = 0
            while i < len(actions):
                if actions[i] == '簽到':
                    for j in range(i + 1, len(actions)):
                        if actions[j] == '簽退':
                            total_seconds += (times[j] - times[i]).total_seconds()
                            i = j
                            break
                    i += 1
                else: i += 1
        return int(total_seconds // 3600)
    except: return 0

@st.cache_data(ttl=60)
def load_dashboard_stats():
    stats = {
        "vol_count": 0, "vol_age": 0, "vol_hours": 0,
        "eld_count": 0, "eld_age": 0,
        "care_count": 0, "care_items": 0
    }
    
    try:
        supabase = get_supabase_client()
        
        # 1. 抓取主檔
        res_master = supabase.table("master_residents").select("*").execute()
        df_m = pd.DataFrame(res_master.data) if res_master.data else pd.DataFrame()
        
        # 2. 抓取志工打卡
        res_vl = supabase.table("logs").select("*").execute()
        df_vl = pd.DataFrame(res_vl.data) if res_vl.data else pd.DataFrame()
        
        # 3. 抓取關懷戶發放紀錄
        res_cl = supabase.table("care_logs").select("*").execute()
        df_cl = pd.DataFrame(res_cl.data) if res_cl.data else pd.DataFrame()
        
        if not df_m.empty:
            df_m['age'] = df_m['出生年月日'].apply(calculate_age)
            
            # --- 志工數據 ---
            df_v = df_m[df_m['身分_志工'].astype(str).str.upper() == 'TRUE']
            if not df_v.empty:
                active_volunteers = df_v[~df_v.apply(check_is_fully_retired, axis=1)]
                stats["vol_count"] = len(active_volunteers)
                valid_ages = active_volunteers[active_volunteers['age'] > 0]['age']
                stats["vol_age"] = round(valid_ages.mean(), 1) if not valid_ages.empty else 0
                
            # --- 長輩數據 ---
            df_e = df_m[df_m['身分_據點長輩'].astype(str).str.upper() == 'TRUE']
            if not df_e.empty:
                stats["eld_count"] = len(df_e)
                valid_ages = df_e[df_e['age'] > 0]['age']
                stats["eld_age"] = round(valid_ages.mean(), 1) if not valid_ages.empty else 0

            # --- 關懷戶數據 ---
            df_c = df_m[df_m['身分_關懷戶'].astype(str).str.upper() == 'TRUE']
            # 排除身分別含「一般戶」的人（與 care.py 統一）
            df_c = df_c[~df_c['關懷_身分別'].astype(str).str.contains("一般戶", na=False)]
            if not df_c.empty:
                stats["care_count"] = len(df_c)
                
        if not df_vl.empty:
            stats["vol_hours"] = calculate_year_hours(df_vl)
            
        if not df_cl.empty:
            cur_year = datetime.now().year
            df_cl['dt'] = pd.to_datetime(df_cl['發放日期'], errors='coerce')
            df_cl['qty'] = pd.to_numeric(df_cl['發放數量'], errors='coerce').fillna(0)
            stats["care_items"] = int(df_cl[df_cl['dt'].dt.year == cur_year]['qty'].sum())

    except Exception as e:
        print(f"Stats Error: {e}")
    
    return stats

def get_image_as_base64(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

# =========================================================
# 3) 頁面渲染
# =========================================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:var(--color-text-primary); margin-bottom:20px;'>🚀 系統快速入口</h2>", unsafe_allow_html=True)
    if st.button("💜 進入 志工管理系統"): st.switch_page("pages/1_volunteer.py")
    if st.button("👴 進入 長輩關懷系統"): st.switch_page("pages/2_elderly.py")
    if st.button("🏠 進入 關懷戶系統"): st.switch_page("pages/3_care.py")
    st.markdown("---")
    st.markdown("<div style='text-align:center; color:var(--color-text-tertiary); font-size:0.8rem; margin-top:20px;'>福德里辦公處 © 2026</div>", unsafe_allow_html=True)

st.markdown('<div class="hero-title">🏘️ 福德里 - 社區數位管理中樞</div>', unsafe_allow_html=True)
st.markdown(f'<div class="hero-subtitle">志工調度．長輩照護．弱勢關懷．一站整合 ({datetime.now().year} 年度數據)</div>', unsafe_allow_html=True)
st.markdown("---")

# 讀取數據
data = load_dashboard_stats()

# 定義服務內容與對應數據
services = [
    {
        "title": "志工管理系統",
        "desc": "整合志工排班、時數統計與榮譽名冊。透過數位化管理，讓志工服務歷程清晰可見，並能快速調度人力支援社區活動。",
        "color": "#4A148C",
        "icon": "💜",
        "img_file": "volunteer.jpg",
        "stats": [
            f"👥 志工總數: <b>{data['vol_count']}</b> 人",
            f"🎂 平均年齡: <b>{data['vol_age']}</b> 歲",
            f"⏳ 本年服務: <b>{data['vol_hours']}</b> 小時"
        ]
    },
    {
        "title": "長輩關懷系統",
        "desc": "針對社區長者提供據點報到、血壓健康追蹤與活動參與記錄。透過數據分析，主動關懷長輩健康狀況，落實在地安老。",
        "color": "#EF6C00",
        "icon": "👴",
        "img_file": "elderly.jpg",
        "stats": [
            f"👥 長者總數: <b>{data['eld_count']}</b> 人",
            f"🎂 平均年齡: <b>{data['eld_age']}</b> 歲"
        ]
    },
    {
        "title": "關懷戶系統",
        "desc": "建立弱勢家庭數位名冊，記錄物資發放與訪視歷程。確保資源能精準送達需要的人手中，不遺漏任何一個角落。",
        "color": "#2E7D32",
        "icon": "🏠",
        "img_file": "care.jpg",
        "stats": [
            f"📉 關懷戶數: <b>{data['care_count']}</b> 戶",
            f"📦 本年發放: <b>{data['care_items']}</b> 份"
        ]
    }
]

# 渲染卡片
for svc in services:
    # 處理圖片
    img_html = f"""<div class="service-img" style="background-color: {svc['color']}15;"><div class="service-icon-placeholder">{svc['icon']}</div></div>"""
    if os.path.exists(svc['img_file']):
        img_b64 = get_image_as_base64(svc['img_file'])
        if img_b64:
            ext = svc['img_file'].split('.')[-1].lower()
            mime = "image/png" if ext == 'png' else "image/jpeg"
            img_html = f"""<div class="service-img" style="background-image: url('data:{mime};base64,{img_b64}');"></div>"""

    # 產生數據 HTML
    stats_html = "".join([f'<div class="stat-item" style="border-left: 4px solid {svc["color"]};">{s}</div>' for s in svc['stats']])

    st.markdown(f"""
<div class="service-box">
{img_html}
<div class="service-content">
<div class="service-title" style="color: {svc['color']}">{svc['title']}</div>
<div class="service-desc">{svc['desc']}</div>
<div class="stats-row">
{stats_html}
</div>
</div>
</div>
""", unsafe_allow_html=True)
# =========================================================
# 4) 整合新增居民功能
# =========================================================
with st.expander("➕ 新增居民 / 志工 / 長者 / 關懷戶", expanded=False):
    st.markdown("#### 基本資料")
    c1, c2, c3 = st.columns(3)
    r_name   = c1.text_input("姓名", key="add_name")
    r_pid    = c2.text_input("身分證字號", key="add_pid")
    r_gender = c3.selectbox("性別", ["男", "女"], key="add_gender")

    c4, c5, c6 = st.columns(3)
    r_dob   = c4.date_input("出生年月日", value=date(1950, 1, 1),
                             min_value=date(1900, 1, 1), 
                             max_value=date.today(),    # 👈 加上這行，確保年份能選到今年
                             key="add_dob")
    r_phone = c5.text_input("電話", key="add_phone")
    r_addr  = c6.text_input("地址", key="add_addr")

    c7, c8 = st.columns(2)
    r_ec_name  = c7.text_input("緊急聯絡人", key="add_ec_name")
    r_ec_phone = c8.text_input("緊急聯絡電話", key="add_ec_phone")

    st.markdown("#### 身份選擇（可複選）")
    ci1, ci2, ci3 = st.columns(3)
    is_vol  = ci1.checkbox("💜 志工", key="add_is_vol")
    is_eld  = ci2.checkbox("👴 長者", key="add_is_eld")
    is_care = ci3.checkbox("🏠 關懷戶", key="add_is_care")

    # --- 志工專屬欄位 ---
    vol_cats = []
    d_xiang  = d_tue = d_wed = d_eco = None

    if is_vol:
        st.markdown("#### 志工資料")
        st.caption("勾選參與的分類，並填入加入日期")
        vc1, vc2 = st.columns(2)
        is_xiang = vc1.checkbox("祥和志工",       key="add_xiang")
        is_tue   = vc1.checkbox("關懷據點週二志工", key="add_tue")
        is_wed   = vc2.checkbox("關懷據點週三志工", key="add_wed")
        is_eco   = vc2.checkbox("環保志工",        key="add_eco")

        if is_xiang:
            d_xiang = st.date_input("祥和 加入日期",       value=date.today(), key="add_d_xiang")
        if is_tue:
            d_tue   = st.date_input("據點週二 加入日期",   value=date.today(), key="add_d_tue")
        if is_wed:
            d_wed   = st.date_input("據點週三 加入日期",   value=date.today(), key="add_d_wed")
        if is_eco:
            d_eco   = st.date_input("環保 加入日期",       value=date.today(), key="add_d_eco")

        if is_xiang: vol_cats.append("祥和志工")
        if is_tue:   vol_cats.append("關懷據點週二志工")
        if is_wed:   vol_cats.append("關懷據點週三志工")
        if is_eco:   vol_cats.append("環保志工")

    # --- 長者專屬欄位 ---
    r_eld_join = None
    if is_eld:
        st.markdown("#### 長者資料")
        r_eld_join = st.date_input("長者_加入日期", value=date.today(), key="add_eld_join")

    # --- 關懷戶專屬欄位 ---
    r_care_type = ""
    r_u18 = r_adult = r_o65 = 0
    r_reject = ""
    if is_care:
        st.markdown("#### 關懷戶資料")
        CARE_TYPES = ["低收入戶", "中低收入戶", "獨居老人", "身心障礙", "特殊境遇家庭", "其他"]
        # 改用 multiselect 支援複選，回傳會是一個 List
        r_care_type = st.multiselect("關懷身分別 (可複選)", CARE_TYPES, key="add_care_type")
        cc1, cc2, cc3 = st.columns(3)
        r_u18   = cc1.number_input("同住 18歲以下", min_value=0, step=1, key="add_u18")
        r_adult = cc2.number_input("同住成人數",    min_value=0, step=1, key="add_adult")
        r_o65   = cc3.number_input("同住 65歲以上", min_value=0, step=1, key="add_o65")
        r_reject = st.text_input("拒絕物資（如有）", key="add_reject")

    st.markdown("")
    if st.button("✅ 確認新增", key="add_submit", use_container_width=True):
        # --- 驗證 ---
        if not r_name.strip():
            st.error("請填寫姓名")
        elif not r_pid.strip():
            st.error("請填寫身分證字號")
        elif not is_vol and not is_eld and not is_care:
            st.error("請至少勾選一種身份")
        elif is_vol and not vol_cats:
            st.error("勾選志工後，請至少選擇一種志工分類")
        else:
            uid = r_pid.strip().upper()
            payload = {
                "姓名":         r_name.strip(),
                "身分證字號":    uid,
                "性別":         r_gender,
                "出生年月日":    str(r_dob),
                "電話":         r_phone.strip(),
                "地址":         r_addr.strip(),
                "緊急聯絡人":    r_ec_name.strip(),
                "緊急聯絡電話":  r_ec_phone.strip(),
                "身分_志工":     "TRUE" if is_vol  else "FALSE",
                "身分_據點長輩": "TRUE" if is_eld  else "FALSE",
                "身分_關懷戶":   "TRUE" if is_care else "FALSE",
                # 志工欄位
                "志工分類":          ",".join(vol_cats),
                "祥和_加入日期":      str(d_xiang) if d_xiang else "",
                "據點週二_加入日期":  str(d_tue)   if d_tue   else "",
                "據點週三_加入日期":  str(d_wed)   if d_wed   else "",
                "環保_加入日期":      str(d_eco)   if d_eco   else "",
                # 長者欄位
                "長者_加入日期":       str(r_eld_join) if r_eld_join else "",
                # 關懷戶欄位
                "關懷_身分別":   ",".join(r_care_type) if r_care_type else "",
                "同住_18歲以下": str(r_u18),
                "同住_成人":     str(r_adult),
                "同住_65歲以上": str(r_o65),
                "拒絕物資":      r_reject.strip(),
                "人際關係":      "",
            }
            try:
                supabase = get_supabase_client()
                existing = supabase.table("master_residents").select(
                    "id", "身分_志工", "身分_據點長輩", "身分_關懷戶"
                ).eq("身分證字號", uid).execute()

                if existing.data:
                    # 已存在：疊加身份與對應欄位，不覆蓋舊資料
                    rec = existing.data[0]
                    update = {}

                    if is_vol and str(rec.get("身分_志工","")).upper() != "TRUE":
                        update["身分_志工"] = "TRUE"
                    if is_vol:
                        update["志工分類"]         = ",".join(vol_cats)
                        update["祥和_加入日期"]     = str(d_xiang) if d_xiang else ""
                        update["據點週二_加入日期"] = str(d_tue)   if d_tue   else ""
                        update["據點週三_加入日期"] = str(d_wed)   if d_wed   else ""
                        update["環保_加入日期"]     = str(d_eco)   if d_eco   else ""

                    if is_eld and str(rec.get("身分_據點長輩","")).upper() != "TRUE":
                        update["身分_據點長輩"] = "TRUE"
                    if is_eld:
                        update["長者_加入日期"] = str(r_eld_join) if r_eld_join else ""

                    if is_care and str(rec.get("身分_關懷戶","")).upper() != "TRUE":
                        update["身分_關懷戶"] = "TRUE"
                    if is_care:
                        update["關懷_身分別"]   = ",".join(r_care_type) if r_care_type else ""
                        update["同住_18歲以下"] = str(r_u18)
                        update["同住_成人"]     = str(r_adult)
                        update["同住_65歲以上"] = str(r_o65)
                        update["拒絕物資"]      = r_reject.strip()

                    if update:
                        supabase.table("master_residents").update(update).eq("id", rec["id"]).execute()
                        st.success(f"✅ {r_name} 已存在，已更新身份與資料")
                    else:
                        st.info(f"ℹ️ {r_name} 已存在且身份相同，無需更新")
                else:
                    supabase.table("master_residents").insert(payload).execute()
                    label = " / ".join(filter(None, [
                        "志工" if is_vol else "",
                        "長者" if is_eld else "",
                        "關懷戶" if is_care else ""
                    ]))
                    st.success(f"✅ {r_name} 新增成功！身份：{label}")

                load_dashboard_stats.clear()

            except Exception as e:
                st.error(f"寫入失敗：{e}")
# =========================================================
# 5) 整合退出管理功能
# =========================================================
with st.expander("📤 退出管理 / 志工・長者・關懷戶", expanded=False):
    st.markdown("#### 選擇要退出的人員")

    try:
        supabase = get_supabase_client()
        res = supabase.table("master_residents").select(
            "id", "姓名", "身分證字號", "性別", "出生年月日",
            "電話", "地址", "緊急聯絡人", "緊急聯絡電話",
            "身分_志工", "身分_據點長輩", "身分_關懷戶",
            "祥和_加入日期", "祥和_退出日期",
            "據點週二_加入日期", "據點週二_退出日期",
            "據點週三_加入日期", "據點週三_退出日期",
            "環保_加入日期", "環保_退出日期"
        ).execute()
        df_all = pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as e:
        st.error(f"讀取資料失敗：{e}")
        df_all = pd.DataFrame()

    if df_all.empty:
        st.info("目前無資料")
    else:
        exit_type = st.selectbox(
            "篩選身份",
            ["志工", "長者", "關懷戶"],
            key="exit_type"
        )

        col_map = {
            "志工":   "身分_志工",
            "長者":   "身分_據點長輩",
            "關懷戶": "身分_關懷戶"
        }
        target_col = col_map[exit_type]

        active_df = df_all[
            df_all[target_col].astype(str).str.upper() == 'TRUE'
        ].copy()

        if active_df.empty:
            st.info(f"目前沒有在籍的{exit_type}")
        else:
            options = [
                f"{row['姓名']} ({row['身分證字號']})"
                for _, row in active_df.iterrows()
            ]
            selected = st.selectbox(
                f"選擇要退出的{exit_type}",
                ["--- 請選擇 ---"] + options,
                key="exit_target"
            )

            EXIT_REASONS = ["過世", "搬遷/無法聯繫", "自願退出", "進入長照機構", "其他"]
            exit_reason = st.selectbox("退出原因", EXIT_REASONS, key="exit_reason")

            # 志工：額外選退出的分類
            exit_vol_cols = []
            if exit_type == "志工" and selected != "--- 請選擇 ---":
                target_pid = selected.split("(")[-1].replace(")", "")
                vdata = active_df[active_df['身分證字號'] == target_pid].iloc[0]
                role_map = {
                    "祥和志工":        "祥和_退出日期",
                    "關懷據點週二志工": "據點週二_退出日期",
                    "關懷據點週三志工": "據點週三_退出日期",
                    "環保志工":        "環保_退出日期",
                }
                
                st.markdown("##### 退出哪些志工分類？")
                ev1, ev2 = st.columns(2)
                checkbox_count = 0
                for i, (role_name, exit_col) in enumerate(role_map.items()):
                    # 放寬條件：只要還沒有「退出日期」的分類就顯示
                    already_exited = str(vdata.get(exit_col, "")).strip() not in ("", "nan", "None")
                    if not already_exited:
                        col = ev1 if i % 2 == 0 else ev2
                        if col.checkbox(role_name, key=f"exit_vol_{role_name}"):
                            exit_vol_cols.append(exit_col)
                        checkbox_count += 1
                        
                # 防呆：如果舊資料完全沒分類紀錄，提供強制退出選項
                if checkbox_count == 0:
                    if st.checkbox("強制註銷志工身分 (因資料庫無舊有分類紀錄)", key="exit_vol_force"):
                        exit_vol_cols.append("force_exit")

            st.warning(f"⚠️ 確認後將把此人的「{exit_type}」身份標記為退出，並封存至 residents_archive，過去紀錄不受影響。")

            if st.button("確認退出", key="exit_submit", type="primary"):
                if selected == "--- 請選擇 ---":
                    st.error("請先選擇人員")
                elif exit_type == "志工" and not exit_vol_cols:
                    st.error("請至少勾選一個要退出的志工分類")
                else:
                    target_pid = selected.split("(")[-1].replace(")", "")
                    target_name = selected.split("(")[0].strip()
                    rec = active_df[active_df['身分證字號'] == target_pid].iloc[0]
                    rec_id = int(rec["id"])

                    # ==========================================
                    # 1. 準備更新 master_residents 的資料 (維持單列更新)
                    # ==========================================
                    update = {target_col: "FALSE"}
                    if exit_type == "志工":
                        for exit_col in exit_vol_cols:
                            if exit_col != "force_exit":
                                update[exit_col] = str(date.today())
                        
                        # 檢查是否所有志工分類都已退出，才把 身分_志工 整個改為 FALSE
                        all_exit_cols = ["祥和_退出日期", "據點週二_退出日期", "據點週三_退出日期", "環保_退出日期"]
                        all_join_cols = ["祥和_加入日期", "據點週二_加入日期", "據點週三_加入日期", "環保_加入日期"]
                        still_active = False
                        for jc, ec in zip(all_join_cols, all_exit_cols):
                            joined = str(rec.get(jc, "")).strip() not in ("", "nan", "None")
                            exited = str(rec.get(ec, "")).strip() not in ("", "nan", "None")
                            will_exit = ec in exit_vol_cols
                            if joined and not exited and not will_exit:
                                still_active = True
                        if still_active:
                            del update[target_col] # 還有其他分類在籍，保留志工身分

                    # ==========================================
                    # 2. 準備寫入 residents_archive 的資料 (拆分成多列)
                    # ==========================================
                    base_archive_data = {
                        "姓名":        target_name,
                        "身分證字號":   target_pid,
                        "性別":        str(rec.get("性別", "")),
                        "出生年月日":   str(rec.get("出生年月日", "")),
                        "電話":        str(rec.get("電話", "")),
                        "地址":        str(rec.get("地址", "")),
                        "緊急聯絡人":   str(rec.get("緊急聯絡人", "")),
                        "緊急聯絡電話": str(rec.get("緊急聯絡電話", "")),
                        "備註":        "",
                    }

                    today_str = str(date.today())
                    rows_to_insert = []

                    if exit_type in ["長者", "關懷戶"]:
                        row = base_archive_data.copy()
                        row["退出身份"] = exit_type
                        row["退出日期"] = today_str
                        row["退出原因"] = exit_reason
                        rows_to_insert.append(row)
                        
                    elif exit_type == "志工":
                        col_to_name_map = {
                            "祥和_退出日期": "祥和志工",
                            "據點週二_退出日期": "據點週二志工",
                            "據點週三_退出日期": "據點週三志工",
                            "環保_退出日期": "環保志工"
                        }
                        for exit_col in exit_vol_cols:
                            if exit_col in col_to_name_map:
                                row = base_archive_data.copy()
                                row["退出身份"] = col_to_name_map[exit_col]
                                row["退出日期"] = today_str
                                row["退出原因"] = exit_reason
                                rows_to_insert.append(row)
                            elif exit_col == "force_exit":
                                row = base_archive_data.copy()
                                row["退出身份"] = "志工(強制註銷)"
                                row["退出日期"] = today_str
                                row["退出原因"] = exit_reason
                                rows_to_insert.append(row)

                    # ==========================================
                    # 3. 執行寫入 (先 Insert 明細，再 Update 主檔)
                    # ==========================================
                    try:
                        if rows_to_insert:
                            supabase.table("residents_archive").insert(rows_to_insert).execute()
                            
                        supabase.table("master_residents").update(update).eq("id", rec_id).execute()
                        
                        st.success(f"✅ {target_name} 已退出{exit_type}，原因：{exit_reason}，資料已封存。")
                        load_dashboard_stats.clear()
                        import time; time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"操作失敗：{e}")
