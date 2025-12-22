import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import plotly.express as px
import random

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
# 1) CSS 樣式 (高對比 + 莫蘭迪)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
html, body, [class*="css"], div, p, span, li, ul {{ font-family: "Noto Sans TC", sans-serif; color: #333 !important; }}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 數據看板：強制白字 */
.care-metric-box {{
    padding: 30px; border-radius: 20px; color: #FFFFFF !important; text-align: center; margin-bottom: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}}
.care-metric-box div, .care-metric-box span {{ color: #FFFFFF !important; font-weight: 900 !important; }}

/* 下拉選單與輸入框 (白底黑字) */
div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {{
    background-color: #FFFFFF !important; color: #000 !important;
    border: 2px solid #D1D1D1 !important; border-radius: 12px !important; font-weight: 700 !important;
}}
div[data-baseweb="select"] span {{ color: #000 !important; }}

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
# 2) 資料邏輯 (Google Sheets 鉤稽)
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"

# 定義各表欄位
COLS_MEM = ["姓名", "身分證字號", "性別", "生日", "地址", "電話", "緊急聯絡人", "緊急聯絡人電話", "身分別", "18歲以下子女", "成人數量", "65歲以上長者", "是否有假牙", "今年洗牙", "握力", "身高", "體重", "聽力測試"]
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
    df_fix = df.fillna("").replace(['nan', 'NaN', 'nan.0'], "").astype(str)
    sheet = get_client().open_by_key(SHEET_ID).worksheet(sn)
    sheet.clear()
    sheet.update([df_fix.columns.values.tolist()] + df_fix.values.tolist())
    st.cache_data.clear()

def calculate_age(dob_str):
    try:
        bd = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        return date.today().year - bd.year - ((date.today().month, date.today().day) < (bd.month, bd.day))
    except: return 0

# =========================================================
# 3) 頁面渲染
# =========================================================
def render_nav():
    st.markdown('<div style="background:white; padding:12px; border-radius:20px; margin-bottom:20px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    pages = [("🏠 首頁", 'home'), ("📋 名冊", 'members'), ("📦 物資", 'inventory'), ("🤝 訪視", 'visit'), ("📊 統計", 'stats')]
    for i, (label, p_key) in enumerate(pages):
        with [c1, c2, c3, c4, c5][i]:
            if st.button(label, use_container_width=True): st.session_state.page = p_key; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 頁面 0：首頁看板 ---
if st.session_state.page == 'home':
    if st.button("🚪 回大廳"): st.switch_page("Home.py")
    st.markdown("<h1 style='text-align: center;'>福德里 - 關懷戶管理系統</h1>", unsafe_allow_html=True)
    
    mems = load_data("care_members", COLS_MEM)
    logs = load_data("care_logs", COLS_LOG)
    
    if not mems.empty:
        mems['age'] = mems['生日'].apply(calculate_age)
        total_p = len(mems)
        avg_age = round(mems['age'].mean(), 1)
        
        # 篩選身分別
        dis_mems = mems[mems['身分別'].str.contains("身障", na=False)]
        welfare_mems = mems[mems['身分別'].str.contains("低收|老人", na=False)]
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class="care-metric-box" style="background:linear-gradient(135deg,#8E9775 0%,#6D6875 100%);"><div>🏠 關懷戶總人數</div><div style="font-size:3.5rem;">{total_p} <span style="font-size:1.5rem;">人</span></div><div>平均 {avg_age} 歲</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="care-metric-box" style="background:linear-gradient(135deg,#A4AC86 0%,#8E9775 100%);"><div>♿ 身障關懷人數</div><div style="font-size:3.5rem;">{len(dis_mems)} <span style="font-size:1.5rem;">人</span></div><div>平均 {round(dis_mems['age'].mean(),1) if not dis_mems.empty else 0} 歲</div></div>""", unsafe_allow_html=True)
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="dash-card"><b>福利身份統計</b><br>低收/中低收：{len(mems[mems["身分別"].str.contains("低收", na=False)])} 人<br>中低老人：{len(mems[mems["身分別"].str.contains("中低老人", na=False)])} 人</div>', unsafe_allow_html=True)
        with c2:
            total_dist = logs['發放數量'].astype(float).sum() if not logs.empty else 0
            st.markdown(f'<div class="dash-card"><b>物資發放總量</b><br><span style="font-size:1.5rem; color:{PRIMARY}; font-weight:900;">{int(total_dist)} 份</span></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="dash-card"><b>獨居狀況</b><br>獨居：{len(mems[mems["身分別"].str.contains("獨居", na=False)])} 人</div>', unsafe_allow_html=True)

# --- 頁面 1：關懷戶名冊 ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 關懷戶名冊管理")
    df = load_data("care_members", COLS_MEM)
    
    with st.expander("➕ 新增關懷戶資料"):
        with st.form("add_care"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("姓名")
            pid = c2.text_input("身分證字號")
            dob = c3.date_input("生日", value=date(1950, 1, 1))
            
            c4, c5 = st.columns([2, 1])
            addr = c4.text_input("地址")
            phone = c5.text_input("電話")
            
            st.markdown("---")
            c6, c7 = st.columns(2)
            e_name = c6.text_input("緊急聯絡人")
            e_phone = c7.text_input("緊急聯絡電話")
            
            id_types = st.multiselect("身分別 (可複選)", ["低收", "中低收", "中低老人", "身障", "獨居", "獨居有子女"])
            
            st.markdown("###### 同住家人人數")
            cj1, cj2, cj3 = st.columns(3)
            child = cj1.number_input("18歲以下子女", 0, 10, 0)
            adult = cj2.number_input("成人數量", 0, 10, 0)
            elder = cj3.number_input("65歲以上長者", 0, 10, 0)
            
            st.markdown("###### 健康狀況")
            h1, h2, h3, h4, h5, h6 = st.columns(6)
            dent = h1.selectbox("假牙", ["無", "有"])
            wash = h2.selectbox("今年洗牙", ["否", "是"])
            grip = h3.text_input("握力")
            height = h4.text_input("身高")
            weight = h5.text_input("體重")
            hear = h6.selectbox("聽力測試", ["正常", "需注意"])
            
            if st.form_submit_button("確認新增"):
                new_row = {
                    "姓名": name, "身分證字號": pid.upper(), "生日": str(dob), "地址": addr, "電話": phone,
                    "緊急聯絡人": e_name, "緊急聯絡人電話": e_phone, "身分別": ",".join(id_types),
                    "18歲以下子女": child, "成人數量": adult, "65歲以上長者": elder,
                    "是否有假牙": dent, "今年洗牙": wash, "握力": grip, "身高": height, "體重": weight, "聽力測試": hear
                }
                if save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True), "care_members"):
                    st.success("資料已存入"); st.rerun()
    
    if not df.empty:
        df['年齡'] = df['生日'].apply(calculate_age)
        st.data_editor(df, use_container_width=True, num_rows="dynamic", key="care_mem_edit")
        if st.button("💾 儲存名冊修改"): save_data(df, "care_members"); st.success("已更新")

# --- 頁面 2：物資管理 ---
elif st.session_state.page == 'inventory':
    render_nav()
    st.markdown("## 📦 物資捐贈與庫存管理")
    inv = load_data("care_inventory", COLS_INV)
    logs = load_data("care_logs", COLS_LOG)
    
    with st.form("add_inv"):
        c1, c2, c3, c4 = st.columns(4)
        donor = c1.text_input("捐贈者")
        v_type = c2.selectbox("物資類型", ["食物", "日用品", "輔具", "現金", "服務"])
        content = c3.text_input("詳細內容 (如: 5公斤白米)")
        qty = c4.number_input("總數量", min_value=1)
        if st.form_submit_button("錄入捐贈"):
            new_v = {"捐贈者": donor, "物資類型": v_type, "物資內容": content, "總數量": qty, "捐贈日期": str(date.today())}
            save_data(pd.concat([inv, pd.DataFrame([new_v])], ignore_index=True), "care_inventory")
            st.success("物資已入庫"); st.rerun()
    
    st.markdown("### 📊 目前物資庫存表")
    if not inv.empty:
        # 核心：庫存扣除邏輯 (總捐贈 - 總發放)
        summary = []
        for item_name, group in inv.groupby('物資內容'):
            total_in = group['總數量'].astype(float).sum()
            total_out = logs[logs['物資內容'] == item_name]['發放數量'].astype(float).sum() if not logs.empty else 0
            summary.append({"物資名稱": item_name, "類型": group.iloc[0]['物資類型'], "入庫總數": total_in, "已發放": total_out, "剩餘庫存": total_in - total_out})
        
        st.dataframe(pd.DataFrame(summary), use_container_width=True)

# --- 頁面 3：訪視與發放 ---
elif st.session_state.page == 'visit':
    render_nav()
    st.markdown("## 🤝 訪視與物資發放紀錄")
    mems = load_data("care_members", COLS_MEM)
    inv = load_data("care_inventory", COLS_INV)
    logs = load_data("care_logs", COLS_LOG)
    
    # 鉤稽志工管理系統 (從 members 工作表讀取)
    vol_df = load_data("members", ["姓名", "志工分類"]) # 這裡會去讀 1_volunteer.py 用的表
    vol_list = vol_df['姓名'].tolist() if not vol_df.empty else ["請先新增志工"]

    with st.container(border=True):
        st.markdown("#### 🎁 新增紀錄")
        c1, c2, c3 = st.columns(3)
        sel_vol = c1.selectbox("執行志工", vol_list)
        sel_date = c2.date_input("日期", value=date.today())
        sel_care = c3.selectbox("領取關懷戶", mems['姓名'].tolist() if not mems.empty else ["請先新增名冊"])
        
        c4, c5 = st.columns([2, 1])
        # 庫存鉤稽
        available_items = inv['物資內容'].unique().tolist()
        sel_item = c4.selectbox("選擇發放物資", ["(不發放物資，僅訪視)"] + available_items)
        send_qty = c5.number_input("數量", min_value=0, value=1)
        
        visit_note = st.text_area("訪視紀錄內容")
        
        # 🔥 優先提示邏輯
        if sel_item != "(不發放物資，僅訪視)":
            receive_counts = logs[logs['物資內容'] == sel_item]['關懷戶姓名'].value_counts()
            st.info(f"💡 優先發放建議：目前領取『{sel_item}』次數較少的關懷戶為 {', '.join(mems[~mems['姓名'].isin(receive_counts.index)]['姓名'].head(3).tolist())}")

        if st.button("確認提交紀錄"):
            new_log = {"志工": sel_vol, "發放日期": str(sel_date), "關懷戶姓名": sel_care, "物資內容": sel_item, "發放數量": send_qty, "訪視紀錄": visit_note}
            save_data(pd.concat([logs, pd.DataFrame([new_log])], ignore_index=True), "care_logs")
            st.success("紀錄已存檔，庫存已自動連動。"); time.sleep(1); st.rerun()

    st.markdown("### 📋 歷史訪視/發放清單")
    if not logs.empty:
        st.data_editor(logs.sort_values('發放日期', ascending=False), use_container_width=True, num_rows="dynamic", key="care_log_edit")
        if st.button("💾 儲存修改 (庫存會自動依新數量重新計算)"): save_data(logs, "care_logs"); st.success("已更新")

# --- 頁面 4：數據統計 ---
elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 數據統計查詢")
    inv = load_data("care_inventory", COLS_INV)
    logs = load_data("care_logs", COLS_LOG)
    
    t1, t2 = st.tabs(["📦 物資捐贈統計", "🔍 個案歷程查詢"])
    with t1:
        if not inv.empty:
            st.markdown("### 各類物資捐贈場次 (泡泡圖)")
            random.seed(42)
            counts = inv['物資類型'].value_counts().reset_index()
            counts.columns = ['類型', '次數']
            counts['x'] = [random.uniform(0, 10) for _ in range(len(counts))]
            counts['y'] = [random.uniform(0, 10) for _ in range(len(counts))]
            fig = px.scatter(counts, x='x', y='y', size='次數', color='類型', text='類型', size_max=60, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=False, xaxis=dict(showticklabels=False, title=""), yaxis=dict(showticklabels=False, title=""), height=400)
            st.plotly_chart(fig, use_container_width=True)
            
    with t2:
        mems = load_data("care_members", COLS_MEM)
        c1, c2 = st.columns(2)
        q_name = c1.selectbox("選擇關懷戶", mems['姓名'].tolist())
        q_range = c2.date_input("查詢期間", value=(date(date.today().year, 1, 1), date.today()))
        
        if isinstance(q_range, tuple) and len(q_range) == 2:
            res = logs[(logs['關懷戶姓名'] == q_name) & (pd.to_datetime(logs['發放日期']).dt.date >= q_range[0]) & (pd.to_datetime(logs['發放日期']).dt.date <= q_range[1])]
            st.markdown(f"#### {q_name} 在此期間共受訪/領取 {len(res)} 次")
            st.dataframe(res, use_container_width=True)
