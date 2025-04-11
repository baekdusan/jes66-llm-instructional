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
        margin: 0;  /* 여백을 0으로 설정 */
        overflow-x: auto;
        overflow-y: hidden;
    }
    .katex-html {
        white-space: normal;
        word-wrap: break-word;
    }
    </style>
    """

def render_with_latex(text: str) -> str:
    """
    - \(...\): inline 수식 → $...$로 변환
    - \[...\]: block 수식 → $$...$$로 변환
    - 마크다운 문법(###, -, **)은 그대로 유지됨
    """
    # block 수식 변환 ( \[...\] → $$...$$ )
    text = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", text, flags=re.DOTALL)
    
    # inline 수식 변환 ( \(...\) → $...$ )
    text = re.sub(r"\\\((.*?)\\\)", r"$\1$", text)
    
    return text
