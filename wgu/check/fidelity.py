"""Mechanical fidelity pre-check of aligned segments (`%@ KEY` markers): numbers, rule cross-references,
modality/negation/condition/exception/limit cues and glossary coverage.

It produces FLAGS for the meaning reviewer (pass 2), not verdicts: a matching count of cues does not prove the
meaning is preserved, and a mismatch may be legitimate (Polish uses different constructions). Every flag must be
read against the source by the reviewer.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .segments import segments_of

EN_NUM = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
          "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "half": 0.5, "twice": 2, "once": 1, "double": 2}
PL_NUM = {
    0: "zero zera", 1: "jeden jedna jedno jednego jednej jednemu jednym jedną raz",
    2: "dwa dwie dwóch dwu dwoma dwiema dwukrotnie podwójny podwójna podwójnie dwójka",
    3: "trzy trzech trzema trzykrotnie", 4: "cztery czterech czterema", 5: "pięć pięciu pięcioma",
    6: "sześć sześciu sześcioma", 7: "siedem siedmiu", 8: "osiem ośmiu", 9: "dziewięć dziewięciu",
    10: "dziesięć dziesięciu", 11: "jedenaście jedenastu", 12: "dwanaście dwunastu", 0.5: "połowa połowę połowy pół",
}
PL_NUM_MAP = {w: n for n, ws in PL_NUM.items() for w in ws.split()}

# cue categories: (EN regexes, PL regexes). Order matters: prohibition is matched before permission/negation.
CUES = {
    "prohibition": (r"\b(may not|cannot|can not|can't|must not|is not allowed|are not allowed|never|prohibited|forbidden)\b",
                    r"\b(nie może|nie mogą|nie można|nie wolno|nigdy|zabronione|zakazane|nie jest dozwolone|nie są dozwolone)\b"),
    "obligation": (r"\b(must|is required|are required|has to|have to|shall|mandatory|always)\b",
                   r"\b(musi|muszą|należy|trzeba|obowiązkowo|obowiązany|obowiązana|zawsze|wymagane)\b"),
    "permission": (r"\b(may|can|is allowed|are allowed|optionally|at (?:his|her|their|the owning player's) option)\b",
                   r"\b(może|mogą|można|wolno|dozwolone|według uznania|wedle uznania|opcjonalnie)\b"),
    "condition": (r"\b(if|only if|when|whenever|provided|as long as|any time|each time|every time)\b",
                  r"\b(jeśli|jeżeli|gdy|kiedy|o ile|pod warunkiem|tylko wtedy|ilekroć)\b"),
    # only strong exception markers: 'but/however/ale/jednak' are too common to be useful signals
    "exception": (r"\b(unless|except|exception|exceptions|other than)\b",
                  r"\b(chyba że|z wyjątkiem|wyjątek|wyjątki|wyjątkiem|poza tym że)\b"),
    "limit": (r"\b(up to|at least|at most|more than|fewer than|less than|maximum|minimum|only|each|every|per|exactly|no more than)\b",
              r"\b(do|co najmniej|najwyżej|więcej niż|mniej niż|maksymalnie|minimalnie|maksimum|minimum|tylko|wyłącznie|jedynie|każd\w*|na|dokładnie|nie więcej niż)\b"),
    "order": (r"\b(before|after|then|first|immediately|until|during|simultaneously)\b",
              r"\b(przed|po|następnie|potem|najpierw|natychmiast|niezwłocznie|aż|dopóki|podczas|w trakcie|jednocześnie)\b"),
    "negation": (r"\b(not|no|none|neither|nor)\b|n't\b", r"\b(nie|żaden|żadna|żadne|żadnych|żadnej|ani)\b"),
    # scope/limit markers whose loss usually widens or narrows a rule (only, once, boundaries)
    # 'once' is left out: 'Once Depleted, …' means 'when'; 'only once per' is still caught by 'only'/'per'
    "scope": (r"\b(only|twice|per|or more|or less|or fewer|equal to|at least|at most|up to|no more than|maximum|minimum|exceeds?)\b",
              r"\b(tylko|wyłącznie|jedynie|raz|dwa razy|w granicach|lub więcej|lub mniej|co najmniej|najwyżej|nie więcej niż|maksymalnie|minimalnie|osiąg\w*|równ\w*|przekracza\w*|przekroczy\w*)\b"),
}


MACRO_TEXT = {r"\wyjatek": " Wyjątek: ", r"\wyjatki": " Wyjątki: ", r"\uwaga": " Uwaga: ", r"\opcja": " (Opcjonalnie) "}


def detex(s: str) -> str:
    s = re.sub(r"(?<!\\)%.*", "", s)
    for macro, text in MACRO_TEXT.items():            # semantic macros that print words
        s = re.sub(re.escape(macro) + r"(?![a-zA-Z])", text, s)
    s = re.sub(r"\\ang\{[^}]*\}", "", s)                 # bilingual glosses are not content
    s = re.sub(r"\\(?:begin|end)\{[^}]*\}(?:\[[^\]]*\])?(?:\{[^}]*\})?", " ", s)
    s = re.sub(r"\\[a-zA-Z@]+\*?", " ", s)
    s = s.replace("{", "").replace("}", "").replace("~", " ").replace("--", "–")
    return re.sub(r"[ \t]+", " ", s)


def numbers(text: str, lang: str) -> Counter:
    c = Counter()
    t = text.replace("½", " 0.5 ").replace("¼", " 0.25 ")
    for m in re.finditer(r"(?<![\w.])(\d+(?:[.,]\d+)?)(?![\w]|\.\d)", t):
        c[float(m.group(1).replace(",", "."))] += 1
    if lang == "digits":
        return c
    words = re.findall(r"[A-Za-zÀ-žąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+", t.lower())
    table = EN_NUM if lang == "en" else PL_NUM_MAP
    for w in words:
        if w in table:
            c[float(table[w])] += 1
    return c


def refs(text: str) -> Counter:
    return Counter(re.findall(r"(?<![\d.])\d+\.\d+(?:\.\d+)*(?![\d])", text))


def cues(text: str, lang: str) -> Counter:
    t = text.lower()
    c = Counter()
    for cat, (en, pl) in CUES.items():
        rx = en if lang == "en" else pl
        hits = re.findall(rx, t)
        c[cat] = len(hits)
        if cat == "prohibition":   # do not double count 'nie może' as negation+permission
            t = re.sub(rx, " ", t)
    return c


def compare(src_seg: str, pl_seg: str, terms=None) -> list[str]:
    flags = []
    pl = detex(pl_seg)
    # dice notation and ranges are numbers too; ignore rule refs in number comparison
    en_n = numbers(re.sub(r"\d+\.\d+(?:\.\d+)*", " ", src_seg), "en")
    pl_n = numbers(re.sub(r"\d+\.\d+(?:\.\d+)*", " ", pl), "pl")
    # 'one/a single/once' vs 'jeden/raz' are too ambiguous as words (articles, 'once Depleted' = 'when'):
    # the value 1 is compared only when written as a digit
    en_d, pl_d = numbers(re.sub(r"\d+\.\d+(?:\.\d+)*", " ", src_seg), "digits"), numbers(re.sub(r"\d+\.\d+(?:\.\d+)*", " ", pl), "digits")
    for n in list(en_n):
        if n == 1:
            en_n[n] = en_d[n]
    for n in list(pl_n):
        if n == 1:
            pl_n[n] = pl_d[n]
    miss, extra = +(en_n - pl_n), +(pl_n - en_n)
    if miss:
        flags.append(f"numbers missing in PL: {dict(miss)}")
    if extra:
        flags.append(f"numbers only in PL: {dict(extra)}")
    r_en, r_pl = refs(src_seg), refs(pl)
    if r_en - r_pl:
        flags.append(f"cross-refs missing in PL: {sorted(r_en - r_pl)}")
    if r_pl - r_en:
        flags.append(f"cross-refs only in PL: {sorted(r_pl - r_en)}")
    ce, cp = cues(src_seg, "en"), cues(pl, "pl")
    for cat in ["prohibition", "obligation", "permission", "exception", "condition"]:
        if ce[cat] and not cp[cat]:
            flags.append(f"{cat}: {ce[cat]}× in EN, none in PL")
        elif cp[cat] and not ce[cat]:
            flags.append(f"{cat}: {cp[cat]}× in PL, none in EN")
    for cat in ["negation", "scope"]:          # one-directional: losing them in PL changes the rule
        if ce[cat] and not cp[cat]:
            flags.append(f"{cat}: {ce[cat]}× in EN, none in PL")
        elif ce[cat] >= 2 and cp[cat] * 3 < ce[cat]:
            flags.append(f"{cat}: {ce[cat]}× in EN, only {cp[cat]}× in PL")
    if terms:
        from ..terms.store import forms, word_re
        # longest source terms first; a matched term is masked so that 'Cohesion' inside 'Cohesion Hit'
        # does not count as a separate occurrence of the shorter concept
        masked = src_seg
        pairs = [(s, c) for c in terms.effective.values() if c["status"] in ("approved", "proposal", "disputed") and c.get("pl")
                 for s in [c["source_term"], *c.get("variants", [])]]
        hit = {}
        for s, c in sorted(pairs, key=lambda p: len(p[0]), reverse=True):
            rx = word_re(s, ignore_case=False)
            if rx.search(masked):
                hit[c["id"]] = c
                masked = rx.sub(" ", masked)
        for c in hit.values():
            if not any(word_re(f).search(pl) for f in forms(c)):
                flags.append(f"term [{c['id']}] '{c['source_term']}' in EN, no form of '{c['pl']}' in PL")
    return flags


def run(src: Path, tex_paths: list[Path], terms=None) -> int:
    s = segments_of(src)
    p = {}
    for f in tex_paths:
        p.update(segments_of(f))
    n_flag = 0
    for key in s:
        if key not in p:
            print(f"[{key}] MISSING in translation")
            n_flag += 1
            continue
        flags = compare(s[key], p[key], terms)
        print(f"[{key}] {'ok' if not flags else 'CHECK'}")
        for fl in flags:
            print("   -", fl)
        n_flag += bool(flags)
    for key in p:
        if key not in s:
            print(f"[{key}] only in translation (no source segment)")
    print(f"\n{len(s)} source segments, {n_flag} flagged. Flags are hints for the meaning review, not verdicts.")
    return 0
