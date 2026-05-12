import streamlit as st
import pandas as pd
import plotly.express as px
import io
from modules.ai_evaluator import get_ai_feedback, generate_next_week_data, generate_next_background
import time

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
if 'current_background' not in st.session_state:
    st.session_state.current_background = "어플리케이션의 마이너 업데이트가 수행되었습니다. 요약 및 TTS 기능이 소폭 개선되었습니다."
if 'next_background' not in st.session_state:
    st.session_state.next_background = None

if 'macro_metrics_history' not in st.session_state:
    # 1주차 가상 전체 고객 베이스라인 데이터 (AARRR 퍼널)
    st.session_state.macro_metrics_history = [{
        "week": 1,
        "new_signups": 1512,    # [Acquisition] 주간 신규 가입자 수
        "mau": 543214,           # [Activation] 주간 활성 유저
        "churn_rate": 0.08,     # [Retention] 전체 이탈률
        "referral_rate": 0.025, # [Referral] 고객 추천율
        "arpu": 33000,          # 전체 평균 객단가 (LTV 산출용)
        "gross_margin": 0.35,   # 매출 총이익률 65% (LTV 산출용)
        "cac": 150000            # (참고용) 고객 획득 비용
    }]

with st.sidebar:
    st.title("📚 CX 지표 사전")
    with st.expander("⏱️ FRT (First Response Time)"): st.write("고객 문의 후 첫 응답까지의 시간. 운영 효율의 척도입니다.")
    with st.expander("✅ FCR (First Contact Resolution)"): st.write("첫 상담에서 즉시 해결된 비율. 유저 피로도를 방어합니다.")
    with st.expander("😊 CSAT (Top-2 % 기준)"): st.write("4, 5점 긍정 응답 비율. 단기적 서비스 만족도 표준입니다.")
    with st.expander("📣 NPS (Net Promoter Score)"): st.write("추천자(9-10) % - 비추천자(0-6) %. 브랜드 충성도 지표입니다.")
    with st.expander("💎 LTV (Lifetime Value)"): st.write("유저별 평균 매출액 / 이탈률 * 그로스 마진. 고객의 비즈니스적 가치를 나타냅니다.")
    with st.expander("🏃 Churn (이탈률)"): st.write("활성 상태(is_active)가 FALSE인 고객의 비율. 서비스 이탈 및 구독 해지를 나타냅니다.")

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
    with st.expander("🏢 이번 주차 서비스 배경 (Business Context)", expanded=True):
        st.info(st.session_state.current_background)
    st.write(f"📊 분석 대상 데이터: **{len(filtered_df)}건**")
    
    with st.expander("👀 분석 대상 로데이터 확인", expanded=False):
        st.dataframe(filtered_df, use_container_width=True)
    
    st.divider()
    st.subheader("📈 전체 고객 그로스 지표")
    # 현재 주차 및 전 주차의 거시 지표 가져오기
    curr_macro = next((m for m in st.session_state.macro_metrics_history if m["week"] == st.session_state.current_sim_week), st.session_state.macro_metrics_history[-1])
    prev_macro = next((m for m in st.session_state.macro_metrics_history if m["week"] == st.session_state.current_sim_week - 1), curr_macro)

    # Global LTV 산출 (ARPU / Churn Rate * Gross Margin)
    def calc_global_ltv(macro_data):
        return (macro_data["arpu"] / max(macro_data["churn_rate"], 0.001)) * macro_data["gross_margin"]

    curr_global_ltv = calc_global_ltv(curr_macro)
    prev_global_ltv = calc_global_ltv(prev_macro)

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Acquisition\n(신규 가입자)", f"{curr_macro['new_signups']:,} 명", delta=f"{curr_macro['new_signups'] - prev_macro['new_signups']:,} 명")
    m2.metric("Activation\n(MAU)", f"{curr_macro['mau']:,} 명", delta=f"{curr_macro['mau'] - prev_macro['mau']:,} 명")
    m3.metric("Retention\n(이탈률)", f"{curr_macro['churn_rate']*100:.1f}%", delta=f"{(curr_macro['churn_rate'] - prev_macro['churn_rate'])*100:.1f}%", delta_color="inverse")
    m4.metric("Referral\n(고객 추천율)", f"{curr_macro['referral_rate']*100:.1f}%", delta=f"{(curr_macro['referral_rate'] - prev_macro['referral_rate'])*100:.1f}%")
    m5.metric("Revenue\n(LTV)", f"{curr_global_ltv:,.0f} 원", delta=f"{curr_global_ltv - prev_global_ltv:,.0f} 원")
    m6.metric("Cost\n(CAC)", f"{curr_macro['cac']:,} 원", delta=f"{curr_macro['cac'] - prev_macro['cac']:,} 원", delta_color="inverse")
    
    st.divider()
    st.subheader("🗣️ [VOC] 인입 고객 대상 서비스 지표")
    
    def calc_voc_metrics(data_df):
        if data_df.empty: return {"frt": None, "fcr": None, "csat": None, "nps": None}
        dt_resp = pd.to_datetime(data_df['first_response_at'], format='mixed', errors='coerce')
        dt_crea = pd.to_datetime(data_df['created_at'], format='mixed', errors='coerce')
        frt = (dt_resp - dt_crea).dt.total_seconds().mean() / 60
        fcr = (data_df['is_fcr'].astype(bool).sum() / len(data_df)) * 100
        csat = (len(data_df[data_df['csat_score'] >= 4]) / len(data_df)) * 100
        nps = ((len(data_df[data_df['nps_score'] >= 9]) - len(data_df[data_df['nps_score'] <= 6])) / len(data_df)) * 100
        return {"frt": frt, "fcr": fcr, "csat": csat, "nps": nps}

    curr_voc = calc_voc_metrics(filtered_df)
    prev_df = df[df['week'] == (st.session_state.current_sim_week - 1)] if st.session_state.current_sim_week > 1 else pd.DataFrame()
    prev_voc = calc_voc_metrics(prev_df)

    v1, v2, v3, v4 = st.columns(4)
    v1.metric("VOC 평균 FRT", f"{curr_voc['frt']:.1f} 분" if curr_voc['frt'] else "N/A", delta=f"{curr_voc['frt'] - prev_voc['frt']:.1f} 분" if prev_voc.get('frt') else None, delta_color="inverse")
    v2.metric("VOC FCR", f"{curr_voc['fcr']:.1f}%", delta=f"{curr_voc['fcr'] - prev_voc['fcr']:.1f}%" if prev_voc.get('fcr') else None)
    v3.metric("VOC CSAT (Top-2)", f"{curr_voc['csat']:.1f}%", delta=f"{curr_voc['csat'] - prev_voc['csat']:.1f}%" if prev_voc.get('csat') else None)
    v4.metric("VOC NPS", f"{curr_voc['nps']:.1f}", delta=f"{curr_voc['nps'] - prev_voc['nps']:.1f}" if prev_voc.get('nps') else None)


    if "누적 데이터" in view_mode and st.session_state.current_sim_week > 1:
        st.divider()
        st.subheader("📈 주간 그로스 및 서비스 트렌드 (최대 5주)")
        
       
        chart_options = [
            "Acquisition (신규 가입자)", "Activation (MAU)", "Retention (이탈률 %)", 
            "Referral (추천율 %)", "Revenue (LTV)", "Cost (CAC)", 
            "FRT (평균 응답시간)", "CSAT (만족도 %)"
        ]
        selected_charts = st.multiselect(
            "트렌드를 확인할 지표를 선택하세요 (최대 4개 권장)", 
            chart_options, 
            default=["Activation (MAU)", "Revenue (LTV)", "Retention (이탈률 %)", "CSAT (만족도 %)"]
        )
        
        if selected_charts:
            start_week = max(1, st.session_state.current_sim_week - 4)
            trend_data = []
            
            for w in range(start_week, st.session_state.current_sim_week + 1):
               
                w_df = filtered_df[filtered_df['week'] == w]
                voc_m = calc_voc_metrics(w_df) if not w_df.empty else {"frt": None, "csat": None}
                
                
                mac_m = next((m for m in st.session_state.macro_metrics_history if m["week"] == w), None)
                
                if mac_m:
                    
                    current_ltv = (mac_m["arpu"] / max(mac_m["churn_rate"], 0.001)) * mac_m["gross_margin"]
                    
                    trend_data.append({
                        'Week': f'W{w}', 
                        'Acquisition': mac_m["new_signups"],
                        'Activation': mac_m["mau"],
                        'Retention': mac_m["churn_rate"] * 100, 
                        'Referral': mac_m["referral_rate"] * 100, 
                        'Revenue': current_ltv,
                        'Cost': mac_m["cac"],
                        'FRT': voc_m.get('frt'), 
                        'CSAT': voc_m.get('csat')
                    })
            
            trend_df = pd.DataFrame(trend_data)
            chart_cols = st.columns(2)
            
            for idx, m in enumerate(selected_charts):
                col = chart_cols[idx % 2]
                with col:
                    if "Acquisition" in m:
                        fig = px.bar(trend_df, x='Week', y='Acquisition', title="Acquisition: 신규 가입자 유입량", color_discrete_sequence=['#636EFA'])
                    elif "Activation" in m:
                        fig = px.area(trend_df, x='Week', y='Activation', title="Activation: 주간 MAU 성장 추이", markers=True, color_discrete_sequence=['#00CC96'])
                    elif "Retention" in m:
                        fig = px.line(trend_df, x='Week', y='Retention', title="Retention: 전체 이탈률 트렌드 (%)", markers=True, color_discrete_sequence=['#EF553B'])
                    elif "Referral" in m:
                        fig = px.line(trend_df, x='Week', y='Referral', title="Referral: 고객 추천율 변화 (%)", markers=True, color_discrete_sequence=['#AB63FA'])
                    elif "Revenue" in m:
                        fig = px.bar(trend_df, x='Week', y='Revenue', title="Revenue: LTV 추이 (원)", color_discrete_sequence=['#FFA15A'])
                    elif "Cost" in m:
                        fig = px.line(trend_df, x='Week', y='Cost', title="Cost: 고객 획득 비용 (CAC) 변동", markers=True, color_discrete_sequence=['#19D3F3'])
                    elif "FRT" in m:
                        fig = px.line(trend_df, x='Week', y='FRT', title="VOC: 평균 응답 시간 (분)", markers=True, color_discrete_sequence=['#FF6692'])
                    elif "CSAT" in m:
                        fig = px.line(trend_df, x='Week', y='CSAT', title="VOC: 고객 만족도 (Top-2, %)", markers=True, color_discrete_sequence=['#B6E880'])
                    
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
            st.session_state.next_background = generate_next_background(user_action, feedback)
            
            time.sleep(3)
            generated_csv = generate_next_week_data(filtered_df.to_string(), user_action, st.session_state.current_sim_week + 1)
            
            try:
                new_df = pd.read_csv(io.StringIO(generated_csv.strip()))
                st.session_state.master_df = pd.concat([st.session_state.master_df, new_df], ignore_index=True)
               
                last_macro = st.session_state.macro_metrics_history[-1]
                
                new_voc_csat = (len(new_df[new_df['csat_score'] >= 4]) / len(new_df)) * 100 if not new_df.empty else 50
                impact_factor = (new_voc_csat - 50) / 100 
                
                new_signups = int(last_macro["new_signups"] * (1 + (0.05 * impact_factor))) # 오가닉 신규 유입 증감
                new_churn = max(0.005, last_macro["churn_rate"] - (0.03 * impact_factor))   # 만족도에 따른 이탈률 하락
                new_referral = min(0.15, last_macro["referral_rate"] + (0.015 * impact_factor)) # 바이럴에 의한 추천율 상승
                
                new_mau = int((last_macro["mau"] * (1 - new_churn)) + new_signups + (last_macro["mau"] * new_referral))
                
                new_macro = {
                    "week": st.session_state.current_sim_week + 1,
                    "new_signups": new_signups,
                    "mau": new_mau, 
                    "cac": max(5000, int(last_macro["cac"] * (1 - (0.08 * impact_factor)))), 
                    "arpu": last_macro["arpu"], 
                    "churn_rate": new_churn, 
                    "referral_rate": new_referral,
                    "gross_margin": last_macro["gross_margin"]
                }
                st.session_state.macro_metrics_history.append(new_macro)
                
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
    if st.session_state.next_background:
        st.session_state.current_background = st.session_state.next_background
        
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
