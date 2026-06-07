# -*- coding: utf-8 -*-
"""Diagrama de arquitectura escalable de Big Data — Examen Parcial.
Flujo: Ingestión -> Almacenamiento -> Procesamiento -> Catalogación/Metadatos
       -> Indexado/Consulta -> Visualización/Serving, con banda transversal de
       Monitoreo & Seguridad y capa de gobernanza FAIR (modelo de la clase).
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({'font.family': 'sans-serif',
                     'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans']})

# Paleta Okabe-Ito suavizada para fondos
COLORS = {
    'ing':  ('#E69F00', '#FDF1DC'),
    'alm':  ('#0072B2', '#DCEBF5'),
    'proc': ('#009E73', '#DCF2EA'),
    'cat':  ('#CC79A7', '#F7E8F0'),
    'idx':  ('#D55E00', '#FBE7DA'),
    'viz':  ('#56B4E9', '#E4F2FB'),
    'mon':  ('#555555', '#EEEEEE'),
    'fair': ('#8B7500', '#FAF5DC'),
}

BLOCKS = [
    ('ing', '1. INGESTIÓN', ['Estación MET → colector edge', 'Apache Kafka / MSK (streaming)',
                             'Schema Registry + DLQ', '.dat históricos → S3 (batch)']),
    ('alm', '2. ALMACENAMIENTO', ['Data Lake: AWS S3', 'Zonas: raw(00)/clean(b1)/analytics',
                                  'Parquet part. site/facility/año/mes', 'NoSQL: DynamoDB / Cassandra']),
    ('proc', '3. PROCESAMIENTO', ['Apache Spark (AWS EMR)', 'Batch incremental + Streaming',
                                  'Limpieza QC, EDA, MLlib', 'Lambda: batch+velocidad+serving']),
    ('cat', '4. CATALOGACIÓN /\nMETADATOS', ['AWS Glue Data Catalog', 'Metadatos ricos + DOI',
                                             'Principios FAIR', 'Linaje de datos']),
    ('idx', '5. INDEXADO /\nCONSULTA', ['Amazon Athena (SQL serverless)', 'OpenSearch Serverless',
                                        'Spark SQL', 'Consultas ad-hoc']),
    ('viz', '6. VISUALIZACIÓN /\nSERVING', ['Tableau / Power BI', 'Jupyter + matplotlib',
                                            'API REST (Data Discovery)', 'Dashboards interactivos']),
]

fig, ax = plt.subplots(figsize=(13.5, 6.2))
ax.set_xlim(0, 13.5); ax.set_ylim(0, 6.2); ax.axis('off')

BW, BH, Y0 = 2.0, 2.6, 2.1
xs = [0.25 + i * 2.22 for i in range(6)]

for (key, title, items), x in zip(BLOCKS, xs):
    edge, face = COLORS[key]
    box = FancyBboxPatch((x, Y0), BW, BH, boxstyle="round,pad=0.06",
                         linewidth=2, edgecolor=edge, facecolor=face)
    ax.add_patch(box)
    ax.text(x + BW/2, Y0 + BH - 0.32, title, ha='center', va='center',
            fontsize=10.5, fontweight='bold', color=edge)
    for j, it in enumerate(items):
        ax.text(x + BW/2, Y0 + BH - 0.85 - j * 0.42, it, ha='center',
                va='center', fontsize=8.2, color='#222222')

# Flechas entre bloques
for i in range(5):
    x_from = xs[i] + BW + 0.06
    x_to = xs[i + 1] - 0.06
    ax.add_patch(FancyArrowPatch((x_from, Y0 + BH/2), (x_to, Y0 + BH/2),
                                 arrowstyle='-|>', mutation_scale=22,
                                 linewidth=2, color='#333333'))

# Banda superior: gobernanza FAIR
edge, face = COLORS['fair']
ax.add_patch(FancyBboxPatch((0.25, 5.15), 13.0, 0.75, boxstyle="round,pad=0.06",
                            linewidth=2, edgecolor=edge, facecolor=face))
ax.text(6.75, 5.66, 'GOBERNANZA DE DATOS — PRINCIPIOS FAIR', ha='center',
        fontsize=10, fontweight='bold', color=edge)
ax.text(6.75, 5.34,
        'Findable (DOI, metadatos ricos)  ·  Accessible (control de acceso)  ·  '
        'Interoperable (NetCDF, estándares)  ·  Reusable (documentación, niveles 00/a1/b1)',
        ha='center', fontsize=8.5, color='#444444')

# Banda inferior: monitoreo y seguridad
edge, face = COLORS['mon']
ax.add_patch(FancyBboxPatch((0.25, 0.65), 13.0, 1.0, boxstyle="round,pad=0.06",
                            linewidth=2, edgecolor=edge, facecolor=face))
ax.text(6.75, 1.38, '7. MONITOREO & SEGURIDAD (transversal)', ha='center',
        fontsize=10, fontweight='bold', color=edge)
ax.text(6.75, 1.02,
        'Grafana + Prometheus (métricas y alertas)  ·  AWS CloudWatch (logs)  ·  IAM (roles y permisos)  ·  '
        'Cifrado en reposo (S3-KMS) y en tránsito (TLS)  ·  Auditoría CloudTrail',
        ha='center', fontsize=8.5, color='#444444')

# Conectores verticales suaves entre bandas y pipeline
for x in [xs[0] + BW/2, xs[2] + BW/2, xs[4] + BW/2]:
    ax.plot([x, x], [1.68, Y0 - 0.04], color='#999999', lw=1, ls=':')
    ax.plot([x, x], [Y0 + BH + 0.07, 5.12], color='#999999', lw=1, ls=':')

ax.text(6.75, 6.0, 'Arquitectura escalable de Big Data para análisis de datos meteorológicos (caso ARM — sgpmetE32.b1)',
        ha='center', fontsize=12.5, fontweight='bold')

fig.tight_layout()
fig.savefig('figures/fig_arquitectura.png', dpi=220, bbox_inches='tight')
print('OK figures/fig_arquitectura.png')
