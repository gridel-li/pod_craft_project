"""
Mood Analyzer Agent — 分析用户心情，确定内容基调
"""

from agents.base import BaseAgent, AgentContext


MOOD_PROMPTS = {
    "excited": "充满活力、热情洋溢、语速稍快、用感叹号",
    "calm": "平和舒缓、语速慢、温暖治愈、像在耳边轻声细语",
    "humorous": "幽默风趣、轻松活泼、加入段子和比喻",
    "serious": "严肃专业、逻辑清晰、数据支撑、像纪录片旁白",
    "neutral": "自然平和、娓娓道来、像朋友聊天",
}


class MoodAnalyzerAgent(BaseAgent):
    """分析用户心情，输出内容策略"""

    def __init__(self, llm_client=None):
        super().__init__("mood_analyzer", llm_client)

    async def execute(self, context: AgentContext) -> AgentContext:
        self.logger.info(f"分析心情: mood={context.mood}, style={context.style}")

        mood_desc = MOOD_PROMPTS.get(context.mood, MOOD_PROMPTS["neutral"])

        messages = [
            {"role": "system", "content": "你是一个播客内容策略师。根据用户的心情和风格偏好，制定内容策略。"},
            {"role": "user", "content": f"""主题：{context.topic}
心情基调：{context.mood}（{mood_desc}）
风格：{context.style}
时长：{context.duration_min} 分钟

请输出内容策略 JSON：
{{
    "tone": "具体的语气描述",
    "pace": "语速建议",
    "vocabulary": "用词风格",
    "structure": "结构建议",
    "key_elements": ["必须包含的元素"]
}}"""},
        ]

        strategy = await self._llm_json(messages, temperature=0.5)
        context.metadata["mood_strategy"] = strategy
        self.logger.info(f"内容策略: {strategy.get('tone', '')}")
        return context
