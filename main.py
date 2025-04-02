import streamlit as st
from openai import OpenAI
from utils import render_with_latex
from prompts import for_system_prompt, system_prompt
from sidebar import render_sidebar
from database import Database
import os
import json


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
            st.markdown(msg["content"])

# 사용자 입력
user_input = st.chat_input("메시지를 입력하세요")

if user_input:
    # 첫 번째 메시지인 경우 시스템 프롬프트 생성
    if not st.session_state.messages:
        # 새로운 대화 세션 생성
        if not st.session_state.current_conversation_id:
            conversation_title = user_input[:50] + "..." if len(user_input) > 50 else user_input
            st.session_state.current_conversation_id = db.create_conversation(conversation_title)
        
        with st.spinner("교수 설계 프레임워크를 생성하는 중 ..."):
            # 프롬프트 생성
            prompt = for_system_prompt.format(user_input=user_input)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            try:
                # JSON 응답 파싱
                content = response.choices[0].message.content
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
                
            except json.JSONDecodeError:
                st.error("프레임워크 생성 중 오류가 발생했습니다.")
                
                # 재시도 버튼 추가
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("다시 시도", key="retry_button"):
                        st.session_state.messages = []  # 메시지 초기화
                        st.rerun()  # 페이지 새로고침
                with col2:
                    st.info("재시도 버튼을 클릭하여 다시 시도해보세요.")

            # 사용자의 첫 번째 질문을 메시지 히스토리에 추가
            st.session_state.messages.append({"role": "user", "content": user_input})
            db.save_message(st.session_state.current_conversation_id, "user", user_input)

            # AI 응답 출력 영역
            with st.chat_message("assistant"):
                stream_placeholder = st.empty()
                full_response = ""

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
    else:
        # 첫 번째 메시지가 아닌 경우 일반적인 대화 진행
        st.session_state.messages.append({"role": "user", "content": user_input})
        db.save_message(st.session_state.current_conversation_id, "user", user_input)
        
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            stream_placeholder = st.empty()
            full_response = ""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                stream=True
            )

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    stream_placeholder.markdown(full_response + "▌")

            stream_placeholder.empty()
            render_with_latex(full_response)

            # 응답 저장
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
            db.save_message(st.session_state.current_conversation_id, "assistant", full_response)
