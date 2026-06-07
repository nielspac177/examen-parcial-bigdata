# ADR-0003: Tratar los outliers como eventos reales y separar el ruido instrumental

## Estado

Aceptado

## Contexto

La detección de outliers por IQR y z-score marcó miles de registros, sobre todo en temperatura
(1,760 por IQR), presión (10,432) y viento (12,769). La pregunta es si eliminarlos.

En datos meteorológicos un outlier estadístico no equivale a un error:

- Los outliers fríos de temperatura coinciden con la **ola de frío histórica de febrero de
  2021** en Oklahoma (mínimo −27.1 °C). Es un evento real y con valor científico.
- Los outliers de viento y presión corresponden a frentes y sistemas de presión reales.
- El verdadero ruido instrumental es otra cosa: la sobresaturación de humedad (>100%, ver
  [ADR-0002](0002-limpieza-qc-clip-rh-interpolacion.md)) y los huecos temporales.

## Decisión

**No eliminar los outliers** detectados por IQR/z-score. Se reportan y se interpretan como
eventos meteorológicos reales. El tratamiento se reserva para el ruido instrumental genuino
(sobresaturación de HR) y los faltantes.

Para los saltos bruscos de temperatura se usa un umbral exploratorio propio (>5 °C/min, 5 casos),
que se reporta como tal y se distingue del criterio del ARM, cuyo bit 4 de QC usa
`valid_delta = 20` °C/min.

## Consecuencias

**A favor**

- Se preserva la señal física, incluido un evento extremo relevante, en vez de "aplanar" la
  serie.
- Se evita el error común de confundir significancia estadística con error de medición.

**En contra**

- Los outliers conservados afectan a escaladores sensibles a extremos. La normalización Min-Max
  queda comprimida por el evento de febrero; se documenta y se sugiere un escalado robusto
  (mediana/IQR) o winsorización para modelos que lo requieran.

**Verificación**

- La validación de eventos extremos se apoya en consistencia temporal (horas contiguas) y
  espacial (estaciones vecinas E13/E15), descrita en el ejemplo práctico de la arquitectura.
