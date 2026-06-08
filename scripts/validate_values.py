#!/usr/bin/env python3
"""
validate_values.py — Extrae valores del HTML renderizado y compara contra
las cifras citadas en el texto interpretativo.

Uso:
    python scripts/validate_values.py docs/chapters/semana08.html
    python scripts/validate_values.py --all

La auditoría manual del 2026-06-01 encontró 37+ inconsistencias entre la
salida de R y el texto. Este script automatiza esa verificación.
"""

import argparse
import json
import math
import re
import sys
import unicodedata
from pathlib import Path
from collections import OrderedDict

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Error: BeautifulSoup4 no instalado. Ejecuta: pip install beautifulsoup4")


# ── Regex patterns for value extraction ────────────────────────────────────

# Each pattern defines: (name, regex, value_group_index)
# The regex must capture the numeric value in group 1 (or groups 1 and 2 for IC bounds)

# Patterns for R output (more structured, = or : separators)
R_PATTERNS = [
    # Chi-squared variants
    ("chi2", re.compile(
        r"(?:χ²|chi[-\s]?sq(?:uared)?|X-squared|K-squared|Bartlett'?s?\s*K-squared)"
        r"\s*[=:]\s*([\d.eE+-]+)",
        re.IGNORECASE
    )),
    # p-value (all variants)
    ("p", re.compile(
        r"p[-\s]*(?:value|valor|val)?\s*[=:<]\s*([\d.eE+-]+)",
        re.IGNORECASE
    )),
    # t-statistic
    ("t", re.compile(
        r"\b(?:t|t[-\s]*obs|texp)\s*[=:]\s*([\d.eE+-]+)",
        re.IGNORECASE
    )),
    # Degrees of freedom
    ("df", re.compile(
        r"\b(?:df|gl|gl[₁₁12]?|g\.l\.)\s*[=:]\s*([\d.eE+-]+)",
        re.IGNORECASE
    )),
    # Shapiro-Wilk W
    ("W", re.compile(
        r"\bW\s*[=:]\s*([\d.eE+-]+)",
        re.IGNORECASE
    )),
    # Odds Ratio
    ("OR", re.compile(
        r"\b(?:OR|Odds\s*Ratio)\s*[=:]\s*([\d.eE+-]+)",
        re.IGNORECASE
    )),
    # Risk Ratio / Relative Risk
    ("RR", re.compile(
        r"\b(?:RR|Risk\s*Ratio|Riesgo\s*Relativo)\s*[=:]\s*([\d.eE+-]+)",
        re.IGNORECASE
    )),
    # F-statistic
    ("F", re.compile(
        r"\b(?:F|F[-\s]*exp|F[-\s]*statistic|F[-\s]*value)\s*[=:]\s*([\d.eE+-]+)",
        re.IGNORECASE
    )),
    # Effect size r
    ("r_effect", re.compile(
        r"\br\s*[=:]\s*([\d.eE+-]+)",
        re.IGNORECASE
    )),
    # R-squared
    ("R2", re.compile(
        r"\b(?:R²|R-squared|R2|Multiple\s+R-squared)\s*[=:]\s*([\d.eE+-]+)",
        re.IGNORECASE
    )),
    # Mean
    ("mean", re.compile(
        r"\b(?:media|mean)\s*[=:]\s*([\d.eE+-]+)",
        re.IGNORECASE
    )),
    # Sample size n
    ("n", re.compile(
        r"(?:^|\s)n\s*[=:]\s*(\d+)",
        re.IGNORECASE
    )),
    # Standard deviation
    ("sd", re.compile(
        r"\b(?:sd|dt|desviación|std\.?\s*dev)\s*[=:]\s*([\d.eE+-]+)",
        re.IGNORECASE
    )),
]


def extract_ic_bounds_r(text):
    """Extract ALL CI bounds from R output. Multiple ICs are indexed:
    IC_lo, IC_hi, IC_lo_2, IC_hi_2, ...

    Handles:
      95%-IC(OR)= (1.070, 7.013) and 95%-IC(Ra)= (0.082, 0.615)
      IC 95%: [ 22.7 ,  24.4 ]
      95 percent confidence interval: -12.54  -8.76
    """
    results = []

    # Single pattern that handles all Spanish/BioEstatR IC formats
    ic_pat = re.compile(
        r'(?:IC|CI)\s*'
        r'(?:\([^)]*\))?'          # optional (OR), (Ra), etc.
        r'(?:[_\s]*(?:95%?|del?\s*95%?))?'  # optional 95%
        r'\s*[=:]\s*'
        r'[\[\(]\s*([\d.-]+(?:\s*[eE][+-]?\d+)?)\s*[,;\s]+\s*([\d.-]+(?:\s*[eE][+-]?\d+)?)\s*[\]\)]',
        re.IGNORECASE
    )
    for m in ic_pat.finditer(text):
        lo, hi = safe_float(m.group(1)), safe_float(m.group(2))
        results.append(("IC_lo", lo))
        results.append(("IC_hi", hi))

    # Base R: "95 percent confidence interval:\n -12.54  -8.76"
    r_ci = re.compile(
        r'95\s*(?:%|percent)\s*confidence\s*interval\s*:?\s*\n?\s*'
        r'([\d.-]+)\s+([\d.-]+)',
        re.IGNORECASE
    )
    for m in r_ci.finditer(text):
        lo, hi = safe_float(m.group(1)), safe_float(m.group(2))
        results.append(("IC_lo", lo))
        results.append(("IC_hi", hi))

    return results


# Patterns for interpretive text (values may be inside MathJax or plain text)
# These match within MathJax delimiters \(...\) or in plain text
# Number pattern allowing scientific notation (5e-06, 1.23E+05)
_NUM_T = r'([\d.]+(?:[eE][+-]?\d+)?)'

TEXT_PATTERNS = [
    ("chi2", re.compile(
        r'(?:χ²|\\\\chi\^2[_\sA-Za-z]*|chi[-\s]?cuadrado)\s*[≈=]?\s*' + _NUM_T,
        re.IGNORECASE
    )),
    ("p", re.compile(
        r'p\s*[=<>]\s*' + _NUM_T,
        re.IGNORECASE
    )),
    ("t", re.compile(
        r'\b(?:t|t_\{?obs\}?)\s*[=]\s*([\d.-]+(?:[eE][+-]?\d+)?)',
        re.IGNORECASE
    )),
    ("df", re.compile(
        r'\b(?:df|gl|g\.?l\.?)\s*[=]\s*' + _NUM_T,
        re.IGNORECASE
    )),
    ("W", re.compile(
        r'\bW\s*[=]\s*' + _NUM_T,
        re.IGNORECASE
    )),
    ("OR", re.compile(
        r'\b(?:OR|odds\s*ratio)\s*[=]\s*' + _NUM_T,
        re.IGNORECASE
    )),
    ("RR", re.compile(
        r'\b(?:RR|riesgo\s*relativo)\s*[=]\s*' + _NUM_T,
        re.IGNORECASE
    )),
    ("r_effect", re.compile(
        r'\br\s*[=]\s*' + _NUM_T,
        re.IGNORECASE
    )),
    ("R2", re.compile(
        r'\b(?:R²|R\^2|R2)\s*[=≈]?\s*' + _NUM_T,
        re.IGNORECASE
    )),
    ("mean", re.compile(
        r'\b(?:media|mean)\s*[=≈]?\s*' + _NUM_T,
        re.IGNORECASE
    )),
    ("n", re.compile(
        r'\bn\s*[=≈]\s*(\d+)',
        re.IGNORECASE
    )),
]


def extract_ic_bounds_text(text):
    """Extract CI bounds from interpretive text.

    Handles:
      IC 95%: 1.07–7.01
      IC_{95%}: 2.30–5.25
      CI 95%: [1.79, 3.98]
      IC 95% resultante (≈ [22.7, 24.4] kg/m²)
    """
    results = []
    pat = re.compile(
        r'(?:IC|CI)[_\s]*(?:\d+\s*%|\\?95\\?%?)\s*[=:(]*'
        r'(?:≈\s*)?[\[\(]?\s*([\d.eE+-]+)\s*[,;\-–—]+\s*([\d.eE+-]+)\s*[\]\)]?',
        re.IGNORECASE
    )
    for m in pat.finditer(text):
        lo, hi = safe_float(m.group(1)), safe_float(m.group(2))
        results.append(("IC_lo", lo))
        results.append(("IC_hi", hi))
    return results


# ── Tolerance configuration ────────────────────────────────────────────────

# For each stat type: absolute tolerance for numeric comparison
# Also: whether to flag as critical if significance changes (for p-values)
TOLERANCES = {
    "chi2": 0.1,
    "p": None,  # dynamic: see p_tolerance()
    "t": 0.05,
    "df": 1.0,    # df are integers, but text may round
    "W": 0.01,
    "OR": 0.1,
    "RR": 0.1,
    "F": 0.1,
    "r_effect": 0.05,
    "R2": 0.01,
    "mean": 0.1,
    "n": 0,       # exact match for sample size
    "sd": 0.1,
    "IC_lo": 0.1,
    "IC_hi": 0.1,
}


def p_tolerance(p_actual):
    """Dynamic tolerance for p-values based on magnitude."""
    if p_actual < 0.001:
        return 0.0005
    elif p_actual < 0.01:
        return 0.002
    elif p_actual < 0.05:
        return 0.01
    else:
        return 0.02


def severity_for_p(claimed, actual):
    """Check if p-value discrepancy changes statistical conclusion at α=0.05."""
    sig_claimed = claimed < 0.05
    sig_actual = actual < 0.05
    if sig_claimed != sig_actual:
        return "critical"
    tol = p_tolerance(actual)
    if abs(claimed - actual) > tol * 5:
        return "warning"
    if abs(claimed - actual) > tol:
        return "info"
    return None  # within tolerance


def severity_for_stat(name, claimed, actual):
    """Determine severity of a discrepancy for non-p-value stats."""
    tol = TOLERANCES.get(name, 0.05)
    diff = abs(claimed - actual)
    if tol == 0:
        # exact match required (e.g., n)
        return "critical" if diff > 0 else None
    if diff > tol * 5:
        return "critical"
    elif diff > tol * 2:
        return "warning"
    elif diff > tol:
        return "info"
    return None


def values_match(name, claimed, actual, text_snippet=""):
    """Check if claimed and actual values match within tolerance.

    For p-values with inequalities in text:
      - "p < 0.05" → actual must be < claimed
      - "p > 0.05" → actual must be > claimed
    """
    if name == "p":
        # Check for inequality in the original text snippet
        ineq = extract_p_inequality(text_snippet)
        if ineq and ineq[0] == '<':
            return actual <= ineq[1] * 1.01  # 1% grace for precision
        if ineq and ineq[0] == '>':
            return actual >= ineq[1] * 0.99
        # Exact-ish comparison
        tol = p_tolerance(actual)
        return abs(claimed - actual) <= tol
    tol = TOLERANCES.get(name, 0.05)
    if tol == 0:
        return claimed == actual
    return abs(claimed - actual) <= tol


# ── HTML parsing ───────────────────────────────────────────────────────────


def safe_float(s):
    """Convert string to float, stripping trailing punctuation."""
    s = s.strip().rstrip(".,;:)}\"']")
    return float(s)


def normalize_text(text):
    """Normalize Unicode to NFC so precomposed accents match regex."""
    return unicodedata.normalize("NFC", text)


def clean_mathjax(text):
    """Remove MathJax delimiters from text, keeping the LaTeX content.

    \( ... \) → keep content
    \[ ... \] → keep content
    $ ... $ → keep content
    """
    text = normalize_text(text)
    # Inline math: \( ... \)
    text = re.sub(r'\\\((.*?)\\\)', r'\1', text)
    # Display math: \[ ... \]
    text = re.sub(r'\\\[(.*?)\\\]', r'\1', text, flags=re.DOTALL)
    # Dollar math: $ ... $ (single line, non-greedy)
    text = re.sub(r'\$(.*?)\$', r'\1', text)
    return text


def extract_from_text(text):
    """Extract all numeric statistical values from a text string."""
    cleaned = clean_mathjax(text)

    values = OrderedDict()

    for name, pattern in TEXT_PATTERNS:
        for m in pattern.finditer(cleaned):
            val = safe_float(m.group(1))
            if name not in values:
                values[name] = val

    for name, val in extract_ic_bounds_text(cleaned):
        key = name
        i = 1
        while key in values:
            i += 1
            key = f"{name}_{i}"
        values[key] = val

    return values


def extract_p_inequality(text):
    """Check if a p-value in text has an inequality operator.

    Returns ('<', threshold) or ('>', threshold) or ('=', value) or None.
    """
    # Look for p < value or p > value or p = value
    p_ineq = re.search(
        r'p\s*(<|>)\s*([\d.]+(?:[eE][+-]?\d+)?)',
        clean_mathjax(text),
        re.IGNORECASE
    )
    if p_ineq:
        return p_ineq.group(1), safe_float(p_ineq.group(2))
    return None


def extract_from_r_output(text):
    """Extract all numeric statistical values from R console output."""
    values = OrderedDict()

    for name, pattern in R_PATTERNS:
        matches = list(pattern.finditer(text))
        for m in matches:
            val = safe_float(m.group(1))
            key = name
            i = 1
            while key in values:
                i += 1
                key = f"{name}_{i}"
            values[key] = val

    # CI bounds — use indexing for multiple ICs
    for name, val in extract_ic_bounds_r(text):
        key = name
        i = 1
        while key in values:
            i += 1
            key = f"{name}_{i}"
        values[key] = val

    return values


def parse_html(html_path):
    """Parse HTML and extract R-output blocks and interpretive paragraphs.

    Only paragraphs inside callout-body-container that contain
    "Interpretación" (or follow R output directly) are checked.

    Returns:
        r_blocks: list of { "chunk_id": N, "text": "...", "values": {...} }
        text_claims: list of { "text": "...", "values": {...} }
    """
    with open(html_path) as f:
        soup = BeautifulSoup(f, "html.parser")

    r_blocks = []

    # Collect all R output blocks in DOM order
    for i, cell in enumerate(soup.select("div.cell-output-stdout")):
        code = cell.select_one("pre code")
        if code:
            text = normalize_text(code.get_text())
            values = extract_from_r_output(text)
            if values:
                r_blocks.append({
                    "chunk_id": i,
                    "text": text.strip()[:200],
                    "values": values,
                    "sourceline": cell.sourceline or 0,
                })

    if not r_blocks:
        return r_blocks, [], soup

    # Collect interpretive paragraphs.
    # Only consider: (a) inside callout-body with "Interpretación" keyword,
    # or (b) directly follow an R output block within short distance.
    # Skip exercise paragraphs.
    text_claims = []

    # Get all sourcelines of R blocks for proximity matching
    r_lines = [b["sourceline"] for b in r_blocks]

    for p in soup.select("p"):
        # Skip if this is an exercise paragraph
        raw_text = p.get_text()
        text = normalize_text(raw_text)
        if re.search(r'Ejercicio\s+\d', text):
            continue

        # Check if inside a callout-body
        parent_callout_body = p.find_parent("div", class_="callout-body-container")
        is_interp_callout = False
        if parent_callout_body:
            # Check if THIS paragraph contains "Interpretación"
            if re.search(r'Interpretaci[oó]n', text, re.IGNORECASE):
                is_interp_callout = True
            else:
                # Or if the parent callout's TITLE contains "Interpretación"
                parent_callout = parent_callout_body.find_parent(
                    "div", class_=lambda c: c and "callout" in c and "callout-body" not in c
                )
                if parent_callout:
                    header = parent_callout.find("div", class_="callout-title-container")
                    if header:
                        header_text = normalize_text(header.get_text())
                        if re.search(r'Interpretaci[oó]n', header_text, re.IGNORECASE):
                            is_interp_callout = True

        if not is_interp_callout:
            # Non-callout paragraphs must be very close to R output
            p_line = p.sourceline or 0
            nearby_r = any(abs(p_line - rl) < 15 for rl in r_lines)
            if not nearby_r:
                continue
        else:
            # Interpretation callout: must be within 40 lines of R output
            p_line = p.sourceline or 0
            nearby_r = any(0 < p_line - rl < 40 for rl in r_lines)
            if not nearby_r:
                continue

        values = extract_from_text(text)
        # Also extract from MathJax spans
        for span in p.select("span.math.inline"):
            mj_text = span.get_text()
            mj_values = extract_from_text(mj_text)
            values.update(mj_values)

        if values:
            text_claims.append({
                "text": text.strip()[:200],
                "values": values,
                "sourceline": p.sourceline or 0,
            })

    return r_blocks, text_claims, soup


def find_nearest_r_block(para_line, r_blocks):
    """Find the R output block closest to and preceding this paragraph.

    Only matches to the single most recent R output block. Merges
    at most the 2 most recent blocks if they are very close together.
    """
    # Find the most recent R block that precedes this paragraph
    preceding = [b for b in r_blocks if b["sourceline"] < para_line]

    if not preceding:
        return OrderedDict(), None

    # Build values: merge all nearby preceding blocks without overwriting.
    # Same-named keys from different blocks get indexed: p, p_2, p_3, ...
    recent = preceding[-1]
    merged = OrderedDict()
    # Always include the most recent block
    merged.update(recent["values"])
    # Also include earlier blocks if close enough
    for prev in reversed(preceding[:-1]):
        if (para_line - prev["sourceline"]) < 80:
            for k, v in prev["values"].items():
                key = k
                i = 1
                while key in merged:
                    i += 1
                    key = f"{k}_{i}"
                merged[key] = v

    return merged, recent


# ── Comparison engine ──────────────────────────────────────────────────────


def compare_chapter(html_path):
    """Main comparison function for a single chapter HTML."""
    r_blocks, text_claims, soup = parse_html(html_path)

    chapter = Path(html_path).stem
    discrepancies = []
    matched = 0
    unmatched = 0

    for claim in text_claims:
        para_values = claim["values"]
        if not para_values:
            continue

        # Find the R output that corresponds to this paragraph
        r_values, r_block = find_nearest_r_block(claim["sourceline"], r_blocks)

        if not r_values:
            unmatched += len(para_values)
            continue

        for name, claimed_val in para_values.items():
            # Collect all values for this stat from R output:
            #   name, name_2, name_3, ...
            candidates = []
            for i in range(1, 20):
                key = name if i == 1 else f"{name}_{i}"
                if key in r_values:
                    candidates.append(r_values[key])
            # Also try fuzzy: any key starting with name_
            if not candidates:
                for k, v in r_values.items():
                    if k.startswith(f"{name}_") and k != name:
                        candidates.append(v)

            if not candidates:
                unmatched += 1
                continue

            # Check if ANY candidate matches the claimed value
            best_actual = candidates[0]
            best_diff = abs(claimed_val - best_actual)

            for actual_val in candidates:
                if values_match(name, claimed_val, actual_val, claim["text"]):
                    matched += 1
                    best_actual = None  # signal: match found
                    break
                diff = abs(claimed_val - actual_val)
                if diff < best_diff:
                    best_diff = diff
                    best_actual = actual_val

            if best_actual is None:
                continue  # matched above

            # No candidate matched — report discrepancy with closest
            if name == "p":
                sev = severity_for_p(claimed_val, best_actual)
            else:
                sev = severity_for_stat(name, claimed_val, best_actual)

            if sev is None:
                matched += 1
                continue

            discrepancies.append({
                "severity": sev,
                "text_snippet": claim["text"][:150],
                "stat": name,
                "claimed": claimed_val,
                "actual": best_actual,
                "r_output_snippet": r_block["text"][:150] if r_block else "",
            })

    return {
        "chapter": chapter,
        "discrepancies": discrepancies,
        "summary": {
            "total_claims_checked": matched + unmatched + len(discrepancies),
            "matched": matched,
            "unmatched": unmatched,
            "discrepancies": len(discrepancies),
            "critical": sum(1 for d in discrepancies if d["severity"] == "critical"),
            "warning": sum(1 for d in discrepancies if d["severity"] == "warning"),
            "info": sum(1 for d in discrepancies if d["severity"] == "info"),
        }
    }


# ── Report formatting ──────────────────────────────────────────────────────


def print_report(result, verbose=False):
    """Print comparison results to terminal."""
    s = result["summary"]

    print(f"\n{'='*70}")
    print(f"  Capítulo: {result['chapter']}")
    print(f"{'='*70}")
    print(f"  Valores comprobados: {s['total_claims_checked']}")
    print(f"  Coincidencias:       {s['matched']} ✓")
    print(f"  Sin emparejar:       {s['unmatched']} ?")
    print(f"  Discrepancias:       {s['discrepancies']}")
    if s['discrepancies'] > 0:
        print(f"    - Críticas:  {s['critical']}")
        print(f"    - Warning:   {s['warning']}")
        print(f"    - Info:      {s['info']}")

    if result["discrepancies"]:
        print(f"\n{'-'*70}")
        print("  DISCREPANCIAS ENCONTRADAS:")
        print(f"{'-'*70}")
        for i, d in enumerate(result["discrepancies"], 1):
            icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[d["severity"]]
            print(f"\n  [{i}] {icon} [{d['severity'].upper()}] {d['stat']}")
            print(f"      Texto dice:  {d['claimed']}")
            print(f"      R produce:   {d['actual']}")
            print(f"      Contexto:    {d['text_snippet'][:120]}")
            if verbose and d["r_output_snippet"]:
                print(f"      Salida R:    {d['r_output_snippet'][:120]}")

    # Score: based on matched vs discrepant only (unmatched are neutral)
    total = s['matched'] + s['discrepancies']
    if total > 0:
        score = round(100 * s['matched'] / total)
        print(f"\n  Score: {score}/100 (sobre {total} valores comparables)")
        if score < 80:
            print("  ❌ Por debajo del umbral de calidad (80)")
        else:
            print("  ✓ Por encima del umbral de calidad (80)")

    print()


def run_all(base_dir="docs/chapters"):
    """Run validation on all chapter HTML files."""
    base = Path(base_dir)
    if not base.exists():
        sys.exit(f"Error: directorio {base_dir} no encontrado")

    html_files = sorted(base.glob("semana*.html"))
    if not html_files:
        sys.exit(f"Error: no se encontraron capítulos en {base_dir}")

    all_results = []
    total_critical = 0

    for html_file in html_files:
        result = compare_chapter(str(html_file))
        all_results.append(result)
        print_report(result)
        total_critical += result["summary"]["critical"]

    # Global summary
    total_checked = sum(r["summary"]["total_claims_checked"] for r in all_results)
    total_matched = sum(r["summary"]["matched"] for r in all_results)
    total_disc = sum(r["summary"]["discrepancies"] for r in all_results)
    total_crit = sum(r["summary"]["critical"] for r in all_results)
    total_warn = sum(r["summary"]["warning"] for r in all_results)
    total_info = sum(r["summary"]["info"] for r in all_results)

    print(f"{'='*70}")
    print(f"  RESUMEN GLOBAL — {len(all_results)} capítulos")
    print(f"{'='*70}")
    print(f"  Total comprobado:  {total_checked}")
    print(f"  Coincidencias:     {total_matched}")
    print(f"  Discrepancias:     {total_disc} (críticas: {total_crit}, "
          f"warnings: {total_warn}, info: {total_info})")

    if total_checked > 0:
        score = round(100 * total_matched / total_checked)
        print(f"  Score global:      {score}/100")

    return all_results


# ── CLI ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Validar consistencia entre valores R y texto interpretativo"
    )
    parser.add_argument(
        "html_file", nargs="?",
        help="Archivo HTML de un capítulo (ej: docs/chapters/semana08.html)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Validar todos los capítulos en docs/chapters/"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Emitir resultado como JSON"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Mostrar snippets de salida R en discrepancias"
    )

    args = parser.parse_args()

    if args.all:
        results = run_all()
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
        # Exit with non-zero if critical errors found
        total_crit = sum(r["summary"]["critical"] for r in results)
        if total_crit > 0:
            sys.exit(1)

    elif args.html_file:
        if not Path(args.html_file).exists():
            sys.exit(f"Error: archivo no encontrado: {args.html_file}")
        result = compare_chapter(args.html_file)

        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            print_report(result, verbose=args.verbose)

        if result["summary"]["critical"] > 0:
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
