import streamlit as st
import pandas as pd
import plotly.express as px
import io
from modules.ai_evaluator import get_ai_feedback, generate_next_week_data

st.set_page_config(page_title="CX Strategy Sandbox", layout="wide")

INITIAL_CSV_DATA = """ticket_id,week,user_id,channel,created_at,first_response_at,closed_at,is_fcr,user_message,csat_score,nps_score,user_tier,total_purchase_amount,is_active
TKT-2026-001,1,user_alpha,Chat,2026-04-29 09:00,2026-04-29 09:05,2026-04-29 09:20,TRUE,결제 단계에서 무한 로딩이 걸려서 결제가 안 됩니다.,2,3,Pro,540000,TRUE
TKT-2026-002,1,user_beta,Email,2026-04-29 10:15,2026-04-29 14:00,2026-04-29 15:30,FALSE,환불 요청합니다. 문의한 지 한참 됐는데 왜 이제 답장을 주시나요?,1,1,Free,0,FALSE
TKT-2026-003,1,user_gamma,Chat,2026-04-29 11:00,2026-04-29 11:02,2026-04-29 11:15,TRUE,기업용 플랜 도입 시 보안 가이드라인이 따로 있나요?,5,9,Enterprise,1200000,TRUE
TKT-2026-004,1,user_alpha,Chat,2026-04-29 13:30,2026-04-29 13:40,2026-04-29 14:10,FALSE,아까 결제 오류 문의했던 유저입니다. 카드 등록 단계에서도 튕기네요.,1,2,Pro,540000,TRUE
TKT-2026-005,1,user_delta,Call,2026-04-29 14:20,2026-04-29 14:21,2026-04-29 14:35,TRUE,로그인이 안 돼서 앱을 세 번이나 다시 깔았어요.,2,4,Pro,120000,TRUE
TKT-2026-006,1,user_epsilon,Chat,2026-04-29 15:00,2026-04-29 15:05,2026-04-29 15:30,TRUE,분석 결과 텍스트 다운로드 버튼이 안 보여요.,3,6,Free,45000,TRUE
TKT-2026-007,1,user_zeta,Chat,2026-04-29 15:45,2026-04-29 15:47,2026-04-29 16:00,TRUE,업데이트 이후에 오탐률이 확실히 줄어든 게 느껴지네요. 만족합니다.,5,10,Enterprise,2500000,TRUE
TKT-2026-008,1,user_eta,Email,2026-04-29 09:30,2026-04-29 11:50,2026-04-29 13:40,FALSE,구독 해지했는데 왜 또 결제가 된 거죠? 확인 부탁드려요.,1,0,Pro,350000,FALSE
TKT-2026-009,1,user_theta,Chat,2026-04-29 16:30,2026-04-29 16:32,2026-04-29 16:45,TRUE,무료 체험 기간 남은 거 어디서 확인하나요?,4,8,Free,0,TRUE
TKT-2026-010,1,user_iota,Chat,2026-04-29 17:10,2026-04-29 17:55,2026-04-29 18:30,FALSE,대량 분석 요청했는데 1시간째 대기 중입니다. 너무 느려요.,2,4,Pro,600000,TRUE"""

if 'master_df' not in st.session_state:
    st.session_state.master_df = pd.read_csv(io.StringIO(INITIAL_CSV_DATA))
if 'current_sim_week' not in st.session_state: st.session_state.current_sim_week = 1
if 'feedback_history' not in st.session_state: st.session_state.feedback_history = []
if 'current_feedback' not in st.session_state: st.session_state.current_feedback = None

with st.sidebar:
    st.title("📚 CX 지표 사전")
    with st.expander("⏱️ FRT (First Response Time)"): st.write("고객 문의 후 첫 응답까지의 시간. 운영 효율의 척도입니다.")
    with st.expander("✅ FCR (First Contact Resolution)"): st.write("첫 상담에서 즉시 해결된 비율. 유저 피로도를 방어합니다.")
    with st.expander("😊 CSAT (Top-2 % 기준)"): st.write("4, 5점 긍정 응답 비율. 단기적 서비스 만족도 표준입니다.")
    with st.expander("📣 NPS (Net Promoter Score)"): st.write("추천자(9-10) % - 비추천자(0-6) %. 브랜드 충성도 지표입니다.")
    with st.expander("💎 LTV (Lifetime Value)"): st.write("유저별 누적 매출액. 고객의 비즈니스적 가치를 나타냅니다.")

    st.divider()
    
    csv_export = st.session_state.master_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 전체 누적 데이터 다운로드 (.csv)",
        data=csv_export,
        file_name=f"cx_sandbox_data_week{st.session_state.current_sim_week}.csv",
        mime="text/csv",
        help="현재까지 시뮬레이션된 모든 데이터를 CSV 파일로 추출합니다."
    )

    if st.session_state.feedback_history:
        history_md = f"# CX Strategy Sandbox - 누적 분석 히스토리 (Week 1 ~ {st.session_state.current_sim_week})\n\n"
        for item in st.session_state.feedback_history:
            history_md += f"## [Week {item['week']}] 나의 전략\n"
            history_md += f"**🔍 분석:**\n{item['analysis']}\n\n"
            history_md += f"**🛠️ 액션:**\n{item['action']}\n\n"
            history_md += f"**🤖 AI 평가:**\n{item['feedback']}\n\n"
            history_md += "---\n\n"
            
        st.download_button(
            label="📝 분석 히스토리 다운로드 (.md)",
            data=history_md.encode('utf-8-sig'),
            file_name=f"cx_analysis_history_week{st.session_state.current_sim_week}.md",
            mime="text/markdown",
            help="지금까지 작성한 분석, 액션 및 AI 피드백을 노션/블로그용 마크다운 형식으로 추출합니다."
        )

    st.divider()
    if st.button("🔄 앱 전체 초기화 (1주차로 리셋)"):
        st.session_state.clear()
        st.rerun()
    st.caption("※ 주의: 이 버튼을 누르면 모든 시뮬레이션 데이터와 히스토리가 지워지고 초기 상태로 돌아갑니다.")

df = st.session_state.master_df
df['week'] = pd.to_numeric(df['week'], errors='coerce').fillna(1).astype(int)

st.title(f"🎯 CX Strategy Sandbox - [Week {st.session_state.current_sim_week}]")
st.markdown("---")

view_mode = st.radio("📊 데이터 조회 방식", ["현재 주차만 보기 (주간 액션 성과)", "전체 누적 데이터 보기 (장기 트렌드)"], horizontal=True)

if "현재 주차" in view_mode:
    base_df = df[df['week'] == st.session_state.current_sim_week]
else:
    base_df = df[df['week'] <= st.session_state.current_sim_week]

st.subheader("🔍 세그먼트 필터링")
col_f1, col_f2 = st.columns(2)
with col_f1: banner = st.selectbox("1단계 기준 필터", ["Total", "channel", "user_tier"])
with col_f2:
    if banner == "Total": filtered_df = base_df
    else: filtered_df = base_df[base_df[banner] == st.selectbox(f"2단계 상세 {banner}", base_df[banner].unique().tolist())]

if not filtered_df.empty:
    st.write(f"📊 분석 대상 데이터: **{len(filtered_df)}건**")
    
    with st.expander("👀 분석 대상 로데이터 확인", expanded=False):
        st.dataframe(filtered_df, use_container_width=True)
    
    st.divider()
    st.subheader("📊 핵심 KPI (전주 대비 증감)")
    kpis = ["FRT (분)", "FCR (%)", "CSAT (Top-2 %)", "NPS Score", "LTV (평균)"]
    selected = st.multiselect("분석 지표 선택", kpis, default=["CSAT (Top-2 %)", "NPS Score", "LTV (평균)"])
    
    prev_df = df[df['week'] == (st.session_state.current_sim_week - 1)] if st.session_state.current_sim_week > 1 else pd.DataFrame()
    if banner != "Total" and not prev_df.empty:
        prev_df = prev_df[prev_df[banner] == filtered_df[banner].iloc[0]]

    def calc_metrics(data_df):
        if data_df.empty: return {"frt": None, "fcr": None, "csat": None, "nps": None, "ltv": None}
        dt_resp = pd.to_datetime(data_df['first_response_at'], format='mixed', errors='coerce')
        dt_crea = pd.to_datetime(data_df['created_at'], format='mixed', errors='coerce')
        frt = (dt_resp - dt_crea).dt.total_seconds().mean() / 60
        fcr = (data_df['is_fcr'].astype(bool).sum() / len(data_df)) * 100
        csat = (len(data_df[data_df['csat_score'] >= 4]) / len(data_df)) * 100
        nps = ((len(data_df[data_df['nps_score'] >= 9]) - len(data_df[data_df['nps_score'] <= 6])) / len(data_df)) * 100
        ltv = data_df['total_purchase_amount'].mean()
        return {"frt": frt, "fcr": fcr, "csat": csat, "nps": nps, "ltv": ltv}

    curr_metrics = calc_metrics(filtered_df)
    prev_metrics = calc_metrics(prev_df)

    if selected:
        cols = st.columns(len(selected))
        for idx, m in enumerate(selected):
            with cols[idx]:
                if "FRT" in m:
                    val = curr_metrics["frt"]
                    if pd.isna(val): st.metric("평균 FRT", "오류")
                    else:
                        delta = f"{val - prev_metrics['frt']:.1f} 분" if prev_metrics['frt'] is not None else None
                        st.metric("평균 FRT", f"{val:.1f} 분", delta=delta, delta_color="inverse")
                elif "FCR" in m:
                    val = curr_metrics["fcr"]
                    delta = f"{val - prev_metrics['fcr']:.1f}%" if prev_metrics['fcr'] is not None else None
                    st.metric("FCR", f"{val:.1f}%", delta=delta)
                elif "CSAT" in m:
                    val = curr_metrics["csat"]
                    delta = f"{val - prev_metrics['csat']:.1f}%" if prev_metrics['csat'] is not None else None
                    st.metric("CSAT (Top-2)", f"{val:.1f}%", delta=delta)
                elif "NPS" in m:
                    val = curr_metrics["nps"]
                    delta = f"{val - prev_metrics['nps']:.1f}" if prev_metrics['nps'] is not None else None
                    st.metric("NPS", f"{val:.1f}", delta=delta)
                elif "LTV" in m:
                    val = curr_metrics["ltv"]
                    delta = f"{val - prev_metrics['ltv']:,.0f}원" if prev_metrics['ltv'] is not None else None
                    st.metric("평균 LTV", f"{val:,.0f}원", delta=delta)

    if "누적 데이터" in view_mode and st.session_state.current_sim_week > 1 and selected:
        st.divider()
        st.subheader("📈 선택 지표별 주간 트렌드 (최대 5주)")
        
        start_week = max(1, st.session_state.current_sim_week - 4)
        trend_data = []
        for w in range(start_week, st.session_state.current_sim_week + 1):
            w_df = filtered_df[filtered_df['week'] == w]
            if not w_df.empty:
                w_metrics = calc_metrics(w_df)
                trend_data.append({'Week': f'W{w}', 'FRT': w_metrics['frt'], 'FCR': w_metrics['fcr'], 'CSAT': w_metrics['csat'], 'NPS': w_metrics['nps'], 'LTV': w_metrics['ltv']})
        
        trend_df = pd.DataFrame(trend_data)
        chart_cols = st.columns(2)
        for idx, m in enumerate(selected):
            col = chart_cols[idx % 2]
            with col:
                if "FRT" in m:
                    fig = px.area(trend_df, x='Week', y='FRT', title="평균 FRT 누적 추이 (분)", markers=True, color_discrete_sequence=['#FF7F0E'])
                    st.plotly_chart(fig, use_container_width=True)
                elif "FCR" in m:
                    fig = px.line(trend_df, x='Week', y='FCR', title="FCR 달성률 트렌드 (%)", markers=True, color_discrete_sequence=['#1F77B4'])
                    st.plotly_chart(fig, use_container_width=True)
                elif "CSAT" in m:
                    fig = px.line(trend_df, x='Week', y='CSAT', title="CSAT (Top-2) 변화 추이 (%)", markers=True, color_discrete_sequence=['#2CA02C'])
                    st.plotly_chart(fig, use_container_width=True)
                elif "NPS" in m:
                    fig = px.bar(trend_df, x='Week', y='NPS', title="NPS Score 등락", color='NPS', color_continuous_scale=px.colors.diverging.RdYlGn)
                    st.plotly_chart(fig, use_container_width=True)
                elif "LTV" in m:
                    fig = px.bar(trend_df, x='Week', y='LTV', title="평균 LTV 볼륨 (원)", color_discrete_sequence=['#9467BD'])
                    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("데이터가 없습니다.")

st.divider()
st.subheader("💡 CX 분석 및 액션 시뮬레이션")
c1, c2 = st.columns(2)
with c1: user_analysis = st.text_area("1. 데이터 분석", height=150)
with c2: user_action = st.text_area("2. 실행 액션", height=150)

if st.button("🚀 3. 전략 실행 및 차주 데이터 생성"):
    if user_analysis and user_action:
        with st.spinner("AI가 20건의 시뮬레이션 데이터를 생성 중입니다... (약 15~20초)"):
            feedback = get_ai_feedback(user_analysis, f"Week {st.session_state.current_sim_week}", user_action, filtered_df.to_string())
            st.session_state.current_feedback = feedback
            
            generated_csv = generate_next_week_data(filtered_df.to_string(), user_action, st.session_state.current_sim_week + 1)
            
            try:
                new_df = pd.read_csv(io.StringIO(generated_csv.strip()))
                st.session_state.master_df = pd.concat([st.session_state.master_df, new_df], ignore_index=True)
                
                st.session_state.feedback_history.append({
                    "week": st.session_state.current_sim_week,
                    "analysis": user_analysis,
                    "action": user_action,
                    "feedback": feedback
                })
                st.success("✅ 시뮬레이션 데이터가 내장 DB에 성공적으로 통합되었습니다! 하단의 '다음 주차' 버튼을 누르세요.")
            except Exception as e:
                st.error(f"데이터 파싱 오류. AI가 지정된 스키마를 어겼습니다: {e}")
                st.code(generated_csv)

if st.session_state.current_feedback: st.info(st.session_state.current_feedback)

st.divider()
if st.button("⏭️ 4. 다음 주차(Next Week) 대시보드로 이동"):
    st.session_state.current_sim_week += 1
    st.session_state.current_feedback = None
    st.rerun()

st.divider()
with st.expander("📁 나의 누적 분석 히스토리", expanded=False):
    if st.session_state.feedback_history:
        for item in reversed(st.session_state.feedback_history):
            st.markdown(f"### [Week {item['week']}] 나의 전략")
            st.markdown(f"**🔍 분석:** {item['analysis']}")
            st.markdown(f"**🛠️ 액션:** {item['action']}")
            st.markdown("**🤖 AI 평가:**")
            st.info(item['feedback'])
            st.write("---")
    else:
        st.write("아직 저장된 전략 히스토리가 없습니다.")
