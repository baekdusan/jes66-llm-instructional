import streamlit as st

# 공통 주의사항
COMMON_INSTRUCTIONS = """
Important Notes:
1. You must include both [Analysis Stage] and [Design Stage] sections.
2. Each section must follow the format above.
3. Do not omit or modify the content.
4. Please follow the JSON format exactly.
"""

# 의도 분류 프롬프트
INTENT_CLASSIFICATION_PROMPT = """
Classify the intent of the following user input.

User Input: {user_input}

Please classify into one of the following 5 types:

1. **Information Retrieval**: Requests for existing facts or information
   Examples: "Women's World Cup schedule", "Unemployment rate statistics by country"

2. **Problem Solving**: Mathematical, logical operations or transformations
   Examples: "Interest rate comparison", "Distance between point and line calculation", "Chinese to English translation"

3. **Learning**: Requests aimed at understanding concepts or phenomena
   Examples: "Explain the difference between GPT-3 and GPT-4", "Explain non-Newtonian fluids", "Learn about structural system types"

4. **Content Creation**: Writing or editing requests for specific purposes
   Examples: "Write an introduction about geothermal energy", "Edit report sentences", "Change poem to different format"

5. **Leisure**: Leisure activities or intimate conversations with AI
   Examples: "Ask about AI's sexual orientation", "Listen to romantic stories", "Play games, flirt"

Response Format: JSON
{{
    "intent": "Information Retrieval|Problem Solving|Learning|Content Creation|Leisure",
    "confidence": 0.0-1.0,
    "reason": "Classification reason (one sentence)"
}}
"""

# 참조 문서가 있는 경우의 프롬프트
for_system_prompt_with_reference = """
Generate a system prompt for the 'Analysis' and 'Design' stages of the ADDIE model to solve the following user request using the reference document.

References: {addie_reference_content}
User's Request: {user_input}
User's Background: User is a first-year master's student in Industrial Engineering, and his main research field is Human Factors and Ergonomics.
Learning Environment: The learning will take place exclusively through conversation with a chatbot.

Output Format: Please respond in the following JSON format:
{{
    "analysis_content": "[Analysis Stage]",
    "design_content": "[Design Stage]"
}}

{common_instructions}
"""

# 참조 문서가 없는 경우의 프롬프트
for_system_prompt_without_reference = """
Generate a system prompt for the 'Analysis' and 'Design' stages of the ADDIE model to solve the following user request.

User's Request: {user_input}
User's Background: User is a first-year master's student in Industrial Engineering, and his main research field is Human Factors and Ergonomics.
Learning Environment: The learning will take place exclusively through conversation with a chatbot.

Output Format: Please respond in the following JSON format:
{{
    "analysis_content": "[Analysis Stage]",
    "design_content": "[Design Stage]"
}}

{common_instructions}
"""

# 시스템 프롬프트
system_prompt = """
You are an AI tutor who uses the ADDIE model to teach users in a conversational and engaging way.
Based on the following analysis and design, provide personalized and interactive responses.

[Analysis Stage]
{analysis_content}

[Design Stage]
{design_content}

[Teaching Guidelines]
1. Start with a friendly greeting and ask about the user's prior knowledge
2. Use a conversational tone throughout the interaction
3. Break down complex concepts into digestible parts
4. Encourage active participation through questions and discussions
5. Provide real-world examples and analogies
6. Adapt the pace and depth based on user's responses
7. Use visual aids and formatting to enhance understanding
8. Regularly check for understanding and provide feedback

[Response Format]
- Write in a natural, conversational style
- Use markdown for formatting
- Include LaTeX for mathematical expressions when needed
- Break down information into smaller, manageable chunks
- End each response with a question or prompt for user engagement

[Feedback Integration]
- Monitor user's understanding and interest level
- Adjust content and approach based on user's responses
- Provide constructive feedback and encouragement
- Suggest related topics or deeper exploration when appropriate
"""

# 이전 프롬프트
"""
[Analysis Stage]
1. User Analysis: A first-year master's student majoring in Human Factors and Ergonomics
2. Environment Analysis: LLM-based chatbot platform
3. Requirement Analysis: Define the learning need based on the user's query "{user_input}"
4. Job and Task Analysis: Perform the learning task based on the above learning need using an LLM-based chatbot

[설계 단계]
1. Task Goal: [Write specific learning goals based on the user's query]
2. Evaluation Tools: [Provide methods to check if the learning goals are met]
3. Structuring: [Provide the logical structure and order of the learning content]
4. Selection of Teaching Strategies and Media: [Provide teaching methods and appropriate media for effective learning in the chatbot environment]
"""

# 피드백 분석 프롬프트
feedback_analysis_prompt = """
Analyze the user's feedback and current learning context to provide a more engaging and personalized learning experience.

Current Learning Context: {current_context}

User Feedback: {user_feedback}

Please respond in the following JSON format:
{{
    "status": "progress" or "evaluation",
    "reason": "detailed reason for the status determination",
    "suggested_adjustment": "following the reason, provide the suggested adjustment for the analysis and design content"
}}

Important Notes:
1. Consider both the current learning context and the user's feedback holistically
2. "progress" means normal learning progression
3. "evaluation" indicates need for change in the analysis and design content
4. Include specific suggestions for improvement in suggested_adjustment
5. Consider the user's engagement level when making recommendations
"""
