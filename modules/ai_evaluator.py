import google.generativeai as genai
import streamlit as st

def configure_api():
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)

def get_ai_feedback(scenario, analysis_context, action, raw_data_summary):
    try:
        configure_api()
        model = genai.GenerativeModel('gemini-3-flash-preview')
        prompt = f"""
        당신은 IT 스타트업의 시니어 CX 전략가입니다.
        아래 CX 매니저의 리서치 결과 분석과 대응안을 비판적으로 평가하십시오.
        CX 매니저의 주요 업무는 인입된 고객 VOC 분석 결과를 바탕으로 타 부서와의 협업을 통해 CX를 개선하는 유저 리서치 직무입니다.
        
        [데이터 요약]: {raw_data_summary}
        [나의 분석]: {scenario}
        [나의 액션]: {action}
        
        [평가 가이드라인]:
        1. 첫 줄에 종합 평가 점수를 100점 만점으로 제시하세요. (예: [종합 평가: 85/100])
        2. 논리적 비약 지적, 리소스 효율성, 비즈니스 임팩트 위주로 서술하세요.
        3. 개선이 필요한 지점 위주로 실무적인 톤으로 작성하세요.
        4. 현업에서 활용하는 용어를 사용하되, 주석으로 설명이 필요한 용어들은 각주처럼 보여주세요.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"피드백 생성 오류: {str(e)}"

def generate_next_week_data(current_data_summary, user_action, next_week_num):
    try:
        configure_api()
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        prompt = f"""
        당신은 CX 데이터 시뮬레이터입니다.
        사용자의 액션: [{user_action}]
        위 액션을 반영하여 'Week {next_week_num}'의 가상 로데이터 20행을 생성하세요.
        
        [데이터 스키마 및 절대 규격 - 이 규칙을 어기면 시스템이 붕괴됩니다]:
        1. ticket_id: "TKT-2026-" 뒤에 무작위 3자리 숫자 (예: TKT-2026-101)
        2. week: 반드시 숫자 {next_week_num}
        3. user_id: "user_" 뒤에 무작위 알파벳 또는 숫자
        4. channel: 반드시 ["Chat", "Email", "App", "Call"] 중 하나만 사용
        5. created_at: "YYYY-MM-DD HH:MM" 형식 (예: 2026-05-06 09:00). 절대 초(:SS)를 넣지 말 것.
        6. first_response_at: "YYYY-MM-DD HH:MM" 형식. 반드시 created_at과 같거나 더 늦은 시간일 것.
        7. closed_at: "YYYY-MM-DD HH:MM" 형식. 반드시 first_response_at보다 더 늦은 시간일 것.
        8. is_fcr: 반드시 대문자 [TRUE, FALSE] 중 하나
        9. user_message: 고객 문의 내용 (한국어). **[CRITICAL] 내용 안에 쉼표(,)나 따옴표(")가 들어가면 CSV가 깨지므로 문장 부호는 마침표(.)나 물음표(?)만 사용하세요.**
        10. csat_score: 1 부터 5 사이의 정수
        11. nps_score: 0 부터 10 사이의 정수
        12. user_tier: 반드시 ["Free", "Pro", "Enterprise"] 중 하나만 사용
        13. total_purchase_amount: 0 이상의 정수 (단위 없이 숫자만)
        14. is_active: 반드시 대문자 [TRUE, FALSE] 중 하나
        
        [출력 규칙]:
        - 반드시 위의 14개 칼럼 순서를 유지하여 첫 줄에 헤더를 작성할 것.
        - 헤더를 포함하여 정확히 21줄(헤더 1줄 + 데이터 20줄)의 텍스트를 생성할 것.
        - 중간에 '...' 같은 생략 기호를 절대 쓰지 말고 끝까지 생성할 것.
        - 마크다운 기호(```csv 등) 없이 순수한 CSV 텍스트만 출력할 것.
        """
        response = model.generate_content(prompt)
        
        clean_text = response.text.replace('```csv', '').replace('```', '').strip()
        
        return clean_text
    except Exception as e:
        return f"ticket_id,week,error,error,error,error,error,error,error,error,error,error,error,error\n0,{next_week_num},생성 중 오류 발생: {str(e)},,,,,,,,,,,"
