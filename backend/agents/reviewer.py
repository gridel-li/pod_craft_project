"""
Reviewer Agent — 播客脚本质量审查器

功能说明：
读取 context.segments 中的全部台词，拼接成完整文本后调用大模型进行质量评估。
评估维度包括：连贯性、口语风格统一性、冗余重复性、时长合理性。
评估结果（是否通过、修改建议）写入 context.review_notes 与 context.metadata["review"]。
"""

from agents.base import BaseAgent, AgentContext


class ReviewerAgent(BaseAgent):
    """审查脚本质量并输出结构化审查意见"""

    def __init__(self, llm_client=None):
        super().__init__("reviewer", llm_client)

    async def execute(self, context: AgentContext) -> AgentContext:
        """
        执行脚本审查任务
        :param context: 输入上下文，读取 context.segments
        :return: 写入 context.review_notes 与 context.metadata["review"] 后的上下文
        """
        self.logger.info("开始审查播客脚本质量...")

        # 遍历分段列表，格式化为包含段落类型的全文文本供模型审查
        script_text = ""
        for seg in context.segments:
            seg_type = seg.get("type", "")
            content = seg.get("content", "")
            script_text += f"[{seg_type}]\n{content}\n\n"

        messages = [
            {
                "role": "system",
                "content": "你是一个播客编辑，负责检查脚本质量。给出修改建议或确认通过。"
            },
            {
                "role": "user",
                "content": f"""请审查以下播客脚本：

{script_text}

检查要点：
1. 内容是否连贯（开场→正文→结尾有逻辑）
2. 风格是否一致（不要一会儿口语一会儿书面）
3. 是否有重复内容
4. 时长是否合理

如果质量合格，输出：{{"approved": true, "notes": "质量合格"}}
如果存在问题，输出：{{"approved": false, "notes": "修改建议", "suggestions": ["建议1", "建议2"]}}
"""
            },
        ]

        # 质检评估需要标准严格且输出稳定，temperature 设为 0.3
        review = await self._llm_json(messages, temperature=0.3)

        context.review_notes = review.get("notes", "")
        context.metadata["review"] = review

        if review.get("approved"):
            self.logger.info("脚本审查通过")
        else:
            self.logger.info(f"脚本需要修改: {review.get('notes', '')}")

        return context
