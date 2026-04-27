import json
import secrets
import traceback
import urllib.parse
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import gspread
from google.oauth2.service_account import Credentials

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="유실유기동물 대시보드",
    page_icon="🐾",
    layout="wide",
)

# ── 디자인 시스템 CSS 주입 ────────────────────────────────────────────────────
st.html("""
<link href="https://fonts.googleapis.com/...">
<style>
/* ── 글꼴 전역 적용 ── */
html, body, [class*="css"], * {
  font-family: 'Noto Sans KR', sans-serif !important;
}

/* ── CSS 변수 ── */
:root {
  --teal:        #0d9488;
  --teal-light:  #f0fdfa;
  --amber:       #d97706;
  --amber-light: #fffbeb;
  --indigo:      #6366f1;
  --indigo-light:#eef2ff;
  --rose:        #e11d48;
  --rose-light:  #fff1f2;
  --surface:     #ffffff;
  --bg:          #f3f6f9;
  --text-primary:   #0f172a;
  --text-secondary: #64748b;
  --text-muted:     #94a3b8;
  --border:      #e8edf2;
  --shadow-sm:   0 1px 3px rgba(15,23,42,0.06), 0 1px 2px rgba(15,23,42,0.04);
  --radius:      12px;
}

/* ── 메인 배경 ── */
.stApp { background-color: var(--bg) !important; }
.block-container {
  padding-top: 1.5rem !important;
  padding-bottom: 2rem !important;
  max-width: 100% !important;
}

/* ── 다크 사이드바 ── */
[data-testid="stSidebar"] {
  background-color: #151f32 !important;
}
[data-testid="stSidebar"] > div:first-child {
  background-color: #151f32 !important;
}
/* 사이드바 텍스트 */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span:not(.st-emotion-cache-1xw8zd0) {
  color: #e2e8f0 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  color: #f1f5f9 !important;
}
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small {
  color: #64748b !important;
}
/* 사이드바 divider */
[data-testid="stSidebar"] hr {
  border-color: rgba(255,255,255,0.07) !important;
}
/* 사이드바 multiselect */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background-color: rgba(255,255,255,0.06) !important;
  border-color: rgba(255,255,255,0.12) !important;
  color: #e2e8f0 !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] {
  background-color: rgba(13,148,136,0.3) !important;
  color: #5eead4 !important;
}
/* 사이드바 date input */
[data-testid="stSidebar"] input[type="date"] {
  background-color: rgba(255,255,255,0.06) !important;
  border-color: rgba(255,255,255,0.12) !important;
  color: #e2e8f0 !important;
  color-scheme: dark;
  border-radius: 7px;
}
/* 사이드바 로그아웃 버튼 */
[data-testid="stSidebar"] .stButton > button {
  background-color: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  color: #94a3b8 !important;
  border-radius: 8px !important;
  font-size: 12px !important;
  transition: all 0.15s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background-color: rgba(255,255,255,0.12) !important;
  color: #e2e8f0 !important;
}
/* 사이드바 expander */
[data-testid="stSidebar"] details {
  background: rgba(255,255,255,0.04) !important;
  border-color: rgba(255,255,255,0.08) !important;
  border-radius: 8px !important;
}
[data-testid="stSidebar"] details summary {
  color: #94a3b8 !important;
  font-size: 12px !important;
}
[data-testid="stSidebar"] [data-testid="stExpanderDetails"] * {
  color: #94a3b8 !important;
  font-size: 11px !important;
}

/* ── 탭 스타일 ── */
.stTabs [data-baseweb="tab-list"] {
  background-color: #e2e8f0 !important;
  border-radius: 8px !important;
  padding: 3px !important;
  gap: 2px !important;
  border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 6px !important;
  font-size: 12.5px !important;
  font-weight: 500 !important;
  color: #64748b !important;
  padding: 6px 16px !important;
  background: transparent !important;
  border: none !important;
}
.stTabs [aria-selected="true"] {
  background-color: #ffffff !important;
  color: #0f172a !important;
  font-weight: 600 !important;
  box-shadow: 0 1px 3px rgba(15,23,42,0.08) !important;
}
.stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

/* ── KPI 카드 ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}
.kpi-card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 18px 20px;
  box-shadow: var(--shadow-sm);
  border-left: 3px solid transparent;
  position: relative;
  overflow: hidden;
}
.kpi-card.teal   { border-left-color: var(--teal);   }
.kpi-card.amber  { border-left-color: var(--amber);  }
.kpi-card.rose   { border-left-color: var(--rose);   }
.kpi-card.indigo { border-left-color: var(--indigo); }
.kpi-label {
  font-size: 11.5px; font-weight: 500;
  color: var(--text-secondary); margin-bottom: 8px;
}
.kpi-value {
  font-size: 26px; font-weight: 700;
  color: var(--text-primary); line-height: 1;
  margin-bottom: 8px; letter-spacing: -0.03em;
}
.kpi-delta {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; font-weight: 500;
  padding: 2px 8px; border-radius: 99px;
}
.kpi-delta.up      { background: #dcfce7; color: #166534; }
.kpi-delta.down    { background: #fee2e2; color: #991b1b; }
.kpi-delta.neutral { background: #f1f5f9; color: #64748b; }

/* ── 차트 카드 ── */
.chart-card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 16px 20px 12px;
  box-shadow: var(--shadow-sm);
  margin-bottom: 14px;
}
.chart-card-title {
  font-size: 13px; font-weight: 600;
  color: var(--text-primary);
  display: flex; align-items: center; gap: 7px;
  margin-bottom: 4px;
}

/* ── 섹션 헤더 ── */
.section-badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 14px; background: var(--teal-light);
  border-radius: 8px; font-size: 12px; font-weight: 500;
  color: var(--teal); margin-bottom: 16px;
}

/* ── 상태 배지 ── */
.status-badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px; border-radius: 99px; font-size: 11px; font-weight: 500;
}
.status-badge.adoption  { background: #dcfce7; color: #166534; }
.status-badge.protect   { background: #dbeafe; color: #1e40af; }
.status-badge.natural   { background: #f1f5f9; color: #64748b; }
.status-badge.euthanasia{ background: #fee2e2; color: #991b1b; }
.status-badge.return_   { background: #fef3c7; color: #92400e; }

/* ── AI 인사이트 박스 ── */
.insight-box {
  background: linear-gradient(135deg, #f5f3ff, #f0fdfa);
  border: 1px solid #ddd6fe;
  border-radius: var(--radius);
  padding: 20px;
  margin-top: 14px;
}

/* ── Streamlit 기본 제목 숨기기 / 재스타일 ── */
h1 { font-size: 16px !important; font-weight: 700 !important; color: var(--text-primary) !important; }
h2 { font-size: 14px !important; font-weight: 600 !important; color: var(--text-primary) !important; }
h3 { font-size: 13px !important; font-weight: 600 !important; color: var(--text-primary) !important; }

/* ── 메트릭 숨기기 (커스텀 KPI 카드로 대체) ── */
div[data-testid="metric-container"] { display: none !important; }

/* ── 다운로드 버튼 ── */
.stDownloadButton > button {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--text-primary) !important;
  border-radius: 8px !important;
  font-size: 12.5px !important;
  font-weight: 500 !important;
  transition: all 0.15s !important;
}
.stDownloadButton > button:hover {
  background: #f8fafc !important;
  border-color: var(--teal) !important;
  color: var(--teal) !important;
}

/* ── Primary 버튼 (AI 인사이트) ── */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--indigo), var(--teal)) !important;
  border: none !important;
  border-radius: 9px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
  transition: all 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
  opacity: 0.9 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2) !important;
}

/* ── 데이터프레임 ── */
[data-testid="stDataFrame"] {
  border-radius: 8px !important;
  overflow: hidden !important;
  border: 1px solid var(--border) !important;
}

/* ── 스크롤바 ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 99px; }
</style>
""")


# ── 공통 Plotly 레이아웃 테마 ─────────────────────────────────────────────────
CHART_THEME = dict(
    font=dict(family="Noto Sans KR, Apple SD Gothic Neo, sans-serif", size=12),
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    margin=dict(t=40, b=36, l=36, r=16),
)

# ── 색상 팔레트 ───────────────────────────────────────────────────────────────
C_TEAL   = "#0d9488"
C_AMBER  = "#f59e0b"
C_INDIGO = "#6366f1"
C_ROSE   = "#e11d48"
C_GRAY   = "#94a3b8"
TEAL_SCALE  = ["#0f766e", "#0d9488", "#14b8a6", "#2dd4bf", "#5eead4", "#99f6e4"]
INDIGO_SCALE= ["#4338ca", "#6366f1", "#818cf8", "#a5b4fc", "#c7d2fe"]

# ── KPI 카드 헬퍼 ─────────────────────────────────────────────────────────────
def kpi_card(label: str, value: str, delta: str = None,
             delta_type: str = "neutral", color: str = "teal") -> str:
    delta_html = ""
    if delta:
        arrow = "▲ " if delta_type == "up" else ("▼ " if delta_type == "down" else "")
        delta_html = f'<span class="kpi-delta {delta_type}">{arrow}{delta}</span>'
    return f"""
    <div class="kpi-card {color}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>"""


def kpi_grid(*cards: str):
    inner = "".join(cards)
    st.markdown(f'<div class="kpi-grid">{inner}</div>', unsafe_allow_html=True)


# ── 차트 카드 헬퍼 ────────────────────────────────────────────────────────────
def chart_card_header(icon: str, title: str):
    st.markdown(
        f'<div class="chart-card-title">{icon}&nbsp;{title}</div>',
        unsafe_allow_html=True,
    )


# ── Secrets 로드 ──────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID    = st.secrets["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI        = st.secrets["REDIRECT_URI"]
WHITELIST_SHEET_ID  = st.secrets["WHITELIST_SHEET_ID"]
WHITELIST_GID       = int(st.secrets.get("WHITELIST_GID", 0))

AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL         = "https://oauth2.googleapis.com/token"
USERINFO_URL      = "https://www.googleapis.com/oauth2/v3/userinfo"

# ── 시/도 매핑 ────────────────────────────────────────────────────────────────
SIDO_MAP = {
    "서울": "서울특별시", "부산": "부산광역시", "대구": "대구광역시",
    "인천": "인천광역시", "광주": "광주광역시", "대전": "대전광역시",
    "울산": "울산광역시", "세종": "세종특별자치시", "경기": "경기도",
    "강원": "강원특별자치도", "충북": "충청북도", "충남": "충청남도",
    "전북": "전북특별자치도", "전남": "전라남도", "경북": "경상북도",
    "경남": "경상남도", "제주": "제주특별자치도",
}

def extract_sido(val) -> str:
    if pd.isna(val):
        return "미상"
    s = str(val).strip()
    for short, full in SIDO_MAP.items():
        if s.startswith(full) or s.startswith(short):
            return full
    first = s.split()[0] if s else "미상"
    return first


# ── Google OAuth 유틸리티 ─────────────────────────────────────────────────────
def get_google_auth_url(state: str) -> str:
    params = {
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         "openid email profile",
        "state":         state,
        "access_type":   "online",
        "prompt":        "select_account",
    }
    return AUTHORIZATION_URL + "?" + urllib.parse.urlencode(params)


def exchange_code_for_userinfo(code: str) -> dict | None:
    try:
        token_resp = requests.post(
            TOKEN_URL,
            data={
                "code":          code,
                "client_id":     GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri":  REDIRECT_URI,
                "grant_type":    "authorization_code",
            },
            timeout=10,
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return None
        info_resp = requests.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        return info_resp.json()
    except Exception:
        return None


# ── 화이트리스트 로드 ──────────────────────────────────────────────────────────
def load_whitelist() -> set:
    creds_info = json.loads(json.dumps(dict(st.secrets["gcp_service_account"])))
    gc = gspread.service_account_from_dict(creds_info)
    sh = gc.open_by_key(WHITELIST_SHEET_ID)
    ws = next(
        (w for w in sh.worksheets() if w.id == WHITELIST_GID),
        sh.worksheets()[0],
    )
    records = ws.get_all_records()
    return {
        str(row.get("email", "")).strip().lower()
        for row in records
        if str(row.get("email", "")).strip()
    }


# ── 로그인 화면 ───────────────────────────────────────────────────────────────
def show_login_page():
    params = st.query_params
    code  = params.get("code")
    state = params.get("state")

    if code:
        with st.spinner("Google 계정을 확인하는 중..."):
            user_info = exchange_code_for_userinfo(code)

        if not user_info or "email" not in user_info:
            st.error("⚠️ Google 인증에 실패했습니다. 다시 시도해 주세요.")
            st.query_params.clear()
            st.stop()

        email = user_info["email"].strip().lower()

        try:
            whitelist = load_whitelist()
        except Exception as e:
            st.error(f"⚠️ 접근권한 시트를 불러올 수 없습니다.\n\n오류: `{type(e).__name__}: {e}`")
            st.code(traceback.format_exc(), language="text")
            st.query_params.clear()
            st.stop()

        if email not in whitelist:
            st.error(
                f"❌ **{email}** 은(는) 접근 권한이 없는 계정입니다.  \n"
                "관리자에게 접근 권한을 요청하세요."
            )
            st.query_params.clear()
            st.stop()

        st.session_state["authenticated"] = True
        st.session_state["user_email"]    = email
        st.session_state["user_name"]     = user_info.get("name") or email
        st.session_state["user_picture"]  = user_info.get("picture", "")
        st.query_params.clear()
        st.rerun()
        return

    # ── 로그인 UI ─────────────────────────────────────────────────────────────
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style='text-align:center; margin-bottom:8px;'>
                <div style='width:60px;height:60px;border-radius:16px;
                    background:linear-gradient(135deg,#0d9488,#6366f1);
                    display:flex;align-items:center;justify-content:center;
                    font-size:28px;margin:0 auto 16px;'>🐾</div>
            </div>
            <h2 style='text-align:center;margin-bottom:4px;font-size:20px;font-weight:700;color:#0f172a;'>
                유실유기동물 현황 대시보드
            </h2>
            <p style='text-align:center;color:#64748b;margin-bottom:32px;font-size:13px;'>
                동물자유연대 구성원 전용입니다.
            </p>
            """,
            unsafe_allow_html=True,
        )

        if "oauth_state" not in st.session_state:
            st.session_state["oauth_state"] = secrets.token_hex(16)

        auth_url = get_google_auth_url(st.session_state["oauth_state"])
        st.link_button(
            "🔐 Google 계정으로 로그인",
            auth_url,
            use_container_width=True,
            type="primary",
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("접근 권한 요청: 관리자에게 Google 계정 이메일 주소를 알려주세요.")


# ── 인증 게이트 ───────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    show_login_page()
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#   이하 코드는 로그인 성공 후에만 실행됩니다.
# ══════════════════════════════════════════════════════════════════════════════

# ── 컬럼 후보 매핑 ────────────────────────────────────────────────────────────
COL_CANDIDATES = {
    "date":    ["접수일", "발생일시", "noticeEdDt", "happenDt", "접수일자", "발생일"],
    "region":  ["관할기관", "orgNm", "careNm", "보호기관", "시군구"],
    "status":  ["처리상태", "processState", "상태", "state"],
    "species": ["축종", "kindCd", "동물종류", "종류"],
    "breed":   ["품종", "breed", "kindNm"],
}

def detect_col(df: pd.DataFrame, key: str) -> str | None:
    for candidate in COL_CANDIDATES[key]:
        if candidate in df.columns:
            return candidate
    keywords = {
        "date": ["일"], "region": ["기관", "지역", "시군"],
        "status": ["상태"], "species": ["종류", "축종"], "breed": ["품종"],
    }
    for c in df.columns:
        if any(kw in c for kw in keywords.get(key, [])):
            return c
    return None


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    creds_info = json.loads(json.dumps(dict(st.secrets["gcp_service_account"])))
    gc = gspread.service_account_from_dict(creds_info)
    sh = gc.open_by_key(WHITELIST_SHEET_ID)
    ws = sh.worksheet("summary")
    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()
    return pd.DataFrame(values[1:], columns=values[0]).astype(str)


def parse_date_col(series: pd.Series) -> pd.Series:
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return pd.to_datetime(series.str[:10], format=fmt, errors="coerce")
        except Exception:
            continue
    return pd.to_datetime(series, errors="coerce")


# ── 데이터 로드 ────────────────────────────────────────────────────────────────
with st.spinner("데이터를 불러오는 중..."):
    try:
        df_raw = load_data()
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.stop()

date_col    = detect_col(df_raw, "date")
region_col  = detect_col(df_raw, "region")
status_col  = detect_col(df_raw, "status")
species_col = detect_col(df_raw, "species")
breed_col   = detect_col(df_raw, "breed")

df = df_raw.copy()
if date_col:
    df["_date"] = parse_date_col(df[date_col])
if region_col:
    df["_sido"] = df[region_col].apply(extract_sido)


# ── 헤더 ──────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
        background:#ffffff;border-bottom:1px solid #e8edf2;
        padding:14px 0 12px;margin-bottom:20px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <span style="font-size:18px;">🐾</span>
        <span style="font-size:16px;font-weight:700;color:#0f172a;">유실유기동물 현황 대시보드</span>
      </div>
      <span style="font-size:11.5px;color:#94a3b8;">
        데이터 출처: Google Sheets · 매일 자동 갱신 · 마지막 조회: {datetime.now().strftime('%Y-%m-%d %H:%M')}
      </span>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # 브랜드 로고
    st.markdown(
        """
        <div style="padding:8px 0 16px;">
          <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:34px;height:34px;border-radius:10px;
                background:#0d9488;display:flex;align-items:center;
                justify-content:center;font-size:16px;flex-shrink:0;">🐾</div>
            <div>
              <div style="color:#ffffff;font-weight:600;font-size:13px;">유실유기동물</div>
              <div style="color:#94a3b8;font-size:11px;margin-top:1px;">현황 대시보드</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 프로필
    picture = st.session_state.get("user_picture", "")
    name    = st.session_state["user_name"]
    email   = st.session_state["user_email"]
    initial = name[0] if name else "?"

    if picture:
        avatar_html = f"<img src='{picture}' style='width:36px;height:36px;border-radius:50%;'>"
    else:
        avatar_html = (
            f"<div style='width:36px;height:36px;border-radius:50%;"
            f"background:linear-gradient(135deg,#0d9488,#6366f1);"
            f"display:flex;align-items:center;justify-content:center;"
            f"font-size:14px;font-weight:600;color:white;flex-shrink:0;'>{initial}</div>"
        )

    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:10px;
            padding:12px 0 14px;border-top:1px solid rgba(255,255,255,0.07);
            border-bottom:1px solid rgba(255,255,255,0.07);">
          {avatar_html}
          <div style="flex:1;min-width:0;">
            <div style="color:#f1f5f9;font-size:13px;font-weight:500;
                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
              {name} 님 환영합니다 👋</div>
            <div style="color:#64748b;font-size:11px;
                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{email}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("로그아웃", use_container_width=True):
        for key in ["authenticated", "user_email", "user_name", "user_picture", "oauth_state"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()

    # 필터 섹션
    st.markdown(
        '<div style="color:#475569;font-size:10px;font-weight:600;'
        'letter-spacing:0.08em;text-transform:uppercase;margin-bottom:10px;">필터</div>',
        unsafe_allow_html=True,
    )

    selected_sidos = []
    if region_col:
        all_sidos = sorted(df["_sido"].dropna().unique().tolist())
        selected_sidos = st.multiselect(
            "시/도 (지역)", options=all_sidos, default=[],
            placeholder="전체 (미선택 시 전체 표시)",
        )

    selected_statuses = []
    if status_col:
        all_statuses = sorted(df[status_col].dropna().unique().tolist())
        selected_statuses = st.multiselect(
            "처리 상태", options=all_statuses, default=[],
            placeholder="전체 (미선택 시 전체 표시)",
        )

    if date_col and df["_date"].notna().any():
        min_date = df["_date"].min().date()
        max_date = df["_date"].max().date()
        date_range = st.date_input(
            "접수일 범위", value=(min_date, max_date),
            min_value=min_date, max_value=max_date,
        )
    else:
        date_range = None

    st.divider()
    with st.expander("🗂 컬럼 목록 확인"):
        st.write(df_raw.columns.tolist())


# ── 필터 적용 ─────────────────────────────────────────────────────────────────
filtered = df.copy()
if selected_sidos and region_col:
    filtered = filtered[filtered["_sido"].isin(selected_sidos)]
if selected_statuses and status_col:
    filtered = filtered[filtered[status_col].isin(selected_statuses)]
if date_range and len(date_range) == 2 and date_col:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    filtered = filtered[filtered["_date"].between(start, end)]


# ── 탭 구성 ───────────────────────────────────────────────────────────────────
tab_dash, tab_daily, tab_monthly = st.tabs(["📊 대시보드", "📅 일간 보고서", "📆 월간 보고서"])


# ══════════════════════════════════════════════════════════════════════════════
#   탭 1: 대시보드
# ══════════════════════════════════════════════════════════════════════════════
with tab_dash:
    total = len(filtered)

    def rate(keyword: str) -> float:
        if not status_col or total == 0:
            return 0.0
        return round(filtered[status_col].str.contains(keyword, na=False).sum() / total * 100, 1)

    adoption_rate   = rate("입양")
    euthanasia_rate = rate("안락사")
    total_all       = len(df)
    adoption_all    = round(df[status_col].str.contains("입양", na=False).sum() / total_all * 100, 1) if status_col and total_all else 0
    euthanasia_all  = round(df[status_col].str.contains("안락사", na=False).sum() / total_all * 100, 1) if status_col and total_all else 0
    protect_cnt     = filtered[status_col].str.contains("보호중", na=False).sum() if status_col else 0

    # ── KPI 카드 ──────────────────────────────────────────────────────────────
    is_filtered = bool(selected_sidos or selected_statuses)

    total_delta      = f"전체 {total_all:,}건 중" if is_filtered else None
    adoption_delta   = f"{adoption_rate - adoption_all:+.1f}%p (전체 대비)" if is_filtered else None
    euthanasia_delta = f"{euthanasia_rate - euthanasia_all:+.1f}%p (전체 대비)" if is_filtered else None

    kpi_grid(
        kpi_card("총 발생 건수",  f"{total:,}건",
                 total_delta, "neutral", "teal"),
        kpi_card("입양률",       f"{adoption_rate}%",
                 adoption_delta,
                 "up" if adoption_rate >= adoption_all else "down", "amber"),
        kpi_card("안락사율",     f"{euthanasia_rate}%",
                 euthanasia_delta,
                 "down" if euthanasia_rate > euthanasia_all else "up", "rose"),
        kpi_card("현재 보호중",  f"{protect_cnt:,}건",
                 color="indigo"),
    )

    # ── 차트 Row 1 ────────────────────────────────────────────────────────────
    row1_left, row1_right = st.columns([3, 2])

    with row1_left:
        chart_card_header("📈", "최근 30일 일별 유기동물 발생 추이")
        if date_col and df["_date"].notna().any():
            cutoff = filtered["_date"].max() - timedelta(days=29)
            recent = filtered[filtered["_date"] >= cutoff].copy()
            daily = (
                recent.groupby(recent["_date"].dt.date).size()
                .reset_index(name="발생 건수").rename(columns={"_date": "접수일"})
            )
            if not daily.empty:
                full_range = pd.date_range(daily["접수일"].min(), daily["접수일"].max())
                daily = (daily.set_index("접수일").reindex(full_range.date, fill_value=0)
                         .reset_index().rename(columns={"index": "접수일"}))
            fig_line = px.line(daily, x="접수일", y="발생 건수", markers=True,
                               color_discrete_sequence=[C_TEAL])
            fig_line.update_traces(
                line=dict(width=2.5), marker=dict(size=5),
                fill="tozeroy", fillcolor="rgba(13,148,136,0.08)",
            )
            fig_line.update_xaxes(tickformat="%m/%d", tickangle=-30, showgrid=False,
                                  showline=False)
            fig_line.update_yaxes(gridcolor="#f1f5f9", showline=False)
            fig_line.update_layout(**CHART_THEME)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("날짜 컬럼을 감지하지 못해 추이 차트를 표시할 수 없습니다.")

    with row1_right:
        chart_card_header("🌿", "축종·품종별 비율 (상위 30)")
        if species_col or breed_col:
            path = [c for c in [species_col, breed_col] if c]
            top_breeds = filtered.groupby(path).size().reset_index(name="건수").nlargest(30, "건수")
            fig_tree = px.treemap(top_breeds, path=path, values="건수",
                                  color="건수", color_continuous_scale=TEAL_SCALE)
            fig_tree.update_traces(
                textinfo="label+percent parent",
                hovertemplate="<b>%{label}</b><br>건수: %{value:,}<br>비율: %{percentParent:.1%}<extra></extra>",
            )
            fig_tree.update_layout(**CHART_THEME)
            st.plotly_chart(fig_tree, use_container_width=True)
        else:
            st.info("축종/품종 컬럼을 감지하지 못했습니다.")

    # ── 차트 Row 2 ────────────────────────────────────────────────────────────
    row2_left, row2_right = st.columns(2)

    with row2_left:
        chart_card_header("🔄", "처리 상태 비율")
        if status_col:
            status_cnt = filtered[status_col].value_counts().reset_index()
            status_cnt.columns = ["처리 상태", "건수"]
            # HTML 디자인과 동일한 색상 매핑
            color_map = {
                "보호중": "#3b82f6", "입양": "#10b981", "자연사": "#94a3b8",
                "안락사": "#f87171", "반환": "#f59e0b", "기증": "#a78bfa", "방사": "#34d399",
            }
            colors = [color_map.get(s, "#94a3b8") for s in status_cnt["처리 상태"]]
            fig_donut = go.Figure(go.Pie(
                labels=status_cnt["처리 상태"],
                values=status_cnt["건수"],
                hole=0.52,
                marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
                textposition="outside",
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>%{value:,}건<br>%{percent}<extra></extra>",
            ))
            fig_donut.update_layout(
                **CHART_THEME,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.25,
                            xanchor="center", x=0.5, font=dict(size=11)),
                annotations=[dict(text=f"{total:,}건", x=0.5, y=0.5,
                                  font=dict(size=14, color="#0f172a", family="Noto Sans KR"),
                                  showarrow=False)],
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("처리 상태 컬럼을 감지하지 못했습니다.")

    with row2_right:
        chart_card_header("📍", "시/도별 접수 건수")
        if region_col:
            sido_cnt = filtered["_sido"].value_counts().reset_index()
            sido_cnt.columns = ["시/도", "건수"]
            fig_bar = px.bar(sido_cnt, x="건수", y="시/도", orientation="h",
                             text="건수", color="건수",
                             color_continuous_scale=TEAL_SCALE)
            fig_bar.update_traces(textposition="outside",
                                  marker=dict(line=dict(width=0)))
            fig_bar.update_yaxes(autorange="reversed", tickfont=dict(size=11),
                                 showline=False)
            fig_bar.update_xaxes(showgrid=True, gridcolor="#f1f5f9",
                                 showline=False, zeroline=False)
            fig_bar.update_layout(**CHART_THEME, showlegend=False,
                                  coloraxis_showscale=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("관할기관 컬럼을 감지하지 못했습니다.")

    st.divider()

    # ── 상세 데이터 ───────────────────────────────────────────────────────────
    chart_card_header("📋", "상세 데이터")
    display_df = filtered.drop(columns=["_date", "_sido"], errors="ignore")
    st.dataframe(display_df, use_container_width=True, height=380)

    csv_bytes = display_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="↓ 필터 결과 CSV 다운로드",
        data=csv_bytes,
        file_name=f"유실유기동물_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )


# ══════════════════════════════════════════════════════════════════════════════
#   탭 2: 일간 보고서
# ══════════════════════════════════════════════════════════════════════════════
with tab_daily:
    today = datetime.now().date()
    d1 = today - timedelta(days=1)
    d2 = today - timedelta(days=2)

    st.markdown(
        f'<div class="section-badge">📅 일간 발생현황 보고서 &nbsp;·&nbsp; '
        f'기준: <b>{d1.strftime("%Y년 %m월 %d일")}</b> (전일) vs '
        f'<b>{d2.strftime("%Y년 %m월 %d일")}</b> (전전일)</div>',
        unsafe_allow_html=True,
    )

    if not date_col or not df["_date"].notna().any():
        st.warning("날짜 컬럼을 감지하지 못해 일간 보고서를 표시할 수 없습니다.")
    else:
        df_d1 = df[df["_date"].dt.date == d1]
        df_d2 = df[df["_date"].dt.date == d2]
        cnt_d1, cnt_d2 = len(df_d1), len(df_d2)
        delta_cnt = cnt_d1 - cnt_d2

        def daily_rate(df_sub, keyword):
            if not status_col or len(df_sub) == 0:
                return 0.0
            return round(df_sub[status_col].str.contains(keyword, na=False).sum() / len(df_sub) * 100, 1)

        adopt_d1, adopt_d2 = daily_rate(df_d1, "입양"), daily_rate(df_d2, "입양")
        euth_d1,  euth_d2  = daily_rate(df_d1, "안락사"), daily_rate(df_d2, "안락사")

        kpi_grid(
            kpi_card(f"전일({d1.strftime('%m/%d')}) 접수", f"{cnt_d1:,}건",
                     f"{delta_cnt:+,}건 (전전일 대비)",
                     "down" if delta_cnt > 0 else "up", "teal"),
            kpi_card("입양률", f"{adopt_d1}%",
                     f"{adopt_d1 - adopt_d2:+.1f}%p",
                     "up" if adopt_d1 >= adopt_d2 else "down", "amber"),
            kpi_card("안락사율", f"{euth_d1}%",
                     f"{euth_d1 - euth_d2:+.1f}%p",
                     "down" if euth_d1 > euth_d2 else "up", "rose"),
            kpi_card(f"전전일({d2.strftime('%m/%d')}) 접수", f"{cnt_d2:,}건",
                     color="indigo"),
        )

        col_l, col_r = st.columns(2)

        with col_l:
            chart_card_header("📍", "시/도별 접수 건수 비교")
            if region_col:
                sido_d1 = df_d1["_sido"].value_counts().rename("전일")
                sido_d2 = df_d2["_sido"].value_counts().rename("전전일")
                sido_cmp = pd.concat([sido_d1, sido_d2], axis=1).fillna(0).astype(int)
                sido_cmp["증감"] = sido_cmp["전일"] - sido_cmp["전전일"]
                sido_cmp = sido_cmp.sort_values("전일", ascending=False).reset_index()
                sido_cmp.columns = ["시/도", "전일", "전전일", "증감"]

                fig_sido = go.Figure()
                fig_sido.add_bar(name=f"전전일({d2.strftime('%m/%d')})",
                                 x=sido_cmp["시/도"], y=sido_cmp["전전일"],
                                 marker_color=C_GRAY)
                fig_sido.add_bar(name=f"전일({d1.strftime('%m/%d')})",
                                 x=sido_cmp["시/도"], y=sido_cmp["전일"],
                                 marker_color=C_TEAL)
                fig_sido.update_layout(**CHART_THEME, barmode="group",
                                       xaxis_tickangle=-30)
                st.plotly_chart(fig_sido, use_container_width=True)

                sido_cmp["증감"] = sido_cmp["증감"].apply(lambda x: f"{x:+,}")
                st.dataframe(sido_cmp, use_container_width=True, hide_index=True)
            else:
                st.info("지역 컬럼을 감지하지 못했습니다.")

        with col_r:
            chart_card_header("🐾", "축종별 접수 건수 비교")
            if species_col:
                sp_d1 = df_d1[species_col].value_counts().rename("전일")
                sp_d2 = df_d2[species_col].value_counts().rename("전전일")
                sp_cmp = pd.concat([sp_d1, sp_d2], axis=1).fillna(0).astype(int)
                sp_cmp["증감"] = sp_cmp["전일"] - sp_cmp["전전일"]
                sp_cmp = sp_cmp.sort_values("전일", ascending=False).reset_index()
                sp_cmp.columns = ["축종", "전일", "전전일", "증감"]

                fig_sp = go.Figure()
                fig_sp.add_bar(name=f"전전일({d2.strftime('%m/%d')})",
                               x=sp_cmp["축종"], y=sp_cmp["전전일"],
                               marker_color=C_GRAY)
                fig_sp.add_bar(name=f"전일({d1.strftime('%m/%d')})",
                               x=sp_cmp["축종"], y=sp_cmp["전일"],
                               marker_color=C_AMBER)
                fig_sp.update_layout(**CHART_THEME, barmode="group")
                st.plotly_chart(fig_sp, use_container_width=True)

                sp_cmp["증감"] = sp_cmp["증감"].apply(lambda x: f"{x:+,}")
                st.dataframe(sp_cmp, use_container_width=True, hide_index=True)
            else:
                st.info("축종 컬럼을 감지하지 못했습니다.")

        st.divider()
        chart_card_header("📋", "전일 상세 데이터")
        if cnt_d1 > 0:
            st.dataframe(
                df_d1.drop(columns=["_date", "_sido"], errors="ignore"),
                use_container_width=True, height=300,
            )
            csv_d1 = df_d1.drop(columns=["_date", "_sido"], errors="ignore").to_csv(
                index=False, encoding="utf-8-sig"
            ).encode("utf-8-sig")
            st.download_button(
                label=f"↓ 전일({d1.strftime('%Y%m%d')}) 데이터 다운로드",
                data=csv_d1,
                file_name=f"유실유기동물_일간_{d1.strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        else:
            st.info(f"{d1.strftime('%Y-%m-%d')} 데이터가 없습니다.")


# ══════════════════════════════════════════════════════════════════════════════
#   탭 3: 월간 보고서
# ══════════════════════════════════════════════════════════════════════════════
with tab_monthly:
    today = datetime.now().date()
    first_of_this_month = today.replace(day=1)
    last_of_m1   = first_of_this_month - timedelta(days=1)
    first_of_m1  = last_of_m1.replace(day=1)
    last_of_m2   = first_of_m1 - timedelta(days=1)
    first_of_m2  = last_of_m2.replace(day=1)
    label_m1 = first_of_m1.strftime("%Y년 %m월")
    label_m2 = first_of_m2.strftime("%Y년 %m월")

    st.markdown(
        f'<div class="section-badge">📆 월간 발생현황 보고서 &nbsp;·&nbsp; '
        f'비교: <b>{label_m1}</b> (전월) vs <b>{label_m2}</b> (전전월)</div>',
        unsafe_allow_html=True,
    )

    if not date_col or not df["_date"].notna().any():
        st.warning("날짜 컬럼을 감지하지 못해 월간 보고서를 표시할 수 없습니다.")
    else:
        df_m1 = df[(df["_date"].dt.date >= first_of_m1) & (df["_date"].dt.date <= last_of_m1)]
        df_m2 = df[(df["_date"].dt.date >= first_of_m2) & (df["_date"].dt.date <= last_of_m2)]

        cnt_m1, cnt_m2 = len(df_m1), len(df_m2)
        delta_m   = cnt_m1 - cnt_m2
        delta_pct = round((delta_m / cnt_m2 * 100) if cnt_m2 else 0, 1)

        def monthly_rate(df_sub, keyword):
            if not status_col or len(df_sub) == 0:
                return 0.0
            return round(df_sub[status_col].str.contains(keyword, na=False).sum() / len(df_sub) * 100, 1)

        adopt_m1, adopt_m2 = monthly_rate(df_m1, "입양"), monthly_rate(df_m2, "입양")
        euth_m1,  euth_m2  = monthly_rate(df_m1, "안락사"), monthly_rate(df_m2, "안락사")
        protect_m1 = df_m1[status_col].str.contains("보호중", na=False).sum() if status_col else 0
        protect_m2 = df_m2[status_col].str.contains("보호중", na=False).sum() if status_col else 0

        kpi_grid(
            kpi_card(f"전월({label_m1}) 접수", f"{cnt_m1:,}건",
                     f"{delta_m:+,}건 ({delta_pct:+.1f}%)",
                     "down" if delta_m > 0 else "up", "teal"),
            kpi_card("입양률", f"{adopt_m1}%",
                     f"{adopt_m1 - adopt_m2:+.1f}%p",
                     "up" if adopt_m1 >= adopt_m2 else "down", "amber"),
            kpi_card("안락사율", f"{euth_m1}%",
                     f"{euth_m1 - euth_m2:+.1f}%p",
                     "down" if euth_m1 > euth_m2 else "up", "rose"),
            kpi_card("보호중", f"{protect_m1:,}건",
                     f"{protect_m1 - protect_m2:+,}건",
                     "down" if protect_m1 > protect_m2 else "up", "indigo"),
        )

        col_l, col_r = st.columns(2)

        with col_l:
            chart_card_header("📍", "시/도별 접수 건수")
            if region_col:
                sido_m1 = df_m1["_sido"].value_counts().rename(label_m1)
                sido_m2 = df_m2["_sido"].value_counts().rename(label_m2)
                sido_cmp = pd.concat([sido_m1, sido_m2], axis=1).fillna(0).astype(int)
                sido_cmp["증감"] = sido_cmp[label_m1] - sido_cmp[label_m2]
                sido_cmp = sido_cmp.sort_values(label_m1, ascending=False).reset_index()
                sido_cmp.columns = ["시/도", label_m1, label_m2, "증감"]

                fig_sido_m = go.Figure()
                fig_sido_m.add_bar(name=label_m2, x=sido_cmp["시/도"],
                                   y=sido_cmp[label_m2], marker_color=C_GRAY)
                fig_sido_m.add_bar(name=label_m1, x=sido_cmp["시/도"],
                                   y=sido_cmp[label_m1], marker_color=C_INDIGO)
                fig_sido_m.update_layout(**CHART_THEME, barmode="group",
                                         xaxis_tickangle=-30)
                st.plotly_chart(fig_sido_m, use_container_width=True)
            else:
                st.info("지역 컬럼을 감지하지 못했습니다.")

        with col_r:
            chart_card_header("📈", f"{label_m1} 일별 발생 추이")
            if cnt_m1 > 0:
                daily_m1 = (
                    df_m1.groupby(df_m1["_date"].dt.date).size()
                    .reset_index(name="건수").rename(columns={"_date": "날짜"})
                )
                days_in_m1 = calendar.monthrange(first_of_m1.year, first_of_m1.month)[1]
                full_m1 = pd.date_range(first_of_m1, periods=days_in_m1)
                daily_m1 = (
                    daily_m1.set_index("날짜")
                    .reindex(full_m1.date, fill_value=0)
                    .reset_index().rename(columns={"index": "날짜"})
                )
                fig_m1_trend = px.bar(daily_m1, x="날짜", y="건수",
                                      color_discrete_sequence=[C_INDIGO])
                fig_m1_trend.update_layout(**CHART_THEME)
                fig_m1_trend.update_xaxes(tickformat="%d일", tickangle=-30, showgrid=False)
                fig_m1_trend.update_yaxes(gridcolor="#f1f5f9")
                st.plotly_chart(fig_m1_trend, use_container_width=True)
            else:
                st.info(f"{label_m1} 데이터가 없습니다.")

        st.divider()

        if status_col:
            chart_card_header("🔄", "처리 상태 비교")
            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown(f"<div style='font-size:12px;font-weight:600;color:#64748b;margin-bottom:8px;'>{label_m2}</div>", unsafe_allow_html=True)
                s2 = df_m2[status_col].value_counts().reset_index()
                s2.columns = ["처리 상태", "건수"]
                fig_s2 = px.pie(s2, names="처리 상태", values="건수", hole=0.4,
                                color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_s2.update_traces(textposition="outside", textinfo="percent+label")
                fig_s2.update_layout(**CHART_THEME)
                st.plotly_chart(fig_s2, use_container_width=True)
            with sc2:
                st.markdown(f"<div style='font-size:12px;font-weight:600;color:#64748b;margin-bottom:8px;'>{label_m1}</div>", unsafe_allow_html=True)
                s1 = df_m1[status_col].value_counts().reset_index()
                s1.columns = ["처리 상태", "건수"]
                fig_s1 = px.pie(s1, names="처리 상태", values="건수", hole=0.4,
                                color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_s1.update_traces(textposition="outside", textinfo="percent+label")
                fig_s1.update_layout(**CHART_THEME)
                st.plotly_chart(fig_s1, use_container_width=True)

        st.divider()

        # ── AI 인사이트 ───────────────────────────────────────────────────────
        st.markdown(
            """
            <div style="display:flex;align-items:flex-start;justify-content:space-between;
                margin-bottom:14px;gap:16px;">
              <div>
                <div style="font-size:14px;font-weight:700;margin-bottom:3px;">🤖 AI 인사이트</div>
                <div style="font-size:12px;color:#94a3b8;">
                  Claude AI가 월간 데이터를 분석하여 주요 인사이트와 제언을 제공합니다.
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        def build_monthly_summary() -> str:
            lines = [
                "[월간 유실유기동물 발생현황 요약]",
                f"비교 기간: {label_m2} → {label_m1}", "",
                "■ 전체 접수 건수",
                f"  - {label_m2}: {cnt_m2:,}건",
                f"  - {label_m1}: {cnt_m1:,}건 ({delta_m:+,}건, {delta_pct:+.1f}%)", "",
                "■ 입양률",
                f"  - {label_m2}: {adopt_m2}%",
                f"  - {label_m1}: {adopt_m1}% ({adopt_m1 - adopt_m2:+.1f}%p)", "",
                "■ 안락사율",
                f"  - {label_m2}: {euth_m2}%",
                f"  - {label_m1}: {euth_m1}% ({euth_m1 - euth_m2:+.1f}%p)", "",
                "■ 보호중 건수",
                f"  - {label_m2}: {protect_m2:,}건",
                f"  - {label_m1}: {protect_m1:,}건 ({protect_m1 - protect_m2:+,}건)",
            ]
            if region_col:
                top5_m1 = df_m1["_sido"].value_counts().head(5)
                top5_m2 = df_m2["_sido"].value_counts().head(5)
                lines += ["", f"■ 시/도별 상위 5개 지역 ({label_m1})"]
                for sido, cnt in top5_m1.items():
                    prev = top5_m2.get(sido, 0)
                    lines.append(f"  - {sido}: {cnt:,}건 (전월 대비 {cnt - prev:+,}건)")
            if species_col:
                sp_m1 = df_m1[species_col].value_counts()
                sp_m2 = df_m2[species_col].value_counts()
                lines += ["", f"■ 축종별 현황 ({label_m1})"]
                for sp, cnt in sp_m1.items():
                    prev = sp_m2.get(sp, 0)
                    lines.append(f"  - {sp}: {cnt:,}건 (전월 대비 {cnt - prev:+,}건)")
            return "\n".join(lines)

        if st.button("🔍 AI 인사이트 생성", type="primary"):
            try:
                import anthropic
                api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
                if not api_key:
                    st.error("⚠️ Streamlit Secrets에 `ANTHROPIC_API_KEY`가 설정되어 있지 않습니다.")
                else:
                    summary = build_monthly_summary()
                    with st.spinner("Claude AI가 분석 중입니다..."):
                        client = anthropic.Anthropic(api_key=api_key)
                        message = client.messages.create(
                            model="claude-sonnet-4-6",
                            max_tokens=1500,
                            messages=[{
                                "role": "user",
                                "content": f"""당신은 동물복지 정책 분석 전문가입니다.
아래 유실유기동물 월간 통계 데이터를 바탕으로 다음 내용을 한국어로 작성해 주세요:

1. **핵심 요약** (3줄 이내): 이번 달의 가장 중요한 변화
2. **주목할 트렌드**: 긍정적·부정적 신호 각 2~3가지
3. **지역별 특이사항**: 특이한 증감을 보인 지역과 가능한 원인
4. **정책적 제언**: 데이터를 바탕으로 한 실질적 개선 방향 2~3가지
5. **다음 달 모니터링 포인트**: 주의 깊게 봐야 할 지표

데이터:
{summary}

응답은 마크다운 형식으로 작성해 주세요.""",
                            }],
                        )
                        insight_text = message.content[0].text

                    st.markdown(
                        f'<div class="insight-box">{insight_text}</div>',
                        unsafe_allow_html=True,
                    )
                    st.download_button(
                        label="↓ AI 인사이트 다운로드 (txt)",
                        data=insight_text.encode("utf-8"),
                        file_name=f"AI인사이트_{label_m1.replace(' ', '')}.txt",
                        mime="text/plain",
                    )
            except ImportError:
                st.error("⚠️ `anthropic` 패키지가 설치되지 않았습니다. requirements.txt를 확인하세요.")
            except Exception as e:
                st.error(f"AI 인사이트 생성 중 오류: {e}")

        st.divider()
        csv_m1 = df_m1.drop(columns=["_date", "_sido"], errors="ignore").to_csv(
            index=False, encoding="utf-8-sig"
        ).encode("utf-8-sig")
        st.download_button(
            label=f"↓ {label_m1} 데이터 다운로드",
            data=csv_m1,
            file_name=f"유실유기동물_월간_{first_of_m1.strftime('%Y%m')}.csv",
            mime="text/csv",
        )
