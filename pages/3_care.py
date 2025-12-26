import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import plotly.express as px
import random
import time

# =========================================================
# 0) 系統設定
# =========================================================
st.set_page_config(
    page_title="關懷戶管理系統", 
    page_icon="🏠", 
    layout="wide", 
    initial_sidebar_state="expanded" # 🔥 1. 改為預設展開側邊欄
)

# --- 🔒 安全登入門禁 ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("### 🔒 福德里管理系統 - 登入")
    pwd = st.text_input("請輸入管理員授權碼", type="password")
    
    if st.button("確認登入"):
        if pwd == st.secrets["admin_password"]:
            st.session_state.authenticated = True
            st.success("登入成功！正在跳轉...")
            st.rerun()
        else:
            st.error("授權碼錯誤，請重新輸入。")
    st.stop()

if 'page' not in st.session_state:
    st.session_state.page = 'home'

TW_TZ = timezone(timedelta(hours=8))
# 🔥 維持原本配色
PRIMARY = "#4A4E69"   # 深藍灰 (按鈕、文字強調)
GREEN   = "#8E9775"   # 苔蘚綠 (主視覺、側邊欄選中)
BG_MAIN = "#F8F9FA"   # 淺灰底
TEXT    = "#333333"

# =========================================================
# 1) CSS 樣式 (視覺大改版：懸浮卡片 + 側邊欄)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');

html, body, [class*="css"], div, p, span, li, ul {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif;
    color: {TEXT} !important;
}}

/* 🔥 1. 整體背景 */
.stApp {{
    background-color: {BG_MAIN} !important;
}}

/* 🔥 2. 側邊欄背景 (無縫融合) */
section[data-testid="stSidebar"] {{
    background-color: {BG_MAIN};
    border-right: none;
}}

/* 🔥 3. 主內容區：懸浮大卡片 */
.block-container {{
    background-color: #FFFFFF;
    border-radius: 25px;
    padding: 3rem 3rem !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    margin-top: 2rem; margin-bottom: 2rem;
    max-width: 95% !important;
}}

/* 🔥 4. 修復 Header */
header[data-testid="stHeader"] {{
    display: block !important;
    background-color: transparent !important;
}}
header[data-testid="stHeader"] .decoration {{ display: none; }}

/* --- 側邊欄按鈕 (膠囊狀) --- */
section[data-testid="stSidebar"] button {{
    background-color: #FFFFFF !important;
    color: #666 !important;
    border: 1px solid transparent !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    border-radius: 25px !important;
    padding: 10px 0 !important;
    font-weight: 700 !important;
    width: 100%; margin-bottom: 8px !important;
    transition: all 0.2s;
}}
section[data-testid="stSidebar"] button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
    color: {GREEN} !important;
}}
/* 選中狀態 (苔蘚綠漸層) */
.nav-active {{
    background: linear-gradient(135deg, {GREEN}, #6D6875);
    color: white !important;
    padding: 12px 0; text-align: center; border-radius: 25px;
    font-weight: 900; box-shadow: 0 4px 10px rgba(142, 151, 117, 0.4);
    margin-bottom: 12px; cursor: default;
}}

/* --- 表格與輸入框優化 --- */
div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
    background-color: #FFFFFF !important; border-radius: 10px; padding: 5px;
}}
div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {{
    background-color: #F8F9FA !important; color: #000000 !important;
    border: 2px solid #E0E0E0 !important; border-radius: 12px !important; font-weight: 700 !important;
}}
div[role="listbox"], ul[data-baseweb="menu"], li[role="option"] {{
    background-color: #FFFFFF !important; color: #000000 !important;
}}
li[role="option"]:hover {{
    background-color: #E8F5E9 !important; /* 淡綠色 hover */
    color: {GREEN} !important;
}}

/* --- 按鈕樣式 --- */
div[data-testid="stFormSubmitButton"] > button,
div[data-testid="stDownloadButton"] > button {{
    background-color: {PRIMARY} !important; color: #FFFFFF !important;
    border: none !important; border-radius: 12px !important; font-weight: 900 !important;
    padding: 10px 25px !important;
}}
div[data-testid="stFormSubmitButton"] > button:hover,
div[data-testid="stDownloadButton"] > button:hover {{
    background-color: {GREEN} !important;
    transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.15);
}}

/* --- 數據看板卡片 (維持原本設計) --- */
.care-metric-box {{
    padding: 20px; border-radius: 20px; color: #FFFFFF !important; text-align: center; margin-bottom: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1); min-height: 140px;
    display: flex; flex-direction: column; justify-content: center;
}}
.care-metric-box div, .care-metric-box span {{ color: #FFFFFF !important; font-weight: 900 !important; }}

/* --- 物資卡片樣式 --- */
.inv-card-header {{
    font-weight: 900; font-size: 1.1rem; color: #333;
    margin-bottom: 5px;
}}
.inv-card-stock {{
    font-size: 0.9rem; color: #666; background-color: #eee;
    padding: 2px 8px; border-radius: 10px; display: inline-block;
    margin-bottom: 10px;
}}
.inv-card-stock.low {{
    color: #D32F2F !important; background-color: #FFEBEE !important;
    border: 1px solid #D32F2F;
}}

/* 🔥 物資卡片懸浮特效 */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    border: 2px solid #E0E0E0 !important;
    background-color: #FFFFFF;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    transform: translateY(-8px);
    box-shadow: 0 12px 24px rgba(0,0,0,0.15);
    border-color: {GREEN} !important;
    z-index: 10;
}}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 資料邏輯
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
COLS_MEM = ["姓名", "身分證字號", "性別", "生日", "地址", "電話", "緊急聯絡人", "緊急聯絡人電話", "身分別", "18歲以下子女", "成人數量", "65歲以上長者"]
COLS_HEALTH = ["姓名", "身分證字號", "是否有假牙", "今年洗牙", "握力", "身高", "體重", "聽力測試"]
COLS_INV = ["捐贈者", "物資類型", "物資內容", "總數量", "捐贈日期"]
COLS_LOG = ["志工", "發放日期", "關懷戶姓名", "物資內容", "發放數量", "訪視紀錄"]

@st.cache_resource
def get_client(): return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=10)
def load_data(sn, target_cols):
    try:
        client = get_client(); sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        df = pd.DataFrame(sheet.get_all_records()).astype(str)
        for c in target_cols:
            if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame(columns=target_cols)

def save_data(df, sn):
    try:
        df_fix = df.fillna("").replace(['nan', 'NaN', 'nan.0', 'None', '<NA>'], "").astype(str)
        client = get_client(); sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        sheet.clear(); sheet.update([df_fix.columns.values.tolist()] + df_fix.values.tolist())
        st.cache_data.clear(); return True
    except Exception as e:
        st.error(f"寫入失敗：{e}"); return False

def calculate_age(dob_str):
    try:
        bd = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        today = date.today(); return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except: return 0

# =========================================================
# 3) Navigation (改為側邊欄)
# =========================================================
def render_nav():
    with st.sidebar:
        st.markdown(f"<h2 style='color:{GREEN}; margin-bottom:5px; padding-left:10px;'>🏠 關懷戶中心</h2>", unsafe_allow_html=True)
        st.write("") 

        # 1. 首頁
        if st.session_state.page == 'home':
            st.markdown('<div class="nav-active">📊 關懷概況看板</div>', unsafe_allow_html=True)
        else:
            if st.button("📊 關懷概況看板", key="nav_home", use_container_width=True):
                st.session_state.page = 'home'; st.rerun()

        # 2. 名冊
        if st.session_state.page == 'members':
            st.markdown('<div class="nav-active">📋 名冊管理</div>', unsafe_allow_html=True)
        else:
            if st.button("📋 名冊管理", key="nav_members", use_container_width=True):
                st.session_state.page = 'members'; st.rerun()

        # 3. 健康
        if st.session_state.page == 'health':
            st.markdown('<div class="nav-active">🏥 健康追蹤</div>', unsafe_allow_html=True)
        else:
            if st.button("🏥 健康追蹤", key="nav_health", use_container_width=True):
                st.session_state.page = 'health'; st.rerun()

        # 4. 物資
        if st.session_state.page == 'inventory':
            st.markdown('<div class="nav-active">📦 物資庫存</div>', unsafe_allow_html=True)
        else:
            if st.button("📦 物資庫存", key="nav_inv", use_container_width=True):
                st.session_state.page = 'inventory'; st.rerun()

        # 5. 訪視
        if st.session_state.page == 'visit':
            st.markdown('<div class="nav-active">🤝 訪視發放</div>', unsafe_allow_html=True)
        else:
            if st.button("🤝 訪視發放", key="nav_visit", use_container_width=True):
                st.session_state.page = 'visit'; st.rerun()

        # 6. 統計
        if st.session_state.page == 'stats':
            st.markdown('<div class="nav-active">📈 數據統計</div>', unsafe_allow_html=True)
        else:
            if st.button("📈 數據統計", key="nav_stats", use_container_width=True):
                st.session_state.page = 'stats'; st.rerun()

        st.markdown("---")
        if st.button("🚪 回系統大廳", key="nav_back", use_container_width=True):
            st.switch_page("Home.py")
        
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#999; font-size:0.8rem;'>Designed for Fude Community</div>", unsafe_allow_html=True)

# =========================================================
# 4) Pages
# =========================================================

# --- [分頁 0：首頁看板] ---
if st.session_state.page == 'home':
    render_nav()
    st.markdown(f"<h2 style='color: {GREEN};'>📊 關懷戶概況看板</h2>", unsafe_allow_html=True)
    
    mems, logs = load_data("care_members", COLS_MEM), load_data("care_logs", COLS_LOG)
    
    if not mems.empty:
        cur_y = datetime.now(TW_TZ).year
        prev_y = cur_y - 1
        mems['age'] = mems['生日'].apply(calculate_age)
        
        # 數據計算
        dist_df = logs.copy()
        if not logs.empty:
            dist_df['dt'] = pd.to_datetime(dist_df['發放日期'], errors='coerce')
            cur_val = dist_df[dist_df['dt'].dt.year == cur_y]['發放數量'].replace("","0").astype(float).sum()
            prev_val = dist_df[dist_df['dt'].dt.year == prev_y]['發放數量'].replace("","0").astype(float).sum()
        else: cur_val = prev_val = 0
        
        dis_c = len(mems[mems['身分別'].str.contains("身障", na=False)])
        low_c = len(mems[mems['身分別'].str.contains("低收|中低收", na=False)])

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#8E9775 0%,#6D6875 100%);"><div>🏠 關懷戶總人數</div><div style="font-size:2.8rem;">{len(mems)} <span style="font-size:1.2rem;">人</span></div><div>平均 {round(mems["age"].mean(),1)} 歲</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#A4AC86 0%,#8E9775 100%);"><div>♿ 身障關懷人數</div><div style="font-size:2.8rem;">{dis_c} <span style="font-size:1.2rem;">人</span></div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#6D6875 0%,#4A4E69 100%);"><div>📉 低收/中低收</div><div style="font-size:2.8rem;">{low_c} <span style="font-size:1.2rem;">人</span></div></div>', unsafe_allow_html=True)
        
        c4, c5 = st.columns(2)
        with c4: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#BC6C25 0%,#8E9775 100%);"><div>🎁 {cur_y} 當年度發放量</div><div style="font-size:3.5rem;">{int(cur_val)} <span style="font-size:1.5rem;">份</span></div></div>', unsafe_allow_html=True)
        with c5: st.markdown(f'<div class="care-metric-box" style="background:linear-gradient(135deg,#A4AC86 0%,#6D6875 100%);"><div>⏳ {prev_y} 上年度發放量</div><div style="font-size:3.5rem;">{int(prev_val)} <span style="font-size:1.5rem;">份</span></div></div>', unsafe_allow_html=True)

# --- [分頁 1：名冊管理] ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 關懷戶名冊管理")
    df = load_data("care_members", COLS_MEM)
    
    with st.expander("➕ 新增關懷戶 (防重複機制)"):
        with st.form("add_care", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            n = c1.text_input("姓名")
            p = c2.text_input("身分證")
            g = c3.selectbox("性別", ["男", "女"])
            b = c4.date_input("生日", value=date(1950, 1, 1), min_value=date(1911, 1, 1), max_value=date(2025, 12, 31))
            
            addr, ph = st.text_input("地址"), st.text_input("電話")
            ce1, ce2 = st.columns(2)
            en, ep = ce1.text_input("緊急聯絡人"), ce2.text_input("緊急聯絡電話")
            
            cn1, cn2, cn3 = st.columns(3)
            child = cn1.number_input("18歲以下子女", min_value=0, value=0, step=1)
            adult = cn2.number_input("成人數量", min_value=0, value=0, step=1)
            senior = cn3.number_input("65歲以上長者", min_value=0, value=0, step=1)
            
            id_t = st.multiselect("身分別 (可多選)", ["低收", "中低收", "中低老人", "身障", "獨居", "獨居有子女"])
            
            if st.form_submit_button("確認新增關懷戶"):
                if p.upper() in df['身分證字號'].values: st.error("❌ 該身分證號已存在！")
                elif not n: st.error("❌ 姓名為必填")
                else:
                    new = {"姓名": n, "身分證字號": p.upper(), "性別": g, "生日": str(b), "地址": addr, "電話": ph, 
                           "緊急聯絡人": en, "緊急聯絡人電話": ep, "身分別": ",".join(id_t),
                           "18歲以下子女": str(child), "成人數量": str(adult), "65歲以上長者": str(senior)}
                    if save_data(pd.concat([df, pd.DataFrame([new])], ignore_index=True), "care_members"):
                        st.success("✅ 已新增關懷戶！"); time.sleep(1); st.rerun()
    if not df.empty:
        df['歲數'] = df['生日'].apply(calculate_age)
        ed = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="mem_ed")
        if st.button("💾 儲存名冊修改"): 
            if save_data(ed, "care_members"): st.success("已更新雲端資料")

# --- [分頁 2：健康指標] ---
elif st.session_state.page == 'health':
    render_nav()
    st.markdown("## 🏥 關懷戶健康指標管理")
    h_df, m_df = load_data("care_health", COLS_HEALTH), load_data("care_members", COLS_MEM)
    with st.expander("➕ 登記健康指標數據"):
        with st.form("h_form"):
            sel_n = st.selectbox("選擇關懷戶", m_df['姓名'].tolist() if not m_df.empty else ["無名冊"])
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            dent, wash = c1.selectbox("假牙",["無","有"]), c2.selectbox("洗牙",["否","是"])
            grip, h, w, hear = c3.text_input("握力"), c4.text_input("身高"), c5.text_input("體重"), c6.selectbox("聽力",["正常","需注意"])
            if st.form_submit_button("儲存健康紀錄"):
                pid = m_df[m_df['姓名']==sel_n]['身分證字號'].iloc[0]
                new = {"姓名":sel_n, "身分證字號":pid, "是否有假牙":dent, "今年洗牙":wash, "握力":grip, "身高":h, "體重":w, "聽力測試":hear}
                if save_data(pd.concat([h_df, pd.DataFrame([new])], ignore_index=True), "care_health"): st.success("已存檔"); st.rerun()
    if not h_df.empty:
        ed_h = st.data_editor(h_df, use_container_width=True, num_rows="dynamic", key="h_ed")
        if st.button("💾 儲存修改內容"): save_data(ed_h, "care_health")

# --- [分頁 3：物資管理] ---
elif st.session_state.page == 'inventory':
    render_nav()
    st.markdown("## 📦 物資庫存管理")
    inv, logs = load_data("care_inventory", COLS_INV), load_data("care_logs", COLS_LOG)
    with st.form("add_inv"):
        c1, c2, co, qt = st.columns(4)
        do, ty, co, qt = c1.text_input("捐贈者"), c2.selectbox("類型",["食物","日用品","輔具","現金","服務"]), co.text_input("名稱"), qt.number_input("數量/金額", min_value=1)
        if st.form_submit_button("錄入捐贈資料"):
            new = {"捐贈者":do, "物資類型":ty, "物資內容":co, "總數量":qt, "捐贈日期":str(date.today())}
            if save_data(pd.concat([inv, pd.DataFrame([new])], ignore_index=True), "care_inventory"): st.rerun()
    if not inv.empty:
        sm = []
        for itm, gp in inv.groupby('物資內容'):
            tin = gp['總數量'].replace("","0").astype(float).sum()
            tout = logs[logs['物資內容'] == itm]['發放數量'].replace("","0").astype(float).sum() if not logs.empty else 0
            sm.append({"名稱":itm, "類型":gp.iloc[0]['物資類型'], "入庫":tin, "已發放":tout, "剩餘":tin-tout})
        st.markdown("#### 📊 目前庫存/餘額概況")
        st.dataframe(pd.DataFrame(sm), use_container_width=True)
        ed_i = st.data_editor(inv, use_container_width=True, num_rows="dynamic", key="inv_ed")
        if st.button("💾 儲存修改內容"): save_data(ed_i, "care_inventory")

# --- [分頁 4：訪視發放 (卡片式 + 懸浮)] ---
elif st.session_state.page == 'visit':
    render_nav()
    st.markdown("## 🤝 訪視與物資發放紀錄")
    mems = load_data("care_members", COLS_MEM)
    inv = load_data("care_inventory", COLS_INV)
    logs = load_data("care_logs", COLS_LOG)
    
    # 1. 計算即時庫存
    stock_map = {}
    if not inv.empty:
        for itm, gp in inv.groupby('物資內容'):
            tin = gp['總數量'].replace("","0").astype(float).sum()
            tout = logs[logs['物資內容'] == itm]['發放數量'].replace("","0").astype(float).sum() if not logs.empty else 0
            stock_map[itm] = int(tin - tout)
    
    # --- 身分別篩選 ---
    st.markdown("#### 1. 選擇訪視對象")
    all_tags = set()
    if not mems.empty:
        for s in mems['身分別'].astype(str):
            for t in s.split(','):
                if t.strip(): all_tags.add(t.strip())
    
    c_filter, c_person = st.columns([1, 2])
    with c_filter:
        tag_opts = ["(全部顯示)"] + sorted(list(all_tags))
        sel_tag = st.selectbox("🌪️ 依身分別篩選", tag_opts)
    
    with c_person:
        if sel_tag == "(全部顯示)": filtered_mems = mems
        else: filtered_mems = mems[mems['身分別'].str.contains(sel_tag, na=False)] if not mems.empty else mems
        p_list = filtered_mems['姓名'].tolist() if not filtered_mems.empty else []
        target_p = st.selectbox("👤 選擇關懷戶", p_list)

    # --- 卡片式發放 ---
    st.markdown("#### 2. 填寫訪視內容與物資")
    
    with st.form("visit_multi_form"):
        c1, c2 = st.columns(2)
        try:
            v_df = load_data("members", ["姓名"]) 
            v_list = v_df['姓名'].tolist() if not v_df.empty else ["預設志工"]
        except:
            v_list = ["預設志工"]
            
        visit_who = c1.selectbox("執行志工", v_list)
        visit_date = c2.date_input("日期", value=date.today())
        
        st.write("📦 **點擊下方卡片輸入數量 (0 代表不發)**")
        
        valid_items = {k:v for k,v in stock_map.items() if v > 0}
        quantities = {} 
        
        if not valid_items:
            st.info("💡 目前無任何庫存物資，僅能進行純訪視記錄。")
        else:
            cols = st.columns(3) 
            for idx, (item, stock) in enumerate(valid_items.items()):
                col = cols[idx % 3] 
                with col:
                    # 使用 container 當作卡片框 (懸浮效果會作用在這裡)
                    with st.container(border=True):
                        st.markdown(f'<div class="inv-card-header">{item}</div>', unsafe_allow_html=True)
                        stock_class = "low" if stock < 5 else "normal"
                        stock_label = f"⚠️ 庫存告急: {stock}" if stock < 5 else f"庫存: {stock}"
                        st.markdown(f'<div class="inv-card-stock {stock_class}">{stock_label}</div>', unsafe_allow_html=True)
                        qty = st.number_input("發放數量", min_value=0, max_value=stock, step=1, key=f"q_{idx}_{item}")
                        quantities[item] = qty

        note = st.text_area("訪視紀錄 / 備註")
        submitted = st.form_submit_button("✅ 確認提交紀錄")
        
        if submitted:
            if not target_p:
                st.error("❌ 請先選擇關懷戶！")
            else:
                items_to_give = [(k, v) for k, v in quantities.items() if v > 0]
                new_logs = []
                
                if items_to_give:
                    for item_name, amount in items_to_give:
                        new_logs.append({
                            "志工": visit_who, "發放日期": str(visit_date), "關懷戶姓名": target_p,
                            "物資內容": item_name, "發放數量": amount, "訪視紀錄": note
                        })
                else:
                    new_logs.append({
                        "志工": visit_who, "發放日期": str(visit_date), "關懷戶姓名": target_p,
                        "物資內容": "(僅訪視)", "發放數量": 0, "訪視紀錄": note
                    })
                
                if save_data(pd.concat([logs, pd.DataFrame(new_logs)], ignore_index=True), "care_logs"):
                    st.success(f"✅ 已成功紀錄！(包含 {len(items_to_give)} 項物資)")
                    time.sleep(1); st.rerun()

    if not logs.empty:
        st.markdown("#### 📝 最近 20 筆訪視紀錄")
        ed_l = st.data_editor(logs.sort_values('發放日期', ascending=False).head(20), use_container_width=True, num_rows="dynamic", key="v_ed")
        if st.button("💾 儲存歷史紀錄修改"): save_data(ed_l, "care_logs")

# --- [分頁 5：統計] ---
elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 數據統計與個案查詢")
    logs, mems = load_data("care_logs", COLS_LOG), load_data("care_members", COLS_MEM)
    tab1, tab2 = st.tabs(["👤 個案詳細檔案", "📈 整體物資統計"])
    
    with tab1:
        if mems.empty: st.info("目前尚無關懷戶名冊資料")
        else:
            all_names = mems['姓名'].unique().tolist()
            target_name = st.selectbox("🔍 請選擇或輸入關懷戶姓名", all_names)
            if target_name:
                p_data = mems[mems['姓名'] == target_name].iloc[0]
                age = calculate_age(p_data['生日'])
                with st.container():
                    st.markdown(f"""
                    <div style="background-color: white; padding: 20px; border-radius: 15px; border-left: 5px solid {GREEN}; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <div style="font-size: 1.8rem; font-weight: 900; color: #333;">{p_data['姓名']} <span style="font-size: 1rem; color: #666; background: #eee; padding: 2px 8px; border-radius: 10px;">{p_data['性別']} / {age} 歲</span></div>
                            <div style="font-weight: bold; color: {PRIMARY}; border: 2px solid {PRIMARY}; padding: 5px 15px; border-radius: 20px;">{p_data['身分別']}</div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                            <div><b>🆔 身分證：</b> {p_data['身分證字號']}</div><div><b>🎂 生日：</b> {p_data['生日']}</div>
                            <div><b>📞 電話：</b> {p_data['電話']}</div><div><b>📍 地址：</b> {p_data['地址']}</div>
                        </div>
                        <hr style="border-top: 1px dashed #ccc;">
                        <div style="margin-top: 10px; color: #555;"><b>🏠 家庭結構：</b> 18歲以下 <b>{p_data['18歲以下子女']}</b> 人，成人 <b>{p_data['成人數量']}</b> 人，65歲以上長者 <b>{p_data['65歲以上長者']}</b> 人</div>
                        <div style="margin-top: 5px; color: #d9534f;"><b>🚨 緊急聯絡：</b> {p_data['緊急聯絡人']} ({p_data['緊急聯絡人電話']})</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("### 🤝 歷史訪視與領取紀錄")
                p_logs = logs[logs['關懷戶姓名'] == target_name]
                if p_logs.empty: st.info("此人目前尚無訪視或物資領取紀錄。")
                else: st.dataframe(p_logs.sort_values("發放日期", ascending=False)[['發放日期', '物資內容', '發放數量', '訪視紀錄', '志工']], use_container_width=True, hide_index=True)
    
    with tab2:
        if not logs.empty:
            st.markdown("#### 📊 各類物資發放排行")
            bar_data = logs.groupby('物資內容')['發放數量'].apply(lambda x: x.replace("","0").astype(float).sum()).reset_index()
            fig = px.bar(bar_data, x='物資內容', y='發放數量', color='物資內容')
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("#### 📝 所有發放流水帳")
            st.dataframe(logs, use_container_width=True)
        else: st.info("目前無任何發放紀錄")
