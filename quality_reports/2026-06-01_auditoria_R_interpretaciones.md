# Auditoría de inconsistencias entre código R e interpretación textual

**Fecha:** 2026-06-01
**Alcance:** Capítulos modificados (semana 01-06, 08, 10, 11) del libro `MatematicaEstadisticaMedicinaR`
**Criterio:** Detectar discrepancias entre la salida de R y el texto interpretativo en español (numéricas, de dirección/sentido, terminológicas o de etiqueta).

## Estado de correcciones (2026-06-01)

Todos los hallazgos críticos y la mayoría de los menores se aplicaron directamente sobre los `.qmd`. Pendiente: **re-renderizar Quarto** (`quarto render`) para actualizar `docs/` y verificar que los HTML reflejan las nuevas interpretaciones.

| Capítulo | Críticos | Aplicado | Notas |
|----------|----------|----------|-------|
| semana01 | 1 | ✅ 5/5 | H3 (datos Ej 1.12) corregido vía aclaración en intro (no se regeneraron los datos del chunk). |
| semana02 | 2 | ✅ 4/4 | Condicionales P(A\|B) intercambiadas en comentarios, print() y bloque de interpretación clínica. |
| semana03 | 0 | — | Sin hallazgos. |
| semana04 | 1 | ✅ 2/3 | `dnorm(0)` separado como densidad. H3 (semilla) no se tocó para no cascadear otras cifras. |
| semana05 | 2 | ✅ 5/5 | Recalculados CPF y p-valor χ²; numeración 5.1/5.2; `label=` eliminado de `curve()`. |
| semana06 | 1 | ✅ 6/6 | IC99% recalculado; "MoM" diferenciado de "EMV"; ejemplos renumerados 6.5.1-6.5.3; labels `lst-semana07-*` → `lst-semana06-*`. |
| semana08 | 5 | ✅ 7/7 | Bartlett invertido; IC bootstrap; p-valor KW; p-valor + PS de WMW; r=0.627 (no 0.89); labels `lst-semana09-*` → `lst-semana08-*`; ejercicios 9.x → 8.x. |
| **semana09** | **2** | ✅ 4/4 | **R² PAS~Edad real 0.597 (no 0.351), b₁=0.83 (no 0.80), t=13.2 (no 8.0)**. **R² Col~IMC real 0.357 (no 0.391), b₁=4.81 (no 5.0)**. Cross-ref "sec 10.12"→"9.12"; ejemplos "PAS vs Edad" marcados como hipotéticos; labels `lst-s10-*`→`lst-s09-*`. |
| semana10 | 1 | ✅ 3/3 | L212 reescrita con cifras reales del modelo; L345 explica diferencia poblacional vs muestral; redondeo 0.699/0.700 aclarado. |
| semana11 | 2 | ✅ 6/6 | "cúbito" → "cuello femoral" (dos ocurrencias); IC del OR (2.30–5.25); RR (3.98); referencia "sección 12.5.5" → `@sec-semana11-mcnemar`; p-valor McNemar; dirección de la confusión. |
| **apendiceB** | **1** | ✅ 2/2 | **`icl(x=12, n=1000)` → `icl(x=12)`** porque `icl()` interpreta `n` como tamaño muestral, no como persona-tiempo (sumax=n·x=12000); IC real era (11.79, 12.22) en vez del 6.2-21.0 indicado. `tablarxc()` ahora reordena el factor `grupo_edad` cronológicamente para que las filas coincidan con `fcat`. |

**Hallazgos no aplicados (por bajo impacto o cascada en otros chunks):**
- semana04 H3 — Semilla de aleatorización (`A-alta:76` por azar): solo se matizó el texto en el reporte, no en el .qmd; cambiar la semilla regeneraría todos los conteos.
- Renombrado global de labels `lst-s12-*` en semana11 (vestigio de cuando era semana12): no realizado para evitar romper cross-references; conviene hacerlo en una pasada separada con verificación de referencias.

---

## Resumen ejecutivo

| Capítulo | Hallazgos | Críticos | Comentario |
|----------|-----------|----------|------------|
| semana01 | 5 | 1 | Etiqueta "n impar" cuando n=10; referencia cruzada errónea; datos del ej. 1.12 no coinciden con el Ejemplo 1.6; confusión Pearson/Fisher en curtosis |
| semana02 | 4 | 2 | Condicionales P(A\|B) invertidas en el ejemplo de VIH (código + interpretación); ejercicios con cálculos imprecisos |
| semana03 | 0 | 0 | Limpio (sólo nota menor pregunta/respuesta en Ej 3.4) |
| semana04 | 1 + 2 menores | 1 | `dnorm(0)` etiquetado como "P(X=0)" cuando es densidad |
| semana05 | 5 | 2 | Cálculo CPF erróneo; p-valor χ² mal calculado; numeración inconsistente de ejemplos |
| semana06 | 6 | 1 | IC99% mal calculado; etiquetas `lst-semana07-*` en capítulo 6; "EMV del MoM" confunde métodos |
| semana08 | 7 | 5 | **El más grave**: Bartlett invertido (rechazar vs no rechazar), IC bootstrap completamente erróneo (27.2-29.1 vs real 22.7-24.4), p-valor de Kruskal-Wallis x100, etiquetas `semana09-*` |
| semana10 | 3 | 1 | Ejemplo ilustrativo (R²=0.504) contradice salida real (R²=0.414) del mismo modelo |
| semana11 | 6 | 2 | `osteo_cue` etiquetado como "cúbito" cuando es "cuello femoral"; IC de OR no coincide con salida R |
| **Total** | **37+** | **15** | |

---

## semana01.qmd (5 hallazgos)

### H1 — Etiqueta: "n impar" cuando n=10 (par)
- **Líneas:** 676-679
- **R produce:** `Mediana de PAS: 124.5 mmHg` (n=10, caso par)
- **Texto dice:** "**Conjunto 1** (n impar): 115, 118, 120, 122, 124, 125, 128, 129, 130, 135" — luego "Con $n = 10$ (par)"
- **Fix:** Cambiar "n impar" por "n par" o añadir un segundo conjunto con n impar.

### H2 — Referencia cruzada errónea: "Ejemplo 1.5.1" no existe
- **Líneas:** 1059 y 1096
- **Texto dice:** "Considera el histograma de IMC del **Ejemplo 1.5.1**"
- **Realidad:** El ejemplo del IMC es el **Ejemplo 1.7** (línea 440)
- **Fix:** Reemplazar "Ejemplo 1.5.1" por "Ejemplo 1.7" en ambas apariciones.

### H3 — Numérico: Los datos del Ejemplo 1.12 NO son los del Ejemplo 1.6
- **Líneas:** 834-844 (texto) vs 847-869 (chunk)
- **Texto dice:** "Con los datos de supervivencia (Ejemplo 1.6), podemos aproximar los cuartiles..."
- **R produce:** Q1=500.37, Q2=828.9, Q3≈... con datos simulados (25 valores en 1000-2000 y 5 fijos en 3200-3950); no se corresponde con la tabla del Ej 1.6 (30 valores en 1000-4000).
- **Fix:** Regenerar los datos respetando la tabla original o aclarar que son "datos inspirados en" el Ejemplo 1.6.

### H4 — Terminología: Curtosis de Pearson etiquetada como "de Fisher"
- **Línea:** 778
- **Texto dice:** "...el coeficiente de curtosis de **Fisher**: $g_2 = \frac{\frac{1}{n}\sum (x_i-\bar x)^4}{s^4}$"
- **Realidad:** Esa fórmula es la curtosis de **Pearson** (centrada en 3 para la normal). La de Fisher es justamente la curtosis en exceso ($g_2 - 3$).
- **Fix:** "...curtosis de **Pearson** $g_2 = \dots$; la curtosis en exceso (Fisher) es $g_2 - 3$".

### H5 — Notación incoherente: Media para datos agrupados
- **Líneas:** 580-589 (definición) vs 597-606 (Ejemplo 1.9)
- **Problema:** La definición usa $\bar x = \frac{1}{n}\sum x_j n_j$ (frecuencias absolutas) pero el Ejemplo 1.9 usa $\bar x = \sum x_j f_j$ (relativas) sin explicitar el cambio.
- **Fix:** Mostrar ambas formas equivalentes en la definición.

---

## semana02.qmd (4 hallazgos)

### H1 — **CRÍTICO**: Comentarios y `print()` con probabilidades condicionales invertidas
- **Líneas:** 547-552
- **R produce:** `prop.table(tabla_hiv, 1)` (Test en filas, Infectado en columnas) → P(Infección|Test) = PPV. `prop.table(tabla_hiv, 2)` → P(Test|Infección) = sensibilidad.
- **Texto dice:** Línea 547 etiqueta filas como `P(Resultado | Infección)`; línea 551 etiqueta columnas como `P(Infección | Test)`.
- **Fix:** Intercambiar etiquetas:
  - L547: `# Porcentajes por FILA (P(Infección | Test) — Valor Predictivo)`
  - L551: `# Porcentajes por COLUMNA (Sensibilidad/Especificidad: P(Test | Infección))`

### H2 — **CRÍTICO**: Interpretación clínica con condicionales invertidas
- **Líneas:** 555-557
- **Texto dice:** "Por filas: (Test | Infección)... Por columnas: (Infección | Test)..."
- **Realidad:** Es al revés. Por filas se obtiene PPV/VPN; por columnas, sensibilidad/especificidad.
- **Fix:** Intercambiar los dos puntos del bloque "Interpretación Clínica".

### H3 — Estadísticos imprecisos en Ej 2.1
- **Líneas:** 956-957
- **R produce:** Para los 12 valores dados: media = **276.25** ms; sd ≈ **24.74** ms; IQR (type 7) ≈ **41.25**.
- **Texto dice:** "Media ≈ 278.3 ms; sd ≈ 26.9 ms; IQR ≈ 35 ms (Q3−Q1=290−255)".
- **Fix:** Recalcular y sustituir por los valores correctos.

### H4 — Ej 2.6: r=1.2 es imposible, el "ajuste" a 0.12 es arbitrario
- **Líneas:** 1005-1010
- **Problema:** Con Cov=180, sx=15, sy=10 se viola Cauchy-Schwarz ($|s_{xy}| \le s_x s_y$). La "corrección" a r=0.12 no tiene justificación matemática.
- **Fix:** Reescribir explicando la inconsistencia o cambiar la covarianza del enunciado (p.ej. 120) para obtener r=0.8.

---

## semana03.qmd

**Sin hallazgos significativos.** Todos los valores numéricos coinciden con la salida real de R.

*Nota menor (fuera de alcance):* en la línea 821 (Ejercicio 3.4b) la pregunta dice "tiene 30 años" pero la respuesta condiciona en "menos de 30 años".

---

## semana04.qmd (1 hallazgo crítico + 2 menores)

### H1 — **CRÍTICO**: `dnorm(0)` etiquetado como "P(X=0)"
- **Líneas:** 100-107
- **R produce:** `"P(X = 0) = 0.398942280401433"` (es la **densidad** $\varphi(0)$, no una probabilidad)
- **Texto dice:** Comentario `# P(X = 0) es cero` y, justo arriba, párrafo teórico que afirma $P(X=x)=0$ para continuas.
- **Fix:**
```r
# f(0) = densidad en 0; la probabilidad P(X = 0) es 0
print(paste("f(0) =", dnorm(0)))
print("P(X = 0) = 0 (por definición de variable continua)")
```

### H2 — Comentario redundante sin aclaración
- **Líneas:** 104-106
- **Problema:** `pnorm(0)` calculado dos veces para "P(X≤0)" y "P(X<0)" sin advertir que en continuas P(X<a)=P(X≤a).
- **Fix:** Añadir comentario explicativo.

### H3 — Aleatorización "aproximadamente 100" no respaldada por la semilla
- **Líneas:** 303-311
- **R produce:** A-baja:100, A-media:112, A-alta:**76**, B-baja:102, B-media:108, B-alta:102 (24% por debajo en A-alta).
- **Fix:** Cambiar la semilla o matizar el texto: "los conteos fluctúan entre 76 y 112".

---

## semana05.qmd (5 hallazgos)

### H1 — **CRÍTICO**: Cálculo CPF erróneo en Ej de muestreo finito
- **Línea:** 570
- **R produce (manualmente):** Var con CPF = (45²/320)×((8000−320)/(8000−1)) ≈ **6.076**; diferencia ≈ **4%**
- **Texto dice:** "Var ≈ 6.19 (diferencia 2%)"
- **Fix:** "Sin CPF: 6.33; Con CPF: ≈ 6.08; diferencia ≈ 4%".

### H2 — **CRÍTICO**: p-valor χ² mal calculado
- **Línea:** 593
- **R produce:** `1 - pchisq(34.56, 24)` ≈ **0.0755**
- **Texto dice:** "$P(\chi^2_{24} \geq 34.56) \approx 0.055$ (cola superior 5%)"
- **Fix:** "≈ 0.075 (cola superior ~7.5%); el valor crítico al 5% para χ²₂₄ es 36.42".

### H3 — Numeración inconsistente del Ejemplo 5.1/5.2
- **Líneas:** 359, 362
- **Problema:** Encabezado "Ejemplo 5.1" pero título del callout "Ejemplo 5.2".
- **Fix:** Unificar (probablemente ambos a 5.1).

### H4 — Falta numeración del segundo ejemplo del bloque
- **Línea:** 422
- **Problema:** "Ejemplo: Distribuciones Muestrales de la Media" sin número.
- **Fix:** Numerar como "Ejemplo 5.2".

### H5 — Argumento `label` inválido en `curve()`
- **Línea:** 442
- **Problema:** `curve(..., label = "...")` es ignorado silenciosamente.
- **Fix:** Eliminar o reemplazar por una anotación legítima.

---

## semana06.qmd (6 hallazgos)

### H1 — **CRÍTICO**: IC99% mal calculado
- **Línea:** 835
- **R produce (manualmente):** Con `qt(0.995, 35) ≈ 2.7238` y SE=2: IC = 50 ± 5.45 = **[44.55, 55.45]**
- **Texto dice:** "≈ [44.35, 55.65] (usa t₀.₀₀₅,₃₅ ≈ 2.72)"
- **Fix:** "[44.55, 55.45] (usa t₀.₉₉₅,₃₅ ≈ 2.72)" — además corregir notación del cuantil.

### H2 — Terminología: "EMV del MoM"
- **Línea:** 337
- **Texto dice:** "el EMV del MoM es también $S'^2$"
- **Problema:** MoM no es un EMV. Son dos métodos distintos que aquí coinciden.
- **Fix:** "...el estimador por el **método de momentos** es también $S'^2$".

### H3 — Numeración de ejemplos: 6.5.1, 6.5.3, 6.5.4 (falta 6.5.2)
- **Líneas:** 168, 224, 231
- **Fix:** Renumerar a 6.5.1, 6.5.2, 6.5.3.

### H4 — Labels `lst-semana07-*` en capítulo 6
- **Líneas:** 189, 367, 483, 537, 597, 655, 729, 770
- **Fix:** Renombrar a `lst-semana06-*`.

### H5 — Atribución incorrecta del sesgo MoM
- **Línea:** 219
- **Problema:** Texto atribuye la diferencia σ²=144 vs σ̂²=119 al sesgo de $S'^2$, cuando el sesgo teórico es solo −1.44 y la mayor parte (~25) viene de la variabilidad muestral.
- **Fix:** Reformular destacando variabilidad muestral como causa principal.

### H6 — "Los cuatro IC coinciden" no es cierto en el ejemplo
- **Línea:** 744
- **R produce:** Clopper-Pearson (0.339, 0.542); Wilson (0.335, 0.542); Wald (0.331, 0.542); Agresti-Coull (0.341, 0.537).
- **Fix:** Cambiar "coinciden" por "convergen" (las diferencias disminuyen con n).

---

## semana08.qmd (7 hallazgos) — **Capítulo con más problemas**

### H1 — **CRÍTICO**: Bartlett con conclusión INVERTIDA
- **Línea:** 765
- **R produce:** `Bartlett's K-squared ≈ 11, df = 2, p-value = 0.004` → **se rechaza homocedasticidad**
- **Texto dice:** "$\chi^2_B = 2.18$, $p = 0.335 > 0.05$: **no se rechaza** igualdad de varianzas. Procede usar t-test o ANOVA clásico."
- **Fix:** "$\chi^2_B \approx 10.96$, $p = 0.004 < 0.05$: **se rechaza** la igualdad de varianzas. No se cumple homocedasticidad; usar Welch o test de Levene."

### H2 — **CRÍTICO**: IC bootstrap completamente erróneo + interpretación clínica errónea
- **Línea:** 873
- **R produce:** IC bootstrap percentil = **[22.7, 24.4]** kg/m²; BCa = [22.8, 24.5]; media muestral = 23.5 kg/m²
- **Texto dice:** "IC 95% ≈ [27.2, 29.1] kg/m²... situado en el umbral entre sobrepeso (25–29.9) y obesidad (≥ 30)"
- **Fix:** "IC 95% ≈ [22.7, 24.4] kg/m²... dentro del rango **normopeso** (18.5–24.9), próximo al umbral del sobrepeso."

### H3 — **CRÍTICO**: p-valor de Kruskal-Wallis 100× más grande de lo real
- **Línea:** 1041
- **R produce:** `p-value = 0.0002`
- **Texto dice:** "$p = 0.017$"
- **Fix:** "$p \approx 0.0002$" (la conclusión de rechazar sigue siendo correcta).

### H4 — **CRÍTICO**: p-valor Wilcoxon-Mann-Whitney y PS mal reportados
- **Línea:** 974
- **R produce:** p = **0.751**; PS = 0.519 (M1 < M2) → P(M1 > M2) = 0.481 = **48.1%**
- **Texto dice:** "$p = 0.523$... la probabilidad ... es del 46.1%"
- **Fix:** "$p = 0.751$... la probabilidad ... es del 48.1% (1 − PS)".

### H5 — **CRÍTICO**: Tamaño del efecto de Wilcoxon pareado inventado
- **Línea:** 1010
- **R produce:** $r = 0.627$
- **Texto dice:** "El tamaño del efecto es muy fuerte ($r = 0.89$)"
- **Fix:** "El tamaño del efecto es grande ($r = 0.627$, criterio $r > 0.5$)".

### H6 — Labels `lst-semana09-*` en capítulo 8
- **Líneas:** 116, 400, 482, 525, 548, 567, 589, 709, 752, 825, 884, 960, 996, 1031
- **Fix:** Global `replace_all` de `lst-semana09-` por `lst-semana08-`.

### H7 — Ejercicios numerados "9.1"-"9.10" en capítulo 8
- **Líneas:** 1046-1088
- **Fix:** Renumerar a 8.1-8.10 en ejercicios y respuestas.

---

## semana10.qmd (3 hallazgos)

### H1 — Ejemplo teórico contradice salida real para el MISMO modelo
- **Líneas:** 345 vs 733
- **R produce:** IECA = 10.67, ARA-II = 11.07 (ARA-II > IECA por ruido muestral con set.seed(42))
- **Texto dice (L345):** "$\hat{\beta}_1 = 11.8$ ([IECA]), $\hat{\beta}_2 = 10.3$ ([ARA-II])"
- **Fix:** Aclarar que L345 son valores poblacionales y que la muestra puede invertir el orden por azar, o cambiar la semilla.

### H2 — Ejemplo ilustrativo con R² distinto al modelo simulado idéntico
- **Línea:** 212
- **R produce:** PAS~Edad → R²=0.414, R²adj=0.409; PAS~Edad+IMC → R²=0.705, R²adj=0.700
- **Texto dice:** R²=0.504/0.499 y R²=0.561/0.553
- **Fix:** Sustituir por valores reales o etiquetar inequívocamente como ejemplo ficticio.

### H3 — Inconsistencia interna 0.699 vs 0.700 (misma R²adj)
- **Líneas:** 537 vs salida cod03 (HTML 1279)
- **Problema:** `round(..., 3)` produce 0.699 en cod01 y `round(..., 4)` produce 0.700 en cod03 — para el mismo modelo.
- **Fix:** Unificar el redondeo (3 decimales en ambos chunks).

---

## semana11.qmd (6 hallazgos)

### H1 — **CRÍTICO**: `osteo_cue` etiquetado como "cúbito" cuando es "cuello femoral"
- **Líneas:** 80, 108
- **Realidad:** Confirmado en apendiceB.qmd y en la sección 11.9.3 del propio capítulo: `osteo_cue` = osteoporosis del **cuello femoral** (`osteo_cub` sería cúbito, variable distinta).
- **Fix:** Reemplazar "osteoporosis de cúbito" por "osteoporosis del cuello femoral" en líneas 80 y 108.

### H2 — **CRÍTICO**: IC del OR de cirrosis no coincide con salida R
- **Línea:** 575
- **R produce:** `OR=3.500; IC95%=(2.300, 5.253)`
- **Texto dice:** "$OR = 3.50$ ($IC_{95\%}$: 2.28–5.37)"
- **Fix:** "$OR = 3.50$ ($IC_{95\%}$: 2.30–5.25)".

### H3 — Límite superior del IC del RR (cohorte)
- **Línea:** 508
- **R produce:** `IC 95%: [1.79, 3.98]`
- **Texto dice:** "$IC_{95\%}$: 1.79–3.97"
- **Fix:** "1.79–3.98".

### H4 — Referencia cruzada a "sección 12.5.5" inexistente
- **Línea:** 667
- **Problema:** Vestigio de cuando el capítulo era "semana12". Los labels `lst-s12-*` también.
- **Fix:** "ver sección 11.5..." y renombrar labels a `lst-s11-*`.

### H5 — p-valor McNemar inconsistente entre dos salidas R
- **Líneas:** 404, 443
- **R produce:** `mcnemar.test(correct=FALSE)` → p = 0.0009; `testmcnemar()` → p = 0.0012
- **Texto dice:** "$p < 0.001$" (estrictamente válido para 0.0009, no para 0.0012)
- **Fix:** "$p \approx 0.001$" o citar el valor exacto.

### H6 — Direccionalidad ambigua de la confusión
- **Línea:** 821
- **R produce:** OR crudo = 5.67 < OR_MH = 6.83 → la confusión **subestima**.
- **Texto dice:** "El OR crudo subestima (o sobreestima) el efecto real..."
- **Fix:** Eliminar el hedge para el caso concreto: "subestima el efecto real (en 1.2 puntos en este caso)".

---

## Prioridades para corrección

### Tier 1 — Errores graves de interpretación estadística (corregir primero)
1. **semana08 H1**: Bartlett — conclusión invertida (rechazar vs no rechazar)
2. **semana08 H2**: Bootstrap IC del IMC — números equivocados y diagnóstico clínico erróneo (sobrepeso/obesidad vs normopeso)
3. **semana08 H3**: p-valor de Kruskal-Wallis (0.017 vs 0.0002)
4. **semana08 H5**: Tamaño del efecto r=0.89 inventado (real 0.627)
5. **semana02 H1, H2**: Probabilidades condicionales invertidas en VIH (código + interpretación)
6. **semana04 H1**: `dnorm(0)` etiquetado como P(X=0)
7. **semana05 H1, H2**: Cálculos numéricos de CPF y p-valor de χ² incorrectos
8. **semana06 H1**: IC99% mal calculado

### Tier 2 — Inconsistencias numéricas o de etiqueta
- semana01 H1, H2, H3
- semana02 H3, H4
- semana08 H4
- semana10 H1, H2, H3
- semana11 H1, H2, H3, H5, H6

### Tier 3 — Limpieza terminológica y de labels
- semana01 H4, H5 (Pearson/Fisher, notación)
- semana05 H3, H4, H5 (numeración, argumento inválido)
- semana06 H2, H3, H4, H5, H6
- semana08 H6, H7 (labels `semana09-*`)
- semana11 H4 (referencia a sec 12.5.5)

---

## Próximos pasos sugeridos

1. Revisar este reporte y validar/descartar hallazgos
2. Aplicar las correcciones por capítulo
3. Re-renderizar Quarto (`quarto render`) y verificar que los HTML actualizados son consistentes
4. Considerar añadir un test automatizado que extraiga los valores del HTML y compare contra las cifras citadas en el texto (para evitar regresiones futuras)
