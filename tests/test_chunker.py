from app.rag.chunking import TextChunker


def test_chunker_keeps_overlap_and_source():
    chunks = TextChunker(200, 30).split("policy.txt", [(1, "Sentence one. " * 40)])
    assert len(chunks) > 1
    assert all(c.source == "policy.txt" and c.page == 1 for c in chunks)
    assert len({c.id for c in chunks}) == len(chunks)

