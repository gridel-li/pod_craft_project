"""
Mood Analyzer Agent — 情绪基调分析器

功能说明：
读取 context 中的 topic（主题）、mood（情绪偏好）和 style（风格），
调用大模型生成一套具体的内容策略（tone 语调、pace 语速、vocabulary 用词、structure 结构），
并将策略字典写入 context.metadata["mood_strategy"]。
"""

from agents.base import BaseAgent, AgentContext

# 预设情绪的中文描述映射表
MOOD_PROMPTS = {
    "excited": "充满活力、热情洋溢、语速稍快、用感叹号",
    "calm": "平和舒缓、语速慢、温暖治愈、像在耳边轻声细语",
    "humorous": "幽默风趣、轻松活泼、加入段子和比喻",
    "serious": "严肃专业、逻辑清晰、数据支撑、像纪录片旁白",
    "neutral": "自然平和、娓娓道来、像朋友聊天",
}


class MoodAnalyzerAgent(BaseAgent):
    """分析用户情绪与风格偏好，输出具体内容策略"""

    def __init__(self, llm_client=None):
        # super().__init__ 调用父类 BaseAgent 的构造函数，注册当前 Agent 名称为 "mood_analyzer"
        super().__init__("mood_analyzer", llm_client)

    async def execute(self, context: AgentContext) -> AgentContext:
        """
        执行情绪分析任务
        :param context: 输入上下文，包含 topic, mood, style, duration_min
        :return: 写入 context.metadata["mood_strategy"] 后的上下文
        """
        self.logger.info(f"执行情绪分析: mood={context.mood}, style={context.style}")

        # 使用 dict.get 提取预设描述，第二个参数为默认兜底值
        mood_desc = MOOD_PROMPTS.get(context.mood, MOOD_PROMPTS["neutral"])

        # 组装发送给大模型的 Prompt 消息列表
        # role: "system" 用于设定大模型的系统级角色定位
        # role: "user" 传入具体的输入参数和期望输出的 JSON 数据结构
        messages = [
            {
                "role": "system",
                "content": "你是一个播客内容策略师。根据用户的心情和风格偏好，制定内容策略。"
            },
            {
                "role": "user",
                "content": f"""主题：{context.topic}
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
}}"""
            },
        ]

        # temperature 控制生成多样性。0.5 较低，使策略类任务输出更可控、更稳定
        strategy = await self._llm_json(messages, temperature=0.5)

        # 将生成的策略保存到 context 的 metadata 字段中
        context.metadata["mood_strategy"] = strategy
        self.logger.info(f"情绪策略分析完成: {strategy.get('tone', '')}")

        return context
