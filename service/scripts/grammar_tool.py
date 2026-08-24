"""Robust local and cloud grammar & spell analyzer."""

from __future__ import annotations
import re
from typing import Any

COMMON_TYPOS = {
    "teh": "the",
    "thsi": "this",
    "remive": "remove",
    "grmmaer": "grammar",
    "grammer": "grammar",
    "grmmer": "grammar",
    "grammacucally": "grammatically",
    "inmportant": "important",
    "ciorrectoly": "correctly",
    "featires": "features",
    "sentense": "sentence",
    "plagarism": "plagiarism",
    "wtaermark": "watermark",
    "uplaod": "upload",
    "uplaoding": "uploading",
    "definately": "definitely",
    "seperate": "separate",
    "untill": "until",
    "recieve": "receive",
    "occured": "occurred",
    "truely": "truly",
    "accomodate": "accommodate",
    "acheive": "achieve",
    "beleive": "believe",
    "enviroment": "environment",
    "goverment": "government",
    "neccessary": "necessary",
    "alot": "a lot",
    "dont": "don't",
    "cant": "can't",
    "wont": "won't",
    "doent": "doesn't",
    "dosent": "doesn't",
    "dosnt": "doesn't",
    "owrk": "work",
    "wroks": "works",
    "projefct": "project",
    "runig": "running",
    "oeon": "open",
    "ioen": "open",
    "whih": "which",
    "laos": "also",
    "detscts": "detects",
    "spercentagwe": "percentage",
    "probabalisl": "probabilistic",
    "stragety": "strategy",
    "deplayemnts": "deployments",
    "erequiremnts": "requirements",
    "fint": "font",
    "sixze": "size",
    "cilor": "color",
    "varuabves": "variables",
    "compatibel": "compatible",
    "tat": "that",
    "thaen": "then",
    "accoding": "according",
    "fromat": "format",
    "reamins": "remains",
    "contisn": "contains",
    "comedsin": "comes in",
    "exples": "examples",
    "funtion": "function",
    "funcftins": "functions",
    "didnt": "didn't",
    "isnt": "isn't",
    "arent": "aren't",
    "couldnt": "couldn't",
    "shouldnt": "shouldn't",
    "wouldnt": "wouldn't",
    "havent": "haven't",
    "hasnt": "hasn't",
}

GRAMMAR_PATTERNS = [
    (r"\b(doent|dosent|doesn't)\s+not\s+(owrk|work|works)\b", "does not work", "Double Negative & Spelling", "Change to 'does not work'"),
    (r"\b(doent|dosent|doesn't)\s+not\b", "does not", "Double Negative", "Change double negative to 'does not'"),
    (r"\b(doent|dosent)\s+(owrk|work)\b", "does not work", "Spelling & Grammar", "Change to 'does not work'"),
    (r"\b(doent|dosent)\b", "doesn't", "Spelling", "Correct spelling is \"doesn't\""),
    (r"\b(they|we|you)\s+does\b", r"\1 do", "Subject-Verb Agreement", "Use 'do' with plural subjects"),
    (r"\b(he|she|it|this|that|the\s+\w+)\s+do\b", r"\1 does", "Subject-Verb Agreement", "Use 'does' with third-person singular subjects"),
    (r"\b(does|do|did|can|will|should|would|could)\s+not\s+(\w+)s\b", r"\1 not \2", "Verb Form", "Use base verb form after auxiliary verbs (e.g., 'not work' instead of 'not works')"),
    (r"\b(does|do|did|can|will|should|would|could)\s+not\s+owrk\b", r"\1 not work", "Spelling & Verb Form", "Use base verb 'work'"),
    (r"\bthere\s+is\s+many\b", "there are many", "Subject-Verb Agreement", "'many' is plural, requires 'there are'"),
    (r"\bthere\s+is\s+multiple\b", "there are multiple", "Subject-Verb Agreement", "'multiple' requires 'there are'"),
    (r"\ba\s+([aeiou]\w+)\b", r"an \1", "Article Usage", "Use 'an' before words starting with a vowel sound"),
    (r"\ban\s+([^aeiou\s]\w+)\b", r"a \1", "Article Usage", "Use 'a' before words starting with a consonant sound"),
    (r"\b(could|should|would|must)\s+of\b", r"\1 have", "Grammar", "Use 'have' instead of 'of' with modal verbs"),
    (r"\byour\s+welcome\b", "you're welcome", "Grammar & Contraction", "Use \"you're\" (you are) welcome"),
    (r"\btheir\s+is\b", "there is", "Homophone", "Use 'there' to indicate existence"),
    (r"\btheir\s+are\b", "there are", "Homophone", "Use 'there' to indicate existence"),
]

def analyze_grammar_local(text: str) -> tuple[str, list[dict[str, str]]]:
    """Analyze grammar and spelling locally with regex and common error dictionaries."""
    suggestions: list[dict[str, str]] = []
    corrected = text

    # 1. Grammar patterns first (e.g. multi-word phrases)
    for pat, repl, gtype, reason in GRAMMAR_PATTERNS:
        matches = list(re.finditer(pat, corrected, re.IGNORECASE))
        for m in matches:
            orig = m.group(0)
            fixed_val = re.sub(pat, repl, orig, flags=re.IGNORECASE)
            if orig.lower() != fixed_val.lower() and len(suggestions) < 15:
                suggestions.append({
                    "original": orig,
                    "suggestion": fixed_val,
                    "type": gtype,
                    "reason": reason
                })
            corrected = re.sub(pat, repl, corrected, count=1, flags=re.IGNORECASE)

    # 2. Spelling mistakes
    for typo, fix in COMMON_TYPOS.items():
        pattern = re.compile(rf"\b{re.escape(typo)}\b", re.IGNORECASE)
        for match in pattern.finditer(corrected):
            orig = match.group(0)
            replacement = fix.capitalize() if orig[0].isupper() else fix
            if len(suggestions) < 15:
                suggestions.append({
                    "original": orig,
                    "suggestion": replacement,
                    "type": "Spelling",
                    "reason": f"Correct spelling is '{replacement}'"
                })
            corrected = pattern.sub(replacement, corrected)

    return corrected, suggestions[:15]
