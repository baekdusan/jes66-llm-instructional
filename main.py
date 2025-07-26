import streamlit as st
from openai import OpenAI
from utils import render_with_latex
from prompts import (
    for_system_prompt_with_reference,
    for_system_prompt_without_reference,
    system_prompt,
    COMMON_INSTRUCTIONS,
    feedback_analysis_prompt,
    INTENT_CLASSIFICATION_PROMPT
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

def classify_user_intent(user_input, client):
    """사용자 입력의 의도를 분류합니다."""
    try:
        prompt = INTENT_CLASSIFICATION_PROMPT.format(user_input=user_input)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200
        )
        
        content = response.choices[0].message.content
        content = content.replace("```json", "").replace("```", "").strip()
        content = " ".join(line.strip() for line in content.splitlines())
        result = json.loads(content)
        
        return result
        
    except Exception as e:
        st.error(f"의도 분류 중 오류가 발생했습니다: {str(e)}")
        return {"intent": "Learning", "confidence": 0.5, "reason": "오류로 인한 기본값"}

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

# 대화 모드가 없으면 None로 초기화
if "conversation_mode" not in st.session_state:
    st.session_state.conversation_mode = None

# 히스토리에서 불러왔는지 표시하는 플래그
if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = False

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
st.title("🧑‍🏫 AI Tutor")

# 사이드바 렌더링
render_sidebar()

# API 키 유효성 검증 상태 확인
if not st.session_state.api_key_valid:
    st.warning("OpenAI API 키가 유효하지 않습니다. 사이드바에서 유효한 API 키를 입력해주세요.")
    st.stop()  # 여기서 실행을 중단하여 채팅 기능 제한

# OpenAI 클라이언트 설정
api_key = st.session_state.get("openai_api_key", st.secrets.get("openai", {}).get("api_key", ""))
client = OpenAI(api_key=api_key)

# 히스토리에서 불러온 경우 답변 생성 로직을 건너뜀
if st.session_state.get("history_loaded", False):
    st.session_state.history_loaded = False  # 한 번만 건너뜀
    # 메시지 렌더만 하고, 답변 생성/append는 하지 않음

# 이전 대화 히스토리 출력 (첫 번째 메시지가 아닌 경우에만)
if st.session_state.messages and st.session_state.system_prompt_created:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "system":
                if msg["content"] == "REFRESH":
                    continue  # REFRESH 메시지는 표시하지 않음
                # 교육 모드인 경우에만 시스템 프롬프트 표시
                if st.session_state.conversation_mode == "educational":
                    with st.expander("시스템 프롬프트 보기"):
                        st.markdown(render_with_latex(msg["content"]))
                # 일반 대화 모드에서는 시스템 프롬프트 숨김
            elif msg["role"] == "assistant":
                st.markdown(render_with_latex(msg["content"]))
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
    # 첫 번째 메시지인 경우 의도 분류 및 처리
    if not st.session_state.messages:
        # 새로운 대화 세션 생성
        if not st.session_state.current_conversation_id:
            conversation_title = user_input[:50] + "..." if len(user_input) > 50 else user_input
            st.session_state.current_conversation_id = db.create_conversation(conversation_title)
        
        # 의도 분류
        with st.spinner("사용자 의도를 분석하는 중..."):
            intent_result = classify_user_intent(user_input, client)
            
            # Learning인 경우에만 교육 모드로 설정
            if intent_result["intent"] == "Learning":
                st.session_state.conversation_mode = "educational"
                st.info(f"🎓 학습 모드로 전환되었습니다. (의도: {intent_result['intent']})")
                
                # 교육 모드: ADDIE 프레임워크 생성
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
                        
                    else:
                        prompt = for_system_prompt_without_reference.format(
                            user_input=user_input,
                            common_instructions=COMMON_INSTRUCTIONS
                        )
                    
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    try:
                        # JSON 응답 파싱
                        content = response.choices[0].message.content
                        
                        # 마크다운 코드 블록 표시 제거
                        content = content.replace("```json", "").replace("```", "").strip()
                        
                        # JSON 정규화 (여러 줄을 한 줄로)
                        content = " ".join(line.strip() for line in content.splitlines())
                        
                        result = json.loads(content)
                        
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
                        st.session_state.conversation_mode = None
                        
                        # 재시도 버튼
                        if st.button("다시 시도", key="retry_button"):
                            st.rerun()
                        
                        st.stop()  # 여기서 실행 중단
            else:
                # 일반 대화 모드
                st.session_state.conversation_mode = "casual"
                st.info(f"💬 일반 대화 모드입니다. (의도: {intent_result['intent']})")
                
                # 간단한 시스템 프롬프트 생성
                casual_system_prompt = """
                당신은 친근하고 도움이 되는 AI 어시스턴트입니다.
                사용자의 질문에 정확하고 유용한 답변을 제공하세요.
                - 친근하고 자연스러운 톤을 유지하세요
                - 필요한 경우 마크다운과 LaTeX를 사용하세요
                - 사용자가 만족할 수 있도록 도움을 주세요
                """
                st.session_state.messages.append({"role": "system", "content": casual_system_prompt})
                st.session_state.system_prompt_created = True

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
                            stream_placeholder.markdown(render_with_latex(full_response + "▌"))

                    # 스트리밍 끝난 후 수식 포함해서 다시 렌더링
                    stream_placeholder.empty()
                    st.markdown(render_with_latex(full_response))

                    # 응답 저장 (중복 방지)
                    if not (st.session_state.messages and
                            st.session_state.messages[-1]["role"] == "assistant" and
                            st.session_state.messages[-1]["content"] == full_response):
                        st.session_state.messages.append(
                            {"role": "assistant", "content": full_response}
                        )
                        db.save_message(st.session_state.current_conversation_id, "assistant", full_response)
                    
                    # 화면 갱신을 위한 rerun
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"응답 생성 중 오류가 발생했습니다: {str(e)}")
                    st.info("잠시 후 다시 시도해주세요.")
                    st.stop()
    else:

        with st.chat_message("user"):
            st.markdown(user_input)
            # 사용자 메시지 추가
            st.session_state.messages.append({"role": "user", "content": user_input})
            db.save_message(st.session_state.current_conversation_id, "user", user_input)
        
        # 교육 모드인 경우에만 피드백 분석 수행
        if st.session_state.conversation_mode == "educational":
            # 두 번째 메시지부터는 피드백 분석
            # 이전 메시지가 3개 미만인 경우는 있는 만큼만 사용
            context_messages = st.session_state.messages[-3:] if len(st.session_state.messages) >= 3 else st.session_state.messages
            current_context = "\n".join([msg["content"] for msg in context_messages])
            
            feedback_analysis = analyze_feedback(current_context, user_input)
            print(f"[FEEDBACK ANALYSIS] {feedback_analysis}")  # 피드백 분석 결과 로그
            # 피드백이 "평가" 상태인 경우 새로운 분석과 설계 반영
            if feedback_analysis["status"] == "evaluation" and "suggested_adjustment" in feedback_analysis:
                print("[FEEDBACK] evaluation detected, updating system prompt...")  # 분류 로그
                # 기존 system 메시지 찾기 (가장 첫 번째 system 메시지)
                for idx, msg in enumerate(st.session_state.messages):
                    if msg["role"] == "system" and msg["content"] != "REFRESH":
                        system_idx = idx
                        break
                else:
                    system_idx = None
                
                if system_idx is not None:
                    # 기존 system prompt에 피드백 내용을 줄 단위 불릿포인트로 추가
                    old_prompt = st.session_state.messages[system_idx]["content"]
                    adjustment = feedback_analysis["suggested_adjustment"]
                    feedback_lines = [line.strip() for line in str(adjustment).splitlines() if line.strip()]
                    feedback_text = "\n" + "\n".join(f"- {line}" for line in feedback_lines)
                    new_system_prompt = old_prompt.rstrip() + feedback_text
                    st.session_state.messages[system_idx]["content"] = new_system_prompt
                    print(f"[SYSTEM PROMPT UPDATED] {new_system_prompt}")  # system prompt 업데이트 로그
                    # 업데이트된 system prompt와 메시지로 assistant 답변 생성
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=st.session_state.messages,
                        stream=False
                    )
                    full_response = response.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    db.save_message(st.session_state.current_conversation_id, "assistant", full_response)
                    print(f"[LLM RESPONSE] {full_response}")
                st.write("Feedback applied. Please wait for the new response.")
                # st.rerun()
        

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
                        stream_placeholder.markdown(render_with_latex(full_response + "▌"))

                # 스트리밍 도중에도 마크다운으로 계속 갱신 (수식 포함)
                stream_placeholder.empty()
                st.markdown(render_with_latex(full_response))
                # 응답 저장 (중복 방지)
                if not (st.session_state.messages and
                        st.session_state.messages[-1]["role"] == "assistant" and
                        st.session_state.messages[-1]["content"] == full_response):
                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_response}
                    )
                    db.save_message(st.session_state.current_conversation_id, "assistant", full_response)
                
            except Exception as e:
                st.error(f"응답 생성 중 오류가 발생했습니다: {str(e)}")
                st.info("잠시 후 다시 시도해주세요.")
                st.stop()
