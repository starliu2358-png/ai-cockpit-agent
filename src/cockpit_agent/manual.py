from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path


class ManualRetriever:
    """Tiny dependency-free BM25 retriever for the local mock owner manual."""

    def __init__(self, manual_path: Path) -> None:
        self.manual_path = manual_path
        self.sections = self._load_sections(manual_path)
        self.tokenized = [self._tokenize(section) for section in self.sections]
        self.doc_freq = Counter()
        for doc in self.tokenized:
            self.doc_freq.update(set(doc))
        self.avg_doc_len = sum(map(len, self.tokenized)) / max(len(self.tokenized), 1)

    @staticmethod
    def _load_sections(path: Path) -> list[str]:
        text = path.read_text(encoding="utf-8")
        return [chunk.strip() for chunk in re.split(r"\n(?=## )", text) if chunk.strip()]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        # English words + individual CJK characters keeps the demo portable.
        return re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text.lower())

    def _score(self, query_tokens: list[str], doc: list[str], k1: float = 1.5, b: float = 0.75) -> float:
        tf = Counter(doc)
        n_docs = len(self.tokenized)
        score = 0.0
        for token in query_tokens:
            freq = tf[token]
            if freq == 0:
                continue
            df = self.doc_freq[token]
            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            denom = freq + k1 * (1 - b + b * len(doc) / max(self.avg_doc_len, 1))
            score += idf * (freq * (k1 + 1)) / denom
        return score

    def search(self, query: str, top_k: int = 2) -> list[str]:
        query_tokens = self._tokenize(query)
        scored = [(self._score(query_tokens, doc), idx) for idx, doc in enumerate(self.tokenized)]
        scored.sort(reverse=True)
        return [self.sections[idx] for score, idx in scored[:top_k] if score > 0]


DEFAULT_MANUAL = Path(__file__).resolve().parents[2] / "data" / "vehicle_manual.md"
manual_retriever = ManualRetriever(DEFAULT_MANUAL)
