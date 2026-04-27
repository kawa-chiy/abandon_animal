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

# ── CSS 주입 (@import 방식 – <link> 태그 미사용) ──────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], * { font-family: 'Noto Sans KR', sans-serif !important; }

.stApp { background-color: #f3f6f9 !important; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; max-width: 100% !important; }

/* 다크 사이드바 */
[data-testid="stSidebar"] { background-color: #151f32 !important; }
[data-testid="stSidebar"] > div:first-child { background-color: #151f32 !important; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color: #e2e8f0 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #f1f5f9 !important; }
[data-testid="stSidebar"] small { color: #64748b !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.07) !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div { background-color: rgba(255,255,255,0.06) !important; border-color: rgba(255,255,255,0.12) !important; color: #e2e8f0 !important; }
[data-testid="stSidebar"] [data-baseweb="tag"] { background-color: rgba(13,148,136,0.3) !important; color: #5eead4 !important; }
[data-testid="stSidebar"] input[type="date"] { background-color: rgba(255,255,255,0.06) !important; border-color: rgba(255,255,255,0.12) !important; color: #e2e8f0 !important; color-scheme: dark; border-radius: 7px; }
[data-testid="stSidebar"] .stButton > button { background-color: rgba(255,255,255,0.06) !important; border: 1px solid rgba(255,255,255,0.12) !important; color: #94a3b8 !important; border-radius: 8px !important; font-size: 12px !important; }
[data-testid="stSidebar"] .stButton > button:hover { background-color: rgba(255,255,255,0.12) !important; color: #e2e8f0 !important; }
[data-testid="stSidebar"] details { background: rgba(255,255,255,0.04) !important; border-color: rgba(255,255,255,0.08) !important; border-radius: 8px !important; }
[data-testid="stSidebar"] details summary { color: #94a3b8 !important; font-size: 12px !important; }
[data-testid="stSidebar"] [data-testid="stExpanderDetails"] * { color: #94a3b8 !important; font-size: 11px !important; }

/* 탭 */
.stTabs [data-baseweb="tab-list"] { background-color: #e2e8f0 !important; border-radius: 8px !important; padding: 3px !important; gap: 2px !important; border-bottom: none !important; }
.stTabs [data-baseweb="tab"] { border-radius: 6px !important; font-size: 12.5px !important; font-weight: 500 !important; color: #64748b !important; padding: 6px 16px !important; background: transparent !important; border: none !important; }
.stTabs [aria-selected="true"] { background-color: #ffffff !important; color: #0f172a !important; font-weight: 600 !important; box-shadow: 0 1px 3px rgba(15,23,42,0.08) !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

/* 다운로드 버튼 */
.stDownloadButton > button { background: #ffffff !important; border: 1px solid #e8edf2 !important; color: #0f172a !important; border-radius: 8px !important; font-size: 12.5px !important; font-weight: 500 !important; }
.stDownloadButton > button:hover { background: #f8fafc !important; border-color: #0d9488 !important; color: #0d9488 !important; }

/* Primary 버튼 */
.stButton > button[kind="primary"] { background: linear-gradient(135deg, #6366f1, #0d9488) !important; border: none !important; border-radius: 9px !important; font-size: 13px !important; font-weight: 600 !important; box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important; }

/* 데이터프레임 */
[data-testid="stDataFrame"] { border-radius: 8px !important; overflow: hidden !important; border: 1px solid #e8edf2 !important; }

/* 스크롤바 */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 99px; }
</style>
""", unsafe_allow_html=True)


# ── 공통 Plotly 레이아웃 테마 ─────────────────────────────────────────────────
CHART_THEME = dict(
    font=dict(family="Noto Sans KR, Apple SD Gothic Neo, sans-serif", size=12),
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    margin=dict(t=40, b=36, l=36, r=16),
)

C_TEAL   = "#0d9488"
C_AMBER  = "#f59e0b"
C_INDIGO = "#6366f1"
C_ROSE   = "#e11d48"
C_GRAY   = "#94a3b8"
TEAL_SCALE = ["#0f766e", "#0d9488", "#14b8a6", "#2dd4bf", "#5eead4", "#99f6e4"]


# ── 헬퍼: KPI 카드 (100% 인라인 스타일) ──────────────────────────────────────
def kpi_card(label: str, value: str, delta: str = None,
             delta_type: str = "neutral", color: str = "teal") -> str:
    border_map = {"teal": "#0d9488", "amber": "#d97706", "rose": "#e11d48", "indigo": "#6366f1"}
    delta_bg   = {"up": "#dcfce7", "down": "#fee2e2", "neutral": "#f1f5f9"}
    delta_fg   = {"up": "#166534", "down": "#991b1b", "neutral": "#64748b"}
    border = border_map.get(color, "#0d9488")
    delta_html = ""
    if delta:
        arrow = "▲ " if delta_type == "up" else ("▼ " if delta_type == "down" else "")
        bg = delta_bg.get(delta_type, "#f1f5f9")
        fg = delta_fg.get(delta_type, "#64748b")
        delta_html = (
            f'<span style="display:inline-flex;align-items:center;gap:4px;'
            f'font-size:11px;font-weight:500;padding:2px 8px;border-radius:99px;'
            f'background:{bg};color:{fg};">{arrow}{delta}</span>'
        )
    return (
        f'<div style="background:#ffffff;border-radius:12px;padding:18px 20px;'
        f'box-shadow:0 1px 3px rgba(15,23,42,0.06),0 1px 2px rgba(15,23,42,0.04);'
        f'border-left:3px solid {border};overflow:hidden;">'
        f'<div style="font-size:11.5px;font-weight:500;color:#64748b;margin-bottom:8px;">{label}</div>'
        f'<div style="font-size:26px;font-weight:700;color:#0f172a;line-height:1;'
        f'margin-bottom:8px;letter-spacing:-0.03em;">{value}</div>'
        f'{delta_html}</div>'
    )


def kpi_grid(*cards: str):
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            st.markdown(card, unsafe_allow_html=True)


# ── 헬퍼: 차트 섹션 헤더 ─────────────────────────────────────────────────────
def chart_header(icon: str, title: str):
    st.markdown(
        f'<div style="font-size:13px;font-weight:600;color:#0f172a;'
        f'display:flex;align-items:center;gap:7px;margin-bottom:4px;">'
        f'{icon}&nbsp;{title}</div>',
        unsafe_allow_html=True,
    )


# ── 헬퍼: 보고서 상단 배지 ───────────────────────────────────────────────────
def report_badge(text: str):
    st.markdown(
        f'<div style="display:inline-flex;align-items:center;gap:8px;'
        f'padding:6px 14px;background:#f0fdfa;border-radius:8px;'
        f'font-size:12px;font-weight:500;color:#0d9488;margin-bottom:16px;">'
        f'{text}</div>',
        unsafe_allow_html=True,
    )


# ── Secrets 로드 ──────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID     = st.secrets["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI         = st.secrets["REDIRECT_URI"]
WHITELIST_SHEET_ID   = st.secrets["WHITELIST_SHEET_ID"]
WHITELIST_GID        = int(st.secrets.get("WHITELIST_GID", 0))

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
    if pd.isna(val): return "미상"
    s = str(val).strip()
    for short, full in SIDO_MAP.items():
        if s.startswith(full) or s.startswith(short): return full
    return s.split()[0] if s else "미상"


# ── Google OAuth ──────────────────────────────────────────────────────────────
def get_google_auth_url(state: str) -> str:
    params = {
        "client_id": GOOGLE_CLIENT_ID, "redirect_uri": REDIRECT_URI,
        "response_type": "code", "scope": "openid email profile",
        "state": state, "access_type": "online", "prompt": "select_account",
    }
    return AUTHORIZATION_URL + "?" + urllib.parse.urlencode(params)


def exchange_code_for_userinfo(code: str) -> dict | None:
    try:
        token_resp = requests.post(TOKEN_URL, data={
            "code": code, "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI, "grant_type": "authorization_code",
        }, timeout=10)
        access_token = token_resp.json().get("access_token")
        if not access_token: return None
        return requests.get(USERINFO_URL,
                            headers={"Authorization": f"Bearer {access_token}"},
                            timeout=10).json()
    except Exception:
        return None


# ── 화이트리스트 ──────────────────────────────────────────────────────────────
def load_whitelist() -> set:
    creds_info = json.loads(json.dumps(dict(st.secrets["gcp_service_account"])))
    gc = gspread.service_account_from_dict(creds_info)
    sh = gc.open_by_key(WHITELIST_SHEET_ID)
    ws = next((w for w in sh.worksheets() if w.id == WHITELIST_GID), sh.worksheets()[0])
    return {str(r.get("email", "")).strip().lower()
            for r in ws.get_all_records() if r.get("email")}


# ── 로그인 화면 ───────────────────────────────────────────────────────────────
def show_login_page():
    params = st.query_params
    code = params.get("code")

    if code:
        with st.spinner("Google 계정을 확인하는 중..."):
            user_info = exchange_code_for_userinfo(code)
        if not user_info or "email" not in user_info:
            st.error("⚠️ Google 인증에 실패했습니다. 다시 시도해 주세요.")
            st.query_params.clear(); st.stop()

        email = user_info["email"].strip().lower()
        try:
            whitelist = load_whitelist()
        except Exception as e:
            st.error(f"⚠️ 접근권한 시트를 불러올 수 없습니다.\n\n오류: `{type(e).__name__}: {e}`")
            st.code(traceback.format_exc(), language="text")
            st.query_params.clear(); st.stop()

        if email not in whitelist:
            st.error(f"❌ **{email}** 은(는) 접근 권한이 없는 계정입니다.\n관리자에게 접근 권한을 요청하세요.")
            st.query_params.clear(); st.stop()

        st.session_state.update({
            "authenticated": True, "user_email": email,
            "user_name": user_info.get("name") or email,
            "user_picture": user_info.get("picture", ""),
        })
        st.query_params.clear(); st.rerun(); return

    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center;margin-bottom:8px;">'
            '<div style="width:60px;height:60px;border-radius:16px;'
            'background:linear-gradient(135deg,#0d9488,#6366f1);'
            'display:flex;align-items:center;justify-content:center;'
            'font-size:28px;margin:0 auto 16px;">🐾</div></div>'
            '<h2 style="text-align:center;margin-bottom:4px;font-size:20px;'
            'font-weight:700;color:#0f172a;">유실유기동물 현황 대시보드</h2>'
            '<p style="text-align:center;color:#64748b;margin-bottom:32px;font-size:13px;">'
            '동물자유연대 구성원 전용입니다.</p>',
            unsafe_allow_html=True,
        )
        if "oauth_state" not in st.session_state:
            st.session_state["oauth_state"] = secrets.token_hex(16)
        st.link_button("🔐 Google 계정으로 로그인",
                       get_google_auth_url(st.session_state["oauth_state"]),
                       use_container_width=True, type="primary")
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("접근 권한 요청: 관리자에게 Google 계정 이메일 주소를 알려주세요.")


# ── 인증 게이트 ───────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    show_login_page(); st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#   로그인 후 실행
# ══════════════════════════════════════════════════════════════════════════════

COL_CANDIDATES = {
    "date":    ["접수일", "발생일시", "noticeEdDt", "happenDt", "접수일자", "발생일"],
    "region":  ["관할기관", "orgNm", "careNm", "보호기관", "시군구"],
    "status":  ["처리상태", "processState", "상태", "state"],
    "species": ["축종", "kindCd", "동물종류", "종류"],
    "breed":   ["품종", "breed", "kindNm"],
}

def detect_col(df: pd.DataFrame, key: str) -> str | None:
    for c in COL_CANDIDATES[key]:
        if c in df.columns: return c
    kws = {
        "date": ["일"], "region": ["기관", "지역", "시군"],
        "status": ["상태"], "species": ["종류", "축종"], "breed": ["품종"],
    }
    for c in df.columns:
        if any(kw in c for kw in kws.get(key, [])): return c
    return None


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    creds_info = json.loads(json.dumps(dict(st.secrets["gcp_service_account"])))
    gc = gspread.service_account_from_dict(creds_info)
    sh = gc.open_by_key(WHITELIST_SHEET_ID)
    ws = sh.worksheet("summary")
    values = ws.get_all_values()
    if not values: return pd.DataFrame()
    return pd.DataFrame(values[1:], columns=values[0]).astype(str)


def parse_date_col(series: pd.Series) -> pd.Series:
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try: return pd.to_datetime(series.str[:10], format=fmt, errors="coerce")
        except Exception: continue
    return pd.to_datetime(series, errors="coerce")


# ── 데이터 로드 ────────────────────────────────────────────────────────────────
with st.spinner("데이터를 불러오는 중..."):
    try:
        df_raw = load_data()
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}"); st.stop()

date_col    = detect_col(df_raw, "date")
region_col  = detect_col(df_raw, "region")
status_col  = detect_col(df_raw, "status")
species_col = detect_col(df_raw, "species")
breed_col   = detect_col(df_raw, "breed")

df = df_raw.copy()
if date_col:   df["_date"] = parse_date_col(df[date_col])
if region_col: df["_sido"] = df[region_col].apply(extract_sido)


# ── 상단 헤더바 ───────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="display:flex;align-items:center;justify-content:space-between;'
    f'background:#ffffff;border-bottom:1px solid #e8edf2;'
    f'padding:14px 0 12px;margin-bottom:20px;">'
    f'<div style="display:flex;align-items:center;gap:10px;">'
    f'<span style="font-size:18px;">🐾</span>'
    f'<span style="font-size:16px;font-weight:700;color:#0f172a;">유실유기동물 현황 대시보드</span>'
    f'</div>'
    f'<span style="font-size:11.5px;color:#94a3b8;">'
    f'데이터 출처: Google Sheets · 매일 자동 갱신 · 마지막 조회: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    f'</span></div>',
    unsafe_allow_html=True,
)


# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="padding:8px 0 16px;">'
        '<div style="display:flex;align-items:center;gap:10px;">'
        '<div style="width:34px;height:34px;border-radius:10px;background:#0d9488;'
        'display:flex;align-items:center;justify-content:center;font-size:16px;">🐾</div>'
        '<div>'
        '<div style="color:#ffffff;font-weight:600;font-size:13px;">유실유기동물</div>'
        '<div style="color:#94a3b8;font-size:11px;margin-top:1px;">현황 대시보드</div>'
        '</div></div></div>',
        unsafe_allow_html=True,
    )

    name    = st.session_state["user_name"]
    email   = st.session_state["user_email"]
    picture = st.session_state.get("user_picture", "")
    initial = name[0] if name else "?"
    avatar  = (
        f"<img src='{picture}' style='width:36px;height:36px;border-radius:50%;'>"
        if picture else
        f"<div style='width:36px;height:36px;border-radius:50%;font-size:14px;"
        f"background:linear-gradient(135deg,#0d9488,#6366f1);font-weight:600;"
        f"display:flex;align-items:center;justify-content:center;color:white;flex-shrink:0;'>{initial}</div>"
    )
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;padding:12px 0 14px;'
        f'border-top:1px solid rgba(255,255,255,0.07);border-bottom:1px solid rgba(255,255,255,0.07);">'
        f'{avatar}'
        f'<div style="flex:1;min-width:0;">'
        f'<div style="color:#f1f5f9;font-size:13px;font-weight:500;white-space:nowrap;'
        f'overflow:hidden;text-overflow:ellipsis;">{name} 님 환영합니다 👋</div>'
        f'<div style="color:#64748b;font-size:11px;white-space:nowrap;'
        f'overflow:hidden;text-overflow:ellipsis;">{email}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    if st.button("로그아웃", use_container_width=True):
        for k in ["authenticated", "user_email", "user_name", "user_picture", "oauth_state"]:
            st.session_state.pop(k, None)
        st.rerun()

    st.divider()
    st.markdown(
        '<div style="color:#475569;font-size:10px;font-weight:600;'
        'letter-spacing:0.08em;text-transform:uppercase;margin-bottom:10px;">필터</div>',
        unsafe_allow_html=True,
    )

    selected_sidos = []
    if region_col:
        all_sidos = sorted(df["_sido"].dropna().unique().tolist())
        selected_sidos = st.multiselect("시/도 (지역)", options=all_sidos, default=[],
                                        placeholder="전체 (미선택 시 전체 표시)")

    selected_statuses = []
    if status_col:
        all_statuses = sorted(df[status_col].dropna().unique().tolist())
        selected_statuses = st.multiselect("처리 상태", options=all_statuses, default=[],
                                           placeholder="전체 (미선택 시 전체 표시)")

    date_range = None
    if date_col and df["_date"].notna().any():
        min_date = df["_date"].min().date()
        max_date = df["_date"].max().date()
        date_range = st.date_input("접수일 범위", value=(min_date, max_date),
                                   min_value=min_date, max_value=max_date)

    st.divider()
    st.markdown(
        '<div style="color:#475569;font-size:10px;font-weight:600;'
        'letter-spacing:0.08em;text-transform:uppercase;margin-top:8px;margin-bottom:6px;">🗂 컬럼 목록</div>',
        unsafe_allow_html=True,
    )
    st.write(df_raw.columns.tolist())


# ── 필터 적용 ─────────────────────────────────────────────────────────────────
filtered = df.copy()
if selected_sidos and region_col:
    filtered = filtered[filtered["_sido"].isin(selected_sidos)]
if selected_statuses and status_col:
    filtered = filtered[filtered[status_col].isin(selected_statuses)]
if date_range and len(date_range) == 2 and date_col:
    s, e = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    filtered = filtered[filtered["_date"].between(s, e)]


# ── 탭 ───────────────────────────────────────────────────────────────────────
tab_dash, tab_daily, tab_monthly = st.tabs(["📊 대시보드", "📅 일간 보고서", "📆 월간 보고서"])


# ══════════════════════════════════════════════════════════════════════════════
#   탭 1: 대시보드
# ══════════════════════════════════════════════════════════════════════════════
with tab_dash:
    total      = len(filtered)
    total_all  = len(df)
    is_filtered = bool(selected_sidos or selected_statuses)

    def rate(keyword: str, src=None) -> float:
        d = src if src is not None else filtered
        if not status_col or len(d) == 0: return 0.0
        return round(d[status_col].str.contains(keyword, na=False).sum() / len(d) * 100, 1)

    adoption_rate   = rate("입양")
    euthanasia_rate = rate("안락사")
    adoption_all    = rate("입양", df)
    euthanasia_all  = rate("안락사", df)
    protect_cnt     = filtered[status_col].str.contains("보호중", na=False).sum() if status_col else 0

    kpi_grid(
        kpi_card("총 발생 건수", f"{total:,}건",
                 f"전체 {total_all:,}건 중" if is_filtered else None, "neutral", "teal"),
        kpi_card("입양률", f"{adoption_rate}%",
                 f"{adoption_rate - adoption_all:+.1f}%p (전체 대비)" if is_filtered else None,
                 "up" if adoption_rate >= adoption_all else "down", "amber"),
        kpi_card("안락사율", f"{euthanasia_rate}%",
                 f"{euthanasia_rate - euthanasia_all:+.1f}%p (전체 대비)" if is_filtered else None,
                 "down" if euthanasia_rate > euthanasia_all else "up", "rose"),
        kpi_card("현재 보호중", f"{protect_cnt:,}건", color="indigo"),
    )

    r1l, r1r = st.columns([3, 2])

    with r1l:
        chart_header("📈", "최근 30일 일별 유기동물 발생 추이")
        if date_col and df["_date"].notna().any():
            cutoff = filtered["_date"].max() - timedelta(days=29)
            recent = filtered[filtered["_date"] >= cutoff].copy()
            daily = (recent.groupby(recent["_date"].dt.date).size()
                     .reset_index(name="발생 건수").rename(columns={"_date": "접수일"}))
            if not daily.empty:
                fr = pd.date_range(daily["접수일"].min(), daily["접수일"].max())
                daily = (daily.set_index("접수일").reindex(fr.date, fill_value=0)
                         .reset_index().rename(columns={"index": "접수일"}))
            fig = px.line(daily, x="접수일", y="발생 건수", markers=True,
                          color_discrete_sequence=[C_TEAL])
            fig.update_traces(line=dict(width=2.5), marker=dict(size=5),
                              fill="tozeroy", fillcolor="rgba(13,148,136,0.08)")
            fig.update_xaxes(tickformat="%m/%d", tickangle=-30, showgrid=False, showline=False)
            fig.update_yaxes(gridcolor="#f1f5f9", showline=False)
            fig.update_layout(**CHART_THEME)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("날짜 컬럼을 감지하지 못해 추이 차트를 표시할 수 없습니다.")

    with r1r:
        chart_header("🌿", "축종·품종별 비율 (상위 30)")
        if species_col or breed_col:
            path = [c for c in [species_col, breed_col] if c]
            top = filtered.groupby(path).size().reset_index(name="건수").nlargest(30, "건수")
            fig = px.treemap(top, path=path, values="건수",
                             color="건수", color_continuous_scale=TEAL_SCALE)
            fig.update_traces(
                textinfo="label+percent parent",
                hovertemplate="<b>%{label}</b><br>건수: %{value:,}<br>비율: %{percentParent:.1%}<extra></extra>")
            fig.update_layout(**CHART_THEME)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("축종/품종 컬럼을 감지하지 못했습니다.")

    r2l, r2r = st.columns(2)

    with r2l:
        chart_header("🔄", "처리 상태 비율")
        if status_col:
            sc = filtered[status_col].value_counts().reset_index()
            sc.columns = ["처리 상태", "건수"]
            color_map = {"보호중": "#3b82f6", "입양": "#10b981", "자연사": "#94a3b8",
                         "안락사": "#f87171", "반환": "#f59e0b", "기증": "#a78bfa", "방사": "#34d399"}
            colors = [color_map.get(s, "#94a3b8") for s in sc["처리 상태"]]
            fig = go.Figure(go.Pie(
                labels=sc["처리 상태"], values=sc["건수"], hole=0.52,
                marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
                textposition="outside", textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>%{value:,}건<br>%{percent}<extra></extra>",
            ))
            fig.update_layout(
                **CHART_THEME, showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.25,
                            xanchor="center", x=0.5, font=dict(size=11)),
                annotations=[dict(text=f"{total:,}건", x=0.5, y=0.5,
                                  font=dict(size=14, color="#0f172a"), showarrow=False)],
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("처리 상태 컬럼을 감지하지 못했습니다.")

    with r2r:
        chart_header("📍", "시/도별 접수 건수")
        if region_col:
            sc = filtered["_sido"].value_counts().reset_index()
            sc.columns = ["시/도", "건수"]
            fig = px.bar(sc, x="건수", y="시/도", orientation="h",
                         text="건수", color="건수", color_continuous_scale=TEAL_SCALE)
            fig.update_traces(textposition="outside", marker=dict(line=dict(width=0)))
            fig.update_yaxes(autorange="reversed", tickfont=dict(size=11), showline=False)
            fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9", showline=False, zeroline=False)
            fig.update_layout(**CHART_THEME, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("관할기관 컬럼을 감지하지 못했습니다.")

    st.divider()
    chart_header("📋", "상세 데이터")
    display_df = filtered.drop(columns=["_date", "_sido"], errors="ignore")
    st.dataframe(display_df, use_container_width=True, height=380)
    st.download_button(
        label="↓ 필터 결과 CSV 다운로드",
        data=display_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
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

    report_badge(
        f'📅 일간 발생현황 보고서 &nbsp;·&nbsp; '
        f'기준: <b>{d1.strftime("%Y년 %m월 %d일")}</b> (전일) vs '
        f'<b>{d2.strftime("%Y년 %m월 %d일")}</b> (전전일)'
    )

    if not date_col or not df["_date"].notna().any():
        st.warning("날짜 컬럼을 감지하지 못해 일간 보고서를 표시할 수 없습니다.")
    else:
        df_d1 = df[df["_date"].dt.date == d1]
        df_d2 = df[df["_date"].dt.date == d2]
        cnt_d1, cnt_d2 = len(df_d1), len(df_d2)
        delta_cnt = cnt_d1 - cnt_d2

        def daily_rate(df_sub, keyword):
            if not status_col or len(df_sub) == 0: return 0.0
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
            kpi_card(f"전전일({d2.strftime('%m/%d')}) 접수", f"{cnt_d2:,}건", color="indigo"),
        )

        col_l, col_r = st.columns(2)
        with col_l:
            chart_header("📍", "시/도별 접수 건수 비교")
            if region_col:
                sido_d1 = df_d1["_sido"].value_counts().rename("전일")
                sido_d2 = df_d2["_sido"].value_counts().rename("전전일")
                cmp = pd.concat([sido_d1, sido_d2], axis=1).fillna(0).astype(int)
                cmp["증감"] = cmp["전일"] - cmp["전전일"]
                cmp = cmp.sort_values("전일", ascending=False).reset_index()
                cmp.columns = ["시/도", "전일", "전전일", "증감"]
                fig = go.Figure()
                fig.add_bar(name=f"전전일({d2.strftime('%m/%d')})",
                            x=cmp["시/도"], y=cmp["전전일"], marker_color=C_GRAY)
                fig.add_bar(name=f"전일({d1.strftime('%m/%d')})",
                            x=cmp["시/도"], y=cmp["전일"], marker_color=C_TEAL)
                fig.update_layout(**CHART_THEME, barmode="group", xaxis_tickangle=-30)
                st.plotly_chart(fig, use_container_width=True)
                cmp["증감"] = cmp["증감"].apply(lambda x: f"{x:+,}")
                st.dataframe(cmp, use_container_width=True, hide_index=True)
            else:
                st.info("지역 컬럼을 감지하지 못했습니다.")

        with col_r:
            chart_header("🐾", "축종별 접수 건수 비교")
            if species_col:
                sp_d1 = df_d1[species_col].value_counts().rename("전일")
                sp_d2 = df_d2[species_col].value_counts().rename("전전일")
                cmp = pd.concat([sp_d1, sp_d2], axis=1).fillna(0).astype(int)
                cmp["증감"] = cmp["전일"] - cmp["전전일"]
                cmp = cmp.sort_values("전일", ascending=False).reset_index()
                cmp.columns = ["축종", "전일", "전전일", "증감"]
                fig = go.Figure()
                fig.add_bar(name=f"전전일({d2.strftime('%m/%d')})",
                            x=cmp["축종"], y=cmp["전전일"], marker_color=C_GRAY)
                fig.add_bar(name=f"전일({d1.strftime('%m/%d')})",
                            x=cmp["축종"], y=cmp["전일"], marker_color=C_AMBER)
                fig.update_layout(**CHART_THEME, barmode="group")
                st.plotly_chart(fig, use_container_width=True)
                cmp["증감"] = cmp["증감"].apply(lambda x: f"{x:+,}")
                st.dataframe(cmp, use_container_width=True, hide_index=True)
            else:
                st.info("축종 컬럼을 감지하지 못했습니다.")

        st.divider()
        chart_header("📋", "전일 상세 데이터")
        if cnt_d1 > 0:
            d1_df = df_d1.drop(columns=["_date", "_sido"], errors="ignore")
            st.dataframe(d1_df, use_container_width=True, height=300)
            st.download_button(
                label=f"↓ 전일({d1.strftime('%Y%m%d')}) 데이터 다운로드",
                data=d1_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
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
    last_of_m1  = first_of_this_month - timedelta(days=1)
    first_of_m1 = last_of_m1.replace(day=1)
    last_of_m2  = first_of_m1 - timedelta(days=1)
    first_of_m2 = last_of_m2.replace(day=1)
    label_m1 = first_of_m1.strftime("%Y년 %m월")
    label_m2 = first_of_m2.strftime("%Y년 %m월")

    report_badge(
        f'📆 월간 발생현황 보고서 &nbsp;·&nbsp; '
        f'비교: <b>{label_m1}</b> (전월) vs <b>{label_m2}</b> (전전월)'
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
            if not status_col or len(df_sub) == 0: return 0.0
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
            chart_header("📍", "시/도별 접수 건수")
            if region_col:
                sido_m1 = df_m1["_sido"].value_counts().rename(label_m1)
                sido_m2 = df_m2["_sido"].value_counts().rename(label_m2)
                cmp = pd.concat([sido_m1, sido_m2], axis=1).fillna(0).astype(int)
                cmp["증감"] = cmp[label_m1] - cmp[label_m2]
                cmp = cmp.sort_values(label_m1, ascending=False).reset_index()
                cmp.columns = ["시/도", label_m1, label_m2, "증감"]
                fig = go.Figure()
                fig.add_bar(name=label_m2, x=cmp["시/도"], y=cmp[label_m2], marker_color=C_GRAY)
                fig.add_bar(name=label_m1, x=cmp["시/도"], y=cmp[label_m1], marker_color=C_INDIGO)
                fig.update_layout(**CHART_THEME, barmode="group", xaxis_tickangle=-30)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("지역 컬럼을 감지하지 못했습니다.")

        with col_r:
            chart_header("📈", f"{label_m1} 일별 발생 추이")
            if cnt_m1 > 0:
                dm1 = (df_m1.groupby(df_m1["_date"].dt.date).size()
                       .reset_index(name="건수").rename(columns={"_date": "날짜"}))
                days_in = calendar.monthrange(first_of_m1.year, first_of_m1.month)[1]
                full = pd.date_range(first_of_m1, periods=days_in)
                dm1 = (dm1.set_index("날짜").reindex(full.date, fill_value=0)
                        .reset_index().rename(columns={"index": "날짜"}))
                fig = px.bar(dm1, x="날짜", y="건수", color_discrete_sequence=[C_INDIGO])
                fig.update_layout(**CHART_THEME)
                fig.update_xaxes(tickformat="%d일", tickangle=-30, showgrid=False)
                fig.update_yaxes(gridcolor="#f1f5f9")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"{label_m1} 데이터가 없습니다.")

        st.divider()

        if status_col:
            chart_header("🔄", "처리 상태 비교")
            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown(
                    f'<div style="font-size:12px;font-weight:600;color:#64748b;margin-bottom:8px;">{label_m2}</div>',
                    unsafe_allow_html=True)
                s2 = df_m2[status_col].value_counts().reset_index()
                s2.columns = ["처리 상태", "건수"]
                fig = px.pie(s2, names="처리 상태", values="건수", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_traces(textposition="outside", textinfo="percent+label")
                fig.update_layout(**CHART_THEME)
                st.plotly_chart(fig, use_container_width=True)
            with sc2:
                st.markdown(
                    f'<div style="font-size:12px;font-weight:600;color:#64748b;margin-bottom:8px;">{label_m1}</div>',
                    unsafe_allow_html=True)
                s1 = df_m1[status_col].value_counts().reset_index()
                s1.columns = ["처리 상태", "건수"]
                fig = px.pie(s1, names="처리 상태", values="건수", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_traces(textposition="outside", textinfo="percent+label")
                fig.update_layout(**CHART_THEME)
                st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # ── AI 인사이트 ───────────────────────────────────────────────────────
        st.markdown(
            '<div style="display:flex;align-items:flex-start;margin-bottom:14px;gap:16px;">'
            '<div>'
            '<div style="font-size:14px;font-weight:700;margin-bottom:3px;">🤖 AI 인사이트</div>'
            '<div style="font-size:12px;color:#94a3b8;">'
            'Claude AI가 월간 데이터를 분석하여 주요 인사이트와 제언을 제공합니다.'
            '</div></div></div>',
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
                    lines.append(f"  - {sido}: {cnt:,}건 (전월 대비 {cnt - top5_m2.get(sido, 0):+,}건)")
            if species_col:
                sp_m1 = df_m1[species_col].value_counts()
                sp_m2 = df_m2[species_col].value_counts()
                lines += ["", f"■ 축종별 현황 ({label_m1})"]
                for sp, cnt in sp_m1.items():
                    lines.append(f"  - {sp}: {cnt:,}건 (전월 대비 {cnt - sp_m2.get(sp, 0):+,}건)")
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
                            messages=[{"role": "user", "content":
                                f"""당신은 동물복지 정책 분석 전문가입니다.
아래 유실유기동물 월간 통계 데이터를 바탕으로 다음 내용을 한국어로 작성해 주세요:

1. **핵심 요약** (3줄 이내): 이번 달의 가장 중요한 변화
2. **주목할 트렌드**: 긍정적·부정적 신호 각 2~3가지
3. **지역별 특이사항**: 특이한 증감을 보인 지역과 가능한 원인
4. **정책적 제언**: 데이터를 바탕으로 한 실질적 개선 방향 2~3가지
5. **다음 달 모니터링 포인트**: 주의 깊게 봐야 할 지표

데이터:
{summary}

응답은 마크다운 형식으로 작성해 주세요."""}],
                        )
                        insight_text = message.content[0].text

                    st.markdown(
                        f'<div style="background:linear-gradient(135deg,#f5f3ff,#f0fdfa);'
                        f'border:1px solid #ddd6fe;border-radius:12px;padding:20px;margin-top:14px;">'
                        f'{insight_text}</div>',
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
        m1_df = df_m1.drop(columns=["_date", "_sido"], errors="ignore")
        st.download_button(
            label=f"↓ {label_m1} 데이터 다운로드",
            data=m1_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
            file_name=f"유실유기동물_월간_{first_of_m1.strftime('%Y%m')}.csv",
            mime="text/csv",
        )
