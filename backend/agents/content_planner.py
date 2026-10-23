"""
Content Planner Agent — 内容结构策划器

功能说明：
读取 context 中的主题、目标时长、MoodAnalyzer 生成的情绪策略，以及 RAG 检索的参考资料，
调用大模型生成播客的整体大纲（包含标题、副标题、分段大纲、核心要点），
将结果写入 context.plan 和 context.title。
"""

from agents.base import BaseAgent, AgentContext


class ContentPlannerAgent(BaseAgent):
    """根据主题与情绪策略规划播客的大纲骨架"""

    def __init__(self, llm_client=None):
        super().__init__("content_planner", llm_client)

    async def execute(self, context: AgentContext) -> AgentContext:
        """
        执行结构规划任务
        :param context: 输入上下文，读取 topic, duration_min, metadata["mood_strategy"], rag_context
        :return: 写入 context.plan 后的上下文
        """
        self.logger.info(f"规划播客大纲: 主题={context.topic}")

        # 获取上一节点 MoodAnalyzer 输出的策略信息
        strategy = context.metadata.get("mood_strategy", {})

        # 如果存在 RAG 检索文本，组装入 Prompt；若为空则不添加该段落
        rag_section = ""
        if context.rag_context:
            rag_section = f"\n\n参考资料：\n{context.rag_context}"

        messages = [
            {
                "role": "system",
                "content": "你是一个播客策划师。根据主题和内容策略，规划播客的结构。"
            },
            {
                "role": "user",
                "content": f"""主题：{context.topic}
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
}}"""
            },
        ]

        # temperature 设为 0.7，兼顾结构合理性与大纲创意
        plan = await self._llm_json(messages, temperature=0.7)

        # 写入 context 供下一环节 ScriptWriter 读取
        context.plan = plan
        context.title = plan.get("title", context.topic)
        self.logger.info(f"大纲规划完成: 《{context.title}》, 共 {len(plan.get('segments', []))} 个分段")

        return context
