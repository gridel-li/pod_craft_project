"""
Script Writer Agent — 播客逐字稿编剧

功能说明：
读取 context 中的策划大纲（context.plan）、情绪策略（context.metadata["mood_strategy"]）、
参考资料（context.rag_context）和用户自定义要求（context.custom_prompt），
通过少量样本提示（Few-shot prompting）引导大语言模型生成适合语音朗读的逐字稿内容，
并将分段脚本列表写入 context.segments 与 context.script。
"""

from agents.base import BaseAgent, AgentContext


class ScriptWriterAgent(BaseAgent):
    """根据大纲与参考材料生成播客各分段口语逐字稿"""

    def __init__(self, llm_client=None):
        super().__init__("script_writer", llm_client)

    async def execute(self, context: AgentContext) -> AgentContext:
        """
        执行脚本编写任务
        :param context: 输入上下文
        :return: 写入 context.script 与 context.segments 后的上下文
        """
        self.logger.info(f"生成播客脚本: 《{context.plan.get('title', context.topic)}》")

        strategy = context.metadata.get("mood_strategy", {})
        plan_segments = context.plan.get("segments", [])

        # 构造参考资料部分
        rag_section = ""
        if context.rag_context:
            rag_section = f"\n\n参考资料（请适当引用）：\n{context.rag_context}"

        # 获取针对当前风格的 Few-shot 样本，帮助模型掌握期望的口语风格与 JSON 数据格式
        few_shot = self._get_few_shot(context.style)

        messages = [
            {
                "role": "system",
                "content": f"""你是一个专业的中文播客脚本作者。

## 你的风格
- {strategy.get('tone', '温暖、有画面感、像在讲故事')}
- {strategy.get('vocabulary', '用口语化表达，不要书面语')}
- 每段控制在 {strategy.get('max_chars', 1000)} 字以内

## 输出格式
请严格按以下 JSON 格式输出："""
            },
            *few_shot,  # 解包样本对话历史插入 messages
            {
                "role": "user",
                "content": f"""请为「{context.topic}」写播客脚本。

结构规划：
{self._format_plan(plan_segments)}

{rag_section}

要求：
- 标题：{context.plan.get('title', '')}
- 风格：{context.style}
- 时长：约 {context.duration_min} 分钟
{f'- 补充要求：{context.custom_prompt}' if context.custom_prompt else ''}

请输出 JSON：
{{
    "title": "播客标题",
    "segments": [
        {{"type": "intro", "content": "开场白", "duration_sec": 30}},
        {{"type": "body", "content": "正文", "duration_sec": 60}},
        {{"type": "outro", "content": "结尾", "duration_sec": 20}}
    ]
}}"""
            },
        ]

        # 脚本编写需要较强的语言丰富度，将 temperature 设为 0.8
        script = await self._llm_json(messages, temperature=0.8)

        context.script = script
        # segments 是下游 TTSClient 与 Reviewer 直接遍历处理的核心数据
        context.segments = script.get("segments", [])
        self.logger.info(f"脚本生成完成: 共 {len(context.segments)} 个片段")

        return context

    def _format_plan(self, segments: list) -> str:
        """把大纲分段列表格式化为提示词中的文本清单"""
        lines = []
        for seg in segments:
            lines.append(f"- [{seg.get('type', '')}] {seg.get('theme', '')}（{seg.get('duration_sec', 0)}秒）")
        return "\n".join(lines)

    def _get_few_shot(self, style: str) -> list[dict]:
        """
        返回预置的 Few-shot 范例对（user 问题 + assistant 标准回答）。
        通过展示高质量示例，让模型直接对齐输出风格与 JSON 结构。
        """
        if style == "humorous":
            return [
                {"role": "user", "content": "请为「为什么程序员总在深夜写代码」写播客脚本"},
                {
                    "role": "assistant",
                    "content": (
                        '{"title":"深夜码农",'
                        '"segments":['
                        '{"type":"intro","content":"你有没有发现，程序员这个物种，白天看起来人模人样，一到晚上十点，眼睛就开始放光。键盘敲得比白天还响，咖啡续了一杯又一杯。","duration_sec":30},'
                        '{"type":"body","content":"说起来挺有意思的。白天开会、回邮件、改bug，忙得像个陀螺。但真正写代码的时间，往往是从晚上十点开始的。为什么？因为白天太吵了，只有深夜，世界安静了，代码才开始流淌。","duration_sec":60},'
                        '{"type":"outro","content":"所以啊，如果你身边有程序员，别催他早点睡。他不是不想睡，是代码不让他睡。晚安，各位深夜码农。","duration_sec":20}'
                        ']}'
                    )
                },
            ]
        return [
            {"role": "user", "content": "请为「秋天的第一杯奶茶」写播客脚本"},
            {
                "role": "assistant",
                "content": (
                    '{"title":"秋天的仪式感",'
                    '"segments":['
                    '{"type":"intro","content":"你有没有发现，每年一到十月，朋友圈就会被一种奇怪的仪式刷屏？不是万圣节，不是双十一，而是——秋天的第一杯奶茶。","duration_sec":30},'
                    '{"type":"body","content":"说起来挺有意思的。一杯奶茶，撑死了二十块钱，但那份被惦记的感觉，比什么贵重礼物都暖。有时候，生活需要的不是多大的惊喜，而是有人记得你在换季的时候，需要一点甜。","duration_sec":60},'
                    '{"type":"outro","content":"所以啊，如果你今天还没有收到那杯奶茶，不妨自己去买一杯。善待自己，也是一种秋天的仪式感。","duration_sec":20}'
                    ']}'
                )
            },
        ]
