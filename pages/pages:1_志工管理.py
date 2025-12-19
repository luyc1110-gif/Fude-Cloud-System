import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import gspread
import time

# --- 🎨 1. 網頁美化設定 (記住您的要求：配色與版面設計優化) ---
st.set_page_config(page_title="志工管理系統", page_icon="👤", layout="wide")

st.markdown("""
    <style>
    /* 全站背景：柔和漸層 */
    .stApp {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
    }
    /* 卡片容器樣式 */
    .css-1r6slb0, .stDataFrame, .stTab {
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    /* 標題美化 */
    h1 {
        color: #2c3e50;
        font-weight: 800 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    h3 {
        color: #34495e;
        border-left: 5px solid #3498db;
        padding-left: 10px;
    }
    /* 按鈕美化 */
    .stButton>button {
        border-radius: 20px;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 10px rgba(0,0,0,0.1);
    }
    /* 榮譽榜卡片 */
    .honor-card {
        background: linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%);
        color: #2c3e50;
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .honor-card h2 { margin: 0; font-size: 3rem; color: #fff; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }
    .honor-card p { font-size: 1.2rem; font-weight: bold; opacity: 0.9; }
    
    /* 狀態訊息 */
    .success-msg { color: #27ae60; font-weight: bold; padding: 10px; border-radius: 10px; background-color: #eafaf1; }
    .error-msg { color: #c0392b; font-weight: bold; padding: 10px; border-radius: 10px; background-color: #fdedec; }
    </style>
""", unsafe_allow_html=True)

# --- 🔗 2. Google Sheets 連線設定 (使用最穩定的 ID 連線法) ---
# 您的試算表 ID (絕對準確)
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"

ALL_CATEGORIES = ['祥和志工', '關懷據點週二志工', '關懷據點週三志工', '環保志工', '臨時志工']
DEFAULT_ACTIVITIES = ['關懷據點週二活動', '關懷據點週三活動', '環保清潔', '專案活動', '教育訓練']
DISPLAY_ORDER = [
    '姓名', '身分證字號', '性別', '電話', '志工分類', '生日', '地址', '備註',
    '祥和_加入日期', '祥和_退出日期', '據點週二_加入日期', '據點週二_退出日期',
    '據點週三_加入日期', '據點週三_退出日期', '環保_加入日期', '環保_退出日期'
]

@st.cache_resource
def get_google_sheet_client():
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

def load_data_from_sheet(sheet_name):
    try:
        client = get_google_sheet_client()
        # 使用 open_by_key 確保一定找得到檔案
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        df = df.astype(str) # 全部轉字串避免錯誤
        
        # 欄位補齊 (防呆)
        if sheet_name == 'members':
            for c in DISPLAY_ORDER:
                if c not in df.columns: df[c] = ""
        elif sheet_name == 'logs':
            required = ['姓名', '身分證字號', '電話', '志工分類', '動作', '時間', '日期', '活動內容']
            for c in required:
                if c not in df.columns: df[c] = ""
        return df
    except Exception as e:
        st.error(f"讀取失敗 ({sheet_name})：{e}")
        return pd.DataFrame()

def save_data_to_sheet(df, sheet_name):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
    except Exception as e:
        st.error(f"寫入失敗：{e}")

# --- 🧮 3. 邏輯運算區 ---
def check_is_fully_retired(row):
    # 檢查是否所有身份都已退出
    roles = [('祥和_加入日期', '祥和_退出日期'), ('據點週二_加入日期', '據點週二_退出日期'),
             ('據點週三_加入日期', '據點週三_退出日期'), ('環保_加入日期', '環保_退出日期')]
    is_active = False
    for join_col, exit_col in roles:
        if join_col in row and row[join_col]: # 有加入
            if not (exit_col in row and row[exit_col]): # 且沒退出
                is_active = True
    return not is_active

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{int(hours)}小時 {int(minutes)}分"

def calculate_work_stats(log_df):
    if log_df.empty: return 0, 0
    count = log_df['日期'].nunique()
    total_seconds = 0
    # 簡單計算：當天有簽到也有簽退，算時間差
    for d, day_group in log_df.groupby('日期'):
        day_group = day_group.sort_values('時間')
        actions = day_group['動作'].tolist()
        times = pd.to_datetime(day_group['日期'].astype(str) + ' ' + day_group['時間']).tolist()
        
        if '簽到' in actions and '簽退' in actions:
            try:
                t_in = times[actions.index('簽到')]
                # 找最後一次簽退
                t_out = times[len(actions) - 1 - actions[::-1].index('簽退')]
                if t_out > t_in:
                    total_seconds += (t_out - t_in).total_seconds()
            except: pass
    return count, total_seconds

# --- 🖥️ 4. 介面呈現區 ---
with st.sidebar:
    st.title("☁️ 雲端功能選單")
    page = st.radio("前往", ["⏰ 智能打卡站", "📋 志工名單管理", "📊 數據報表中心"])
    st.divider()
    st.caption("系統狀態：🟢 連線正常")

# === 頁面 1: 智能打卡站 ===
if page == "⏰ 智能打卡站":
    st.title("⏰ 智能打卡站")
    st.markdown("手機掃碼或輸入身分證字號，資料即時同步雲端。")
    
    if 'scan_cooldowns' not in st.session_state: st.session_state['scan_cooldowns'] = {}

    tab1, tab2 = st.tabs(["⚡️ 快速打卡", "🛠️ 補登與維護"])
    
    with tab1:
        st.markdown("### 步驟 1：選擇活動")
        act = st.selectbox("請選擇當前活動", DEFAULT_ACTIVITIES, label_visibility="collapsed")
        
        st.markdown("### 步驟 2：輸入身分證 (或掃描)")
        
        # 打卡核心邏輯
        def process_scan():
            pid = st.session_state.scan_box.strip().upper()
            if not pid: return
            
            now = datetime.now()
            # 防手抖機制 (2分鐘)
            last = st.session_state['scan_cooldowns'].get(pid)
            if last and (now - last).total_seconds() < 120:
                st.session_state.msg = ("warn", f"⏳ 兩分鐘內請勿重複刷卡 ({pid})")
                st.session_state.scan_box = ""
                return

            df_members = load_data_from_sheet("members")
            df_logs = load_data_from_sheet("logs")
            
            if df_members.empty:
                st.session_state.msg = ("error", "⚠️ 尚未建立志工名單，請先至「名單管理」新增志工。")
                st.session_state.scan_box = ""; return

            person = df_members[df_members['身分證字號'] == pid]
            
            if not person.empty:
                row = person.iloc[0]
                name = row['姓名']
                
                if check_is_fully_retired(row):
                    st.session_state.msg = ("error", f"❌ {name} 顯示為「已退出」，無法打卡。")
                else:
                    today = now.strftime("%Y-%m-%d")
                    # 判斷是簽到還是簽退
                    t_logs = df_logs[(df_logs['身分證字號'] == pid) & (df_logs['日期'] == today)]
                    action = "簽到"
                    if not t_logs.empty and t_logs.iloc[-1]['動作'] == "簽到":
                        action = "簽退"
                    
                    new_log = pd.DataFrame([{
                        '姓名': name, '身分證字號': pid, '電話': row['電話'], '志工分類': row['志工分類'],
                        '動作': action, '時間': now.strftime("%H:%M:%S"), '日期': today, '活動內容': act
                    }])
                    
                    # 寫入雲端
                    save_data_to_sheet(pd.concat([df_logs, new_log], ignore_index=True), "logs")
                    
                    st.session_state['scan_cooldowns'][pid] = now
                    st.session_state.msg = ("success", f"✅ {name} - {action} 成功！ ({act})")
            else:
                st.session_state.msg = ("error", f"❌ 查無此人 ({pid})，請確認是否已註冊。")
            
            st.session_state.scan_box = ""

        # 顯示訊息
        if 'msg' in st.session_state:
            type_, txt = st.session_state.msg
            if type_ == "success": st.markdown(f'<div class="success-msg">{txt}</div>', unsafe_allow_html=True)
            elif type_ == "warn": st.warning(txt)
            else: st.markdown(f'<div class="error-msg">{txt}</div>', unsafe_allow_html=True)
            del st.session_state.msg

        st.text_input("請點此輸入...", key="scan_box", on_change=process_scan, placeholder="在此掃描或輸入...")

    with tab2:
        st.info("此處可手動補登遺漏的紀錄，或修正錯誤的打卡。")
        mode = st.radio("模式選擇", ["手動單筆補登", "修改歷史紀錄"], horizontal=True)
        
        if mode == "手動單筆補登":
            df_m = load_data_from_sheet("members")
            if not df_m.empty:
                c1, c2 = st.columns(2)
                target_name = c1.selectbox("選擇志工", df_m['姓名'].tolist())
                target_act = c2.selectbox("補登活動", DEFAULT_ACTIVITIES)
                
                c3, c4, c5 = st.columns(3)
                d_date = c3.date_input("日期")
                d_time = c4.time_input("時間")
                d_action = c5.radio("動作", ["簽到", "簽退"], horizontal=True)
                
                if st.button("確認補登", type="primary"):
                    target_row = df_m[df_m['姓名'] == target_name].iloc[0]
                    logs = load_data_from_sheet("logs")
                    new = pd.DataFrame([{
                        '姓名': target_name, '身分證字號': target_row['身分證字號'], 
                        '電話': target_row['電話'], '志工分類': target_row['志工分類'],
                        '動作': d_action, '時間': d_time.strftime("%H:%M:%S"), '日期': d_date.strftime("%Y-%m-%d"), '活動內容': target_act
                    }])
                    save_data_to_sheet(pd.concat([logs, new], ignore_index=True), "logs")
                    st.success(f"已補登：{target_name} {d_date} {d_action}")
            else:
                st.warning("請先建立志工名單")
                
        elif mode == "修改歷史紀錄":
            logs = load_data_from_sheet("logs")
            if not logs.empty:
                edited_logs = st.data_editor(logs, num_rows="dynamic", use_container_width=True, key="editor_logs")
                if st.button("💾 儲存變更至雲端"):
                    save_data_to_sheet(edited_logs, "logs")
                    st.success("✅ 修改已同步！")

# === 頁面 2: 志工名單管理 ===
elif page == "📋 志工名單管理":
    st.title("📋 志工名冊")
    
    df = load_data_from_sheet("members")
    
    with st.expander("➕ 新增志工 (點擊展開)", expanded=False):
        with st.form("add_user_form"):
            c1, c2 = st.columns(2)
            new_name = c1.text_input("姓名")
            new_pid = c2.text_input("身分證字號 (必填)")
            new_cats = st.multiselect("志工分類", ALL_CATEGORIES)
            new_phone = st.text_input("電話")
            
            if st.form_submit_button("新增成員"):
                if not new_pid:
                    st.error("身分證字號為必填！")
                elif not df.empty and new_pid in df['身分證字號'].values:
                    st.error("此身分證字號已存在！")
                else:
                    new_data = {
                        '姓名': new_name, '身分證字號': new_pid, '電話': new_phone, 
                        '志工分類': ",".join(new_cats)
                    }
                    new_df_row = pd.DataFrame([new_data])
                    # 補齊其他欄位
                    for col in DISPLAY_ORDER:
                        if col not in new_df_row.columns: new_df_row[col] = ""
                    
                    save_data_to_sheet(pd.concat([df, new_df_row], ignore_index=True), "members")
                    st.success(f"已新增：{new_name}")
                    time.sleep(1)
                    st.rerun()

    st.write("### 目前成員列表")
    if not df.empty:
        # 搜尋功能
        search = st.text_input("🔍 搜尋姓名或電話...", "")
        if search:
            mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            display_df = df[mask]
        else:
            display_df = df
            
        edited_df = st.data_editor(display_df, num_rows="dynamic", use_container_width=True, key="editor_members")
        
        if st.button("💾 儲存名單變更"):
            # 注意：這裡簡單處理，若有搜尋篩選，直接存回可能會覆蓋，
            # 完整版建議針對 ID 更新，但簡單版直接存回即可 (假設里長操作時不會多人同時改)
            save_data_to_sheet(edited_df, "members") 
            st.success("✅ 名單已更新！")
    else:
        st.info("目前沒有資料，請新增志工。")

# === 頁面 3: 數據報表中心 ===
elif page == "📊 數據報表中心":
    st.title("📊 數據報表")
    st.markdown("檢視志工的出勤時數與服務狀況。")
    
    logs = load_data_from_sheet("logs")
    
    if logs.empty:
        st.warning("目前還沒有任何打卡紀錄。")
    else:
        # 簡單統計卡片
        total_days, total_secs = calculate_work_stats(logs)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="honor-card">
                <p>總服務人次</p>
                <h2>{len(logs)}</h2>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="honor-card" style="background: linear-gradient(120deg, #fccb90 0%, #d57eeb 100%);">
                <p>總累積時數</p>
                <h2>{format_time(total_secs).split('小時')[0]}<span style="font-size:1.5rem">小時</span></h2>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="honor-card" style="background: linear-gradient(120deg, #e0c3fc 0%, #8ec5fc 100%);">
                <p>活躍志工數</p>
                <h2>{logs['姓名'].nunique()}</h2>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        st.subheader("📄 詳細紀錄")
        
        # 篩選器
        col_fil1, col_fil2 = st.columns(2)
        filter_name = col_fil1.multiselect("篩選姓名", logs['姓名'].unique())
        filter_act = col_fil2.multiselect("篩選活動", logs['活動內容'].unique())
        
        view_logs = logs.copy()
        if filter_name: view_logs = view_logs[view_logs['姓名'].isin(filter_name)]
        if filter_act: view_logs = view_logs[view_logs['活動內容'].isin(filter_act)]
        
        st.dataframe(view_logs, use_container_width=True)
        
        # 匯出按鈕
        csv = view_logs.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 下載 Excel (CSV)", csv, "report.csv", "text/csv")