"""
Reviewer Agent — 审查脚本质量
"""

from agents.base import BaseAgent, AgentContext


class ReviewerAgent(BaseAgent):
    """审查脚本质量，提出修改建议"""

    def __init__(self, llm_client=None):
        super().__init__("reviewer", llm_client)

    async def execute(self, context: AgentContext) -> AgentContext:
        self.logger.info("审查脚本质量...")

        script_text = ""
        for seg in context.segments:
            script_text += f"[{seg.get('type', '')}]\n{seg.get('content', '')}\n\n"

        messages = [
            {"role": "system", "content": "你是一个播客编辑，负责检查脚本质量。给出修改建议或确认通过。"},
            {"role": "user", "content": f"""请审查以下播客脚本：

{script_text}

检查要点：
1. 内容是否连贯（开场→正文→结尾有逻辑）
2. 风格是否一致（不要一会儿口语一会儿书面）
3. 是否有重复内容
4. 时长是否合理

如果质量合格，输出：{{"approved": true, "notes": "质量合格"}}
如果有问题，输出：{{"approved": false, "notes": "修改建议", "suggestions": ["建议1", "建议2"]}}
"""},
        ]

        review = await self._llm_json(messages, temperature=0.3)
        context.review_notes = review.get("notes", "")
        context.metadata["review"] = review

        if review.get("approved"):
            self.logger.info("脚本审查通过")
        else:
            self.logger.info(f"脚本需要修改: {review.get('notes', '')}")

        return context
