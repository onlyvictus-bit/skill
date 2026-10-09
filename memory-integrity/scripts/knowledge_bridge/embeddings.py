#!/usr/bin/env python3
"""Phase 4: embedding provider interface. Offline-first, explicit boundaries.

Providers: hashed (stdlib, deterministic, always available), tfidf (needs
scikit-learn; refused with install instructions when absent), learned-*
(DISABLED: refuses until a pinned model artifact + license/privacy approval
exists; never silently substitutes another provider). Every embedding
carries model/version/artifact_hash/dimension/deterministic provenance.
Standard library only (third-party use stays inside provider backends).
"""
import hashlib
import math
import re

PROVIDERS = ("hashed", "tfidf")
DIMENSION = 256


class ProviderError(ValueError):
    pass


def _artifact_hash(provider, version="1"):
    return hashlib.sha256(("victus-embedding:%s:%s" % (provider, version)).encode()).hexdigest()


def _hashed_vector(text, dim=DIMENSION):
    counts = {}
    for token in re.findall(r"[A-Za-z0-9_]+", (text or "").lower()):
        counts[token] = counts.get(token, 0) + 1
    vector = [0.0] * dim
    for token, count in counts.items():
        slot = int(hashlib.sha256(token.encode()).hexdigest(), 16) % dim
        vector[slot] += 1.0 + math.log(1.0 + count)
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def embed(texts, provider="hashed", dim=DIMENSION):
    """Embed a list of strings. Returns {vectors, meta}."""
    if not isinstance(texts, list) or not all(isinstance(t, str) for t in texts):
        raise ProviderError("E_EMBED_INPUT: texts must be a string list")
    if provider == "hashed":
        vectors = [_hashed_vector(t, dim) for t in texts]
        meta = {"model": "victus-hashed-v1", "version": "1",
                "artifact_hash": _artifact_hash("hashed"),
                "dimension": dim, "deterministic": True,
                "evidence_class": "TEST_ONLY"}
        return {"vectors": vectors, "meta": meta}
    if provider == "tfidf":
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
        except ImportError:
            raise ProviderError("E_EMBED_BACKEND: scikit-learn absent; "
                                "install it or use provider='hashed'")
        matrix = TfidfVectorizer().fit_transform(texts).toarray()
        meta = {"model": "sklearn-tfidf", "version": "system",
                "artifact_hash": _artifact_hash("tfidf"),
                "dimension": matrix.shape[1] if len(matrix) else 0,
                "deterministic": True, "evidence_class": "TEST_ONLY"}
        return {"vectors": [list(map(float, row)) for row in matrix], "meta": meta}
    if provider.startswith("learned-"):
        raise ProviderError("E_EMBED_DISABLED: learned provider %r needs a pinned "
                            "model artifact plus license/privacy approval; refusing "
                            "to substitute another backend" % (provider,))
    raise ProviderError("E_EMBED_PROVIDER: unknown provider %r" % (provider,))


def cosine(left, right):
    if len(left) != len(right):
        raise ProviderError("E_EMBED_DIM: vector dimension mismatch")
    denom = math.sqrt(sum(v * v for v in left)) * math.sqrt(sum(v * v for v in right))
    if denom == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / denom


def supported_providers():
    try:
        import sklearn  # noqa: F401
        tfidf = True
    except ImportError:
        tfidf = False
    return {"hashed": True, "tfidf": tfidf, "learned-*": False}
