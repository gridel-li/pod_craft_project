"""
Tests for RAG service (ChromaDB-based knowledge base)
"""

import pytest

from rag.service import RAGService
from config.settings import settings


@pytest.fixture
def rag_service(tmp_path):
    """Create a RAG service with a temporary ChromaDB directory"""
    original = settings.chroma_persist_dir
    settings.chroma_persist_dir = str(tmp_path / "chroma_test")
    service = RAGService()
    yield service
    settings.chroma_persist_dir = original


class TestRAGService:

    def test_add_document(self, rag_service):
        count = rag_service.add_document(
            content="Python 是一门优雅的编程语言，广泛用于数据科学、Web 开发和自动化。",
            title="Python 介绍",
            source="wiki",
        )
        assert count >= 1
        assert rag_service.get_doc_count() >= 1

    def test_search_returns_results(self, rag_service):
        rag_service.add_document(
            content="FastAPI 是基于 Python 的现代 Web 框架，支持异步和自动文档生成。",
            title="FastAPI 简介",
        )
        results = rag_service.search("Web 框架", top_k=3)
        assert len(results) > 0
        assert "content" in results[0]
        assert "metadata" in results[0]

    def test_search_empty_collection(self, rag_service):
        results = rag_service.search("any query")
        assert results == []

    def test_get_context_returns_formatted_string(self, rag_service):
        rag_service.add_document(
            content="React 是一个用于构建用户界面的 JavaScript 库。",
            title="React 入门",
            source="docs",
        )
        ctx = rag_service.get_context("前端框架", top_k=3)
        assert "参考资料" in ctx
        assert "React" in ctx

    def test_get_context_empty_returns_empty_string(self, rag_service):
        ctx = rag_service.get_context("nothing")
        assert ctx == ""

    def test_split_text(self):
        text = "段落一\n\n段落二\n\n段落三\n\n段落四"
        chunks = RAGService._split_text(text, chunk_size=8)
        assert len(chunks) >= 2
        # All original content should be preserved
        joined = " ".join(chunks)
        assert "段落一" in joined
        assert "段落四" in joined

    def test_split_text_single_paragraph(self):
        text = "这是一段很短的文字"
        chunks = RAGService._split_text(text, chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_add_multiple_documents(self, rag_service):
        rag_service.add_document(content="文档一的内容", title="Doc 1")
        rag_service.add_document(content="文档二的内容", title="Doc 2")
        assert rag_service.get_doc_count() >= 2
