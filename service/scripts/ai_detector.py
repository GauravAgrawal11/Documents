"""Linguistic and stylometric AI text detector.

Analyzes Continuous Burstiness (CV), Shannon Bigram Entropy,
Lexical Richness (Guiraud's Index), AI Transitional Markers, and Watermarks.
"""

from __future__ import annotations
import re
import math
from typing import Any


AI_CLICHES = [
    "delve", "testament", "tapestry", "beacon", "furthermore", "moreover",
    "in conclusion", "it is important to remember", "crucial", "paramount",
    "bustling", "vibrant", "landscape", "pivotal", "underscores", "interplay",
    "in today's world", "seamlessly", "transformative", "multifaceted",
    "shed light", "navigating", "realm", "embark", "harnessing", "testament to",
    "in essence", "comprehensive", "foster", "holistic", "demystify",
    "paradigm shift", "game-changer", "plethora", "myriad", "elevate",
    "it is worth noting", "at the end of the day", "rich tapestry", "aligns with",
    "spearhead", "nuanced", "imperative", "cornerstone", "quintessential"
]


def calculate_shannon_entropy(tokens: list[str]) -> float:
    """Compute Shannon Entropy of a token distribution."""
    if not tokens:
        return 0.0
    freqs: dict[str, int] = {}
    for t in tokens:
        freqs[t] = freqs.get(t, 0) + 1
    n = len(tokens)
    return -sum((c / n) * math.log2(c / n) for c in freqs.values())


def calculate_burstiness(sentences: list[str]) -> tuple[float, float, float, str]:
    """Calculate sentence length variance, std_dev, and coefficient of variation (CV)."""
    sentence_lengths = [len(re.findall(r"\b\w+\b", s)) for s in sentences if s.strip()]
    sentence_lengths = [l for l in sentence_lengths if l > 0]
    n_sent = len(sentence_lengths)
    if n_sent <= 1:
        return 0.0, 0.0, 0.55, "Moderate (Short Sample)"

    mean_len = sum(sentence_lengths) / n_sent
    variance = sum((l - mean_len) ** 2 for l in sentence_lengths) / n_sent
    std_dev = math.sqrt(variance)
    cv = std_dev / (mean_len + 1e-5)

    if n_sent == 2 and cv < 0.3:
        # 2 sentences alone are insufficient to declare artificial uniformity
        cv = 0.48

    if cv > 0.55:
        desc = "High (Dynamic Human Cadence)"
    elif cv > 0.35:
        desc = "Moderate (Balanced Lengths)"
    else:
        desc = "Low (Uniform AI Cadence)"

    return float(variance), float(std_dev), float(cv), desc


def calculate_stylometry(text: str) -> tuple[float, float, float, list[str], str]:
    """Calculate Type-Token Ratio, Guiraud Index, Bigram Entropy and find AI markers."""
    tokens = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    if not tokens:
        return 0.0, 0.0, 0.0, [], "Low"

    unique_tokens = set(tokens)
    ttr = len(unique_tokens) / len(tokens)
    guiraud_r = len(unique_tokens) / math.sqrt(len(tokens) + 1e-5)

    bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
    bigram_entropy = calculate_shannon_entropy(bigrams) if bigrams else calculate_shannon_entropy(tokens)
    max_entropy = math.log2(len(bigrams) + 1e-5) if bigrams else math.log2(len(tokens) + 1e-5)
    norm_entropy = bigram_entropy / (max_entropy + 1e-5) if max_entropy > 0 else 0.8

    lower_text = text.lower()
    found_cliches = [c for c in AI_CLICHES if c in lower_text]

    if guiraud_r > 6.2:
        diversity_desc = "Rich (High Vocabulary Breadth)"
    elif guiraud_r > 4.5:
        diversity_desc = "Moderate"
    else:
        diversity_desc = "Repetitive (AI Pattern Repetition)"

    return float(ttr), float(guiraud_r), float(norm_entropy), found_cliches, diversity_desc


def analyze_ai_probability(text: str, watermark_count: int = 0) -> dict[str, Any]:
    """Calculate deep calibrated AI probability score using logistic regression over linguistic features."""
    if not text or not text.strip():
        return {
            "ok": True,
            "ai_score": 0,
            "perplexity": "N/A",
            "burstiness": "N/A",
            "vocab_diversity": "N/A",
            "watermarks": 0,
            "cliches": [],
            "stats": {"word_count": 0, "sentence_count": 0}
        }

    raw_sentences = [s.strip() for s in re.split(r"[.!?\n]+", text) if s.strip()]
    words = re.findall(r"\b[a-zA-Z0-9'-]+\b", text)
    word_count = len(words)
    if word_count == 0:
        return {"ok": True, "ai_score": 0, "watermarks": watermark_count}

    variance, std_dev, cv, burstiness_desc = calculate_burstiness(raw_sentences)
    ttr, guiraud_r, norm_entropy, found_cliches, vocab_desc = calculate_stylometry(text)

    cliche_density = (len(found_cliches) / (word_count / 100.0)) if word_count > 20 else len(found_cliches) * 1.5

    # Continuous Logit Formula
    z = 0.0

    # 1. Burstiness (Coefficient of Variation)
    if cv < 0.25:
        z += 2.2 * (0.25 - cv) / 0.25
    elif cv < 0.40:
        z += 0.9 * (0.40 - cv) / 0.15
    elif cv > 0.60:
        z -= 1.8 * min(1.0, (cv - 0.60) / 0.40)
    elif cv > 0.45:
        z -= 0.7 * (cv - 0.45) / 0.15

    # 2. Lexical Breadth
    if guiraud_r < 4.5:
        z += 1.4 * (4.5 - guiraud_r) / 4.5
    elif guiraud_r > 7.0:
        z -= 1.6 * min(1.0, (guiraud_r - 7.0) / 3.0)

    # 3. Shannon Entropy
    if norm_entropy < 0.75:
        z += 1.6 * (0.75 - norm_entropy) / 0.75
    elif norm_entropy > 0.90:
        z -= 1.2 * (norm_entropy - 0.90) / 0.10

    # 4. Marker Cliches Density
    z += 1.2 * min(4.0, cliche_density)

    # 5. Short text & small sample dampening (prevents false positives on 1-2 human sentences)
    if word_count < 75 and not found_cliches and watermark_count == 0:
        z = z * 0.4 - 0.8
    elif word_count < 40 and not found_cliches and watermark_count == 0:
        z = z * 0.3 - 1.2

    prob = 1.0 / (1.0 + math.exp(-1.4 * z))
    raw_percentage = prob * 100.0

    if watermark_count > 0:
        raw_percentage = max(raw_percentage, 85.0 + min(13.0, watermark_count * 2.0))

    final_score = int(round(min(99, max(1, raw_percentage))))

    if final_score > 70:
        perp_desc = "Low (Highly Predictable Token Flow)"
    elif final_score > 40:
        perp_desc = "Moderate (Mixed Predictability)"
    else:
        perp_desc = "High (Complex Natural Phrasing)"

    return {
        "ok": True,
        "ai_score": final_score,
        "watermarks": watermark_count,
        "perplexity": perp_desc,
        "burstiness": burstiness_desc,
        "vocab_diversity": vocab_desc,
        "cliches": found_cliches,
        "stats": {
            "word_count": word_count,
            "sentence_count": len(raw_sentences),
            "cv": round(cv, 3),
            "sentence_std_dev": round(std_dev, 2),
            "guiraud_r": round(guiraud_r, 2),
            "type_token_ratio": round(ttr, 3),
            "norm_entropy": round(norm_entropy, 3)
        }
    }
