from __future__ import annotations

from app.retrieval.graph_rag import GraphRAG
from app.retrieval.ingestion import build_corpus
from app.services.repository import JsonRepository
from scripts.seed import main as seed_main


def test_graph_rag_expands_entities_and_visualizes_graph() -> None:
    seed_main()
    repo = JsonRepository()
    graph = GraphRAG(build_corpus(repo.load_posts(), repo.load_documents()))
    expanded = graph.expand("图书馆 一卡通")
    visual = graph.visualization()
    assert expanded
    assert visual["nodes"]
    assert visual["edges"]

