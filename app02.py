import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="대회 기록 분석", layout="wide")

st.title("🏁 대회 기록 분석 대시보드")

# --------------------------------------------------
# 데이터 로드
# --------------------------------------------------
uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])

if uploaded_file is None:
    st.info("Google Sheet에서 CSV로 다운로드 후 업로드하세요.")
    st.stop()

df = pd.read_csv(uploaded_file)

# --------------------------------------------------
# 데이터 전처리
# --------------------------------------------------
df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

# 총시간(HH:MM:SS) → 초 단위 변환
def time_to_seconds(t):
    if pd.isna(t):
        return None
    try:
        h, m, s = map(int, t.split(":"))
        return h * 3600 + m * 60 + s
    except:
        return None

df["총시간_초"] = df["총시간"].apply(time_to_seconds)

# DNF 제거 (그래프용)
df_complete = df[df["상태"] != "DNF"].copy()

# --------------------------------------------------
# 사이드바 필터
# --------------------------------------------------
st.sidebar.header("필터 선택")

date_min = df_complete["날짜"].min()
date_max = df_complete["날짜"].max()

date_range = st.sidebar.date_input(
    "날짜 선택",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max
)

players = st.sidebar.multiselect(
    "선수 선택",
    options=sorted(df_complete["선수명"].dropna().unique())
)

events = st.sidebar.multiselect(
    "대회명 선택",
    options=sorted(df_complete["대회명"].dropna().unique())
)

event_types = st.sidebar.multiselect(
    "대회종류 선택",
    options=sorted(df_complete["대회종류"].dropna().unique())
)

# --------------------------------------------------
# 필터 적용
# --------------------------------------------------
filtered_df = df_complete.copy()

if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df["날짜"] >= pd.to_datetime(date_range[0])) &
        (filtered_df["날짜"] <= pd.to_datetime(date_range[1]))
    ]

if players:
    filtered_df = filtered_df[filtered_df["선수명"].isin(players)]

if events:
    filtered_df = filtered_df[filtered_df["대회명"].isin(events)]

if event_types:
    filtered_df = filtered_df[filtered_df["대회종류"].isin(event_types)]

# --------------------------------------------------
# 데이터 테이블
# --------------------------------------------------
st.subheader("📋 선택 조건에 따른 데이터")
st.dataframe(
    filtered_df.sort_values("날짜"),
    use_container_width=True
)

# --------------------------------------------------
# 그래프 1: 선수별 총시간 변화
# --------------------------------------------------
st.subheader("📈 선수별 총시간 변화")

if filtered_df.empty:
    st.warning("선택된 조건에 해당하는 데이터가 없습니다.")
else:
    fig_player = px.line(
        filtered_df,
        x="날짜",
        y="총시간_초",
        color="선수명",
        markers=True,
        title="선수별 총시간 변화"
    )

    fig_player.update_yaxes(
        title="총시간 (분)",
        tickvals=[i * 600 for i in range(0, 30)],
        ticktext=[str(i * 10) for i in range(0, 30)]
    )

    st.plotly_chart(fig_player, use_container_width=True)

# --------------------------------------------------
# 그래프 2: 대회종류별 평균 총시간 변화
# --------------------------------------------------
st.subheader("📊 대회종류별 평균 총시간 변화")

group_df = (
    filtered_df
    .groupby(["날짜", "대회종류"], as_index=False)["총시간_초"]
    .mean()
)

if not group_df.empty:
    fig_type = px.line(
        group_df,
        x="날짜",
        y="총시간_초",
        color="대회종류",
        markers=True,
        title="대회종류별 평균 총시간 변화"
    )

    fig_type.update_yaxes(title="평균 총시간 (초)")
    st.plotly_chart(fig_type, use_container_width=True)
