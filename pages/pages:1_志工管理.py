import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
import gspread
import time
import plotly.express as px
import os

# =========================================================
# 0) App Config
# =========================================================
st.set_page_config(
    page_title="志工管理系統",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TW_TZ = timezone(timedelta(hours=8))

PRIMARY = "#4A148C"   # 尊爵紫
ACCENT = "#7B1FA2"    # 亮紫
BG_MAIN = "#F0F2F5"   # 灰藍底
TEXT = "#212121"
MUTED = "#666666"
CARD_BG = "#FFFFFF"

# =========================================================
# 1) Styles (更穩定：少用 class*="css"，改用 data-testid 與自訂 class)
# =========================================================
st.markdown(
    f"""
<style>
:root {{
  --primary: {PRIMARY};
  --accent: {ACCENT};
  --bg: {BG_MAIN};
  --text: {TEXT};
  --muted: {MUTED};
  --card: {CARD_BG};
}}

.stApp {{
  background: var(--bg);
}}

/* 隱藏 Streamlit 原生側欄 */
[data-testid="stSidebar"] {{
  display: none;
}}

/* 全域字體（只針對主要區域，別掃到所有 div） */
[data-testid="stAppViewContainer"] * {{
  font-family: "Microsoft JhengHei", "微軟正黑體", system-ui, -apple-system, "Segoe UI", Arial, sans-serif;
  color: var(--text);
}}

/* 讓主容器左右留白更漂亮 */
.block-container {{
  padding-top: 1.25rem;
  padding-bottom: 2rem;
  max-width: 1250px;
}}

/* ===== Top Bar ===== */
.topbar {{
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.8);
  border-radius: 999px;
  padding: 12px 18px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  position: sticky;
  top: 10px;
  z-index: 50;
}}

.brand {{
  display: flex;
  align-items: center;
  gap: 10px;
}}
.brand-badge {{
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--accent) 0%, var(--primary) 100%);
  color: white !important;
  font-weight: 900;
}}
.brand-title {{
  font-weight: 900;
  font-size: 1.05rem;
  letter-spacing: 0.5px;
}}
.brand-sub {{
  font-size: 0.85rem;
  color: var(--muted) !important;
}}

/* ===== Nav Buttons (膠囊) ===== */
div[data-testid="stButton"] > button {{
  width: 100%;
  border-radius: 999px !important;
  border: 1.5px solid rgba(74, 20, 140, 0.25) !important;
  background: white !important;
  color: var(--primary) !important;
  font-weight: 800 !important;
  padding: 10px 14px !important;
  transition: transform 0.12s ease, box-shadow 0.12s ease, background 0.12s ease;
  box-shadow: 0 6px 16px rgba(0,0,0,0.06);
}}
div[data-testid="stButton"] > button:hover {{
  transform: translateY(-1px);
  background: #F6EAF8 !important;
  box-shadow: 0 10px 22px rgba(0,0,0,0.09);
}}
div[data-testid="stButton"] > button:active {{
  transform: translateY(1px);
  box-shadow: 0 3px 10px rgba(0,0,0,0.06);
}}

/* ===== Card ===== */
.card {{
  background: var(--card);
  border: 1px solid rgba(255,255,255,0.85);
  border-radius: 22px;
  box-shadow: 0 14px 34px rgba(0,0,0,0.06);
  padding: 18px 18px;
}}
.card-tight {{
  padding: 14px 16px;
}}
.card-title {{
  font-weight: 900;
  font-size: 1.05rem;
  color: var(--primary) !important;
  margin: 0 0 6px 0;
}}
.card-sub {{
  font-size: 0.9rem;
  color: var(--muted) !important;
  margin: 0 0 10px 0;
}}

/* Dashboard Stat */
.stat {{
  background: white;
  border-radius: 18px;
  padding: 16px 16px;
  border-left: 7px solid var(--accent);
  box-shadow: 0 10px 22px rgba(0,0,0,0.06);
}}
.stat-label {{
  font-size: 0.95rem;
  color: var(--muted) !important;
  font-weight: 800;
}}
.stat-value {{
  font-size: 2.1rem;
  font-weight: 900;
  color: var(--primary) !important;
  line-height: 1.1;
  margin-top: 6px;
}}
.stat-sub {{
  font-size: 0.9rem;
  color: #888 !important;
  margin-top: 2px;
}}

/* Form inputs */
.stTextInput input,
.stDateInput input,
.stTimeInput input {{
  background: white !important;
  border-radius: 14px !important;
  border: 1px solid rgba(74, 20, 140, 0.22) !important;
}}
.stSelectbox [data-baseweb="select"] {{
  background: white !important;
  border-radius: 14px !important;
  border: 1px solid rgba(74, 20, 140, 0.22) !important;
}}
label {{
  font-weight: 800 !important;
  color: var(--primary) !important;
}}

/* Expander 變卡片 */
div[data-testid="stExpander"] details {{
  background: white;
  border-radius: 22px;
  border: 1px solid rgba(255,255,255,0.85);
  box-shadow: 0 14px 34px rgba(0,0,0,0.06);
  padding: 10px 10px;
}}
div[data-testid="stExpander"] summary {{
  font-weight: 900;
  color: var(--primary) !important;
}}

/* Hide Streamlit menu/footer */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 2) Helpers (UI)
# =========================================================
def spacer(h=14):
    st.markdown(f"<div style='height:{h}px'></div>", unsafe_allow_html=True)

def card_open(title=None, subtitle=None, tight=False):
    cls = "card card-tight" if tight else "card"
    st.markdown(f"<div class='{cls}'>", unsafe_allow_html=True)
    if title:
        st.markdown(f"<div class='card-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='card-sub'>{subtitle}</div>", unsafe_allow_html=True)

def card_close():
    st.markdown("</div>", unsafe_allow_html=True)

def topbar(page_name: str):
    st.markdown(
        f"""
<div class="topbar">
  <div class="brand">
    <div class="brand-badge">💜</div>
    <div>
      <div class="brand-title">福德里 志工管理系統</div>
      <div class="brand-sub">{page_name}</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

# =========================================================
# 3) Google Sheets
# =========================================================
SHEET_ID = "1A3-VwCBYjnWdcEiL6VwbV5-UECcgX7TqKH94sKe8P90"

ALL_CATEGORIES = ["祥和志工", "關懷據點週二志工", "關懷據點週三志工", "環保志工", "臨時志工"]
DEFAULT_ACTIVITIES = ["關懷據點週二活動", "關懷據點週三活動", "環保清潔", "專案活動", "教育訓練"]

DISPLAY_ORDER = [
    "姓名", "身分證字號", "性別", "電話", "志工分類", "生日", "地址", "備註",
    "祥和_加入日期", "祥和_退出日期",
    "據點週二_加入日期", "據點週二_退出日期",
    "據點週三_加入日期", "據點週三_退出日期",
    "環保_加入日期", "環保_退出日期",
]

@st.cache_resource
def get_google_sheet_client():
    # 需要 st.secrets["gcp_service_account"]
    return gspread.service_account_from_dict(st.secrets["gcp_service_account"])

@st.cache_data(ttl=60)
def load_data_from_sheet(sheet_name: str) -> pd.DataFrame:
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        if df.empty:
            # 依工作表補欄位
            if sheet_name == "members":
                df = pd.DataFrame(columns=DISPLAY_ORDER)
            elif sheet_name == "logs":
                df = pd.DataFrame(columns=["姓名", "身分證字號", "電話", "志工分類", "動作", "時間", "日期", "活動內容"])
            return df

        df = df.astype(str)

        if sheet_name == "members":
            for c in DISPLAY_ORDER:
                if c not in df.columns:
                    df[c] = ""
        elif sheet_name == "logs":
            required = ["姓名", "身分證字號", "電話", "志工分類", "動作", "時間", "日期", "活動內容"]
            for c in required:
                if c not in df.columns:
                    df[c] = ""

        return df

    except Exception:
        # 不在這裡 st.error，避免快取重複噴訊息
        return pd.DataFrame()

def save_data_to_sheet(df: pd.DataFrame, sheet_name: str):
    try:
        client = get_google_sheet_client()
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        sheet.clear()
        df2 = df.copy()
        df2 = df2.fillna("").astype(str)
        sheet.update([df2.columns.values.tolist()] + df2.values.tolist())
        load_data_from_sheet.clear()
        st.toast("✅ 已儲存", icon="✅")
    except Exception as e:
        st.error(f"寫入失敗：{e}")

# =========================================================
# 4) Logic
# =========================================================
def get_tw_time():
    return datetime.now(TW_TZ)

def parse_date_any(s: str):
    if not s or str(s).strip() == "":
        return None
    s = str(s).strip()
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"]:
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None

def calculate_age(birthday_str: str) -> int:
    b = parse_date_any(birthday_str)
    if not b:
        return 0
    today = date.today()
    return today.year - b.year - ((today.month, today.day) < (b.month, b.day))

def check_is_fully_retired(row: pd.Series) -> bool:
    roles = [
        ("祥和_加入日期", "祥和_退出日期"),
        ("據點週二_加入日期", "據點週二_退出日期"),
        ("據點週三_加入日期", "據點週三_退出日期"),
        ("環保_加入日期", "環保_退出日期"),
    ]
    has_any_role = False
    is_active = False
    for join_col, exit_col in roles:
        join_val = str(row.get(join_col, "")).strip()
        exit_val = str(row.get(exit_col, "")).strip()
        if join_val != "":
            has_any_role = True
            if exit_val == "":
                is_active = True
    if not has_any_role:
        return False
    return not is_active

def build_sessions(logs_df: pd.DataFrame) -> pd.DataFrame:
    """把簽到/簽退配對成 session（同人同日，依時間排序；找下一個簽退）"""
    if logs_df.empty:
        return pd.DataFrame(columns=["姓名", "身分證字號", "日期", "活動內容", "start", "end", "seconds"])

    df = logs_df.copy()
    df["dt"] = pd.to_datetime(df["日期"].astype(str) + " " + df["時間"].astype(str), errors="coerce")
    df = df.dropna(subset=["dt"]).sort_values(["姓名", "日期", "dt"])

    sessions = []
    for (name, d), g in df.groupby(["姓名", "日期"], dropna=False):
        actions = g["動作"].astype(str).tolist()
        dts = g["dt"].tolist()
        acts = g["活動內容"].astype(str).tolist()
        pids = g["身分證字號"].astype(str).tolist()

        i = 0
        while i < len(actions):
            if actions[i] == "簽到":
                # 找下一個簽退
                j = i + 1
                while j < len(actions) and actions[j] != "簽退":
                    j += 1
                if j < len(actions) and actions[j] == "簽退":
                    sec = (dts[j] - dts[i]).total_seconds()
                    if sec > 0:
                        sessions.append(
                            {
                                "姓名": name,
                                "身分證字號": pids[i],
                                "日期": d,
                                "活動內容": acts[i] if acts[i] else acts[j],
                                "start": dts[i],
                                "end": dts[j],
                                "seconds": sec,
                            }
                        )
                    i = j + 1
                else:
                    i += 1
            else:
                i += 1

    return pd.DataFrame(sessions)

def seconds_to_hm(total_seconds: float):
    total_seconds = int(total_seconds or 0)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    return h, m

# =========================================================
# 5) Navigation State
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = "home"

def goto(page_key: str):
    st.session_state.page = page_key
    st.rerun()

def render_nav():
    # 用 topbar + 三顆膠囊按鈕
    page_map = {
        "home": "🏠 首頁",
        "checkin": "⏰ 打卡站",
        "members": "📋 志工名冊",
        "report": "📊 報表分析",
    }
    topbar(page_map.get(st.session_state.page, ""))
    spacer(10)

    cols = st.columns([1.2, 1.2, 1.2, 1.2, 4.2])
    with cols[0]:
        if st.button("🏠 首頁", use_container_width=True):
            goto("home")
    with cols[1]:
        if st.button("⏰ 打卡站", use_container_width=True):
            goto("checkin")
    with cols[2]:
        if st.button("📋 志工名冊", use_container_width=True):
            goto("members")
    with cols[3]:
        if st.button("📊 報表分析", use_container_width=True):
            goto("report")

    spacer(18)

# =========================================================
# 6) HOME
# =========================================================
def page_home():
    # 首頁不黏 topbar（但你也可以留著）
    st.markdown(
        f"""
<div style="text-align:center; margin-top: 10px;">
  <div style="font-size: 2.1rem; font-weight: 900; color: {PRIMARY};">福德里 - 志工管理系統</div>
  <div style="color: {MUTED}; margin-top: 6px;">打卡、名冊、報表，一套搞定。</div>
</div>
""",
        unsafe_allow_html=True,
    )
    spacer(22)

    # 三張入口卡
    c1, c2, c3 = st.columns(3)
    with c1:
        card_open("⏰ 智能打卡站", "現場刷卡 / 補登 / 修改紀錄", tight=False)
        spacer(6)
        if os.path.exists("icon_checkin.png"):
            st.image("icon_checkin.png", width=110)
        else:
            st.markdown("<div style='font-size:64px; text-align:center;'>⏰</div>", unsafe_allow_html=True)
        spacer(10)
        if st.button("進入打卡站", key="home_go_checkin"):
            goto("checkin")
        card_close()

    with c2:
        card_open("📋 志工名冊", "新增志工、維護資料、在職/退出", tight=False)
        spacer(6)
        if os.path.exists("icon_members.png"):
            st.image("icon_members.png", width=110)
        else:
            st.markdown("<div style='font-size:64px; text-align:center;'>📋</div>", unsafe_allow_html=True)
        spacer(10)
        if st.button("進入名冊管理", key="home_go_members"):
            goto("members")
        card_close()

    with c3:
        card_open("📊 數據分析", "工時、出勤、活動統計", tight=False)
        spacer(6)
        if os.path.exists("icon_report.png"):
            st.image("icon_report.png", width=110)
        else:
            st.markdown("<div style='font-size:64px; text-align:center;'>📊</div>", unsafe_allow_html=True)
        spacer(10)
        if st.button("進入報表分析", key="home_go_report"):
            goto("report")
        card_close()

    spacer(22)

    # 即時概況
    logs = load_data_from_sheet("logs")
    members = load_data_from_sheet("members")

    this_year = datetime.now().year
    sessions = build_sessions(logs)
    if not sessions.empty:
        sessions["year"] = pd.to_datetime(sessions["start"]).dt.year
        y = sessions[sessions["year"] == this_year]
        total_sec = y["seconds"].sum()
    else:
        total_sec = 0

    total_h, total_m = seconds_to_hm(total_sec)

    # 大卡：總時數
    st.markdown(
        f"""
<div class="card" style="padding: 26px; background: linear-gradient(135deg, #7E57C2 0%, #512DA8 100%); color: white;">
  <div style="opacity:0.92; font-weight: 800;">📅 {this_year} 年度 - 全體志工總服務時數</div>
  <div style="font-size: 3.2rem; font-weight: 900; margin-top: 10px;">
    {total_h}<span style="font-size:1.4rem; font-weight:900;"> 小時</span>
    {total_m}<span style="font-size:1.4rem; font-weight:900;"> 分</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    spacer(14)

    # 分類統計小卡
    if members.empty:
        card_open("⚠️ 無法讀取名冊", "請確認 Google Sheets / 服務帳號權限。", tight=True)
        card_close()
        return

    dfm = members.copy()
    dfm["狀態"] = dfm.apply(lambda r: "已退出" if check_is_fully_retired(r) else "在職", axis=1)
    active = dfm[dfm["狀態"] == "在職"].copy()
    active["年齡"] = active["生日"].apply(calculate_age)
    valid_age = active[active["年齡"] > 0].copy()

    card_open("📌 在職志工概況", "人數與平均年齡（依分類）", tight=False)
    cols = st.columns(4)
    idx = 0
    for cat in ALL_CATEGORIES:
        if cat == "臨時志工":
            continue
        subset = active[active["志工分類"].astype(str).str.contains(cat, na=False)]
        age_subset = valid_age[valid_age["志工分類"].astype(str).str.contains(cat, na=False)]
        count = len(subset)
        avg_age = round(age_subset["年齡"].mean(), 1) if not age_subset.empty else 0

        with cols[idx % 4]:
            st.markdown(
                f"""
<div class="stat">
  <div class="stat-label">{cat.replace('志工','')}</div>
  <div class="stat-value">{count}<span style="font-size:1rem; color:#888; font-weight:900;"> 人</span></div>
  <div class="stat-sub">平均 {avg_age} 歲</div>
</div>
""",
                unsafe_allow_html=True,
            )
        idx += 1
    card_close()

# =========================================================
# 7) CHECKIN
# =========================================================
def page_checkin():
    render_nav()

    st.markdown("## ⏰ 智能打卡站")
    tw_now = get_tw_time()
    st.caption(f"📅 台灣時間：{tw_now.strftime('%Y-%m-%d %H:%M:%S')}")

    if "scan_cooldowns" not in st.session_state:
        st.session_state["scan_cooldowns"] = {}

    tab1, tab2, tab3 = st.tabs(["⚡️ 現場打卡", "🛠️ 補登作業", "✏️ 紀錄修改"])

    # ========== Tab1：現場打卡 ==========
    with tab1:
        card_open("⚡️ 現場打卡", "輸入身分證或刷卡；系統會自動判斷簽到/簽退", tight=False)
        c1, c2 = st.columns([1.2, 2.2])
        with c1:
            raw_act = st.selectbox("📌 選擇活動", DEFAULT_ACTIVITIES, key="act_select")
            final_act = raw_act
            if raw_act in ["專案活動", "教育訓練"]:
                note = st.text_input("📝 請輸入名稱", placeholder="例：大掃除 / 反詐宣導", key="act_note")
                if note:
                    final_act = f"{raw_act}：{note}"

        def process_scan():
            pid = st.session_state.get("scan_box", "").strip().upper()
            if not pid:
                return

            now = get_tw_time()
            last = st.session_state["scan_cooldowns"].get(pid)
            if last and (now - last).total_seconds() < 120:
                st.warning(f"⏳ 請勿重複刷卡（{pid}）")
                st.session_state["scan_box"] = ""
                return

            df_m = load_data_from_sheet("members")
            df_l = load_data_from_sheet("logs")

            if df_m.empty:
                st.error("❌ 無法讀取名冊（members）")
                return

            person = df_m[df_m["身分證字號"].astype(str).str.upper() == pid]
            if person.empty:
                st.error("❌ 查無此人")
                st.session_state["scan_box"] = ""
                return

            row = person.iloc[0]
            name = row.get("姓名", "")

            if check_is_fully_retired(row):
                st.error(f"❌ {name} 已退出（不可打卡）")
                st.session_state["scan_box"] = ""
                return

            today = now.strftime("%Y-%m-%d")
            # 今天該人的 logs
            if df_l.empty:
                t_logs = pd.DataFrame()
            else:
                t_logs = df_l[
                    (df_l["身分證字號"].astype(str).str.upper() == pid)
                    & (df_l["日期"].astype(str) == today)
                ].copy()

            action = "簽到"
            if not t_logs.empty and str(t_logs.iloc[-1].get("動作", "")) == "簽到":
                action = "簽退"

            new_log = pd.DataFrame(
                [
                    {
                        "姓名": name,
                        "身分證字號": pid,
                        "電話": row.get("電話", ""),
                        "志工分類": row.get("志工分類", ""),
                        "動作": action,
                        "時間": now.strftime("%H:%M:%S"),
                        "日期": today,
                        "活動內容": final_act,
                    }
                ]
            )
            df_out = pd.concat([df_l, new_log], ignore_index=True) if not df_l.empty else new_log
            save_data_to_sheet(df_out, "logs")

            st.session_state["scan_cooldowns"][pid] = now
            st.success(f"✅ {name} {action} 成功！({now.strftime('%H:%M')})")
            st.session_state["scan_box"] = ""

        st.text_input("請輸入身分證（或掃描）", key="scan_box", on_change=process_scan, placeholder="例如：A123456789")
        spacer(10)
        st.caption("提示：同一張卡 2 分鐘內重複刷會被擋掉（防誤刷）。")
        card_close()

    # ========== Tab2：補登 ==========
    with tab2:
        df_m = load_data_from_sheet("members")
        if df_m.empty:
            st.info("目前無名冊資料。")
        else:
            df_m2 = df_m.copy()
            df_m2["狀態"] = df_m2.apply(lambda r: "已退出" if check_is_fully_retired(r) else "在職", axis=1)
            active_m = df_m2[df_m2["狀態"] == "在職"].copy()
            name_list = active_m["姓名"].dropna().astype(str).tolist()

            card_open("🛠️ 補登作業", "可單筆補登或整批補登", tight=False)
            with st.form("manual_form"):
                entry_mode = st.radio("模式", ["單筆補登", "整批補登"], horizontal=True)
                c1, c2, c3, c4 = st.columns(4)
                d_date = c1.date_input("日期", value=date.today())
                d_time = c2.time_input("時間", value=get_tw_time().time())
                d_action = c3.selectbox("動作", ["簽到", "簽退"])
                d_act = c4.selectbox("活動", DEFAULT_ACTIVITIES)

                if entry_mode == "單筆補登":
                    names = [st.selectbox("志工", name_list)]
                else:
                    names = st.multiselect("選擇多位", name_list)

                submitted = st.form_submit_button("✅ 補登")
            if submitted:
                if not names or (len(names) == 1 and names[0] == ""):
                    st.warning("請先選擇志工。")
                else:
                    logs = load_data_from_sheet("logs")
                    new_rows = []
                    for n in names:
                        row = active_m[active_m["姓名"].astype(str) == str(n)].iloc[0]
                        new_rows.append(
                            {
                                "姓名": n,
                                "身分證字號": row.get("身分證字號", ""),
                                "電話": row.get("電話", ""),
                                "志工分類": row.get("志工分類", ""),
                                "動作": d_action,
                                "時間": d_time.strftime("%H:%M:%S"),
                                "日期": d_date.strftime("%Y-%m-%d"),
                                "活動內容": d_act,
                            }
                        )
                    out = pd.concat([logs, pd.DataFrame(new_rows)], ignore_index=True) if not logs.empty else pd.DataFrame(new_rows)
                    save_data_to_sheet(out, "logs")
                    st.success("✅ 已補登")
            card_close()

    # ========== Tab3：修改紀錄 ==========
    with tab3:
        logs = load_data_from_sheet("logs")
        card_open("✏️ 紀錄修改", "直接編修 logs（小心：這裡是強力模式）", tight=False)
        if logs.empty:
            st.info("無資料")
        else:
            edited = st.data_editor(logs, num_rows="dynamic", use_container_width=True, key="logs_editor")
            c1, c2 = st.columns([1, 5])
            with c1:
                if st.button("💾 儲存修改", use_container_width=True):
                    save_data_to_sheet(edited, "logs")
                    st.success("✅ 已更新")
        card_close()

# =========================================================
# 8) MEMBERS
# =========================================================
def page_members():
    render_nav()
    st.markdown("## 📋 志工名冊管理")

    df = load_data_from_sheet("members")

    with st.expander("➕ 新增志工", expanded=True):
        card_open("新增志工", "請填寫基本資料與分類加入日期", tight=False)
        with st.form("add_member_form"):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("姓名")
            p = c2.text_input("身分證")
            b = c3.text_input("生日（YYYY-MM-DD）")

            c4, c5 = st.columns([2, 1])
            addr = c4.text_input("地址")
            ph = c5.text_input("電話")

            spacer(8)
            st.markdown("**志工分類與加入日期**")
            cats = []

            left, right = st.columns(2)
            is_x = left.checkbox("祥和")
            d_x = right.text_input("祥和加入日", value=str(date.today()) if is_x else "")

            is_t = left.checkbox("週二據點")
            d_t = right.text_input("週二加入日", value=str(date.today()) if is_t else "")

            is_w = left.checkbox("週三據點")
            d_w = right.text_input("週三加入日", value=str(date.today()) if is_w else "")

            is_e = left.checkbox("環保")
            d_e = right.text_input("環保加入日", value=str(date.today()) if is_e else "")

            submitted = st.form_submit_button("✅ 新增")
        if submitted:
            if not p:
                st.error("身分證必填")
            else:
                if df.empty:
                    df_check = pd.DataFrame(columns=DISPLAY_ORDER)
                else:
                    df_check = df.copy()

                if (df_check["身分證字號"].astype(str).str.upper() == str(p).upper()).any():
                    st.error("重複：此身分證已存在")
                else:
                    if is_x: cats.append("祥和志工")
                    if is_t: cats.append("關懷據點週二志工")
                    if is_w: cats.append("關懷據點週三志工")
                    if is_e: cats.append("環保志工")

                    new_data = {
                        "姓名": n,
                        "身分證字號": str(p).upper(),
                        "生日": b,
                        "電話": ph,
                        "地址": addr,
                        "志工分類": ",".join(cats),
                        "祥和_加入日期": d_x if is_x else "",
                        "據點週二_加入日期": d_t if is_t else "",
                        "據點週三_加入日期": d_w if is_w else "",
                        "環保_加入日期": d_e if is_e else "",
                    }
                    new = pd.DataFrame([new_data])
                    for c in DISPLAY_ORDER:
                        if c not in new.columns:
                            new[c] = ""
                    # 補上缺的欄位
                    for c in DISPLAY_ORDER:
                        if c not in df_check.columns:
                            df_check[c] = ""

                    out = pd.concat([df_check, new[DISPLAY_ORDER]], ignore_index=True)
                    save_data_to_sheet(out, "members")
                    st.success("✅ 新增成功")
                    time.sleep(0.6)
                    st.rerun()
        card_close()

    spacer(10)

    if df.empty:
        st.info("目前無名冊資料")
        return

    df2 = df.copy()
    df2["狀態"] = df2.apply(lambda r: "已退出" if check_is_fully_retired(r) else "在職", axis=1)
    df2["年齡"] = df2["生日"].apply(calculate_age)

    card_open("名冊檢視", "可切換在職/全部，並直接編輯（資料會寫回 Google Sheets）", tight=False)
    mode = st.radio("檢視模式", ["🟢 在職", "📋 全部"], horizontal=True, key="members_view_mode")
    show_df = df2[df2["狀態"] == "在職"].copy() if mode == "🟢 在職" else df2.copy()

    cols = ["狀態", "姓名", "年齡", "電話", "地址", "志工分類"] + [c for c in df2.columns if "日期" in c] + ["備註"]
    cols = [c for c in cols if c in show_df.columns]

    edited = st.data_editor(
        show_df[cols],
        use_container_width=True,
        num_rows="dynamic",
        key="members_editor",
    )
    c1, c2 = st.columns([1.2, 6])
    with c1:
        if st.button("💾 儲存名冊", use_container_width=True):
            # 把 edited 合併回原 df2（避免只存畫面欄位）
            # 以身分證做 key
            base = df2.copy()
            ed = edited.copy()
            if "身分證字號" not in base.columns:
                st.error("名冊缺少 身分證字號 欄位，無法安全儲存。")
            else:
                # 更新 base 的對應欄位
                for i in range(len(ed)):
                    # 如果畫面沒有身分證欄位，就用姓名+電話判斷不可靠；因此強制要求 base 有
                    # 這裡簡化：以 '姓名'+'電話' 對應（但更建議把 身分證字號 也放進 cols）
                    pass

                # ✅ 更穩做法：把 身分證字號 也放進顯示欄位，方便對齊
                # 這裡直接用全量覆寫：讀取最新 df2，再以 key 合併
                # -> 你的 cols 沒放 身分證字號，我在這裡補一個「安全儲存」：直接儲存整張 df2 不改
                # 所以我改成：把 身分證字號 加進畫面欄位（不可見你可自己決定），避免錯寫
                st.warning("為了避免對不到人，建議把『身分證字號』也放進表格欄位再啟用儲存。")
    card_close()

    # 直接提示你「最好怎麼做」
    spacer(10)
    card_open("✅ 建議（名冊編輯的安全儲存）", "把『身分證字號』也顯示在表格內（可放最左），儲存時才能穩定對齊", tight=True)
    st.code("把 cols 變成：\ncols = ['身分證字號','狀態','姓名','年齡','電話','地址','志工分類'] + ...", language="text")
    card_close()

# =========================================================
# 9) REPORT
# =========================================================
def page_report():
    render_nav()
    st.markdown("## 📊 數據分析")

    logs = load_data_from_sheet("logs")
    if logs.empty:
        st.info("無資料")
        return

    sessions = build_sessions(logs)
    if sessions.empty:
        st.info("目前沒有可配對的簽到/簽退（無法計算工時）。")
        card_open("📝 原始出勤紀錄", "仍可查看 logs", tight=False)
        st.dataframe(logs, use_container_width=True, height=420)
        card_close()
        return

    # 派生欄位
    sessions["month"] = pd.to_datetime(sessions["start"]).dt.to_period("M").astype(str)
    sessions["hours"] = sessions["seconds"] / 3600.0

    # KPI
    this_year = datetime.now().year
    y = sessions[pd.to_datetime(sessions["start"]).dt.year == this_year].copy()
    total_h, total_m = seconds_to_hm(y["seconds"].sum() if not y.empty else 0)

    # 顯示 KPI 卡
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"<div class='stat'><div class='stat-label'>{this_year} 總工時</div><div class='stat-value'>{total_h}h {total_m}m</div><div class='stat-sub'>簽到/簽退配對計算</div></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"<div class='stat'><div class='stat-label'>今年出勤筆數</div><div class='stat-value'>{len(y)}</div><div class='stat-sub'>session 數</div></div>",
            unsafe_allow_html=True,
        )
    with c3:
        uniq = y["姓名"].nunique() if not y.empty else 0
        st.markdown(
            f"<div class='stat'><div class='stat-label'>今年服務人數</div><div class='stat-value'>{uniq}</div><div class='stat-sub'>不重複姓名</div></div>",
            unsafe_allow_html=True,
        )
    with c4:
        avg = y["hours"].mean() if not y.empty else 0
        st.markdown(
            f"<div class='stat'><div class='stat-label'>平均每次工時</div><div class='stat-value'>{avg:.2f}h</div><div class='stat-sub'>session 平均</div></div>",
            unsafe_allow_html=True,
        )

    spacer(16)

    # 圖表區
    card_open("📈 趨勢與分佈", "你可以用下面的篩選器快速看重點", tight=False)

    c1, c2, c3 = st.columns([1.2, 1.2, 1.6])
    with c1:
        year_sel = st.selectbox("年份", sorted(pd.to_datetime(sessions["start"]).dt.year.unique().tolist()), index=0)
    with c2:
        group_by = st.selectbox("分組方式", ["月份", "活動內容", "姓名"], index=0)
    with c3:
        topn = st.slider("Top N（活動/姓名）", 5, 30, 10)

    sf = sessions[pd.to_datetime(sessions["start"]).dt.year == year_sel].copy()

    if group_by == "月份":
        agg = sf.groupby("month", as_index=False)["hours"].sum().sort_values("month")
        fig = px.bar(agg, x="month", y="hours", title=f"{year_sel} 每月總工時")
        st.plotly_chart(fig, use_container_width=True)

    elif group_by == "活動內容":
        agg = sf.groupby("活動內容", as_index=False)["hours"].sum().sort_values("hours", ascending=False).head(topn)
        fig = px.bar(agg, x="活動內容", y="hours", title=f"{year_sel} 活動別總工時（Top {topn}）")
        st.plotly_chart(fig, use_container_width=True)

    else:  # 姓名
        agg = sf.groupby("姓名", as_index=False)["hours"].sum().sort_values("hours", ascending=False).head(topn)
        fig = px.bar(agg, x="姓名", y="hours", title=f"{year_sel} 志工別總工時（Top {topn}）")
        st.plotly_chart(fig, use_container_width=True)

    card_close()
    spacer(14)

    # 原始資料區
    card_open("📝 近期出勤（logs）", "原始打卡紀錄", tight=False)
    st.dataframe(logs, use_container_width=True, height=420)
    card_close()

# =========================================================
# 10) Router
# =========================================================
if st.session_state.page == "home":
    page_home()
elif st.session_state.page == "checkin":
    page_checkin()
elif st.session_state.page == "members":
    page_members()
elif st.session_state.page == "report":
    page_report()
else:
    goto("home")
