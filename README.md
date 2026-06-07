# Examen Parcial — Big Data

Análisis exploratorio de datos (EDA) y diseño de una arquitectura escalable de Big Data,
sobre el dataset meteorológico **ARM sgpmetE32.b1 (2021)** de la estación Southern Great
Plains (Medford, Oklahoma).

Trabajo del curso de Big Data de la Maestría en Inteligencia Artificial (UNI), dictado por
la Mg. Rosa Virginia Encinas Quille.

## Contenido

- **EDA del dataset** (521,200 registros × 31 variables, NetCDF): estructura y metadatos,
  integridad, valores faltantes, flags de control de calidad (QC), detección de outliers
  (IQR y z-score), limpieza (enmascarado por QC, acotado físico de la humedad, imputación
  temporal) y normalización (Min-Max y Z-score).
- **Arquitectura escalable de Big Data**: flujo Ingestión → Almacenamiento → Procesamiento →
  Catalogación/Metadatos → Indexado/Consulta → Visualización/Serving, con Monitoreo y
  Seguridad como capa transversal y gobernanza FAIR.

El informe final está en `output/Examen_Parcial_BigData.pdf`.

## Estructura del repositorio

```
.
├── README.md
├── requirements.txt
├── src/
│   ├── descargar_dataset.py     # descarga el .nc (no se versiona, ~71 MB)
│   ├── eda_arm_sgpmet.py        # pipeline completo del EDA y figuras
│   └── diagrama_arquitectura.py # diagrama de la arquitectura
├── docs/
│   ├── examen_parcial.html      # fuente del informe
│   └── adr/                     # decisiones de arquitectura (ADR)
├── figures/                     # figuras generadas (PNG)
└── output/                      # PDF final, CSVs y JSON de resultados
```

## Reproducir

Requiere Python 3.12+ (probado en 3.14).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 1) Descargar el dataset (~71 MB, no incluido en el repo)
python src/descargar_dataset.py

# 2) Ejecutar el EDA (genera figuras en figures/ y resultados en output/)
python src/eda_arm_sgpmet.py

# 3) Generar el diagrama de arquitectura
python src/diagrama_arquitectura.py
```

El PDF se arma exportando `docs/examen_parcial.html` a PDF (por ejemplo con Chrome headless:
`--headless --print-to-pdf`).

## Dataset

- Fuente: ARM Data Discovery, datastream `sgpmetE32.b1`
  (https://adc.arm.gov/discovery/#/results/s::sgpmetE32).
- Copia usada en el curso:
  https://github.com/encinasquille/DataLifecyclePy/raw/main/data/raw/ARM_sgpmetE32.b1.2021.nc

## Decisiones de arquitectura

Las decisiones técnicas del trabajo están documentadas como ADRs en
[`docs/adr/`](docs/adr/README.md).
