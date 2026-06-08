# Plan: Test Automatizado de Consistencia R ↔ Interpretación

**Date:** 2026-06-08
**Status:** DRAFT
**Objective:** Script que extrae valores del HTML renderizado y los compara contra las cifras citadas en el texto interpretativo

---

## Context

La auditoría manual del 2026-06-01 encontró **37+ inconsistencias** entre la salida real de R y el texto interpretativo, incluyendo errores críticos (conclusiones invertidas, ICs erróneos, p-valores inventados). El propio informe recomendó crear un test automatizado para prevenir regresiones.

Este script implementa ese test. Se ejecuta sobre los HTML ya renderizados (no requiere re-ejecutar Quarto).

---

## Diseño

### Archivo único: `scripts/validate_values.py`

**Lenguaje:** Python 3 + BeautifulSoup4 (ya disponible en el sistema)

### Pipeline

```
HTML → Parse DOM → Extraer valores R (ground truth)
                 → Extraer valores texto (claimed)
                 → Emparejar por proximidad + nombre
                 → Comparar con tolerancia
                 → Reporte de discrepancias
```

### Fase 1: Extracción de "ground truth" desde salida R

**Selector CSS:** `div.cell-output-stdout pre code`

Cada bloque `<pre><code>` contiene la salida textual de R. Se aplican regex para extraer pares `(estadístico, valor)`:

| Regex | Captura | Ejemplo |
|-------|---------|---------|
| `(χ²\|X-squared\|Chi-squared)\s*[=:]\s*([\d.]+)` | χ² | `χ² = 4.651` |
| `p[-\s]*(value\|valor)?\s*[=<]\s*([\d.]+)` | p-value | `p = 0.031`, `p-value = 0.03` |
| `\b(OR\|Odds\s*Ratio)\s*[=:]\s*([\d.]+)` | OR | `OR=2.821` |
| `\b(RR\|Risk\s*Ratio)\s*[=:]\s*([\d.]+)` | RR | `RR = 2.67` |
| `\b(W)\s*[=:]\s*([\d.]+)` | Shapiro-Wilk W | `W = 0.907` |
| `\b(t|t[-\s]*obs)\s*[=:]\s*([\d.-]+)` | t | `t = -11` |
| `\b(df\|gl)\s*[=:]\s*([\d.]+)` | df | `df = 38`, `gl = 2` |
| `\b(r)\s*[=:]\s*([\d.]+)` | r (effect size) | `r = 0.627` |
| `(IC\|CI)[_\s]*95%?\s*[=:(].*?([\d.]+).*?[,;\s]+.*?([\d.]+)` | IC 95% bounds | `IC 95%: [1.79, 3.98]` |
| `\b(media\|mean)\s*[=:]\s*([\d.]+)` | mean | `media = 29.4` |
| `\b(R²\|R-squared)\s*[=:]\s*([\d.]+)` | R² | `R² = 0.414` |

**Estructura de datos:** `{ "chunk_id": N, "values": { "chi2": 4.651, "p": 0.031, "OR": 2.821, ... } }`

### Fase 2: Extracción de "claimed values" desde texto interpretativo

**Selector CSS:** `p` (párrafos), con prioridad en `div.callout-note p`, `div.callout-tip p`

Se extrae el texto completo de cada párrafo y se aplican los mismos regex. Además, se extraen valores dentro de MathJax: `<span class="math inline">\(p = 0.005\)</span>`.

**Estructura de datos:** `{ "paragraph_idx": N, "text_snippet": "...", "values": { "p": 0.005, ... } }`

### Fase 3: Emparejamiento

Algoritmo voraz (greedy):
1. Recorrer el DOM en orden
2. Cada bloque R-output se asocia con los párrafos interpretativos que le siguen (hasta el siguiente R-output o hasta 3 párrafos de distancia)
3. Para cada valor citado en el texto, buscar el valor correspondiente en el R-output asociado
4. El matching es por nombre de estadístico (χ² → chi2, p → p, OR → OR, etc.)

### Fase 4: Comparación

| Tipo | Tolerancia | Justificación |
|------|-----------|---------------|
| p-value | ±0.001 para p<0.01, ±0.005 para p<0.05, ±0.01 resto | Redondeo típico a 2-3 decimales |
| Test statistic (χ², t, W) | ±0.05 | Redondeo a 2 decimales |
| OR, RR | ±0.05 | Redondeo a 2 decimales |
| IC bounds | ±0.05 | Redondeo a 1-2 decimales |
| R² | ±0.005 | Redondeo a 3 decimales |
| Effect size (r) | ±0.01 | Redondeo a 2 decimales |

### Fase 5: Reporte

Salida JSON por capítulo y resumen en terminal:

```json
{
  "chapter": "semana08",
  "discrepancies": [
    {
      "severity": "critical",
      "paragraph_line": 765,
      "text_snippet": "χ²_B = 2.18, p = 0.335...",
      "claimed": {"chi2": 2.18, "p": 0.335},
      "actual": {"chi2": 10.96, "p": 0.004},
      "note": "p-value diff changes statistical conclusion (0.335→0.004)"
    }
  ],
  "summary": {
    "total_claimed": 45,
    "discrepancies": 3,
    "critical": 1,
    "warning": 2
  }
}
```

Niveles de severidad:
- **critical:** La discrepancia cambia la conclusión estadística (p pasa de no significativo a significativo o viceversa)
- **warning:** Diferencia numérica > tolerancia pero no cambia conclusión
- **info:** Diferencia menor, posible redondeo distinto

---

## Archivos

| Archivo | Acción |
|---------|--------|
| `scripts/validate_values.py` | **CREAR** — script principal |
| `quality_reports/plans/sparkling-hugging-spring.md` | Este plan |

---

## Verificación

1. Ejecutar sobre `semana08.html` (el capítulo con más errores conocidos) → debe detectar los 5 errores críticos documentados en la auditoría
2. Ejecutar sobre `semana03.html` (capítulo limpio) → debe reportar 0 discrepancias
3. Ejecutar sobre todos los capítulos → generar resumen global
4. Verificar que los falsos positivos son < 10% (el texto cita valores no presentes en el R-output más cercano)

---

## Limitaciones reconocidas

- **Valores en imágenes:** No se pueden extraer (requeriría OCR)
- **Emparejamiento imperfecto:** Cuando el texto cita valores de varios chunks distintos en un mismo párrafo
- **Redacción ambigua:** "aproximadamente", "≈", "cerca de" — se tratan como valores exactos con tolerancia ampliada
- **Valores derivados:** Cuando el texto cita un cálculo manual (no sale directo de R) — puede generar falsos positivos
