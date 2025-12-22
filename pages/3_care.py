import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import plotly.express as px
import random
import time

# =========================================================
# 0) 系統設定與初始化
# =========================================================
st.set_page_config(page_title="關懷戶管理系統", page_icon="🏠", layout="wide", initial_sidebar_state="collapsed")

if 'page' not in st.session_state:
    st.session_state.page = 'home'

TW_TZ = timezone(timedelta(hours=8))

# 🔥 莫蘭迪森林綠配色
PRIMARY = "#8E9775"   # 苔蘚綠
ACCENT  = "#6D6875"   # 灰紫色
BG_MAIN = "#F8F9FA"   

# =========================================================
# 1) CSS 樣式 (V36.0 高對比識別強化)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
html, body, [class*="css"], div, p, span, li, ul {{ font-family: "Noto Sans TC", sans-serif; color: #333 !important; }}
/* --- 強制表格與名冊區域為白底黑字 --- */
/* 針對表格容器 */
div[data-testid="stDataFrame"], div[data-testid="stTable"] {
    background-color: #FFFFFF !important;
    border-radius: 10px;
    padding: 10px;
}

/* 確保表格內部的文字為純黑色 */
.stDataFrame div, .stDataFrame span, .stDataFrame p {
    color: #000000 !important;
}

/* 修改表格內部的「身份別」等下拉選單顏色 */
/* 註：Streamlit 表格內的下拉選單是由 Glide Data Grid 渲染，CSS 控制較受限 */
/* 但這行可以幫助外層選單保持清晰 */
div[role="listbox"] ul li {
    background-color: #FFFFFF !important;
    color: #000000 !important;
}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 🔥 強制下拉式選單與日期選擇顯示 (白底黑字) */
div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {{
    background-color: #FFFFFF !important; 
    color: #000000 !important;
    border: 2px solid #D1D1D1 !important; 
    border-radius: 12px !important; 
    font-weight: 700 !important;
}}
div[data-baseweb="select"] span, div[data-baseweb="select"] div {{ color: #000000 !important; }}
div[role="listbox"], ul[data-baseweb="menu"], li[role="option"] {{
    background-color: #FFFFFF !important; color: #000000 !important; font-weight: 700 !important;
}}

/* 數據看板 */
.care-metric-box {{
    padding: 30px; border-radius: 20px; color: #FFFFFF !important; text-align: center; margin-bottom: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}}
.care-metric-box div, .care-metric-box span {{ color: #FFFFFF !important; font-weight: 900 !important; }}

/* 導航按鈕 */
div[data-testid="stButton"] > button {{
    width: 100%; background-color: white !important; color: {PRIMARY} !important;
    border: 2px solid {PRIMARY} !important; border-radius: 15px !important;
    font-weight: 900 !important; font-size: 1.1rem !important; transition: all 0.2s;
}}
div[data-testid="stButton"] > button:hover {{ background-color: {PRIMARY} !important; color: white !important; }}

.dash-card {{ background-color: white; padding: 15px; border-radius: 15px; border-left: 6px solid {PRIMARY}; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 10px; }}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 資料邏輯
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90" #

# 更新欄位定義
COLS_MEM = ["姓名", "身分證字號", "性別", "生日", "地址", "電話", "緊急聯絡人", "緊急聯絡人電話", "身分別", "18歲以下子女", "成人數量", "65歲以上長者"]
COLS_HEALTH = ["姓名", "身分證字號", "是否有假牙", "今年洗牙", "握力", "身高", "體重", "聽力測試"]
COLS_INV = ["捐贈者", "物資類型", "物資內容", "總數量", "捐贈日期"]
COLS_LOG = ["志工", "發放日期", "關懷戶姓名", "物資內容", "發放數量", "訪視紀錄"]

@st.cache_resource
def get_client(): return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

def load_data(sn, target_cols):
    try:
        client = get_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        df = pd.DataFrame(sheet.get_all_records()).astype(str)
        for c in target_cols:
            if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame(columns=target_cols)

def save_data(df, sn):
    try:
        # 🔥 修正 nan 錯誤
        df_fix = df.fillna("").replace(['nan', 'NaN', 'nan.0'], "").astype(str)
        sheet = get_client().open_by_key(SHEET_ID).worksheet(sn)
        sheet.clear()
        sheet.update([df_fix.columns.values.tolist()] + df_fix.values.tolist())
        load_data.clear()
        return True
    except Exception as e:
        st.error(f"寫入失敗：{e}")
        return False

def calculate_age(dob_str):
    try:
        bd = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        return date.today().year - bd.year - ((date.today().month, date.today().day) < (bd.month, bd.day))
    except: return 0

# =========================================================
# 3) UI 導航
# =========================================================
def render_nav():
    st.markdown('<div style="background:white; padding:12px; border-radius:20px; margin-bottom:20px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    pages = [("🏠 首頁", 'home'), ("📋 名冊", 'members'), ("🏥 健康", 'health'), ("📦 物資", 'inventory'), ("🤝 訪視", 'visit'), ("📊 統計", 'stats')]
    for i, (label, p_key) in enumerate(pages):
        with [c1, c2, c3, c4, c5, c6][i]:
            if st.button(label, use_container_width=True, key=f"nav_{p_key}"): 
                st.session_state.page = p_key
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 頁面 0：首頁 ---
if st.session_state.page == 'home':
    if st.button("🚪 回大廳"): st.switch_page("Home.py")
    st.markdown("<h1 style='text-align: center;'>福德里 - 關懷戶管理系統</h1>", unsafe_allow_html=True)
    render_nav()
    mems = load_data("care_members", COLS_MEM)
    logs = load_data("care_logs", COLS_LOG)
    if not mems.empty:
        mems['age'] = mems['生日'].apply(calculate_age)
        total_p = len(mems)
        avg_age = round(mems['age'].mean(), 1)
        dis_c = len(mems[mems['身分別'].str.contains("身障", na=False)])
        dis_a = round(mems[mems['身分別'].str.contains("身障", na=False)]['age'].mean(), 1) if dis_c > 0 else 0
        
        c1, c2 = st.columns(2)
        with c1: st.markdown(f"""<div class="care-metric-box" style="background:linear-gradient(135deg,#8E9775 0%,#6D6875 100%);"><div>🏠 關懷戶總人數 / 平均年齡</div><div style="font-size:3.5rem;">{total_p} <span style="font-size:1.5rem;">人</span> / {avg_age} <span style="font-size:1.5rem;">歲</span></div></div>""", unsafe_allow_html=True)
        with c2: st.markdown(f"""<div class="care-metric-box" style="background:linear-gradient(135deg,#A4AC86 0%,#8E9775 100%);"><div>♿ 身障關懷人數 / 平均年齡</div><div style="font-size:3.5rem;">{dis_c} <span style="font-size:1.5rem;">人</span> / {dis_a} <span style="font-size:1.5rem;">歲</span></div></div>""", unsafe_allow_html=True)
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            l_c = len(mems[mems['身分別'].str.contains("低收", na=False)])
            l_a = round(mems[mems['身分別'].str.contains("低收", na=False)]['age'].mean(), 1) if l_c > 0 else 0
            st.markdown(f'<div class="dash-card"><b>低收/中低收統計</b><br>{l_c} 人 (平均 {l_a} 歲)</div>', unsafe_allow_html=True)
        with c2:
            o_c = len(mems[mems['身分別'].str.contains("中低老人", na=False)])
            o_a = round(mems[mems['身分別'].str.contains("中低老人", na=False)]['age'].mean(), 1) if o_c > 0 else 0
            st.markdown(f'<div class="dash-card"><b>中低老人統計</b><br>{o_c} 人 (平均 {o_a} 歲)</div>', unsafe_allow_html=True)
        with c3:
            total_dist = logs['發放數量'].replace("", "0").astype(float).sum() if not logs.empty else 0
            st.markdown(f'<div class="dash-card"><b>物資發放總量</b><br><span style="font-size:1.5rem; color:{PRIMARY}; font-weight:900;">{int(total_dist)} 份</span></div>', unsafe_allow_html=True)

# --- 頁面 1：名冊管理 (含防重機制) ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 關懷戶名冊管理")
    df = load_data("care_members", COLS_MEM)
    
    with st.expander("➕ 新增關懷戶資料"):
        with st.form("add_care"):
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            n = c1.text_input("姓名")
            p = c2.text_input("身分證字號")
            g = c3.selectbox("性別", ["男", "女"])
            b = c4.date_input("生日", value=date(1950, 1, 1))
            
            c_addr, c_ph = st.columns([2, 1])
            addr = c_addr.text_input("地址")
            ph = c_ph.text_input("電話")
            
            ce1, ce2 = st.columns(2)
            en = ce1.text_input("緊急聯絡人")
            ep = ce2.text_input("緊急聯絡人電話")
            
            id_types = st.multiselect("身分別", ["低收", "中低收", "中低老人", "身障", "獨居", "獨居有子女"])
            
            st.markdown("###### 同住家人人數")
            cj1, cj2, cj3 = st.columns(3)
            child = cj1.number_input("18歲以下子女", 0, 10, 0)
            adult = cj2.number_input("成人數量", 0, 10, 0)
            elder = cj3.number_input("65歲以上長者", 0, 10, 0)
            
            if st.form_submit_button("確認新增"):
                # 🔥 防重複機制
                if p.upper() in df['身分證字號'].values:
                    st.error(f"❌ 錯誤：身分證字號 {p.upper()} 已存在於名冊中，不可重複建立！")
                elif not n or not p:
                    st.error("❌ 姓名與身分證字號為必填欄位")
                else:
                    new = {"姓名":n, "身分證字號":p.upper(), "性別":g, "生日":str(b), "地址":addr, "電話":ph, "緊急聯絡人":en, "緊急聯絡人電話":ep, "身分別":",".join(id_types), "18歲以下子女":child, "成人數量":adult, "65歲以上長者":elder}
                    if save_data(pd.concat([df, pd.DataFrame([new])], ignore_index=True), "care_members"):
                        st.success("已新增名單"); st.rerun()
    
    if not df.empty:
        df['歲數'] = df['生日'].apply(calculate_age)
        # 🔥 修正刪除失效：必須將修改後的 dataframe 存回變數
        edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="mem_editor")
        if st.button("💾 儲存名冊修改"): 
            if save_data(edited_df, "care_members"): st.success("名冊已成功更新！")

# --- 頁面 2：健康數據 (獨立頁面) ---
elif st.session_state.page == 'health':
    render_nav()
    st.markdown("## 🏥 關懷戶健康指標管理")
    h_df = load_data("care_health", COLS_HEALTH)
    m_df = load_data("care_members", COLS_MEM)
    
    with st.expander("➕ 登記健康數據"):
        with st.form("add_health"):
            sel_n = st.selectbox("請選擇關懷戶", m_df['姓名'].tolist() if not m_df.empty else ["請先建立名冊"])
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            dent = c1.selectbox("假牙", ["無", "有"])
            wash = c2.selectbox("洗牙", ["否", "是"])
            grip = c3.text_input("握力")
            h = c4.text_input("身高")
            w = c5.text_input("體重")
            hear = c6.selectbox("聽力測試", ["正常", "需注意"])
            if st.form_submit_button("儲存健康數據"):
                p_id = m_df[m_df['姓名']==sel_n]['身分證字號'].iloc[0]
                new_h = {"姓名":sel_n, "身分證字號":p_id, "是否有假牙":dent, "今年洗牙":wash, "握力":grip, "身高":h, "體重":w, "聽力測試":hear}
                if save_data(pd.concat([h_df, pd.DataFrame([new_h])], ignore_index=True), "care_health"):
                    st.success("健康紀錄已存檔"); st.rerun()
    if not h_df.empty:
        edited_h = st.data_editor(h_df, use_container_width=True, num_rows="dynamic", key="health_editor")
        if st.button("💾 儲存修改內容"): save_data(edited_h, "care_health")

# --- 頁面 3：物資管理 (庫存自動計算) ---
elif st.session_state.page == 'inventory':
    render_nav()
    st.markdown("## 📦 物資庫存管理")
    inv = load_data("care_inventory", COLS_INV)
    logs = load_data("care_logs", COLS_LOG)
    
    with st.form("add_inv"):
        c1, c2, c3, c4 = st.columns(4)
        donor = c1.text_input("捐贈者")
        v_type = c2.selectbox("物資類型", ["食物", "日用品", "輔具", "現金", "服務"])
        content = c3.text_input("物資詳細名稱")
        qty = c4.number_input("數量", min_value=1)
        if st.form_submit_button("入庫存檔"):
            new_v = {"捐贈者": donor, "物資類型": v_type, "物資內容": content, "總數量": qty, "捐贈日期": str(date.today())}
            save_data(pd.concat([inv, pd.DataFrame([new_v])], ignore_index=True), "care_inventory")
            st.rerun()
    
    # 🔥 核心庫存邏輯：入庫 - 發放
    if not inv.empty:
        summary = []
        for item, group in inv.groupby('物資內容'):
            total_in = group['總數量'].replace("", "0").astype(float).sum()
            # 扣除已發放的數量 (排除僅訪視紀錄)
            total_out = logs[(logs['物資內容'] == item) & (logs['物資內容'] != "(僅訪視，不領取)")]['發放數量'].replace("", "0").astype(float).sum() if not logs.empty else 0
            summary.append({"物資名稱": item, "類型": group.iloc[0]['物資類型'], "累積入庫": total_in, "累計發放": total_out, "剩餘庫存": total_in - total_out})
        st.markdown("### 📊 當前庫存即時表")
        st.dataframe(pd.DataFrame(summary), use_container_width=True)

# --- 頁面 4：訪視與發放 (含優先權提示) ---
elif st.session_state.page == 'visit':
    render_nav()
    st.markdown("## 🤝 訪視與物資發放")
    mems = load_data("care_members", COLS_MEM)
    inv = load_data("care_inventory", COLS_INV)
    logs = load_data("care_logs", COLS_LOG)
    
    # 鉤稽志工管理系統
    vol_df = load_data("members", ["姓名"])
    vol_list = vol_df['姓名'].tolist() if not vol_df.empty else ["無資料"]

    with st.container(border=True):
        st.markdown("#### 🎁 新增發放與訪視紀錄")
        c1, c2, c3 = st.columns(3)
        sel_vol = c1.selectbox("執行志工", vol_list)
        sel_date = c2.date_input("日期", value=date.today())
        sel_care = c3.selectbox("領取關懷戶", mems['姓名'].tolist() if not mems.empty else ["無名冊"])
        
        c4, c5 = st.columns([2, 1])
        avail_items = inv['物資內容'].unique().tolist()
        sel_item = c4.selectbox("選擇物資", ["(僅訪視，不領取)"] + avail_items)
        send_qty = c5.number_input("數量", min_value=0, value=1)
        
        # 🔥 優先權提示邏輯
        if sel_item != "(僅訪視，不領取)":
            history = logs[logs['物資內容'] == sel_item]['關懷戶姓名'].value_counts()
            suggest = mems[~mems['姓名'].isin(history.index)]['姓名'].head(5).tolist()
            if suggest: st.info(f"💡 **發放優先建議**：尚未領取過「{sel_item}」的人：{', '.join(suggest)}")
        
        note = st.text_area("訪視紀錄內容")
        if st.button("確認提交"):
            new_log = {"志工": sel_vol, "發放日期": str(sel_date), "關懷戶姓名": sel_care, "物資內容": sel_item, "發放數量": send_qty, "訪視紀錄": note}
            if save_data(pd.concat([logs, pd.DataFrame([new_log])], ignore_index=True), "care_logs"):
                st.success("紀錄已存檔，庫存同步扣除。"); time.sleep(1); st.rerun()
    
    if not logs.empty:
        st.markdown("### 📋 歷史清單 (修改數量後庫存會自動重算)")
        edited_logs = st.data_editor(logs, use_container_width=True, num_rows="dynamic", key="log_editor")
        if st.button("💾 儲存修改"): save_data(edited_logs, "care_logs")

# --- 頁面 5：統計 ---
elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 數據統計")
    inv, logs = load_data("care_inventory", COLS_INV), load_data("care_logs", COLS_LOG)
    t1, t2 = st.tabs(["📦 物資統計", "🔍 個案查詢"])
    with t1:
        if not inv.empty:
            cts = inv.groupby('物資類型')['總數量'].apply(lambda x: x.astype(float).sum()).reset_index()
            fig = px.bar(cts, x='物資類型', y='總數量', color='物資類型', title="物資累計捐贈總量")
            st.plotly_chart(fig)
    with t2:
        m = load_data("care_members", COLS_MEM)
        c1, c2 = st.columns(2)
        q_n = c1.selectbox("選擇關懷戶", m['姓名'].tolist())
        q_r = c2.date_input("日期區間", value=(date(date.today().year, 1, 1), date.today()))
        if isinstance(q_r, tuple) and len(q_r) == 2:
            res = logs[(logs['關懷戶姓名'] == q_n) & (pd.to_datetime(logs['發放日期']).dt.date >= q_r[0]) & (pd.to_datetime(logs['發放日期']).dt.date <= q_r[1])]
            st.markdown(f"#### {q_n} 受訪/領取紀錄：{len(res)} 次")
            st.dataframe(res, use_container_width=True)
