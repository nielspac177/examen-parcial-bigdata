# ADR-0004: Arquitectura Lambda sobre AWS para el pipeline escalable

## Estado

Aceptado

## Contexto

La Parte 2 del examen pide una arquitectura escalable para datos meteorológicos como los del
programa ARM, que opera cientos de instrumentos desde 1996 y llega a petabytes. El flujo pedido
es Ingestión → Almacenamiento → Procesamiento → Catalogación/Metadatos → Indexado/Consulta →
Visualización/Serving, con Monitoreo y Seguridad transversales.

Hay dos necesidades en tensión: análisis **batch reproducible** sobre todo el histórico
(climatología, reprocesos) y respuesta **casi en tiempo real** (alertas de eventos extremos).

Patrones considerados para combinar batch y streaming:

- **Lambda**: dos rutas de cómputo (batch + velocidad) más una capa de serving que reconcilia
  ambas vistas. Más robusta y reproducible, pero mantiene dos bases de código.
- **Kappa**: una sola ruta de streaming que reprocesa desde el log. Más simple de operar, pero
  el reproceso masivo del histórico es más incómodo para análisis científico.

## Decisión

Adoptar una **arquitectura Lambda sobre AWS**, con procesamiento batch **incremental**:

- **Ingestión**: colector edge en la estación → **Apache Kafka / MSK** (streaming), con Schema
  Registry y cola de descarte (DLQ). Los históricos `.dat` se cargan directo a S3.
- **Almacenamiento**: data lake en **S3** por zonas (raw/clean/analytics), en **NetCDF** y
  **Parquet** particionado por `site/facility/year/month`; NoSQL (**DynamoDB**) para la última
  lectura por estación.
- **Procesamiento**: **Spark sobre EMR**. Capa batch incremental (solo particiones nuevas),
  capa de velocidad (Spark Structured Streaming) y capa de serving que reconcilia ambas.
- **Catalogación**: **AWS Glue Data Catalog** + DOIs + linaje (principios FAIR).
- **Consulta**: **Athena** (SQL serverless) y **OpenSearch Serverless**.
- **Serving/Visualización**: Tableau/Power BI, JupyterHub y API REST sobre agregados.
- **Transversal**: Grafana/Prometheus + CloudWatch (monitoreo); IAM, KMS, TLS, CloudTrail
  (seguridad).

## Consecuencias

**A favor**

- Cada componente escala en horizontal (particiones Kafka, S3, nodos EMR, servicios serverless);
  pasar de 1 a ~30 estaciones solo agrega particiones y nodos.
- El batch incremental evita reprocesar el histórico a diario, lo que acota el costo.
- Separar almacenamiento (S3) de cómputo (EMR) permite apagar clusters cuando no se usan.

**En contra**

- Mantener dos rutas de cómputo (batch y velocidad) duplica lógica respecto a Kappa; se acepta
  a cambio de reproducibilidad sobre el histórico.

**Reemplaza**

- Una versión previa mezclaba Kafka con Kinesis Firehose de forma incoherente (Firehose no
  consume de Kafka) y reprocesaba todo el histórico a diario. Esta decisión unifica la ruta de
  streaming y fija el batch incremental.
