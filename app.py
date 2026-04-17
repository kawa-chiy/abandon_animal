import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="유실유기동물 대시보드",
    page_icon="🐾",
    layout="wide",
)

# ── 공통 Plotly 레이아웃 테마 ─────────────────────────────────────────────────
CHART_THEME = dict(
    font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif", size=13),
    plot_bgcolor="#f8f9fa",
    paper_bgcolor="#ffffff",
    margin=dict(t=50, b=40, l=40, r=20),
)

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQz3RW9aYnvI0FwReoPTS9vdA0Ww9o4dE3IkRoYRV0LPMmaodVJzPwqZV0MSVVR_PBcuUdWtVxr_Qdg"
    "/pub?gid=1138734689&single=true&output=csv"
)

# 공공데이터 유기동물 API 컬럼명 후보 매핑
COL_CANDIDATES = {
    "date":   ["접수일", "발생일시", "noticeEdDt", "happenDt", "접수일자", "발생일"],
    "region": ["관할기관", "orgNm", "careNm", "보호기관", "시군구"],
    "status": ["처리상태", "processState", "상태", "state"],
    "species":["축종", "kindCd", "동물종류", "종류"],
    "breed":  ["품종", "breed", "kindNm"],
}


def detect_col(df: pd.DataFrame, key: str) -> str | None:
    for candidate in COL_CANDIDATES[key]:
        if candidate in df.columns:
            return candidate
    # 부분 문자열 폴백
    keywords = {"date": ["일"], "region": ["기관","지역","시군"], "status": ["상태"],
                "species": ["종류","축종"], "breed": ["품종"]}
    for c in df.columns:
        if any(kw in c for kw in keywords.get(key, [])):
            return c
    return None


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_URL, dtype=str)
    return df


def parse_date_col(series: pd.Series) -> pd.Series:
    """다양한 날짜 형식을 datetime으로 변환."""
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return pd.to_datetime(series.str[:10], format=fmt, errors="coerce")
        except Exception:
            continue
    return pd.to_datetime(series, errors="coerce")


# ── 헤더 ──────────────────────────────────────────────────────────────────────
st.title("🐾 유실유기동물 현황 대시보드")
st.caption(f"데이터 출처: Google Sheets (매일 자동 갱신) · 마지막 조회: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ── 데이터 로드 & 오류 처리 ────────────────────────────────────────────────────
with st.spinner("데이터를 불러오는 중..."):
    try:
        df_raw = load_data()
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.stop()

# ── 컬럼 자동 감지 ────────────────────────────────────────────────────────────
date_col    = detect_col(df_raw, "date")
region_col  = detect_col(df_raw, "region")
status_col  = detect_col(df_raw, "status")
species_col = detect_col(df_raw, "species")
breed_col   = detect_col(df_raw, "breed")

# 날짜 컬럼 파싱
df = df_raw.copy()
if date_col:
    df["_date"] = parse_date_col(df[date_col])

# ── 사이드바: 필터 ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 필터")

    # 관할기관(지역) 다중 선택
    selected_regions = []
    if region_col:
        all_regions = sorted(df[region_col].dropna().unique().tolist())
        selected_regions = st.multiselect(
            "관할기관 (지역)",
            options=all_regions,
            default=[],
            placeholder="전체 (미선택 시 전체 표시)",
        )

    # 처리 상태 다중 선택
    selected_statuses = []
    if status_col:
        all_statuses = sorted(df[status_col].dropna().unique().tolist())
        selected_statuses = st.multiselect(
            "처리 상태",
            options=all_statuses,
            default=[],
            placeholder="전체 (미선택 시 전체 표시)",
        )

    # 날짜 범위 슬라이더
    if date_col and df["_date"].notna().any():
        min_date = df["_date"].min().date()
        max_date = df["_date"].max().date()
        date_range = st.date_input(
            "접수일 범위",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
    else:
        date_range = None

    st.divider()
    with st.expander("🗂 컬럼 목록 확인"):
        st.write(df_raw.columns.tolist())

# ── 필터 적용 ─────────────────────────────────────────────────────────────────
filtered = df.copy()

if selected_regions and region_col:
    filtered = filtered[filtered[region_col].isin(selected_regions)]

if selected_statuses and status_col:
    filtered = filtered[filtered[status_col].isin(selected_statuses)]

if date_range and len(date_range) == 2 and date_col:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    filtered = filtered[filtered["_date"].between(start, end)]

# ── 입양·안락사율 계산 ─────────────────────────────────────────────────────────
total = len(filtered)

def rate(keyword: str) -> float:
    if not status_col or total == 0:
        return 0.0
    count = filtered[status_col].str.contains(keyword, na=False).sum()
    return round(count / total * 100, 1)

adoption_rate    = rate("입양")
euthanasia_rate  = rate("안락사")

# 전체 기준 델타 (필터 적용 전후 비교)
total_all        = len(df)
adoption_all     = round(df[status_col].str.contains("입양", na=False).sum() / total_all * 100, 1) if status_col and total_all else 0
euthanasia_all   = round(df[status_col].str.contains("안락사", na=False).sum() / total_all * 100, 1) if status_col and total_all else 0

# ── KPI 카드 ──────────────────────────────────────────────────────────────────
st.subheader("📊 핵심 지표")
m1, m2, m3, m4 = st.columns(4)

m1.metric("총 발생 건수", f"{total:,} 건",
          delta=f"전체 {total_all:,}건 중" if (selected_regions or selected_statuses) else None)
m2.metric("입양률", f"{adoption_rate} %",
          delta=f"{adoption_rate - adoption_all:+.1f}%p (전체 대비)" if (selected_regions or selected_statuses) else None)
m3.metric("안락사율", f"{euthanasia_rate} %",
          delta=f"{euthanasia_rate - euthanasia_all:+.1f}%p (전체 대비)" if (selected_regions or selected_statuses) else None,
          delta_color="inverse")

if status_col:
    protection_count = filtered[status_col].str.contains("보호중", na=False).sum()
    m4.metric("현재 보호중", f"{protection_count:,} 건")

st.divider()

# ── 차트 1 + 차트 2 ────────────────────────────────────────────────────────────
row1_left, row1_right = st.columns([3, 2])

# ── 차트 1: 최근 30일 일별 발생 추이 (꺾은선) ─────────────────────────────────
with row1_left:
    st.subheader("📈 최근 30일 일별 유기동물 발생 추이")
    if date_col and df["_date"].notna().any():
        cutoff = filtered["_date"].max() - timedelta(days=29)
        recent = filtered[filtered["_date"] >= cutoff].copy()
        daily = (
            recent.groupby(recent["_date"].dt.date)
            .size()
            .reset_index(name="발생 건수")
            .rename(columns={"_date": "접수일"})
        )
        # 날짜 공백 채우기
        if not daily.empty:
            full_range = pd.date_range(daily["접수일"].min(), daily["접수일"].max())
            daily = (
                daily.set_index("접수일")
                .reindex(full_range.date, fill_value=0)
                .reset_index()
                .rename(columns={"index": "접수일"})
            )
        fig_line = px.line(
            daily,
            x="접수일",
            y="발생 건수",
            markers=True,
            title="일별 유기동물 접수 건수 (최근 30일)",
            labels={"접수일": "접수일", "발생 건수": "발생 건수 (건)"},
            color_discrete_sequence=["#3B82F6"],
        )
        fig_line.update_traces(
            line=dict(width=2.5),
            marker=dict(size=6),
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.08)",
        )
        fig_line.update_xaxes(tickformat="%m/%d", tickangle=-30, showgrid=False)
        fig_line.update_yaxes(gridcolor="#e5e7eb")
        fig_line.update_layout(**CHART_THEME)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("날짜 컬럼을 감지하지 못해 추이 차트를 표시할 수 없습니다.")

# ── 차트 2: 축종·품종별 트리맵 ───────────────────────────────────────────────
with row1_right:
    st.subheader("🐶 축종 · 품종별 비율")
    if species_col or breed_col:
        path = [c for c in [species_col, breed_col] if c]
        tree_df = (
            filtered.groupby(path)
            .size()
            .reset_index(name="건수")
        )
        # 품종 상위 30개로 제한해 트리맵 가독성 확보
        top_breeds = tree_df.nlargest(30, "건수")
        fig_tree = px.treemap(
            top_breeds,
            path=path,
            values="건수",
            title="축종 및 품종별 접수 비율 (상위 30)",
            color="건수",
            color_continuous_scale="Blues",
        )
        fig_tree.update_traces(
            textinfo="label+percent parent",
            hovertemplate="<b>%{label}</b><br>건수: %{value:,}<br>비율: %{percentParent:.1%}<extra></extra>",
        )
        fig_tree.update_layout(**CHART_THEME)
        st.plotly_chart(fig_tree, use_container_width=True)
    else:
        st.info("축종/품종 컬럼을 감지하지 못했습니다.")

st.divider()

# ── 차트 3 + 차트 4 (보조 차트) ───────────────────────────────────────────────
row2_left, row2_right = st.columns(2)

# 처리 상태 도넛 차트
with row2_left:
    st.subheader("🔄 처리 상태 비율")
    if status_col:
        status_cnt = filtered[status_col].value_counts().reset_index()
        status_cnt.columns = ["처리 상태", "건수"]
        fig_donut = px.pie(
            status_cnt,
            names="처리 상태",
            values="건수",
            hole=0.45,
            title="처리 상태별 비율",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_donut.update_traces(
            textposition="outside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>건수: %{value:,}<br>비율: %{percent}<extra></extra>",
        )
        fig_donut.update_layout(**CHART_THEME)
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("처리 상태 컬럼을 감지하지 못했습니다.")

# 관할기관(지역)별 가로 막대 차트
with row2_right:
    st.subheader("📍 관할기관(지역)별 접수 건수")
    if region_col:
        region_cnt = (
            filtered[region_col].value_counts().head(15).reset_index()
        )
        region_cnt.columns = ["관할기관", "건수"]
        fig_bar = px.bar(
            region_cnt,
            x="건수",
            y="관할기관",
            orientation="h",
            title="관할기관별 접수 건수 (상위 15)",
            text="건수",
            color="건수",
            color_continuous_scale="Teal",
        )
        fig_bar.update_traces(textposition="outside")
        fig_bar.update_yaxes(autorange="reversed", tickfont=dict(size=11))
        fig_bar.update_xaxes(showgrid=False)
        fig_bar.update_layout(**CHART_THEME, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("관할기관 컬럼을 감지하지 못했습니다.")

st.divider()

# ── 원본 데이터 테이블 ────────────────────────────────────────────────────────
st.subheader("📋 상세 데이터")
display_df = filtered.drop(columns=["_date"], errors="ignore")
st.dataframe(display_df, use_container_width=True, height=380)

csv_bytes = display_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
st.download_button(
    label="📥 필터 결과 CSV 다운로드",
    data=csv_bytes,
    file_name=f"유실유기동물_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
)
