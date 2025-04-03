import streamlit as st
from openai import OpenAI
from utils import render_with_latex
from prompts import (
    for_system_prompt_with_reference,
    for_system_prompt_without_reference,
    system_prompt,
    COMMON_INSTRUCTIONS,
    feedback_analysis_prompt
)
from sidebar import render_sidebar
from database import Database
import os
import json
import PyPDF2

def read_pdf_content(pdf_path):
    """PDF 파일의 내용을 읽어서 문자열로 반환합니다."""
    content = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            content += page.extract_text()
    return content

# PDF 파일 경로 설정
ADDIE_PDF_PATH = "ADDIE_Model_All_Stages_Detailed_Concepts_with_References.pdf"

# 세션 상태 초기화

# 메시지가 없으면 빈 리스트로 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 시스템 프롬프트가 생성되지 않았으면 False로 초기화
if "system_prompt_created" not in st.session_state:
    st.session_state.system_prompt_created = False

# 현재 대화 세션 ID가 없으면 None로 초기화
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None

# API 키 유효성 검증 상태가 없으면 False로 초기화
if "api_key_valid" not in st.session_state:
    st.session_state.api_key_valid = False

# 데이터베이스 초기화
db = Database()

# ADDIE 문서가 데이터베이스에 없으면 저장 시도
if not db.get_addie_document():
    try:
        if os.path.exists(ADDIE_PDF_PATH):
            addie_content = read_pdf_content(ADDIE_PDF_PATH)
            db.save_addie_document(addie_content)
    except Exception as e:
        st.info("ADDIE 문서를 찾을 수 없습니다. LLM의 추론에 기반하여 진행합니다.")

# Streamlit 기본 설정
st.set_page_config(page_title="Dusan Baek", page_icon="🧑‍🏫")
st.title("Chatbot service by Instructional Design Theory")

# 사이드바 렌더링
render_sidebar()

# API 키 유효성 검증 상태 확인
if not st.session_state.api_key_valid:
    st.warning("OpenAI API 키가 유효하지 않습니다. 사이드바에서 유효한 API 키를 입력해주세요.")
    st.stop()  # 여기서 실행을 중단하여 채팅 기능 제한

# OpenAI 클라이언트 설정
api_key = st.session_state.get("openai_api_key", st.secrets.get("openai", {}).get("api_key", ""))
client = OpenAI(api_key=api_key)

# 이전 대화 히스토리 출력 (첫 번째 메시지가 아닌 경우에만)
if st.session_state.messages and st.session_state.system_prompt_created:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                render_with_latex(msg["content"])
            else:
                st.markdown(msg["content"])

# 사용자 입력
user_input = st.chat_input("메시지를 입력하세요")

def analyze_feedback(current_context, user_feedback):
    """사용자의 피드백을 분석하여 학습 상태를 평가합니다."""
    try:
        # 피드백 분석 프롬프트 생성
        prompt = feedback_analysis_prompt.format(
            current_context=current_context,
            user_feedback=user_feedback
        )
        
        # 피드백 분석 요청
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        
        # JSON 응답 파싱
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        content = " ".join(line.strip() for line in content.splitlines())
        result = json.loads(content)
        
        return result
        
    except Exception as e:
        st.error(f"피드백 분석 중 오류가 발생했습니다: {str(e)}")
        return {"status": "진행", "reason": "오류 발생", "feedback_type": "기타"}

if user_input:
    # 첫 번째 메시지인 경우 시스템 프롬프트 생성
    if not st.session_state.messages:
        # 새로운 대화 세션 생성
        if not st.session_state.current_conversation_id:
            conversation_title = user_input[:50] + "..." if len(user_input) > 50 else user_input
            st.session_state.current_conversation_id = db.create_conversation(conversation_title)
        
        with st.spinner("교수 설계 프레임워크를 생성하는 중 ..."):
            # 데이터베이스에서 ADDIE 문서 가져오기
            addie_reference_content = db.get_addie_document()
            
            # 프롬프트 생성
            if addie_reference_content:
                prompt = for_system_prompt_with_reference.format(
                    user_input=user_input,
                    addie_reference_content=addie_reference_content,
                    common_instructions=COMMON_INSTRUCTIONS
                )
                # st.write("참조 문서를 사용하여 프롬프트 생성")
            else:
                prompt = for_system_prompt_without_reference.format(
                    user_input=user_input,
                    common_instructions=COMMON_INSTRUCTIONS
                )
                # st.write("참조 문서 없이 프롬프트 생성")
            
            # st.write("생성된 프롬프트:", prompt)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            try:
                # JSON 응답 파싱
                content = response.choices[0].message.content
                # st.write("모델 응답:", content)
                
                # 마크다운 코드 블록 표시 제거
                content = content.replace("```json", "").replace("```", "").strip()
                
                # JSON 정규화 (여러 줄을 한 줄로)
                content = " ".join(line.strip() for line in content.splitlines())
                
                result = json.loads(content)
                st.write("파싱된 JSON:", result)
                
                # 시스템 프롬프트 생성
                system_prompt_content = system_prompt.format(
                    analysis_content=result["analysis_content"],
                    design_content=result["design_content"]
                )
                
                # 데이터베이스에 저장
                if st.session_state.current_conversation_id:
                    db.save_message(st.session_state.current_conversation_id, "system", system_prompt_content)
                
                st.session_state.system_prompt_created = True
                st.session_state.messages.append({"role": "system", "content": system_prompt_content})
                
            except (json.JSONDecodeError, KeyError) as e:
                st.error(f"프레임워크 생성 중 오류가 발생했습니다: {str(e)}")
                st.info("잠시 후 다시 시도해주세요.")
                
                # 세션 상태 초기화
                st.session_state.messages = []
                st.session_state.system_prompt_created = False
                st.session_state.current_conversation_id = None
                
                # 재시도 버튼
                if st.button("다시 시도", key="retry_button"):
                    st.rerun()
                
                st.stop()  # 여기서 실행 중단

            # 사용자의 첫 번째 질문을 메시지 히스토리에 추가
            st.session_state.messages.append({"role": "user", "content": user_input})
            db.save_message(st.session_state.current_conversation_id, "user", user_input)

            # AI 응답 출력 영역
            with st.chat_message("assistant"):
                stream_placeholder = st.empty()
                full_response = ""

                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=st.session_state.messages,
                        stream=True
                    )

                    # 스트리밍 응답 받기
                    for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            stream_placeholder.markdown(full_response + "▌")

                    # 스트리밍 끝난 후 수식 포함해서 다시 렌더링
                    stream_placeholder.empty()
                    render_with_latex(full_response)

                    # 응답 저장
                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_response}
                    )
                    db.save_message(st.session_state.current_conversation_id, "assistant", full_response)
                    
                except Exception as e:
                    st.error(f"응답 생성 중 오류가 발생했습니다: {str(e)}")
                    st.info("잠시 후 다시 시도해주세요.")
                    st.stop()
    else:
        # 두 번째 메시지부터는 피드백 분석
        # 이전 메시지가 3개 미만인 경우는 있는 만큼만 사용
        context_messages = st.session_state.messages[-3:] if len(st.session_state.messages) >= 3 else st.session_state.messages
        current_context = "\n".join([msg["content"] for msg in context_messages])
        
        feedback_analysis = analyze_feedback(current_context, user_input)
        
        # 피드백이 "평가" 상태인 경우 새로운 분석과 설계 추가
        print(feedback_analysis["status"], feedback_analysis["suggested_adjustment"])
        if feedback_analysis["status"] == "평가" and "suggested_adjustment" in feedback_analysis:
            # 새로운 분석과 설계를 메시지에 추가 (사용자에게는 보이지 않음)
            st.session_state.messages.append({
                "role": "system",
                "content": feedback_analysis["suggested_adjustment"]
            })
        
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": user_input})
        db.save_message(st.session_state.current_conversation_id, "user", user_input)
        
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            stream_placeholder = st.empty()
            full_response = ""

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages,
                    stream=True
                )

                # 스트리밍 응답 받기
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        stream_placeholder.markdown(full_response + "▌")

                # 스트리밍 끝난 후 수식 포함해서 다시 렌더링
                stream_placeholder.empty()
                render_with_latex(full_response)

                # 응답 저장
                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )
                db.save_message(st.session_state.current_conversation_id, "assistant", full_response)
                
            except Exception as e:
                st.error(f"응답 생성 중 오류가 발생했습니다: {str(e)}")
                st.info("잠시 후 다시 시도해주세요.")
                st.stop()
