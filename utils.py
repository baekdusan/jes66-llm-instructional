import streamlit as st
import re

def get_latex_css():
    """LaTeX 렌더링을 위한 CSS 스타일을 반환합니다."""
    return """
    <style>
    .katex {
        font-size: 1.1em;
        line-height: 1.2;
    }
    .katex-display {
        margin: 1em 0;
        overflow-x: auto;
        overflow-y: hidden;
    }
    .katex-html {
        white-space: normal;
        word-wrap: break-word;
    }
    </style>
    """

def render_with_latex(text: str):
    """
    - \(...\): inline 수식 → $...$로 변환 후 st.markdown 출력
    - \[...\]: block 수식 → st.latex 출력
    - 마크다운 문법(###, -, **)은 그대로 유지됨
    """
    # LaTeX CSS 스타일 적용
    st.markdown(get_latex_css(), unsafe_allow_html=True)

    # block 수식 먼저 분리
    block_pattern = r"\\\[(.*?)\\\]"
    blocks = re.split(block_pattern, text, flags=re.DOTALL)
    print(blocks)

    for i, part in enumerate(blocks):
        if i % 2 == 0:
            # inline 수식만 변환 ( \( ... \) → $...$ )
            part = re.sub(r"\\\((.*?)\\\)", r"$\1$", part)
            st.markdown(part)
        else:
            st.latex(part.strip())
