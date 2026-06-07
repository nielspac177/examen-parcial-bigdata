# ADR-0001: Usar NetCDF + xarray para cargar y analizar el dataset

## Estado

Aceptado

## Contexto

El dataset del examen (`ARM_sgpmetE32.b1.2021.nc`) viene en formato **NetCDF**, el estándar
de la comunidad atmosférica. Son 521,200 registros de 1 minuto con 31 variables de datos más
metadatos globales y por variable (unidades, rangos válidos, semántica de los bits de QC).
Hay que cargarlo, inspeccionar su estructura y pasarlo a un formato cómodo para el EDA.

Opciones para leerlo desde Python:

- **xarray** (con backend netCDF4): modela el archivo como un `Dataset` con dimensiones,
  coordenadas, variables y atributos. Conserva los metadatos y convierte a `pandas` con
  `.to_dataframe()`.
- **netCDF4** directo: acceso de bajo nivel a variables y atributos, pero hay que armar a mano
  las estructuras tabulares.
- **Exportar a CSV** y trabajar solo con pandas: pierde los metadatos y los tipos, y un CSV de
  medio millón de filas con 31 columnas es pesado e innecesario.

## Decisión

Cargar el archivo con **xarray** (`xr.open_dataset`) y convertir a un `DataFrame` de **pandas**
indexado por tiempo para el EDA tabular.

## Consecuencias

**A favor**

- Se conservan los metadatos (unidades, `valid_max`, descripción de bits QC) que sustentan
  la discusión de calidad y los principios FAIR.
- El índice temporal de pandas habilita remuestreo (`resample`), interpolación temporal y
  groupby por hora/mes con muy poco código.
- Es el flujo natural para datos científicos y el que se alinea con lo visto en clase.

**En contra**

- Hay que mantener dos dependencias (xarray y netCDF4) y cargar todo el archivo en memoria
  (~54 MB como DataFrame), aceptable para un solo año.

**Notas**

- A escala (varias estaciones, varios años) el mismo enfoque migra a Parquet + Spark, ver
  [ADR-0004](0004-arquitectura-lambda-aws.md).
