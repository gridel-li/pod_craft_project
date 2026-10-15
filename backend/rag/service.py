"""
RAG 服务 — 检索增强生成
"""

import logging
import uuid

import chromadb

from config.settings import settings
from config.exceptions import RAGError

logger = logging.getLogger(__name__)


class RAGService:
    """RAG 知识库服务"""

    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="podcraft_knowledge",
            metadata={"hnsw:space": "cosine"},
        )

    def add_document(self, content: str, title: str = "", source: str = "", chunk_size: int = 500) -> int:
        """添加文档（自动切分）"""
        try:
            chunks = self._split_text(content, chunk_size)
            ids = [f"{uuid.uuid4().hex[:12]}" for _ in chunks]
            metadatas = [{"title": title, "source": source, "chunk_index": i} for i in range(len(chunks))]

            self.collection.add(documents=chunks, ids=ids, metadatas=metadatas)
            logger.info(f"添加文档: {title}, {len(chunks)} 个 chunk")
            return len(chunks)
        except Exception as e:
            raise RAGError(f"添加文档失败: {e}") from e

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """检索相关文档"""
        try:
            if self.collection.count() == 0:
                return []
            results = self.collection.query(query_texts=[query], n_results=min(top_k, self.collection.count()))
            docs = []
            for i, doc in enumerate(results["documents"][0]):
                docs.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
            return docs
        except Exception as e:
            raise RAGError(f"检索失败: {e}") from e

    def get_context(self, query: str, top_k: int = 5) -> str:
        """检索并拼接为上下文"""
        results = self.search(query, top_k)
        if not results:
            return ""
        parts = []
        for i, doc in enumerate(results, 1):
            source = doc["metadata"].get("source", "未知")
            parts.append(f"[参考资料 {i}] (来源: {source})\n{doc['content']}")
        return "\n\n".join(parts)

    def get_doc_count(self) -> int:
        return self.collection.count()

    @staticmethod
    def _split_text(text: str, chunk_size: int = 500) -> list[str]:
        """按段落切分文本"""
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
