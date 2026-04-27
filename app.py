import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import date, timedelta
import random

# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="유실유기동물 현황 대시보드",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# 커스텀 CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif !important;
}

/* ── 배경 ── */
.stApp {
    background: oklch(97.5% 0.006 220);
}

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: #151f32 !important;
    border-right: 1px solid rgba(255,255,255,0.07);
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stDateInput label,
[data-testid="stSidebar"] .stMarkdown p {
    color: #94a3b8 !important;
    font-size: 12px !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}

/* ── 탭 ── */
.stTabs [data-baseweb="tab-list"] {
    background: #f1f5f9;
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
    border: none;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
    color: #64748b;
    background: transparent;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: #0f172a !important;
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(15,23,42,0.08);
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}
.stTabs [data-baseweb="tab-border"] {
    display: none;
}

/* ── 메트릭 카드 ── */
[data-testid="stMetric"] {
    background: #ffffff;
    border-radius: 12px;
    padding: 18px 20px !important;
    box-shadow: 0 1px 3px rgba(15,23,42,0.06), 0 1px 2px rgba(15,23,42,0.04);
}
[data-testid="stMetricLabel"] {
    font-size: 12px !important;
    color: #64748b !important;
    font-weight: 500;
}
[data-testid="stMetricValue"] {
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #0f172a !important;
    letter-spacing: -0.03em;
}
[data-testid="stMetricDelta"] {
    font-size: 12px !important;
    font-weight: 500 !important;
}

/* ── 구분선 ── */
hr {
    border-color: rgba(255,255,255,0.07) !important;
    margin: 12px 0 !important;
}

/* ── 데이터프레임 테이블 ── */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(15,23,42,0.06);
}

/* ── 다운로드 버튼 ── */
.stDownloadButton > button {
    background: #ffffff !important;
    border: 1px solid #e8edf2 !important;
    border-radius: 8px !important;
    color: #0f172a !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 18px !important;
    transition: all 0.15s !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}
.stDownloadButton > button:hover {
    border-color: #0d9488 !important;
    color: #0d9488 !important;
}

/* ── 일반 버튼 ── */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #0d9488) !important;
    border: none !important;
    border-radius: 9px !important;
    color: white !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 10px 22px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.stButton > button:hover {
    opacity: 0.9;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}

/* ── 섹션 헤더 ── */
.section-header {
    font-size: 13px;
    font-weight: 600;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 2px 8px;
    border-bottom: 1px solid #e8edf2;
    margin-bottom: 4px;
}

/* ── KPI 컬러 바 ── */
.kpi-teal  { border-left: 3px solid #0d9488 !important; }
.kpi-amber { border-left: 3px solid #d97706 !important; }
.kpi-rose  { border-left: 3px solid #e11d48 !important; }
.kpi-indigo{ border-left: 3px solid #6366f1 !important; }

/* ── 뱃지 ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: 11.5px;
    font-weight: 500;
    line-height: 1.4;
}
.badge-teal { background: #ccfbf1; color: #0f766e; }
.badge-indigo { background: #e0e7ff; color: #4338ca; }
.badge-amber { background: #fef3c7; color: #92400e; }

/* plotly 툴팁 */
.modebar { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 색상 테마
# ─────────────────────────────────────────────
COLORS = {
    "primary": "#0d9488",
    "primary_light": "#5eead4",
    "secondary": "#f59e0b",
    "indigo": "#6366f1",
    "rose": "#f87171",
    "green": "#10b981",
    "blue": "#3b82f6",
    "gray": "#94a3b8",
    "bg": "#f8fafc",
    "surface": "#ffffff",
    "text": "#0f172a",
    "text2": "#64748b",
}

STATUS_COLORS = {
    "보호중": "#3b82f6",
    "입양":   "#10b981",
    "자연사": "#94a3b8",
    "안락사": "#f87171",
    "반환":   "#f59e0b",
    "기증":   "#a78bfa",
    "방사":   "#34d399",
}

PLOTLY_LAYOUT = dict(
    font=dict(family="Noto Sans KR, sans-serif", size=12, color=COLORS["text2"]),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=16, b=8, l=8, r=8),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(0,0,0,0)",
        font=dict(size=12),
        orientation="h",
        y=-0.15,
    ),
    xaxis=dict(
        showgrid=False,
        showline=False,
        zeroline=False,
        tickfont=dict(size=11),
    ),
    yaxis=dict(
        gridcolor="#f1f5f9",
        showline=False,
        zeroline=False,
        tickfont=dict(size=11),
    ),
    hoverlabel=dict(
        bgcolor=COLORS["surface"],
        bordercolor=COLORS["gray"],
        font=dict(family="Noto Sans KR", size=12, color=COLORS["text"]),
    ),
)


# ─────────────────────────────────────────────
# Mock 데이터
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    random.seed(42)
    np.random.seed(42)

    # 일별 30일 추이
    base = date(2026, 3, 27)
    daily_vals = [312,287,345,298,276,389,401,356,323,298,267,310,345,389,312,298,276,234,298,315,287,345,312,276,298,256,189,245,312,287]
    daily_df = pd.DataFrame({
        "날짜": [base + timedelta(days=i) for i in range(30)],
        "건수": daily_vals,
    })

    # 처리 상태
    status_df = pd.DataFrame({
        "상태": ["보호중", "입양", "자연사", "안락사", "반환", "기증", "방사"],
        "건수": [9537, 4279, 2605, 1954, 1876, 876, 584],
    })

    # 시/도별
    sido_df = pd.DataFrame({
        "지역": ["경기도","경상남도","전라남도","전북특별자치도","경상북도","충청남도","강원특별자치도","제주특별자치도","충청북도","서울특별시","부산광역시","인천광역시","울산광역시","광주광역시","대구광역시","세종특별자치시"],
        "건수_03월": [4082,2404,2350,2180,1879,1358,958,857,846,840,829,601,400,341,271,82],
        "건수_02월": [3770,2315,2238,2124,1902,1298,921,841,789,802,801,578,387,325,258,79],
    })

    # 상세 데이터
    table_df = pd.DataFrame([
        {"공고번호":"대전-동구-2026-00015","발생일자":"2026.01.31","발생장소":"용운동 에프포레시 1동 앞","축종":"개","품종":"말티즈","나이":"2025(년)","처리상태":"입양","특이사항":"수국 제빵 엄마 파름"},
        {"공고번호":"대전-동구-2026-00314","발생일자":"2026.02.03","발생장소":"가오동 대전본47번길","축종":"고양이","품종":"한국고양이","나이":"2025(년)","처리상태":"안락사","특이사항":"안면부골절, 척추 손상"},
        {"공고번호":"경기-성남-2026-03022","발생일자":"2026.02.12","발생장소":"판교역 인근 공원","축종":"개","품종":"포메라니안","나이":"2024(년)","처리상태":"보호중","특이사항":"-"},
        {"공고번호":"서울-강남-2026-00891","발생일자":"2026.02.19","발생장소":"역삼동 테헤란로 인근","축종":"고양이","품종":"코리안숏헤어","나이":"미상","처리상태":"자연사","특이사항":"외상 없음"},
        {"공고번호":"부산-해운대-2026-01124","발생일자":"2026.03.02","발생장소":"해운대구 우동 해변","축종":"개","품종":"믹스견","나이":"2023(년)","처리상태":"반환","특이사항":"보호자 연락됨"},
        {"공고번호":"경기-수원-2026-02341","발생일자":"2026.03.15","발생장소":"영통구 망포동 공원","축종":"개","품종":"푸들","나이":"2024(년)","처리상태":"입양","특이사항":"-"},
        {"공고번호":"인천-남동-2026-00567","발생일자":"2026.03.21","발생장소":"구월동 로데오거리 인근","축종":"고양이","품종":"코리안숏헤어","나이":"미상","처리상태":"보호중","특이사항":"결막염 치료 중"},
    ])

    # 월별 일별
    monthly_daily = pd.DataFrame({
        "일": [f"{i+1}일" for i in range(31)],
        "건수": [int(200 + abs(np.random.normal(0, 60))) for _ in range(31)],
    })

    return daily_df, status_df, sido_df, table_df, monthly_daily


daily_df, status_df, sido_df, table_df, monthly_daily_df = load_data()


# ─────────────────────────────────────────────
# 차트 헬퍼
# ─────────────────────────────────────────────
def apply_layout(fig, **kwargs):
    base = dict(**PLOTLY_LAYOUT)
    base.update(kwargs)
    fig.update_layout(**base)
    fig.update_traces(hovertemplate='%{y:,}건<extra></extra>')
    return fig


def chart_area(df, x_col, y_col, color=None, title=""):
    color = color or COLORS["primary"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y_col],
        mode="lines",
        line=dict(color=color, width=2.5, shape="spline"),
        fill="tozeroy",
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
        hovertemplate="%{x}<br>%{y:,}건<extra></extra>",
    ))
    apply_layout(fig,
        xaxis=dict(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=10), tickangle=-30, nticks=10),
        yaxis=dict(gridcolor="#f1f5f9", showline=False, zeroline=False, tickfont=dict(size=10)),
        height=240,
    )
    return fig


def chart_donut(labels, values, colors=None, title=""):
    colors = colors or list(STATUS_COLORS.values())
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.52,
        marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
        textfont=dict(size=11, family="Noto Sans KR"),
        hovertemplate="%{label}: %{value:,}건 (%{percent})<extra></extra>",
    ))
    total = sum(values)
    
    # PLOTLY_LAYOUT에서 중복되는 키워드를 미리 제외합니다. (TypeError 방지)
    layout_args = {k: v for k, v in PLOTLY_LAYOUT.items() if k not in ["xaxis", "yaxis", "legend", "margin"]}
    
    fig.update_layout(
        **layout_args,
        annotations=[dict(text=f"<b>{total:,}건</b>", x=0.5, y=0.5, font=dict(size=14, color=COLORS["text"]), showarrow=False)],
        legend=dict(orientation="h", y=-0.12, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        height=290,
        margin=dict(t=10, b=30, l=10, r=10),
    )
    return fig


def chart_hbar(labels, values, color=None, title=""):
    color = color or COLORS["primary"]
    fig = go.Figure(go.Bar(
        y=labels, x=values, orientation="h",
        marker=dict(
            color=values,
            colorscale=[[0, f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.35)"],
                        [1, color]],
            showscale=False,
            cornerradius=4,
        ),
        text=[f"{v:,}" for v in values],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text2"]),
        hovertemplate="%{y}: %{x:,}건<extra></extra>",
    ))
    apply_layout(fig,
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9", showline=False, zeroline=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=11), autorange="reversed"),
        height=380,
        margin=dict(t=10, b=8, l=8, r=50),
    )
    return fig


def chart_grouped_bar(categories, series, colors=None, title=""):
    colors = colors or [COLORS["gray"], COLORS["primary"]]
    fig = go.Figure()
    for i, (name, data) in enumerate(series):
        fig.add_trace(go.Bar(
            name=name, x=categories, y=data,
            marker=dict(color=colors[i % len(colors)], cornerradius=3),
            hovertemplate=f"{name}<br>%{{x}}: %{{y:,}}건<extra></extra>",
        ))
    apply_layout(fig,
        barmode="group",
        bargap=0.25, bargroupgap=0.06,
        xaxis=dict(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=11), tickangle=-30),
        yaxis=dict(gridcolor="#f1f5f9", showline=False, zeroline=False, tickfont=dict(size=10)),
        height=260,
        legend=dict(orientation="h", y=-0.2, font=dict(size=12), bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def chart_treemap(labels, values, parents=None, title=""):
    parents = parents or [""] * len(labels)
    fig = go.Figure(go.Treemap(
        labels=labels,
        values=values,
        parents=parents,
        marker=dict(
            colorscale=[[0,"#99f6e4"],[0.3,"#2dd4bf"],[0.6,"#0d9488"],[1,"#0f766e"]],
            cmin=min(values), cmax=max(values),
            showscale=False,
        ),
        textfont=dict(size=11, family="Noto Sans KR"),
        hovertemplate="%{label}: %{value:,}건<extra></extra>",
        tiling=dict(pad=2),
        texttemplate="%{label}<br>%{value:,}건",
    ))
    apply_layout(fig,
        height=240,
        margin=dict(t=4, b=4, l=4, r=4),
    )
    return fig


def chart_vbar(categories, values, color=None, title=""):
    color = color or COLORS["indigo"]
    fig = go.Figure(go.Bar(
        x=categories, y=values,
        marker=dict(color=color, opacity=0.85, cornerradius=3),
        hovertemplate="%{x}: %{y:,}건<extra></extra>",
    ))
    apply_layout(fig,
        xaxis=dict(showgrid=False, showline=False, zeroline=False, tickfont=dict(size=10), tickangle=-45, nticks=10),
        yaxis=dict(gridcolor="#f1f5f9", showline=False, zeroline=False, tickfont=dict(size=10)),
        height=260,
        margin=dict(t=10, b=10, l=8, r=8),
    )
    return fig


# ─────────────────────────────────────────────
# KPI 카드 (HTML 커스텀)
# ─────────────────────────────────────────────
def kpi_card(label, value, delta, delta_type="neutral", border_color="#0d9488"):
    if delta_type == "up":
        delta_style = "color:#0f766e; background:#ccfbf1;"
        arrow = "▲ "
    elif delta_type == "down":
        delta_style = "color:#e11d48; background:#fee2e2;"
        arrow = "▼ "
    else:
        delta_style = "color:#64748b; background:#f1f5f9;"
        arrow = ""
    return f"""
    <div style="
        background:#ffffff;
        border-radius:12px;
        padding:18px 20px;
        box-shadow:0 1px 3px rgba(15,23,42,0.06);
        border-left:3px solid {border_color};
        min-height:110px;
    ">
        <div style="font-size:12px;font-weight:500;color:#64748b;margin-bottom:10px;">{label}</div>
        <div style="font-size:26px;font-weight:700;color:#0f172a;letter-spacing:-0.03em;line-height:1;margin-bottom:10px;">{value}</div>
        <span style="{delta_style} display:inline-block;padding:2px 9px;border-radius:99px;font-size:11px;font-weight:500;">{arrow}{delta}</span>
    </div>"""


def section_title(icon, text):
    st.markdown(f"""
    <div class="section-header">
        {icon} {text}
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:4px 0 12px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
            <div style="width:34px;height:34px;border-radius:10px;background:#0d9488;display:flex;align-items:center;justify-content:center;font-size:16px;">🐾</div>
            <div>
                <div style="color:#ffffff;font-weight:600;font-size:13px;">유실유기동물</div>
                <div style="color:#94a3b8;font-size:11px;">현황 대시보드</div>
            </div>
        </div>
    </div>
    <hr>
    <div style="display:flex;align-items:center;gap:10px;padding:4px 0 12px;">
        <div style="width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#0d9488,#6366f1);display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;color:white;flex-shrink:0;">채</div>
        <div>
            <div style="color:#f1f5f9;font-size:12.5px;font-weight:500;">채일택 국장님 환영합니다 👋</div>
            <div style="color:#64748b;font-size:11px;">동물자유연대 전략사업국</div>
        </div>
    </div>
    <hr>
    """, unsafe_allow_html=True)

    st.markdown('<div style="color:#475569;font-size:10px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:10px;">필터</div>', unsafe_allow_html=True)

    st.markdown('<div style="color:#94a3b8;font-size:11px;font-weight:500;margin-bottom:4px;">시/도 (지역)</div>', unsafe_allow_html=True)
    sido_options = ["전체 (미선택 시 전체 표시)", "서울특별시", "경기도", "부산광역시", "인천광역시", "대구광역시", "광주광역시", "대전광역시", "경상남도", "경상북도", "전라남도", "전북특별자치도", "충청남도", "충청북도", "강원특별자치도", "제주특별자치도"]
    sido_sel = st.selectbox("시도 선택", sido_options, label_visibility="collapsed")

    st.markdown('<div style="color:#94a3b8;font-size:11px;font-weight:500;margin:10px 0 4px;">처리 상태</div>', unsafe_allow_html=True)
    status_options = ["전체 (미선택 시 전체 표시)", "보호중", "입양", "자연사", "안락사", "반환", "기증", "방사"]
    status_sel = st.selectbox("상태 선택", status_options, label_visibility="collapsed")

    st.markdown('<div style="color:#94a3b8;font-size:11px;font-weight:500;margin:10px 0 4px;">접수일 범위</div>', unsafe_allow_html=True)
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        date_from = st.date_input("시작일", value=date(2026, 1, 1), label_visibility="collapsed")
    with col_d2:
        date_to = st.date_input("종료일", value=date(2026, 4, 26), label_visibility="collapsed")

    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown("""
    <div style="color:#475569;font-size:10.5px;line-height:1.6;padding-bottom:8px;">
        데이터 출처: Google Sheets<br>
        매일 자동 갱신 · 마지막 조회:<br>
        2026-04-27 04:22
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 상단 헤더
# ─────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
    <div>
        <h1 style="font-size:20px;font-weight:700;color:#0f172a;margin:0;display:flex;align-items:center;gap:8px;">
            🐾 유실유기동물 현황 대시보드
        </h1>
        <p style="font-size:12px;color:#94a3b8;margin:4px 0 0;">
            데이터 출처: Google Sheets · 매일 자동 갱신 · 마지막 조회: 2026-04-27 04:22
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 탭
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊  대시보드", "📅  일간 보고서", "📆  월간 보고서"])


# ══════════════════════════════════════════════
#  TAB 1 — 대시보드
# ══════════════════════════════════════════════
with tab1:
    # KPI
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(kpi_card("총 발생 건수", "21,711건", "전체 데이터 기준", "neutral", "#0d9488"), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("입양률", "19.7%", "전년 대비 +1.2%p", "up", "#d97706"), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("안락사율", "9.0%", "전년 대비 −0.8%p", "up", "#e11d48"), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card("현재 보호중", "9,537건", "전월 대비 +234건 ▲", "down", "#6366f1"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Row 1: 추이 + 트리맵
    c1, c2 = st.columns([3, 2])
    with c1:
        section_title("📈", "최근 30일 일별 유기동물 발생 추이")
        fig = chart_area(daily_df, "날짜", "건수")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        section_title("🌿", "축종·품종별 비율 (상위 12)")
        treemap_labels = ["믹스견(개)","코리안숏헤어(고양이)","기타고양이","말티즈(개)","푸들(개)","기타동물","포메라니안(개)","진돗개","시바견","리트리버(개)","비글(개)","치와와(개)"]
        treemap_vals   = [5821, 4102, 1230, 1204, 876, 723, 542, 487, 312, 289, 234, 198]
        fig2 = chart_treemap(treemap_labels, treemap_vals)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # Row 2: 도넛 + 수평 막대
    c3, c4 = st.columns(2)
    with c3:
        section_title("🔄", "처리 상태 비율")
        fig3 = chart_donut(
            labels=status_df["상태"].tolist(),
            values=status_df["건수"].tolist(),
            colors=list(STATUS_COLORS.values()),
        )
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with c4:
        section_title("📍", "시/도별 접수 건수")
        fig4 = chart_hbar(
            labels=sido_df["지역"].tolist(),
            values=sido_df["건수_03월"].tolist(),
        )
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

    # 데이터 테이블
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section_title("📋", "상세 데이터")

    # 상태 컬럼 색 표현
    display_df = table_df.copy()
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=280,
        column_config={
            "처리상태": st.column_config.TextColumn("처리상태"),
            "공고번호": st.column_config.TextColumn("공고번호", width="medium"),
            "발생장소": st.column_config.TextColumn("발생장소", width="large"),
            "특이사항": st.column_config.TextColumn("특이사항", width="large"),
        }
    )

    csv = table_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("↓  CSV 다운로드", data=csv.encode("utf-8-sig"), file_name="유실유기동물_전체.csv", mime="text/csv")


# ══════════════════════════════════════════════
#  TAB 2 — 일간 보고서
# ══════════════════════════════════════════════
with tab2:
    st.markdown("""
    <div style="display:inline-flex;align-items:center;gap:8px;padding:6px 16px;
        background:#ccfbf1;border-radius:8px;font-size:12px;font-weight:500;
        color:#0f766e;margin-bottom:20px;">
        📅 기준일: 2026년 04월 26일 (전일) vs 2026년 04월 25일 (전전일)
    </div>
    """, unsafe_allow_html=True)

    # KPI
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.markdown(kpi_card("전일(04/26) 접수", "287건", "−25건 (전전일 대비)", "up", "#0d9488"), unsafe_allow_html=True)
    with d2:
        st.markdown(kpi_card("입양률", "21.3%", "+1.6%p", "up", "#d97706"), unsafe_allow_html=True)
    with d3:
        st.markdown(kpi_card("안락사율", "8.4%", "−0.6%p", "up", "#e11d48"), unsafe_allow_html=True)
    with d4:
        st.markdown(kpi_card("보호중", "123건", "+12건", "down", "#6366f1"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    dc1, dc2 = st.columns(2)
    with dc1:
        section_title("📍", "시/도별 접수 건수 비교")
        sido_cats = ["경기도","경남","전남","전북","경북","충남","강원","제주","충북","서울"]
        fig_d1 = chart_grouped_bar(
            sido_cats,
            [("04/25 (전전일)", [38,27,24,21,19,14,10,9,8,7]),
             ("04/26 (전일)",   [35,24,22,19,17,12,9,8,7,6])],
            colors=[COLORS["gray"], COLORS["primary"]],
        )
        st.plotly_chart(fig_d1, use_container_width=True, config={"displayModeBar": False})

    with dc2:
        section_title("🐾", "축종별 접수 건수 비교")
        fig_d2 = chart_grouped_bar(
            ["개","고양이","기타"],
            [("04/25 (전전일)", [178,112,22]),
             ("04/26 (전일)",   [163,98,26])],
            colors=[COLORS["gray"], COLORS["secondary"]],
        )
        st.plotly_chart(fig_d2, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section_title("📋", "전일 상세 데이터 (04/26)")
    st.dataframe(
        table_df.head(4),
        use_container_width=True,
        hide_index=True,
        height=200,
    )
    csv_d = table_df.head(4).to_csv(index=False)
    st.download_button("↓  04/26 데이터 다운로드", data=csv_d.encode("utf-8-sig"), file_name="유실유기동물_20260426.csv", mime="text/csv")


# ══════════════════════════════════════════════
#  TAB 3 — 월간 보고서
# ══════════════════════════════════════════════
with tab3:
    st.markdown("""
    <div style="display:inline-flex;align-items:center;gap:8px;padding:6px 16px;
        background:#e0e7ff;border-radius:8px;font-size:12px;font-weight:500;
        color:#4338ca;margin-bottom:20px;">
        📆 비교 기간: 2026년 02월 (전전월) → 2026년 03월 (전월)
    </div>
    """, unsafe_allow_html=True)

    # KPI
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(kpi_card("전월(03월) 접수", "7,412건", "+592건 (+8.7%)", "down", "#6366f1"), unsafe_allow_html=True)
    with m2:
        st.markdown(kpi_card("입양률", "19.7%", "+1.2%p", "up", "#d97706"), unsafe_allow_html=True)
    with m3:
        st.markdown(kpi_card("안락사율", "9.0%", "−0.8%p", "up", "#e11d48"), unsafe_allow_html=True)
    with m4:
        st.markdown(kpi_card("보호중", "9,537건", "+234건", "down", "#0d9488"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    mc1, mc2 = st.columns(2)
    with mc1:
        section_title("📍", "시/도별 월간 접수 건수 비교 (상위 10)")
        top10 = sido_df.head(10)
        fig_m1 = chart_grouped_bar(
            top10["지역"].str.replace("특별자치도","").str.replace("특별자치시","").str.replace("광역시","").str.replace("특별시","").tolist(),
            [("2026년 02월", top10["건수_02월"].tolist()),
             ("2026년 03월", top10["건수_03월"].tolist())],
            colors=[COLORS["gray"], COLORS["indigo"]],
        )
        st.plotly_chart(fig_m1, use_container_width=True, config={"displayModeBar": False})

    with mc2:
        section_title("📈", "2026년 03월 일별 발생 건수")
        fig_m2 = chart_vbar(monthly_daily_df["일"].tolist(), monthly_daily_df["건수"].tolist(), color=COLORS["indigo"])
        st.plotly_chart(fig_m2, use_container_width=True, config={"displayModeBar": False})

    # 처리 상태 비교 (도넛 2개)
    md1, md2 = st.columns(2)
    with md1:
        section_title("🔄", "처리 상태 — 2026년 02월")
        fig_s1 = chart_donut(
            labels=["보호중","입양","자연사","안락사","반환","기증","방사"],
            values=[9303, 4012, 2498, 1998, 1820, 823, 543],
        )
        st.plotly_chart(fig_s1, use_container_width=True, config={"displayModeBar": False})

    with md2:
        section_title("🔄", "처리 상태 — 2026년 03월")
        fig_s2 = chart_donut(
            labels=status_df["상태"].tolist(),
            values=status_df["건수"].tolist(),
        )
        st.plotly_chart(fig_s2, use_container_width=True, config={"displayModeBar": False})

    # AI 인사이트
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#ffffff;border-radius:12px;padding:20px 24px;
        box-shadow:0 1px 3px rgba(15,23,42,0.06);margin-bottom:8px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            <span style="font-size:18px;">🤖</span>
            <div>
                <div style="font-size:14px;font-weight:700;color:#0f172a;">AI 인사이트</div>
                <div style="font-size:12px;color:#94a3b8;">
                    버튼을 클릭하면 Claude AI가 이번 달 데이터를 분석하여 주요 인사이트와 정책 제언을 제공합니다.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "ai_insight" not in st.session_state:
        st.session_state.ai_insight = None

    if st.button("🔍  AI 인사이트 생성"):
        with st.spinner("Claude AI가 분석 중입니다..."):
            import anthropic
            client = anthropic.Anthropic()
            prompt = """당신은 동물복지 정책 분석 전문가입니다.
아래 유실유기동물 월간 통계 데이터를 바탕으로 다음 내용을 한국어로 작성해 주세요:

1. **핵심 요약** (2줄 이내): 이번 달의 가장 중요한 변화
2. **주목할 트렌드**: 긍정적·부정적 신호 각 2가지 (bullet)
3. **정책적 제언**: 실질적 개선 방향 2가지 (bullet)
4. **다음 달 모니터링 포인트**: 1~2가지

[데이터]
- 2026년 02월 접수: 6,820건 / 2026년 03월 접수: 7,412건 (+8.7%)
- 입양률: 18.5% → 19.7% (+1.2%p)
- 안락사율: 9.8% → 9.0% (−0.8%p)
- 보호중: 9,303건 → 9,537건 (+234건)
- 경기도 4,082건(+312), 경남 2,404건(+89), 전남 2,350건(+112)
- 축종: 개 9,173건(+623), 고양이 5,332건(+189), 기타 907건(-12)

응답은 마크다운 형식으로 간결하게 작성해 주세요."""

            message = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            st.session_state.ai_insight = message.content[0].text

    if st.session_state.ai_insight:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,oklch(97% 0.01 280),oklch(97% 0.01 200));
            border:1px solid oklch(90% 0.04 260);border-radius:12px;padding:20px 24px;margin-top:8px;">
            <div style="font-size:13px;font-weight:600;color:#4338ca;margin-bottom:14px;display:flex;align-items:center;gap:7px;">
                ✨ Claude AI 분석 결과
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(st.session_state.ai_insight)

        if st.session_state.ai_insight:
            st.download_button(
                "↓  AI 인사이트 다운로드 (txt)",
                data=st.session_state.ai_insight.encode("utf-8"),
                file_name="AI_인사이트_2026년03월.txt",
                mime="text/plain",
            )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    csv_m = table_df.to_csv(index=False)
    st.download_button("↓  2026년 03월 데이터 다운로드", data=csv_m.encode("utf-8-sig"), file_name="유실유기동물_202603.csv", mime="text/csv")
