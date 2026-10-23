"""
RAGService — 检索增强生成服务

功能说明：
使用 ChromaDB 嵌入式向量数据库进行私有文档的切分、特征向量存储与语义检索。
主要步骤：
1. add_document：接收文档纯文本，按段落和字符上限切分成多个 chunk，存储至 ChromaDB 集合。
2. search：接收 query 查询词，由 ChromaDB 计算语义向量并检索出最相近的 Top-K 个 chunk。
3. get_context：将 search 检索到的多个 chunk 格式化为带有来源标注的上下文文本，供 Prompt 引用。
"""

import logging
import uuid
import chromadb

from config.settings import settings
from config.exceptions import RAGError

logger = logging.getLogger(__name__)


class RAGService:
    """RAG 知识库检索与文档切分服务"""

    def __init__(self):
        # 1. 初始化持久化客户端，数据保存在本地目录（settings.chroma_persist_dir）
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        # 2. 获取或新建名为 podcraft_knowledge 的集合，距离算法配置为余弦距离（cosine）
        self.collection = self.client.get_or_create_collection(
            name="podcraft_knowledge",
            metadata={"hnsw:space": "cosine"},
        )

    def add_document(self, content: str, title: str = "", source: str = "", chunk_size: int = 500) -> int:
        """
        向知识库添加长文本：先切块，再入库建立索引
        :param content: 文档正文内容
        :param title: 文档标题
        :param source: 文档来源标识
        :param chunk_size: 单个切块的最大字符数
        :return: 成功入库的 chunk 数量
        """
        try:
            # 步骤 1: 文本切块
            chunks = self._split_text(content, chunk_size)
            # 步骤 2: 为每个 chunk 生成全局唯一 ID
            ids = [f"{uuid.uuid4().hex[:12]}" for _ in chunks]
            # 步骤 3: 构造元数据字典列表
            metadatas = [
                {"title": title, "source": source, "chunk_index": i}
                for i in range(len(chunks))
            ]

            # 步骤 4: 写入 ChromaDB，库内会自动计算向量并建立 HNSW 索引
            self.collection.add(documents=chunks, ids=ids, metadatas=metadatas)
            logger.info(f"添加文档成功: {title}, 生成 {len(chunks)} 个 chunk")
            return len(chunks)
        except Exception as e:
            raise RAGError(f"添加文档失败: {e}") from e

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        向量相似度检索
        :param query: 搜索关键词或自然语言问题
        :param top_k: 最大返回结果数量
        :return: 检索结果列表，每项包含 content, metadata, distance
        """
        try:
            if self.collection.count() == 0:
                return []

            # 检索数量不能超过集合内现存文档总量
            actual_k = min(top_k, self.collection.count())
            results = self.collection.query(
                query_texts=[query],
                n_results=actual_k
            )

            docs = []
            for i, doc in enumerate(results["documents"][0]):
                docs.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    # distance: 余弦距离，取值 0 到 2 之间，数值越小代表语义越相似
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
            return docs
        except Exception as e:
            raise RAGError(f"检索失败: {e}") from e

    def get_context(self, query: str, top_k: int = 5) -> str:
        """
        检索并格式化为上下文文本，供放入大模型 Prompt
        :param query: 检索主题
        :param top_k: 引用切块数量
        :return: 格式化后的参考资料文本
        """
        results = self.search(query, top_k)
        if not results:
            return ""

        parts = []
        for i, doc in enumerate(results, 1):
            source = doc["metadata"].get("source", "未知")
            parts.append(f"[参考资料 {i}] (来源: {source})\n{doc['content']}")

        return "\n\n".join(parts)

    def get_doc_count(self) -> int:
        """获取向量数据库中现存的 chunk 总数"""
        return self.collection.count()

    @staticmethod
    def _split_text(text: str, chunk_size: int = 500) -> list[str]:
        """
        文本切分逻辑：优先按双换行符（自然段）切分，在不超过 chunk_size 的前提下合并相邻短段落
        """
        paragraphs = text.split("\n\n")
        chunks = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) > chunk_size and current:
                chunks.append(current.strip())
                current = para
            else:
                current += "\n\n" + para if current else para

        if current.strip():
            chunks.append(current.strip())

        return chunks if chunks else [text]
