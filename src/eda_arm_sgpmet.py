# -*- coding: utf-8 -*-
"""
Examen Parcial - Big Data (Mg. Rosa Virginia Encinas Quille)
EDA del dataset ARM sgpmetE32.b1 (2021) - Estación meteorológica
Southern Great Plains (SGP), Medford, Oklahoma - facility E32

Aplica el ciclo de vida de los datos visto en clase:
  EDA -> deteccion de problemas (faltantes, outliers, ruido)
  -> limpieza (flags QC, imputacion) -> transformacion (normalizacion)
"""
import json
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

# ------------------------------------------------------------------
# Estilo de publicacion (paleta Okabe-Ito, colorblind-safe)
# ------------------------------------------------------------------
OKABE_ITO = ['#0072B2', '#D55E00', '#009E73', '#E69F00',
             '#56B4E9', '#CC79A7', '#F0E442', '#000000']
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi': 110,
    'savefig.dpi': 200,
    'axes.prop_cycle': plt.cycler(color=OKABE_ITO),
})
sns.set_palette(OKABE_ITO)

FIG = "figures/"
results = {}  # resumen numerico para el informe

# ------------------------------------------------------------------
# 1. CARGA Y ESTRUCTURA
# ------------------------------------------------------------------
ds = xr.open_dataset("data/ARM_sgpmetE32.b1.2021.nc")

n_records = ds.sizes['time']
n_vars = len(ds.data_vars)
results['n_records'] = int(n_records)
results['n_vars'] = int(n_vars)
results['time_start'] = str(ds.time.values[0])[:16]
results['time_end'] = str(ds.time.values[-1])[:16]
results['lat'] = float(ds.lat[0]); results['lon'] = float(ds.lon[0]); results['alt'] = float(ds.alt[0])

# Completitud temporal: datos cada 1 min -> 365*1440 = 525,600 esperados
expected = 365 * 1440
results['expected_records'] = expected
results['missing_minutes'] = expected - int(n_records)
results['temporal_completeness_pct'] = round(100 * n_records / expected, 2)

# Variables fisicas de interes (medias) y sus flags QC
PHYS = {
    'temp_mean': ('Temperatura', '°C'),
    'rh_mean': ('Humedad relativa', '%'),
    'atmos_pressure': ('Presión atmosférica', 'kPa'),
    'vapor_pressure_mean': ('Presión de vapor', 'kPa'),
    'wspd_arith_mean': ('Velocidad del viento', 'm/s'),
    'wdir_vec_mean': ('Dirección del viento', '°'),
    'tbrg_precip_total_corr': ('Precipitación (corr.)', 'mm'),
    'logger_volt': ('Voltaje del datalogger', 'V'),
}

df = ds[[*PHYS.keys(), *(f'qc_{v}' for v in PHYS if f'qc_{v}' in ds)]].to_dataframe()
df.index = pd.to_datetime(df.index)

# ------------------------------------------------------------------
# 2. VALORES FALTANTES Y FLAGS DE CALIDAD (QC)
# ------------------------------------------------------------------
missing = {}
for v in PHYS:
    n_nan = int(df[v].isna().sum())
    qc_col = f'qc_{v}'
    n_qc_bad = int((df[qc_col] != 0).sum()) if qc_col in df else 0
    missing[v] = {'nan': n_nan, 'qc_flagged': n_qc_bad,
                  'pct_flagged': round(100 * n_qc_bad / n_records, 3)}
results['missing'] = missing

# ------------------------------------------------------------------
# 3. ESTADISTICA DESCRIPTIVA (datos crudos)
# ------------------------------------------------------------------
desc = df[list(PHYS)].describe(percentiles=[.05, .25, .5, .75, .95]).T
desc['skew'] = df[list(PHYS)].skew()
desc = desc.round(2)
desc.to_csv("output/descriptivos_crudos.csv")
results['describe_raw'] = desc.to_dict(orient='index')

# ------------------------------------------------------------------
# 4. DETECCION DE OUTLIERS (IQR y z-score) sobre datos crudos
# ------------------------------------------------------------------
outliers = {}
for v in ['temp_mean', 'rh_mean', 'atmos_pressure', 'wspd_arith_mean']:
    s = df[v].dropna()
    q1, q3 = s.quantile([.25, .75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_iqr = int(((s < lo) | (s > hi)).sum())
    z = np.abs((s - s.mean()) / s.std())
    n_z = int((z > 3).sum())
    outliers[v] = {'iqr_low': round(float(lo), 2), 'iqr_high': round(float(hi), 2),
                   'n_outliers_iqr': n_iqr, 'pct_iqr': round(100 * n_iqr / len(s), 3),
                   'n_outliers_z3': n_z, 'pct_z3': round(100 * n_z / len(s), 3)}
results['outliers'] = outliers

# Sobresaturacion de HR: el sensor capacitivo HMP155 reporta hasta ~104 % cerca de
# la saturacion (el propio ARM fija valid_max=104 para rh_mean). No es un valor
# imposible, es comportamiento conocido del sensor que conviene acotar a 100 % para
# analisis.
results['rh_over_100'] = int((df['rh_mean'] > 100).sum())
# Umbral exploratorio propio (no es el criterio QC del ARM, cuyo valid_delta=20 degC/min)
dtemp = df['temp_mean'].diff().abs()
results['temp_jumps_gt5C_per_min'] = int((dtemp > 5).sum())

# Chequeos estandar de integridad (senior-data-scientist): duplicados y orden temporal
results['dup_timestamps'] = int(df.index.duplicated().sum())
results['time_monotonic_increasing'] = bool(df.index.is_monotonic_increasing)

# ------------------------------------------------------------------
# 5. LIMPIEZA: flags QC -> NaN; acotado fisico de HR a 100 %; imputacion temporal
# ------------------------------------------------------------------
clean = df[list(PHYS)].copy()
for v in PHYS:
    qc_col = f'qc_{v}'
    if qc_col in df:
        clean.loc[df[qc_col] != 0, v] = np.nan
# Acotado fisico: la HR se recorta al techo de saturacion (100 %), conservando el dato
# en lugar de descartarlo (decision de no perder ~3 % de una variable valida).
clean['rh_mean'] = clean['rh_mean'].clip(upper=100.0)

n_masked = {v: int(clean[v].isna().sum()) for v in PHYS}
results['masked_after_qc'] = n_masked

# Imputacion: interpolacion temporal lineal (gaps cortos <= 60 registros de 1 min)
clean_imp = clean.interpolate(method='time', limit=60)
results['remaining_nan_after_imputation'] = {v: int(clean_imp[v].isna().sum()) for v in PHYS}
# Completitud por variable tras la limpieza
results['completeness_after_clean_pct'] = {
    v: round(100 * clean_imp[v].notna().sum() / n_records, 2) for v in PHYS}

# ------------------------------------------------------------------
# 6. TRANSFORMACION: normalizacion Min-Max y estandarizacion Z-score
# ------------------------------------------------------------------
norm_vars = ['temp_mean', 'rh_mean', 'atmos_pressure', 'wspd_arith_mean']
minmax = (clean_imp[norm_vars] - clean_imp[norm_vars].min()) / \
         (clean_imp[norm_vars].max() - clean_imp[norm_vars].min())
zscore = (clean_imp[norm_vars] - clean_imp[norm_vars].mean()) / clean_imp[norm_vars].std()
results['normalization_check'] = {
    'minmax_min': minmax.min().round(3).to_dict(),
    'minmax_max': minmax.max().round(3).to_dict(),
    'zscore_mean': zscore.mean().round(3).to_dict(),
    'zscore_std': zscore.std().round(3).to_dict(),
}

# Datos limpios descriptivos
desc_clean = clean_imp[list(PHYS)].describe(percentiles=[.05, .5, .95]).T.round(2)
desc_clean.to_csv("output/descriptivos_limpios.csv")

# ==================================================================
# FIGURAS
# ==================================================================
# --- Fig 1: Serie temporal anual de temperatura (cruda, remuestreo horario)
fig, ax = plt.subplots(figsize=(9, 3))
hourly = df['temp_mean'].resample('1h').mean()
ax.plot(hourly.index, hourly.values, lw=0.4, color=OKABE_ITO[0], label='Media horaria')
daily = df['temp_mean'].resample('1D').mean()
ax.plot(daily.index, daily.values, lw=1.2, color=OKABE_ITO[1], label='Media diaria')
ax.set_xlabel('Fecha (2021)')
ax.set_ylabel('Temperatura (°C)')
ax.set_title('Temperatura media, SGP E32, Medford, Oklahoma (resolución horaria)')
ax.legend(frameon=False, loc='lower right')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
fig.tight_layout(); fig.savefig(FIG + 'fig_serie_temp.png'); plt.close(fig)

# --- Fig 2: Panel multivariable (medias diarias)
fig, axes = plt.subplots(4, 1, figsize=(9, 7), sharex=True)
panels = [('temp_mean', 'Temperatura (°C)'), ('rh_mean', 'Humedad rel. (%)'),
          ('atmos_pressure', 'Presión (kPa)'), ('wspd_arith_mean', 'Viento (m/s)')]
for ax, (v, lab), c in zip(axes, panels, OKABE_ITO):
    d = df[v].resample('1D').mean()
    ax.plot(d.index, d.values, lw=0.9, color=c)
    ax.set_ylabel(lab)
# precipitacion acumulada diaria como barras en el ultimo eje? mantener 4 paneles
for i, ax in enumerate(axes):
    ax.text(0.005, 0.86, chr(65 + i), transform=ax.transAxes, fontweight='bold', fontsize=11)
axes[-1].set_xlabel('Fecha (2021)')
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%b'))
fig.suptitle('Medias diarias de variables meteorológicas, sgpmetE32.b1 (2021)', y=0.995)
fig.tight_layout(); fig.savefig(FIG + 'fig_panel_multivariable.png'); plt.close(fig)

# --- Fig 3: Distribuciones (histogramas + boxplots)
fig, axes = plt.subplots(2, 4, figsize=(11, 5))
for j, (v, (lab, unit)) in enumerate([(k, PHYS[k]) for k in norm_vars]):
    s = df[v].dropna()
    axes[0, j].hist(s, bins=60, color=OKABE_ITO[j], alpha=0.85)
    axes[0, j].set_title(f'{lab}')
    axes[0, j].set_xlabel(unit); axes[0, j].set_ylabel('Frecuencia' if j == 0 else '')
    bp = axes[1, j].boxplot(s, vert=False, widths=0.5, patch_artist=True,
                            flierprops=dict(marker='.', markersize=2, alpha=0.3))
    bp['boxes'][0].set_facecolor(OKABE_ITO[j]); bp['boxes'][0].set_alpha(0.7)
    axes[1, j].set_xlabel(unit); axes[1, j].set_yticks([])
fig.suptitle('Distribución y outliers (método IQR), datos crudos 2021', y=1.0)
fig.tight_layout(); fig.savefig(FIG + 'fig_distribuciones.png'); plt.close(fig)

# --- Fig 4: Completitud temporal y ruido fisico por mes
full_idx = pd.date_range('2021-01-01', '2021-12-31 23:59', freq='1min')
present = pd.Series(1, index=df.index).reindex(full_idx).fillna(0)
gaps_month = (1 - present).groupby(full_idx.month).sum()           # minutos faltantes
rh_bad_month = (df['rh_mean'] > 100).groupby(df.index.month).sum()  # ruido RH
meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
fig, axes = plt.subplots(1, 2, figsize=(10, 3.2))
axes[0].bar(range(1, 13), gaps_month.reindex(range(1, 13)).fillna(0).values, color=OKABE_ITO[5])
axes[0].set_title('A. Huecos temporales (minutos sin registro)')
axes[0].set_ylabel('Minutos faltantes'); axes[0].set_xlabel('Mes (2021)')
axes[1].bar(range(1, 13), rh_bad_month.reindex(range(1, 13)).fillna(0).values, color=OKABE_ITO[1])
axes[1].set_title('B. Sobresaturación del sensor: registros con HR > 100 %')
axes[1].set_ylabel('N° de registros'); axes[1].set_xlabel('Mes (2021)')
for ax in axes:
    ax.set_xticks(range(1, 13)); ax.set_xticklabels(meses, fontsize=7)
fig.suptitle(f'Calidad de los datos por mes (completitud temporal global: {results["temporal_completeness_pct"]}%)', y=1.02)
fig.tight_layout(); fig.savefig(FIG + 'fig_calidad_mensual.png', bbox_inches='tight'); plt.close(fig)
results['gaps_by_month'] = {meses[i-1]: int(gaps_month.get(i, 0)) for i in range(1, 13)}

# --- Fig 5: Matriz de correlacion (datos limpios)
fig, ax = plt.subplots(figsize=(6.2, 5))
corr_vars = ['temp_mean', 'rh_mean', 'atmos_pressure', 'vapor_pressure_mean',
             'wspd_arith_mean', 'tbrg_precip_total_corr']
corr = clean_imp[corr_vars].corr()
labels = [PHYS[v][0] for v in corr_vars]
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
            xticklabels=labels, yticklabels=labels, square=True,
            linewidths=1, cbar_kws={'shrink': 0.8, 'label': 'r de Pearson'}, ax=ax)
plt.setp(ax.get_xticklabels(), rotation=40, ha='right')
ax.set_title('Matriz de correlación (datos limpios)')
fig.tight_layout(); fig.savefig(FIG + 'fig_correlacion.png'); plt.close(fig)
results['correlations'] = corr.round(3).to_dict()
# valores clave para el texto (asi el documento cita exactamente lo que muestra la figura)
results['corr_temp_vp'] = round(float(corr.loc['temp_mean', 'vapor_pressure_mean']), 2)
results['corr_temp_press'] = round(float(corr.loc['temp_mean', 'atmos_pressure']), 2)
results['corr_temp_rh'] = round(float(corr.loc['temp_mean', 'rh_mean']), 2)

# --- Fig 6: Limpieza antes/despues — sobresaturacion del sensor de HR (>100 %)
# elegir la semana de 7 dias con mas registros RH > 100 %
rh_bad_weekly = (df['rh_mean'] > 100).resample('1W').sum()
worst_week = rh_bad_weekly.idxmax()
t0 = worst_week - pd.Timedelta(days=7)
sel_raw = df['rh_mean'][t0:worst_week]
rh_clip = df['rh_mean'].clip(upper=100.0)  # acotado fisico: techo de saturacion 100 %
sel_clean = rh_clip[t0:worst_week]
bad = sel_raw[sel_raw > 100]
fig, axes = plt.subplots(2, 1, figsize=(9, 4.6), sharex=True, sharey=True)
axes[0].plot(sel_raw.index, sel_raw.values, lw=0.6, color=OKABE_ITO[1])
axes[0].scatter(bad.index, bad.values, s=3, color='red', zorder=3, alpha=0.5,
                label=f'HR > 100 % (sobresaturación del sensor, n={len(bad):,})')
axes[0].axhline(100, color='k', lw=0.8, ls='--')
axes[0].set_title('A. Datos crudos: sobresaturación del sensor HMP155 (valid_max ARM = 104 %)')
axes[0].legend(frameon=False, loc='lower left'); axes[0].set_ylabel('HR (%)')
axes[1].plot(sel_clean.index, sel_clean.values, lw=0.6, color=OKABE_ITO[2])
axes[1].axhline(100, color='k', lw=0.8, ls='--')
axes[1].set_title('B. Datos limpios: acotado al techo físico de saturación (100 %)')
axes[1].set_ylabel('HR (%)'); axes[1].set_xlabel('Fecha')
axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
fig.suptitle('Acotado de la sobresaturación en humedad relativa (semana más afectada de 2021)', y=1.0)
fig.tight_layout(); fig.savefig(FIG + 'fig_limpieza_hr.png'); plt.close(fig)
# guardar EXACTAMENTE lo que muestra la figura para que el pie del documento coincida
results['worst_week_start'] = str(sel_raw.index[0].date())
results['worst_week_end'] = str(sel_raw.index[-1].date())
results['worst_week_rh_bad'] = int(len(bad))

# --- Fig 7: Normalizacion (ejemplo enero, min-max vs z-score)
ene = slice('2021-01-01', '2021-01-31')
fig, axes = plt.subplots(1, 3, figsize=(11, 3))
for v, c in zip(['temp_mean', 'rh_mean', 'atmos_pressure'], OKABE_ITO):
    axes[0].plot(clean_imp[v][ene].resample('3h').mean(), lw=0.8, color=c, label=PHYS[v][0])
    axes[1].plot(minmax[v][ene].resample('3h').mean(), lw=0.8, color=c)
    axes[2].plot(zscore[v][ene].resample('3h').mean(), lw=0.8, color=c)
axes[0].set_title('A. Escala original'); axes[0].set_ylabel('Valor (unidades propias)')
axes[1].set_title('B. Normalización Min-Max [0,1]')
axes[2].set_title('C. Estandarización Z-score')
axes[0].legend(frameon=False, fontsize=7)
for ax in axes:
    ax.set_xlabel('Enero 2021')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
fig.tight_layout(); fig.savefig(FIG + 'fig_normalizacion.png'); plt.close(fig)

# --- Fig 8: Ciclo diurno y estacional (climatologia)
fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.4))
hod = clean_imp['temp_mean'].groupby(clean_imp.index.hour)
axes[0].plot(hod.mean(), color=OKABE_ITO[0], lw=1.5)
axes[0].fill_between(range(24), hod.quantile(.25), hod.quantile(.75),
                     alpha=0.25, color=OKABE_ITO[0], label='IQR (P25–P75)')
axes[0].set_xlabel('Hora del día (UTC)'); axes[0].set_ylabel('Temperatura (°C)')
axes[0].set_title('A. Ciclo diurno medio'); axes[0].legend(frameon=False)
mon = clean_imp['tbrg_precip_total_corr'].resample('1ME').sum()
axes[1].bar(range(1, 13), mon.values, color=OKABE_ITO[4])
axes[1].set_xticks(range(1, 13))
axes[1].set_xticklabels(['E','F','M','A','M','J','J','A','S','O','N','D'])
axes[1].set_xlabel('Mes (2021)'); axes[1].set_ylabel('Precipitación (mm)')
axes[1].set_title('B. Precipitación mensual acumulada')
fig.tight_layout(); fig.savefig(FIG + 'fig_ciclos.png'); plt.close(fig)
results['precip_annual_mm'] = round(float(mon.sum()), 1)
results['temp_annual_mean'] = round(float(clean_imp['temp_mean'].mean()), 2)
results['temp_min'] = round(float(clean_imp['temp_mean'].min()), 1)
results['temp_max'] = round(float(clean_imp['temp_mean'].max()), 1)

# tamano en disco / memoria
import os
results['file_size_mb'] = round(os.path.getsize('data/ARM_sgpmetE32.b1.2021.nc') / 1e6, 1)
results['mem_size_mb'] = round(df.memory_usage(deep=True).sum() / 1e6, 1)

with open("output/resultados_eda.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False, default=str)

print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
print("\nFiguras generadas en figures/")
