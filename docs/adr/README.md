# Architecture Decision Records (ADR)

Registro de las decisiones técnicas del examen parcial de Big Data. Cada ADR documenta el
contexto, las opciones consideradas, la decisión tomada y sus consecuencias.

## Índice

| ADR | Título | Estado | Fecha |
| --- | --- | --- | --- |
| [0001](0001-formato-netcdf-y-xarray.md) | Usar NetCDF + xarray para cargar y analizar el dataset | Aceptado | 2026-06-07 |
| [0002](0002-limpieza-qc-clip-rh-interpolacion.md) | Estrategia de limpieza: flags QC, acotado de HR e imputación temporal | Aceptado | 2026-06-07 |
| [0003](0003-outliers-eventos-reales-vs-ruido.md) | Tratar los outliers como eventos reales y separar el ruido instrumental | Aceptado | 2026-06-07 |
| [0004](0004-arquitectura-lambda-aws.md) | Arquitectura Lambda sobre AWS para el pipeline escalable | Aceptado | 2026-06-07 |

## Estados

- **Propuesto**: en discusión.
- **Aceptado**: decisión tomada y aplicada.
- **Deprecado / Reemplazado**: ya no vigente.
