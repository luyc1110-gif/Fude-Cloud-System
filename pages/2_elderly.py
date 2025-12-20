import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import plotly.express as px
import random

# =========================================================
# 0) 系統設定與初始化
# =========================================================
st.set_page_config(page_title="長輩關懷系統", page_icon="👴", layout="wide", initial_sidebar_state="collapsed")

if 'page' not in st.session_state:
    st.session_state.page = 'home'

TW_TZ = timezone(timedelta(hours=8))

# 🔥 莫蘭迪暮色粉配色
PRIMARY = "#B5838D"   # 暮色粉
ACCENT  = "#6D597A"   # 煙燻紫
BG_MAIN = "#F8F9FA"   

# =========================================================
# 1) CSS 樣式 (極致高對比 + 莫蘭迪)
# =========================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700;900&display=swap');
html, body, [class*="css"], div, p, span, li, ul {{ font-family: "Noto Sans TC", sans-serif; color: #333 !important; }}
.stApp {{ background-color: {BG_MAIN}; }}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {{ display: none; }}
.block-container {{ padding-top: 1rem !important; max-width: 1250px; }}

/* 數據看板：強制純白字 */
.elder-metric-box {{
    padding: 30px; border-radius: 20px; color: #FFFFFF !important; text-align: center; margin-bottom: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}}
.elder-metric-box div, .elder-metric-box span {{ color: #FFFFFF !important; font-weight: 900 !important; }}

/* 下拉選單與輸入框 (白底黑字) */
div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTimeInput input, .stNumberInput input {{
    background-color: #FFFFFF !important; color: #000 !important;
    border: 2px solid #D1D1D1 !important; border-radius: 12px !important; font-weight: 700 !important;
}}
div[data-baseweb="select"] span {{ color: #000 !important; }}

/* 導航按鈕 */
div[data-testid="stButton"] > button {{
    width: 100%; background-color: white !important; color: {ACCENT} !important;
    border: 2px solid {ACCENT} !important; border-radius: 15px !important;
    font-weight: 900 !important; font-size: 1.1rem !important; transition: all 0.2s;
}}
div[data-testid="stButton"] > button:hover {{ background-color: {ACCENT} !important; color: white !important; }}

/* 卡片與名片 */
.custom-card {{ background-color: white; border-radius: 20px; padding: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid white; margin-bottom: 20px; }}
.dash-card {{ background-color: white; padding: 15px; border-radius: 15px; border-left: 6px solid {PRIMARY}; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 10px; }}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2) 資料邏輯
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"
COURSE_HIERARCHY = {
    "手作": ["藝術手作", "生活用品"], "講座": ["消防", "反詐", "道路安全", "環境", "心靈成長", "家庭關係", "健康"],
    "外出": ["觀摩", "出遊"], "延緩失能": ["手作", "料理", "運動", "健康講座"],
    "運動": ["有氧", "毛巾操", "其他運動"], "園藝療癒": ["手作"], "烹飪": ["甜品", "鹹食", "醃漬品"], "歌唱": ["歡唱"]
}
M_COLS = ["姓名", "身分證字號", "性別", "出生年月日", "電話", "地址", "備註", "加入日期"]
L_COLS = ["姓名", "身分證字號", "日期", "時間", "課程分類", "課程名稱", "收縮壓", "舒張壓", "脈搏"]

@st.cache_resource
def get_client(): return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

def load_data(sn):
    try:
        client = get_client(); sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        df = pd.DataFrame(sheet.get_all_records()).astype(str)
        target = M_COLS if sn == 'elderly_members' else L_COLS
        for c in target: 
            if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame(columns=M_COLS if sn == 'elderly_members' else L_COLS)

def save_data(df, sn):
    try:
        df_fix = df.fillna("").replace(['nan', 'NaN', 'nan.0', 'None', '<NA>'], "").astype(str)
        client = get_client(); sheet = client.open_by_key(SHEET_ID).worksheet(sn)
        sheet.clear(); sheet.update([df_fix.columns.values.tolist()] + df_fix.values.tolist())
        load_data.clear(); return True
    except Exception as e: st.error(f"寫入失敗：{e}"); return False

def get_tw_time(): return datetime.now(TW_TZ)

def calculate_age(dob_str):
    try:
        bd = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        today = date.today()
        return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except: return 0

# =========================================================
# 3) UI 渲染
# =========================================================
def render_nav():
    st.markdown('<div style="background:white; padding:12px; border-radius:20px; margin-bottom:20px; box-shadow: 0 2px 15px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🏠 長輩首頁", use_container_width=True): st.session_state.page='home'; st.rerun()
    with c2:
        if st.button("📋 名冊管理", use_container_width=True): st.session_state.page='members'; st.rerun()
    with c3:
        if st.button("🩸 據點報到", use_container_width=True): st.session_state.page='checkin'; st.rerun()
    with c4:
        if st.button("📊 統計數據", use_container_width=True): st.session_state.page='stats'; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 頁面：首頁 ---
if st.session_state.page == 'home':
    if st.button("🚪 回大廳"): st.switch_page("Home.py")
    st.markdown("<h1 style='text-align: center; color: #444;'>福德里 - 關懷據點系統</h1>", unsafe_allow_html=True)
    logs, mems = load_data("elderly_logs"), load_data("elderly_members")
    this_y, t_str = get_tw_time().year, get_tw_time().strftime("%Y-%m-%d")
    y_count = len(logs[pd.to_datetime(logs['日期'], errors='coerce').dt.year == this_y]) if not logs.empty else 0
    t_count = len(logs[logs['日期'] == t_str]) if not logs.empty else 0
    avg_age = round(mems['出生年月日'].apply(calculate_age).mean(), 1) if not mems.empty else 0
    m_c, f_c = len(mems[mems['性別']=='男']), len(mems[mems['性別']=='女'])
    
    c_y, c_t = st.columns(2)
    with c_y: st.markdown(f"""<div class="elder-metric-box" style="background:linear-gradient(135deg,#B5838D 0%,#6D597A 100%);"><div>📅 {this_y} 年度總服務人次</div><div style="font-size:3.5rem;">{y_count}</div></div>""", unsafe_allow_html=True)
    with c_t: st.markdown(f"""<div class="elder-metric-box" style="background:linear-gradient(135deg,#E5989B 0%,#B5838D 100%);"><div>☀️ 今日服務人次</div><div style="font-size:3.5rem;">{t_count}</div></div>""", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"""<div class="dash-card"><div style="color:#666;">平均年齡</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{avg_age} 歲</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="dash-card"><div style="color:#666;">男性長輩</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{m_c} 人</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="dash-card"><div style="color:#666;">女性長輩</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{f_c} 人</div></div>""", unsafe_allow_html=True)

# --- 頁面：據點報到 ---
elif st.session_state.page == 'checkin':
    render_nav()
    st.markdown("## 🩸 據點報到站")
    if 'elder_pid' not in st.session_state: st.session_state.elder_pid = ""
    if 'checkin_msg' not in st.session_state: st.session_state.checkin_msg = (None, None)
    
    st.markdown('<div class="custom-card" style="border-left: 6px solid #E5989B;">', unsafe_allow_html=True)
    st.markdown("#### 1. 設定課程項目與補登時間")
    c1, c2, c3 = st.columns([1.5, 1.5, 2.5])
    with c1: m_cat = st.selectbox("課程大分類", list(COURSE_HIERARCHY.keys()))
    with c2: s_cat = st.selectbox("子分類", COURSE_HIERARCHY[m_cat])
    with c3: c_name = st.text_input("課程名稱 (選填)", placeholder="例如：樂齡肌力訓練")
    st.markdown("---")
    cd1, cd2, cd3 = st.columns([1, 1, 2])
    with cd1: t_date = st.date_input("報到日期", value=get_tw_time().date())
    with cd2: t_time = st.time_input("報到時間", value=get_tw_time().time())
    with cd3:
        if st.session_state.get('sbp_val', 120) >= 140: st.error("⚠️ 注意：目前輸入的血壓偏高 (>140)！")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    ct, cm = st.columns([2, 3]); with ct: st.markdown("#### 2. 長輩掃描報到 (支援條碼槍)")
    with cm:
        mt, mx = st.session_state.checkin_msg
        if mt == "error": st.error(mx)
        elif mt == "success": st.success(mx)

    def process_checkin():
        pid = st.session_state.elder_pid.strip().upper(); if not pid: return
        df_m, df_l = load_data("elderly_members"), load_data("elderly_logs")
        d_s, t_s = t_date.strftime("%Y-%m-%d"), t_time.strftime("%H:%M:%S")
        person = df_m[df_m['身分證字號'] == pid]
        if person.empty: st.session_state.checkin_msg = ("error", "❌ 查無此人")
        else:
            name, final_c = person.iloc[0]['姓名'], (c_name if c_name.strip() else s_cat)
            if not df_l[(df_l['身分證字號']==pid) & (df_l['日期']==d_s) & (df_l['課程名稱']==final_c)].empty:
                st.session_state.checkin_msg = ("error", f"❌ {name} 今日已完成此項報到")
            else:
                new = {"姓名":name,"身分證字號":pid,"日期":d_s,"時間":t_s,"課程分類":f"{m_cat}-{s_cat}","課程名稱":final_c,"收縮壓":st.session_state.sbp_val,"舒張壓":st.session_state.dbp_val,"脈搏":st.session_state.pulse_val}
                if save_data(pd.concat([df_l, pd.DataFrame([new])], ignore_index=True), "elderly_logs"):
                    st.session_state.checkin_msg = ("success", f"✅ {name} 報到成功")
        st.session_state.elder_pid = ""

    cb1, cb2, cb3 = st.columns(3)
    with cb1: st.number_input("收縮壓", 50, 250, 120, key="sbp_val")
    with cb2: st.number_input("舒張壓", 30, 150, 80, key="dbp_val")
    with cb3: st.number_input("脈搏", 30, 200, 72, key="pulse_val")
    st.text_input("身分證掃描區", key="elder_pid", on_change=process_checkin)
    st.markdown('</div>', unsafe_allow_html=True)

    logs_v = load_data("elderly_logs"); d_m = (logs_v['日期'] == t_date.strftime("%Y-%m-%d"))
    if not logs_v[d_m].empty:
        st.markdown(f"### 📋 {t_date.strftime('%Y-%m-%d')} 報到名單")
        edited = st.data_editor(logs_v[d_m].sort_values('時間', ascending=False), use_container_width=True, num_rows="dynamic", key="checkin_edit")
        if st.button("💾 儲存修改"):
            logs_v[d_m] = edited; save_data(logs_v, "elderly_logs"); st.success("已更新！")

# --- 頁面：名冊管理 ---
elif st.session_state.page == 'members':
    render_nav()
    st.markdown("## 📋 長輩名冊管理")
    df = load_data("elderly_members")
    with st.expander("➕ 新增長輩資料"):
        with st.form("add_e"):
            c1, c2, c3 = st.columns(3); n, p, g = c1.text_input("姓名"), c2.text_input("身分證"), c3.selectbox("性別",["男","女"])
            d, ph = st.date_input("生日", value=date(1950,1,1)), st.text_input("電話")
            addr = st.text_input("地址")
            if st.form_submit_button("確認新增"):
                new = pd.DataFrame([{"姓名":n,"身分證字號":p.upper(),"性別":g,"出生年月日":str(d),"電話":ph,"地址":addr,"加入日期":str(date.today())}])
                if save_data(pd.concat([df, new], ignore_index=True), "elderly_members"): st.success("成功"); st.rerun()
    if not df.empty:
        df['年齡'] = df['出生年月日'].apply(calculate_age)
        st.data_editor(df[["姓名","性別","年齡","電話","身分證字號","地址","出生年月日","備註"]], use_container_width=True, num_rows="dynamic", key="m_edit")

# --- 頁面：統計數據 ---
elif st.session_state.page == 'stats':
    render_nav()
    st.markdown("## 📊 數據統計分析")
    mems, logs = load_data("elderly_members"), load_data("elderly_logs")
    if not logs.empty:
        logs['dt'] = pd.to_datetime(logs['日期'], errors='coerce')
        d_range = st.date_input("📅 選擇統計區間", value=(date(date.today().year, date.today().month, 1), date.today()))
        if isinstance(d_range, tuple) and len(d_range) == 2:
            f_logs = logs[(logs['dt'].dt.date >= d_range[0]) & (logs['dt'].dt.date <= d_range[1])].copy()
            t1, t2 = st.tabs(["📚 課程與參與度", "🏥 個案健康追蹤"])
            with t1:
                st.markdown("### 🫧 課程場次占比 (靈動泡泡圖)")
                unique_s = f_logs.drop_duplicates(subset=['日期', '課程名稱']).copy()
                unique_s['大分類'] = unique_s['課程分類'].apply(lambda x: x.split('-')[0] if '-' in x else x)
                m_cts = unique_s['大分類'].value_counts().reset_index(); m_cts.columns = ['類別', '場次']
                random.seed(42); m_cts['x'], m_cts['y'] = [random.uniform(0, 10) for _ in range(len(m_cts))], [random.uniform(0, 10) for _ in range(len(m_cts))]
                m_cts['label'] = m_cts['類別'] + '<br>' + m_cts['場次'].astype(str) + '場'
                fig = px.scatter(m_cts, x="x", y="y", size="場次", color="類別", text="label", size_max=90, color_discrete_sequence=px.colors.sequential.RdPu)
                fig.update_traces(textposition='middle center', textfont=dict(size=14, color='white'))
                fig.update_layout(showlegend=False, height=450, xaxis=dict(showticklabels=False, title=""), yaxis=dict(showticklabels=False, title=""), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### 大分類統計")
                    st.dataframe(m_cts[['類別', '場次']], use_container_width=True, column_config={"場次": st.column_config.ProgressColumn("熱度", format="%d", min_value=0, max_value=int(m_cts['場次'].max() or 1))})
                with c2:
                    sh, ss = st.columns([1.2, 2]); with sh: st.markdown("#### 子分類鑽取")
                    with ss: sel_m = st.selectbox("選擇大分類", sorted(m_cts['類別'].unique()), label_visibility="collapsed", key="s_m_s")
                    s_cts = unique_s[unique_s['大分類']==sel_m]['課程分類'].apply(lambda x: x.split('-')[1] if '-' in x else x).value_counts().reset_index(); s_cts.columns = ['子分類', '場次']
                    st.dataframe(s_cts, use_container_width=True, column_config={"場次": st.column_config.ProgressColumn("場次", format="%d", min_value=0, max_value=int(s_cts['場次'].max() or 1))})
            with t2:
                target = st.selectbox("🔍 選擇長輩查看趨勢", sorted(f_logs['姓名'].unique()))
                e_logs = f_logs[f_logs['姓名']==target].sort_values('dt')
                e_logs['收縮壓'] = pd.to_numeric(e_logs['收縮壓'], errors='coerce')
                e_logs['舒張壓'] = pd.to_numeric(e_logs['舒張壓'], errors='coerce')
                high_bp = len(e_logs[e_logs['收縮壓']>=140])
                st.markdown(f"""<div class="dash-card" style="border-left:6px solid #E91E63"><div style="color:#666;">血壓異常次數 (≥140)</div><div style="font-size:1.8rem;color:{PRIMARY};font-weight:900;">{high_bp} 次</div></div>""", unsafe_allow_html=True)
                fig_h = px.line(e_logs, x='dt', y=['收縮壓', '舒張壓'], markers=True, title=f"{target} 健康趨勢", color_discrete_sequence=[PRIMARY, ACCENT])
                fig_h.add_hline(y=140, line_dash="dash", line_color="#E91E63", annotation_text="高壓警戒")
                st.plotly_chart(fig_h, use_container_width=True)
