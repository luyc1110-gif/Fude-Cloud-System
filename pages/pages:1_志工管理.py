import streamlit as st
import pandas as pd
from datetime import datetime, date
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 設定網頁 ---
st.set_page_config(page_title="志工管理 (雲端版)", page_icon="👤", layout="wide")

# --- 全域變數 ---
ALL_CATEGORIES = ['祥和志工', '關懷據點週二志工', '關懷據點週三志工', '環保志工', '臨時志工']
DEFAULT_ACTIVITIES = ['關懷據點週二活動', '關懷據點週三活動', '環保清潔', '專案活動', '教育訓練']
DISPLAY_ORDER = [
    '姓名', '身分證字號', '性別', '電話', '志工分類', '生日', '地址', '備註',
    '祥和_加入日期', '祥和_退出日期', '據點週二_加入日期', '據點週二_退出日期',
    '據點週三_加入日期', '據點週三_退出日期', '環保_加入日期', '環保_退出日期'
]

# --- ☁️ Google Sheets 連線設定 (核心) ---
# 使用 st.cache_resource 讓連線保持，不用每次操作都重連
@st.cache_resource
def get_google_sheet_client():
    # 從 Streamlit 雲端的 secrets 讀取我們剛剛申請的鑰匙
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client

def load_data_from_sheet(sheet_name):
    try:
        client = get_google_sheet_client()
        # 開啟試算表 'Fude_Database' (請確保您的 Google 試算表名稱是這個)
        sheet = client.open("Fude_Database").worksheet(sheet_name)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # 強制轉為字串避免格式跑掉
        df = df.astype(str)
        
        # 欄位補齊
        if sheet_name == 'members':
            for c in DISPLAY_ORDER:
                if c not in df.columns: df[c] = ""
        elif sheet_name == 'logs':
            required = ['姓名', '身分證字號', '電話', '志工分類', '動作', '時間', '日期', '活動內容']
            for c in required:
                if c not in df.columns: df[c] = ""
                
        return df
    except Exception as e:
        st.error(f"無法讀取 Google 試算表 ({sheet_name})：{e}")
        return pd.DataFrame()

def save_data_to_sheet(df, sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open("Fude_Database").worksheet(sheet_name)
        # 清空舊資料並寫入新資料 (這在資料量小時最安全簡單)
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
    except Exception as e:
        st.error(f"無法寫入 Google 試算表：{e}")

# --- CSS 樣式 ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .block-container { background-color: rgba(255,255,255,0.95); padding: 2rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    [data-testid="stMetricValue"] { color: #2c3e50 !important; }
    .honor-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; text-align: center; }
    .honor-card h1 { color: white; margin: 0; font-size: 2.5rem; }
    </style>
""", unsafe_allow_html=True)

# --- 輔助函數 ---
def check_is_fully_retired(row):
    roles = [('祥和_加入日期', '祥和_退出日期'), ('據點週二_加入日期', '據點週二_退出日期'),
             ('據點週三_加入日期', '據點週三_退出日期'), ('環保_加入日期', '環保_退出日期')]
    is_active = False
    for join_col, exit_col in roles:
        if join_col in row and row[join_col]: 
            if not (exit_col in row and row[exit_col]): is_active = True
    return not is_active 

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{int(hours)}小時 {int(minutes)}分"

def calculate_work_stats(log_df):
    count = log_df['日期'].nunique()
    total_seconds = 0
    for d, day_group in log_df.groupby('日期'):
        day_group = day_group.sort_values('時間')
        actions = day_group['動作'].tolist()
        times = pd.to_datetime(day_group['日期'].astype(str) + ' ' + day_group['時間']).tolist()
        if '簽到' in actions and '簽退' in actions:
            t_in = times[actions.index('簽到')]
            t_out = times[len(actions) - 1 - actions[::-1].index('簽退')]
            if t_out > t_in: total_seconds += (t_out - t_in).total_seconds()
    return count, total_seconds

# --- 側邊欄 ---
with st.sidebar:
    st.title("☁️ 雲端管理")
    page = st.radio("選單", ["智能打卡站", "志工名單管理", "數據報表"])

# --- 頁面邏輯 ---
if page == "智能打卡站":
    st.title("⏰ 智能打卡站 (雲端版)")
    st.info("💡 資料將直接同步至 Google 試算表，手機也可操作。")
    
    if 'scan_cooldowns' not in st.session_state: st.session_state['scan_cooldowns'] = {}

    tab1, tab2 = st.tabs(["即時打卡", "補登/維護"])
    
    with tab1:
        act = st.selectbox("選擇活動", DEFAULT_ACTIVITIES)
        
        def process_scan():
            pid = st.session_state.scan_box.strip().upper()
            if not pid: return
            
            # 防手抖
            now = datetime.now()
            last = st.session_state['scan_cooldowns'].get(pid)
            if last and (now - last).total_seconds() < 120:
                st.session_state.msg = ("warning", "⏳ 兩分鐘內請勿重複刷卡")
                st.session_state.scan_box = ""
                return

            # 讀取 Google Sheet
            df = load_data_from_sheet("members")
            logs = load_data_from_sheet("logs")
            
            person = df[df['身分證字號'] == pid]
            if not person.empty:
                row = person.iloc[0]
                name = row['姓名']
                
                if check_is_fully_retired(row):
                    st.session_state.msg = ("error", f"❌ {name} 已完全退出")
                else:
                    today = now.strftime("%Y-%m-%d")
                    t_logs = logs[(logs['身分證字號'] == pid) & (logs['日期'] == today)]
                    action = "簽到"
                    if not t_logs.empty and t_logs.iloc[-1]['動作'] == "簽到": action = "簽退"
                    
                    new_log = pd.DataFrame([{
                        '姓名': name, '身分證字號': pid, '電話': row['電話'], '志工分類': row['志工分類'],
                        '動作': action, '時間': now.strftime("%H:%M:%S"), '日期': today, '活動內容': act
                    }])
                    save_data_to_sheet(pd.concat([logs, new_log], ignore_index=True), "logs")
                    st.session_state['scan_cooldowns'][pid] = now
                    st.session_state.msg = ("success", f"✅ {name} {action} 成功")
            else:
                st.session_state.msg = ("error", "❌ 查無此人")
            st.session_state.scan_box = ""

        if 'msg' in st.session_state:
            t, m = st.session_state.msg
            if t == "success": st.success(m)
            elif t == "warning": st.warning(m)
            else: st.error(m)
            del st.session_state.msg

        st.text_input("輸入身分證 (Enter)", key="scan_box", on_change=process_scan)

    with tab2:
        st.write("手動補登與維護")
        mode = st.radio("模式", ["單筆補登", "整批補登", "紀錄維護"])
        
        if mode == "單筆補登":
            df = load_data_from_sheet("members")
            sel = st.selectbox("選擇志工", ["請選擇"] + df['姓名'].tolist())
            if sel != "請選擇":
                target = df[df['姓名']==sel].iloc[0]
                with st.form("fix"):
                    d = st.date_input("日期")
                    t = st.time_input("時間")
                    a = st.radio("動作", ["簽到", "簽退"], horizontal=True)
                    if st.form_submit_button("補登"):
                        logs = load_data_from_sheet("logs")
                        new = pd.DataFrame([{
                            '姓名': target['姓名'], '身分證字號': target['身分證字號'], 
                            '電話': target['電話'], '志工分類': target['志工分類'],
                            '動作': a, '時間': t.strftime("%H:%M:%S"), '日期': d.strftime("%Y-%m-%d"), '活動內容': act
                        }])
                        save_data_to_sheet(pd.concat([logs, new], ignore_index=True), "logs")
                        st.success("已補登")
                        
        elif mode == "整批補登":
             st.info("批次掃描功能在雲端版需確保網路穩定")
             # (為節省篇幅，邏輯與上面類似，只是寫入 logs)
             
        elif mode == "紀錄維護":
            logs = load_data_from_sheet("logs")
            edited = st.data_editor(logs, num_rows="dynamic", use_container_width=True)
            if st.button("儲存變更"):
                save_data_to_sheet(edited, "logs")
                st.success("已更新雲端資料庫")

elif page == "志工名單管理":
    st.title("📋 志工名單 (雲端版)")
    df = load_data_from_sheet("members")
    
    with st.expander("新增志工"):
        c1, c2 = st.columns(2)
        n = c1.text_input("姓名")
        p = c2.text_input("身分證")
        cats = st.multiselect("分類", ALL_CATEGORIES)
        if st.button("新增"):
            if not df[df['身分證字號']==p].empty:
                st.error("重複")
            else:
                new = pd.DataFrame([{'姓名':n, '身分證字號':p, '志工分類':",".join(cats)}])
                for c in DISPLAY_ORDER: 
                    if c not in new.columns: new[c] = ""
                save_data_to_sheet(pd.concat([df, new], ignore_index=True), "members")
                st.success("已新增")
    
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("儲存修改"):
        save_data_to_sheet(edited, "members")
        st.success("已同步至 Google 試算表")

elif page == "數據報表":
    st.title("📊 數據報表 (雲端版)")
    logs = load_data_from_sheet("logs")
    
    if not logs.empty:
        # 榮譽榜
        _, total_sec = calculate_work_stats(logs)
        st.markdown(f"""<div class="honor-card"><h3>🏆 累積總時數</h3><h1>{format_time(total_sec)}</h1></div>""", unsafe_allow_html=True)
        st.divider()
        st.dataframe(logs, use_container_width=True)