#!/usr/bin/env python3
"""Post-submission deep analysis: feature engineering, regression, plots."""

import re
import json
import glob
import math
import warnings
import numpy as np
import pandas as pd
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats
from sklearn.linear_model import Ridge, ElasticNetCV, LassoCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score

warnings.filterwarnings('ignore')

PLOT_DIR = Path('data/rbx1_plots')
PLOT_DIR.mkdir(parents=True, exist_ok=True)

# ── Style ──
plt.rcParams.update({
    'font.weight': 'normal',
    'axes.titleweight': 'normal',
    'axes.labelweight': 'normal',
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'savefig.facecolor': 'white',
    'font.size': 11,
})

# ═══════════════════════════════════════════════
# 1. LOAD DATA
# ═══════════════════════════════════════════════

# Competition results
comp = pd.read_csv('/global/scratch/users/sergiomar10/adapty_clean.csv')
comp = comp.drop_duplicates(subset='id', keep='first').reset_index(drop=True)
print(f"Competition data: {len(comp)} unique designs")

# Parse designs from HTML
with open('protein-design.html', 'r') as f:
    html = f.read()

start = html.index('const designs = [')
depth = 0
i = start + len('const designs = ')
for j in range(i, len(html)):
    if html[j] == '[':
        depth += 1
    elif html[j] == ']':
        depth -= 1
        if depth == 0:
            end = j + 1
            break
js_array = html[i:end]

# Parse JS objects to dicts
designs_raw = re.findall(r'\{([^}]+)\}', js_array, re.DOTALL)

def parse_js_obj(text):
    d = {}
    for line in text.split('\n'):
        line = line.strip().rstrip(',')
        if ':' not in line:
            continue
        key, val = line.split(':', 1)
        key = key.strip()
        val = val.strip()
        if val.startswith('"') and val.endswith('"'):
            d[key] = val[1:-1]
        elif val in ('null', 'undefined', ''):
            d[key] = None
        else:
            try:
                d[key] = float(val)
            except ValueError:
                d[key] = val
    return d

designs = [parse_js_obj(d) for d in designs_raw]
designs_df = pd.DataFrame(designs)
print(f"Total designs in HTML: {len(designs_df)}")

# Merge: only keep the 83 submitted designs
merged = comp.merge(designs_df, on='id', how='inner')
print(f"Matched designs: {len(merged)}")

# ═══════════════════════════════════════════════
# 2. FEATURE ENGINEERING
# ═══════════════════════════════════════════════

AA_LIST = list('ACDEFGHIKLMNPQRSTVWY')
AA_WEIGHTS = {
    'A': 89.1, 'C': 121.2, 'D': 133.1, 'E': 147.1, 'F': 165.2,
    'G': 75.0, 'H': 155.2, 'I': 131.2, 'K': 146.2, 'L': 131.2,
    'M': 149.2, 'N': 132.1, 'P': 115.1, 'Q': 146.2, 'R': 174.2,
    'S': 105.1, 'T': 119.1, 'V': 117.1, 'W': 204.2, 'Y': 181.2
}
KYTE_DOOLITTLE = {
    'A': 1.8, 'C': 2.5, 'D': -3.5, 'E': -3.5, 'F': 2.8,
    'G': -0.4, 'H': -3.2, 'I': 4.5, 'K': -3.9, 'L': 3.8,
    'M': 1.9, 'N': -3.5, 'P': -1.6, 'Q': -3.5, 'R': -4.5,
    'S': -0.8, 'T': -0.7, 'V': 4.2, 'W': -0.9, 'Y': -1.3
}
PK_VALUES = {
    'D': 3.65, 'E': 4.25, 'C': 8.18, 'Y': 10.07,
    'H': 6.00, 'K': 10.53, 'R': 12.48
}

def compute_sequence_features(seq):
    if seq is None or not isinstance(seq, str) or len(seq) == 0:
        return {}
    seq = seq.upper()
    n = len(seq)
    counts = Counter(seq)
    feats = {}

    # AA composition
    for aa in AA_LIST:
        feats[f'frac_{aa}'] = counts.get(aa, 0) / n

    # Property fractions
    charged = set('DEKRH')
    hydrophobic = set('AVILMFYW')
    polar = set('STNQCY')
    aromatic = set('FWY')
    feats['frac_charged'] = sum(counts.get(a, 0) for a in charged) / n
    feats['frac_hydrophobic'] = sum(counts.get(a, 0) for a in hydrophobic) / n
    feats['frac_polar'] = sum(counts.get(a, 0) for a in polar) / n
    feats['frac_aromatic'] = sum(counts.get(a, 0) for a in aromatic) / n

    # Shannon entropy
    probs = [counts[a] / n for a in counts if a in set(AA_LIST)]
    feats['shannon_entropy'] = -sum(p * math.log2(p) for p in probs if p > 0)

    # Unique AA count
    feats['unique_aa'] = len([a for a in AA_LIST if counts.get(a, 0) > 0])

    # Max homopolymer repeat
    max_rep = 1
    cur = 1
    for i in range(1, n):
        if seq[i] == seq[i-1]:
            cur += 1
            max_rep = max(max_rep, cur)
        else:
            cur = 1
    feats['max_homopolymer'] = max_rep

    # Net charge at pH 7
    pos = counts.get('K', 0) + counts.get('R', 0) + counts.get('H', 0) * 0.1
    neg = counts.get('D', 0) + counts.get('E', 0)
    feats['net_charge'] = pos - neg
    feats['charge_density'] = feats['net_charge'] / n

    # Propensities
    helix_aa = set('AEIKLMR')
    sheet_aa = set('FIVWY')
    disorder_aa = set('PGSN')
    feats['helix_propensity'] = sum(counts.get(a, 0) for a in helix_aa) / n
    feats['sheet_propensity'] = sum(counts.get(a, 0) for a in sheet_aa) / n
    feats['disorder_propensity'] = sum(counts.get(a, 0) for a in disorder_aa) / n

    # Molecular weight
    feats['mol_weight'] = sum(AA_WEIGHTS.get(a, 110) * counts.get(a, 0) for a in AA_LIST) - (n - 1) * 18.0

    # Hydrophobicity (Kyte-Doolittle mean)
    feats['hydrophobicity'] = np.mean([KYTE_DOOLITTLE.get(a, 0) for a in seq])

    # Isoelectric point estimate (bisection)
    def charge_at_pH(pH):
        c = 10**(- pH) / (10**(- pH) + 10**(-8.0))  # N-term ~8
        c += -10**(-pH + 0) / (10**(-3.1) + 10**(-pH))  # C-term ~3.1
        for aa_char in seq:
            if aa_char in ('K', 'R'):
                pk = PK_VALUES[aa_char]
                c += 10**(-pH) / (10**(-pH) + 10**(-pk))
            elif aa_char == 'H':
                c += 10**(-pH) / (10**(-pH) + 10**(-6.0))
            elif aa_char in ('D', 'E', 'C', 'Y'):
                pk = PK_VALUES[aa_char]
                c += -10**(-pk) / (10**(-pk) + 10**(-pH))
        return c

    lo, hi = 0.0, 14.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if charge_at_pH(mid) > 0:
            lo = mid
        else:
            hi = mid
    feats['isoelectric_point'] = (lo + hi) / 2

    # Linguistic complexity
    seen = set()
    total = 0
    for w in range(1, min(4, n) + 1):
        for i in range(n - w + 1):
            seen.add(seq[i:i+w])
            total += 1
    max_possible = sum(min(20**w, n - w + 1) for w in range(1, min(4, n) + 1))
    feats['linguistic_complexity'] = len(seen) / max_possible if max_possible > 0 else 0

    return feats

print("Computing sequence features...")
seq_feats_list = []
for _, row in merged.iterrows():
    sf = compute_sequence_features(row.get('sequence'))
    sf['id'] = row['id']
    seq_feats_list.append(sf)
seq_feats = pd.DataFrame(seq_feats_list)
merged = merged.merge(seq_feats, on='id', how='left')

# ── Structural features from Boltz-2 NPZ files ──
print("Checking for structural prediction files...")

def extract_structural_features(design_id, target_len=108):
    num = design_id.split('design_')[1]
    base = '/clusterfs/nilah/sergio/RBX1/03_scoring'

    pae_files = glob.glob(f'{base}/**/*/pred_batch_*/boltz_results*/predictions/design_{num}/pae_design_{num}_model_0.npz', recursive=True)
    plddt_files = glob.glob(f'{base}/**/*/pred_batch_*/boltz_results*/predictions/design_{num}/plddt_design_{num}_model_0.npz', recursive=True)

    feats = {}
    if pae_files:
        try:
            data = np.load(pae_files[0])
            pae = data[list(data.keys())[0]]
            total_len = pae.shape[0]
            binder_len = total_len - target_len

            if binder_len > 0 and binder_len < total_len:
                # binder->target block
                bt = pae[:binder_len, binder_len:]
                # target->binder block
                tb = pae[binder_len:, :binder_len]
                feats['mean_interface_pae'] = float(np.mean(bt))
                feats['min_interface_pae'] = float(np.min(bt))
                feats['contacts_pae_lt3'] = int(np.sum(bt < 3))
                feats['contacts_pae_lt5'] = int(np.sum(bt < 5))
                feats['pae_asymmetry'] = float(np.mean(bt) - np.mean(tb))
                feats['mean_binder_pae'] = float(np.mean(pae[:binder_len, :binder_len]))
        except Exception as e:
            print(f"  PAE error for {design_id}: {e}")

    if plddt_files:
        try:
            data = np.load(plddt_files[0])
            plddt = data[list(data.keys())[0]].flatten()
            total_len = len(plddt)
            binder_len = total_len - target_len

            if binder_len > 0:
                feats['mean_binder_plddt_npz'] = float(np.mean(plddt[:binder_len]))
                feats['mean_target_plddt_npz'] = float(np.mean(plddt[binder_len:]))
        except Exception as e:
            print(f"  pLDDT error for {design_id}: {e}")

    return feats

struct_feats_list = []
n_found = 0
for _, row in merged.iterrows():
    sf = extract_structural_features(row['id'])
    sf['id'] = row['id']
    if len(sf) > 1:
        n_found += 1
    struct_feats_list.append(sf)
struct_df = pd.DataFrame(struct_feats_list)
merged = merged.merge(struct_df, on='id', how='left')
print(f"Found structural files for {n_found}/{len(merged)} designs")

# ── Design metadata features ──
def get_wave(did):
    prefix = did.split('_')[0]
    return prefix

def get_face(campaign):
    if campaign is None:
        return 'Unknown'
    if 'Cullin' in str(campaign):
        return 'Cullin'
    elif 'BoltzGen' in str(campaign):
        return 'BoltzGen'
    else:
        return 'E2'

merged['wave'] = merged['id'].apply(get_wave)
merged['face'] = merged['campaign'].apply(get_face)
merged['is_boltzgen'] = (merged['face'] == 'BoltzGen').astype(int)
merged['is_cullin'] = (merged['face'] == 'Cullin').astype(int)
merged['binder_len'] = merged['binder_length'].fillna(50).astype(float)

# Our scoring metrics
merged['our_ipsae'] = merged['ipSAE'].fillna(0).astype(float)
merged['our_iptm'] = merged['ipTM'].fillna(0).astype(float)
merged['our_ptm'] = merged['pTM'].fillna(0).astype(float)
merged['our_plddt'] = merged['pLDDT'].fillna(0).astype(float)

# AF3 and OF3
merged['af3_iptm_val'] = pd.to_numeric(merged.get('af3_iptm'), errors='coerce').fillna(0)
merged['has_af3'] = (merged['af3_iptm_val'] > 0).astype(int)
merged['of3_iptm_val'] = pd.to_numeric(merged.get('of3_iptm'), errors='coerce').fillna(0)
merged['has_of3'] = (merged['of3_iptm_val'] > 0).astype(int)

# ── Competition metrics (targets) ──
their_cols = {
    'BOLTZ2 IPSAE': 'their_ipsae',
    'BOLTZ2 IPTM': 'their_iptm',
    'BOLTZ2 LIS': 'their_lis',
    'BOLTZ2 PDOCKQ': 'their_pdockq',
    'BOLTZ2 PDOCKQ2': 'their_pdockq2',
    'BOLTZ2 PTM': 'their_ptm',
    'BOLTZ2 PLDDT': 'their_plddt',
    'BOLTZ2 COMPLEX IPLDDT': 'their_complex_iplddt',
    'BOLTZ2 COMPLEX PDE': 'their_complex_pde',
    'BOLTZ2 COMPLEX PLDDT': 'their_complex_plddt',
    'BOLTZ2 MIN IPSAE': 'their_min_ipsae',
    'SHAPE COMPLIMENTARITY BOLTZ2 BINDER SS': 'their_shape_comp',
}
for old, new in their_cols.items():
    if old in merged.columns:
        merged[new] = pd.to_numeric(merged[old], errors='coerce')

# ═══════════════════════════════════════════════
# 3. BUILD FEATURE MATRIX
# ═══════════════════════════════════════════════

# All our features
seq_feat_cols = [c for c in merged.columns if c.startswith('frac_') or c in [
    'shannon_entropy', 'unique_aa', 'max_homopolymer', 'net_charge',
    'charge_density', 'helix_propensity', 'sheet_propensity',
    'disorder_propensity', 'mol_weight', 'hydrophobicity',
    'isoelectric_point', 'linguistic_complexity'
]]
struct_feat_cols = [c for c in merged.columns if c in [
    'mean_interface_pae', 'min_interface_pae', 'contacts_pae_lt3',
    'contacts_pae_lt5', 'pae_asymmetry', 'mean_binder_pae',
    'mean_binder_plddt_npz', 'mean_target_plddt_npz'
]]
meta_feat_cols = ['binder_len', 'is_boltzgen', 'is_cullin']
score_feat_cols = ['our_ipsae', 'our_iptm', 'our_ptm', 'our_plddt',
                   'af3_iptm_val', 'has_af3', 'of3_iptm_val', 'has_of3']

all_feat_cols = seq_feat_cols + struct_feat_cols + meta_feat_cols + score_feat_cols
print(f"\nTotal features: {len(all_feat_cols)}")
print(f"  Sequence: {len(seq_feat_cols)}")
print(f"  Structural: {len(struct_feat_cols)}")
print(f"  Metadata: {len(meta_feat_cols)}")
print(f"  Scoring: {len(score_feat_cols)}")

# Fill NaN in features with 0
X = merged[all_feat_cols].fillna(0).values
y = merged['their_ipsae'].values
feature_names = all_feat_cols

print(f"\nFeature matrix: {X.shape}")
print(f"Target: their_ipsae, mean={y.mean():.3f}, std={y.std():.3f}")

# ═══════════════════════════════════════════════
# 4. REGRESSION ANALYSIS
# ═══════════════════════════════════════════════

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Ridge
ridge = Ridge(alpha=1.0)
ridge.fit(X_scaled, y)
ridge_cv = cross_val_score(ridge, X_scaled, y, cv=5, scoring='r2')
print(f"\nRidge R2 (5-fold CV): {ridge_cv.mean():.3f} +/- {ridge_cv.std():.3f}")

# ElasticNet CV
enet = ElasticNetCV(l1_ratio=[0.1, 0.5, 0.7, 0.9, 0.95, 0.99],
                    alphas=np.logspace(-3, 1, 50),
                    cv=5, max_iter=10000)
enet.fit(X_scaled, y)
enet_cv = cross_val_score(enet, X_scaled, y, cv=5, scoring='r2')
print(f"ElasticNet R2 (5-fold CV): {enet_cv.mean():.3f} +/- {enet_cv.std():.3f}")
print(f"  Best alpha={enet.alpha_:.4f}, l1_ratio={enet.l1_ratio_:.2f}")

# Random Forest
rf = RandomForestRegressor(n_estimators=500, max_depth=5, min_samples_leaf=3,
                           random_state=42)
rf.fit(X, y)
rf_cv = cross_val_score(rf, X, y, cv=5, scoring='r2')
print(f"Random Forest R2 (5-fold CV): {rf_cv.mean():.3f} +/- {rf_cv.std():.3f}")

# Feature importance
ridge_importance = pd.Series(ridge.coef_, index=feature_names).abs().sort_values(ascending=False)
enet_importance = pd.Series(enet.coef_, index=feature_names)
rf_importance = pd.Series(rf.feature_importances_, index=feature_names).sort_values(ascending=False)

print("\nTop 10 Ridge features (by |coef|):")
print(ridge_importance.head(10))
print("\nTop 10 ElasticNet features (non-zero):")
enet_nonzero = enet_importance[enet_importance != 0].abs().sort_values(ascending=False)
print(enet_nonzero.head(10))
print("\nTop 10 RF features:")
print(rf_importance.head(10))

# Correlations with their OTHER metrics
their_metric_cols = ['their_ipsae', 'their_iptm', 'their_lis', 'their_pdockq',
                     'their_ptm', 'their_plddt', 'their_complex_iplddt',
                     'their_complex_pde', 'their_complex_plddt',
                     'their_min_ipsae', 'their_shape_comp']

# ═══════════════════════════════════════════════
# 5. PLOTS
# ═══════════════════════════════════════════════

# ── Plot 1: Full correlation heatmap ──
print("\nGenerating Plot 1: Full correlation heatmap...")
our_feat_subset = ['our_ipsae', 'our_iptm', 'our_ptm', 'our_plddt',
                   'af3_iptm_val', 'of3_iptm_val', 'binder_len',
                   'is_boltzgen', 'is_cullin',
                   'frac_charged', 'frac_hydrophobic', 'frac_polar', 'frac_aromatic',
                   'shannon_entropy', 'helix_propensity', 'sheet_propensity',
                   'disorder_propensity', 'hydrophobicity', 'isoelectric_point',
                   'net_charge', 'mol_weight', 'linguistic_complexity',
                   'max_homopolymer', 'unique_aa']
# Add structural if available
for c in struct_feat_cols:
    if merged[c].notna().sum() > 5:
        our_feat_subset.append(c)

avail_their = [c for c in their_metric_cols if c in merged.columns and merged[c].notna().sum() > 5]
avail_ours = [c for c in our_feat_subset if c in merged.columns and merged[c].notna().sum() > 5]

corr_data = merged[avail_ours + avail_their].fillna(0)
corr_matrix = corr_data.corr()
# Subset: our features vs their metrics
cross_corr = corr_matrix.loc[avail_ours, avail_their]

fig, ax = plt.subplots(figsize=(14, 12))
sns.heatmap(cross_corr, annot=True, fmt='.2f', cmap='RdBu_r', center=0,
            vmin=-1, vmax=1, ax=ax, annot_kws={'size': 7})
ax.set_title('Our Features vs Competition Metrics: Correlation Matrix', fontweight='normal', fontsize=14)
ax.set_xlabel('Competition Metrics', fontweight='normal')
ax.set_ylabel('Our Features', fontweight='normal')
plt.tight_layout()
plt.savefig(PLOT_DIR / 'post_full_correlation.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved post_full_correlation.png")

# ── Plot 2: Ridge/ElasticNet coefficients ──
print("Generating Plot 2: Regression coefficients...")
# Combine ridge + enet, show top 15 by magnitude
coef_df = pd.DataFrame({
    'Ridge': ridge.coef_,
    'ElasticNet': enet.coef_,
}, index=feature_names)
top_feats = coef_df.abs().max(axis=1).sort_values(ascending=False).head(15).index
coef_plot = coef_df.loc[top_feats]

fig, ax = plt.subplots(figsize=(10, 7))
x_pos = np.arange(len(top_feats))
w = 0.35
ax.barh(x_pos - w/2, coef_plot['Ridge'], w, label='Ridge', color='#4C72B0', alpha=0.85)
ax.barh(x_pos + w/2, coef_plot['ElasticNet'], w, label='ElasticNet', color='#DD8452', alpha=0.85)
ax.set_yticks(x_pos)
ax.set_yticklabels(top_feats, fontsize=10)
ax.set_xlabel('Coefficient (standardized features)', fontweight='normal')
ax.set_title('Top 15 Features: Ridge & ElasticNet Coefficients\nfor Predicting Competition ipSAE', fontweight='normal', fontsize=13)
ax.axvline(0, color='gray', linewidth=0.8, linestyle='--')
ax.legend(fontsize=10)
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(PLOT_DIR / 'post_regression_coefs.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved post_regression_coefs.png")

# ── Plot 3: Random Forest feature importance ──
print("Generating Plot 3: RF feature importance...")
top_rf = rf_importance.head(15)
fig, ax = plt.subplots(figsize=(10, 7))
ax.barh(range(len(top_rf)), top_rf.values, color='#55A868', alpha=0.85)
ax.set_yticks(range(len(top_rf)))
ax.set_yticklabels(top_rf.index, fontsize=10)
ax.set_xlabel('Feature Importance (MDI)', fontweight='normal')
ax.set_title('Random Forest Feature Importance\nfor Predicting Competition ipSAE', fontweight='normal', fontsize=13)
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(PLOT_DIR / 'post_feature_importance_rf.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved post_feature_importance_rf.png")

# ── Plot 4: Survivors vs Failures ──
print("Generating Plot 4: Survivors vs Failures...")
merged['tier'] = 'middle'
merged.loc[merged['their_ipsae'] >= 0.6, 'tier'] = 'survivor'
merged.loc[merged['their_ipsae'] < 0.3, 'tier'] = 'failure'
sf_data = merged[merged['tier'].isin(['survivor', 'failure'])].copy()

# Find most discriminating features (by t-test)
discriminating = []
for feat in all_feat_cols:
    surv = sf_data.loc[sf_data['tier'] == 'survivor', feat].dropna()
    fail = sf_data.loc[sf_data['tier'] == 'failure', feat].dropna()
    if len(surv) > 2 and len(fail) > 2:
        t, p = stats.ttest_ind(surv, fail)
        d = abs(surv.mean() - fail.mean()) / max(surv.std() + fail.std(), 1e-10) * 2
        discriminating.append((feat, p, d, t))
discriminating.sort(key=lambda x: x[1])
top6 = [d[0] for d in discriminating[:6]]
top6_pvals = {d[0]: d[1] for d in discriminating[:6]}

fig, axes = plt.subplots(2, 3, figsize=(15, 9))
axes = axes.flatten()
for i, feat in enumerate(top6):
    ax = axes[i]
    for tier, color in [('survivor', '#55A868'), ('failure', '#C44E52')]:
        data = sf_data.loc[sf_data['tier'] == tier, feat].dropna()
        bp = ax.boxplot([data], positions=[0 if tier == 'survivor' else 1],
                       widths=0.5, patch_artist=True,
                       boxprops=dict(facecolor=color, alpha=0.3))
        ax.scatter(np.full(len(data), 0 if tier == 'survivor' else 1) + np.random.normal(0, 0.05, len(data)),
                  data, c=color, alpha=0.6, s=20, zorder=3)
    pval = top6_pvals[feat]
    pstr = f'p={pval:.2e}' if pval < 0.01 else f'p={pval:.3f}'
    ax.set_title(f'{feat}\n({pstr})', fontweight='normal', fontsize=10)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Survivor\n(ipSAE>=0.6)', 'Failure\n(ipSAE<0.3)'], fontsize=9)
fig.suptitle('Top 6 Discriminating Features: Survivors vs Failures', fontweight='normal', fontsize=14, y=1.01)
plt.tight_layout()
plt.savefig(PLOT_DIR / 'post_survivors_vs_failures.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved post_survivors_vs_failures.png")

# ── Plot 5: OF3 vs their ipSAE ──
print("Generating Plot 5: OF3 vs their ipSAE...")
has_of3_data = merged[merged['of3_iptm_val'] > 0].copy()
fig, ax = plt.subplots(figsize=(8, 7))
colors = {'E2': '#4C72B0', 'Cullin': '#C44E52', 'BoltzGen': '#55A868'}
for face, color in colors.items():
    mask = has_of3_data['face'] == face
    if mask.sum() > 0:
        ax.scatter(has_of3_data.loc[mask, 'of3_iptm_val'],
                  has_of3_data.loc[mask, 'their_ipsae'],
                  c=color, label=face, s=50, alpha=0.7, edgecolors='white', linewidth=0.5)
r, p = stats.pearsonr(has_of3_data['of3_iptm_val'], has_of3_data['their_ipsae'])
ax.set_xlabel('Our OpenFold3 ipTM', fontweight='normal')
ax.set_ylabel('Competition ipSAE', fontweight='normal')
ax.set_title(f'OpenFold3 ipTM vs Competition ipSAE (n={len(has_of3_data)}, r={r:.3f}, p={p:.3f})',
             fontweight='normal', fontsize=12)
ax.legend(fontsize=10)
# Add regression line
z = np.polyfit(has_of3_data['of3_iptm_val'], has_of3_data['their_ipsae'], 1)
xline = np.linspace(has_of3_data['of3_iptm_val'].min(), has_of3_data['of3_iptm_val'].max(), 100)
ax.plot(xline, np.polyval(z, xline), 'k--', alpha=0.5, linewidth=1)
plt.tight_layout()
plt.savefig(PLOT_DIR / 'post_our_of3_vs_their_ipsae.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved post_our_of3_vs_their_ipsae.png")

# ── Plot 6: Submission overview ──
print("Generating Plot 6: Submission overview...")
fig, ax = plt.subplots(figsize=(10, 8))
for face, color in colors.items():
    mask = merged['face'] == face
    if mask.sum() > 0:
        ax.scatter(merged.loc[mask, 'our_ipsae'],
                  merged.loc[mask, 'their_ipsae'],
                  c=color, label=face,
                  s=merged.loc[mask, 'binder_len'] * 2,
                  alpha=0.65, edgecolors='white', linewidth=0.5)

# Diagonal
ax.plot([0, 1], [0, 1], 'k--', alpha=0.3)
# Annotate surprising ones
for _, row in merged.iterrows():
    # Low ours, high theirs
    if row['our_ipsae'] < 0.4 and row['their_ipsae'] > 0.6:
        ax.annotate(row['id'].replace('_design_', '\n'),
                   (row['our_ipsae'], row['their_ipsae']),
                   fontsize=6, alpha=0.8, color='#228B22',
                   textcoords='offset points', xytext=(5, 5))
    # High ours, low theirs
    elif row['our_ipsae'] > 0.7 and row['their_ipsae'] < 0.2:
        ax.annotate(row['id'].replace('_design_', '\n'),
                   (row['our_ipsae'], row['their_ipsae']),
                   fontsize=6, alpha=0.8, color='#B22222',
                   textcoords='offset points', xytext=(5, -10))

r, _ = stats.pearsonr(merged['our_ipsae'], merged['their_ipsae'])
ax.set_xlabel('Our Boltz-2 ipSAE', fontweight='normal')
ax.set_ylabel('Competition Boltz-2 ipSAE', fontweight='normal')
ax.set_title(f'Submission Overview: Our vs Competition ipSAE (n={len(merged)}, r={r:.3f})\nPoint size = binder length',
             fontweight='normal', fontsize=12)
ax.legend(fontsize=10, title='Face', title_fontsize=10)
plt.tight_layout()
plt.savefig(PLOT_DIR / 'post_submission_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved post_submission_overview.png")

# ═══════════════════════════════════════════════
# 6. SAVE REGRESSION RESULTS FOR HTML
# ═══════════════════════════════════════════════

results = {
    'n_designs': int(len(merged)),
    'n_survivors': int((merged['their_ipsae'] >= 0.6).sum()),
    'n_failures': int((merged['their_ipsae'] < 0.3).sum()),
    'n_low_ours_submitted': int((merged['our_ipsae'] < 0.5).sum()),
    'n_low_ours_high_theirs': int(((merged['our_ipsae'] < 0.5) & (merged['their_ipsae'] >= 0.6)).sum()),
    'ridge_cv_r2': float(ridge_cv.mean()),
    'enet_cv_r2': float(enet_cv.mean()),
    'rf_cv_r2': float(rf_cv.mean()),
    'top_ridge_features': ridge_importance.head(10).to_dict(),
    'top_rf_features': rf_importance.head(10).to_dict(),
    'top_enet_features': enet_nonzero.head(10).to_dict() if len(enet_nonzero) > 0 else {},
    'top6_discriminating': [(d[0], float(d[1])) for d in discriminating[:6]],
    'of3_correlation': {
        'r': float(r),
        'p': float(p),
        'n': int(len(has_of3_data)),
    },
    'surprising_low_ours_high_theirs': merged[(merged['our_ipsae'] < 0.4) & (merged['their_ipsae'] > 0.6)][['id', 'our_ipsae', 'their_ipsae']].to_dict('records'),
    'surprising_high_ours_low_theirs': merged[(merged['our_ipsae'] > 0.7) & (merged['their_ipsae'] < 0.2)][['id', 'our_ipsae', 'their_ipsae']].to_dict('records'),
}

with open(PLOT_DIR / 'post_regression_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nSaved regression results to {PLOT_DIR / 'post_regression_results.json'}")

# Print summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"Designs: {results['n_designs']}")
print(f"Survivors (ipSAE >= 0.6): {results['n_survivors']}")
print(f"Failures (ipSAE < 0.3): {results['n_failures']}")
print(f"Low ours (<0.5) submitted: {results['n_low_ours_submitted']}")
print(f"Low ours high theirs: {results['n_low_ours_high_theirs']}")
print(f"Ridge CV R2: {results['ridge_cv_r2']:.3f}")
print(f"ElasticNet CV R2: {results['enet_cv_r2']:.3f}")
print(f"RF CV R2: {results['rf_cv_r2']:.3f}")
print(f"OF3 correlation: r={results['of3_correlation']['r']:.3f}, n={results['of3_correlation']['n']}")
print(f"\nSurprising (low ours, high theirs):")
for s in results['surprising_low_ours_high_theirs']:
    print(f"  {s['id']}: ours={s['our_ipsae']:.3f}, theirs={s['their_ipsae']:.3f}")
print(f"Surprising (high ours, low theirs):")
for s in results['surprising_high_ours_low_theirs']:
    print(f"  {s['id']}: ours={s['our_ipsae']:.3f}, theirs={s['their_ipsae']:.3f}")
