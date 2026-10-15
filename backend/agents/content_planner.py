"""
Content Planner Agent — 规划播客结构
"""

from agents.base import BaseAgent, AgentContext


class ContentPlannerAgent(BaseAgent):
    """规划播客结构"""

    def __init__(self, llm_client=None):
        super().__init__("content_planner", llm_client)

    async def execute(self, context: AgentContext) -> AgentContext:
        self.logger.info(f"规划内容: {context.topic}")

        strategy = context.metadata.get("mood_strategy", {})
        rag_section = ""
        if context.rag_context:
            rag_section = f"\n\n参考资料：\n{context.rag_context}"

        messages = [
            {"role": "system", "content": "你是一个播客策划师。根据主题和内容策略，规划播客的结构。"},
            {"role": "user", "content": f"""主题：{context.topic}
时长：{context.duration_min} 分钟
语气：{strategy.get('tone', '自然平和')}
语速：{strategy.get('pace', '正常')}
{rag_section}

请规划播客结构 JSON：
{{
    "title": "播客标题（10字以内）",
    "subtitle": "副标题",
    "segments": [
        {{"type": "intro", "theme": "开场主题", "duration_sec": 30}},
        {{"type": "body", "theme": "正文主题1", "duration_sec": 60}},
        {{"type": "body", "theme": "正文主题2", "duration_sec": 60}},
        {{"type": "outro", "theme": "结尾主题", "duration_sec": 20}}
    ],
    "key_points": ["要点1", "要点2"]
}}"""},
        ]

        plan = await self._llm_json(messages, temperature=0.7)
        context.plan = plan
        context.title = plan.get("title", context.topic)
        self.logger.info(f"规划完成: {plan.get('title', '')}, {len(plan.get('segments', []))} 个片段")
        return context
