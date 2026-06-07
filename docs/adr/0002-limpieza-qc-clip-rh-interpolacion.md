# ADR-0002: Estrategia de limpieza (flags QC, acotado de HR e imputación temporal)

## Estado

Aceptado

## Contexto

El EDA detectó tres problemas de calidad en las variables físicas:

1. Registros marcados por el control de calidad del ARM (`qc_* ≠ 0`), muy pocos al ser nivel b1.
2. **22,463 registros (4.31%) con humedad relativa > 100%**. No es un valor imposible: el sensor
   capacitivo HMP155 reporta hasta ~104% cerca de la saturación y el ARM fija `valid_max = 104`
   para esta variable.
3. **4,400 minutos sin registro** (huecos temporales), repartidos en marzo, julio y octubre.

Hay que decidir qué hacer con cada uno. Para la humedad, la duda concreta era **descartar
(poner a NaN) o acotar (clip a 100%)**. Una versión previa enmascaraba a NaN, lo que destruía
~15,000 valores (≈3% de una variable válida) y dejaba el dataset "limpio" con menos completitud
de la que se reportaba.

## Decisión

Pipeline de limpieza en tres pasos:

1. **Flags QC → NaN**: todo registro con `qc_* ≠ 0` pasa a `NaN` (regla del ARM: QC=0 significa
   que ninguna prueba falló).
2. **Acotado físico de la humedad**: `rh_mean.clip(upper=100)`. Se **acota, no se descarta**,
   porque la sobresaturación es comportamiento conocido del sensor y no un error.
3. **Imputación temporal**: interpolación lineal por tiempo limitada a tramos de hasta 60
   registros consecutivos (`interpolate(method='time', limit=60)`). Los huecos más largos se
   dejan como NaN para no inventar datos.

## Consecuencias

**A favor**

- No se pierde ningún registro de una variable válida; tras la limpieza las variables
  principales quedan al 100% de completitud.
- El método del código, el del informe (texto y figura) y el del Anexo quedan consistentes.
- Decisión defendible físicamente y alineada con la documentación del instrumento.

**En contra**

- El `clip` a 100% pierde la información de cuánto excedía cada registro (entre 100 y ~104%);
  es aceptable porque para los análisis de este trabajo el techo de saturación es lo relevante.
- La interpolación introduce valores sintéticos en tramos cortos; se acota a ≤60 min para
  limitar el sesgo y se documenta explícitamente.

**Alternativa descartada**

- Enmascarar la HR>100% a NaN: descartaba ~3% de datos válidos y bajaba la completitud sin
  justificación física.
