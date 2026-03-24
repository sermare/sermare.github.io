#!/usr/bin/env python3
"""
Post-submission deep analysis: feature engineering, regression, and plots.
Predicting competition ipSAE from design features.
"""

import json
import os
import re
import glob
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.linear_model import Ridge, ElasticNetCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from pathlib import Path
from collections import Counter

warnings.filterwarnings('ignore')
plt.rcParams.update({
    'font.weight': 'normal',
    'axes.labelweight': 'normal',
    'axes.titleweight': 'normal',
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'savefig.facecolor': 'white',
    'font.size': 11,
})

PLOT_DIR = Path('/clusterfs/nilah/sergio/sermare.github.io/data/rbx1_plots')
PLOT_DIR.mkdir(parents=True, exist_ok=True)

# ======================================================
# STEP 1: Load competition data
# ======================================================
print("Loading competition data...")
comp = pd.read_csv('/global/scratch/users/sergiomar10/adapty_clean.csv')
# Remove duplicates (keep first)
comp = comp.drop_duplicates(subset='id', keep='first').reset_index(drop=True)
print(f"  Competition designs (unique): {len(comp)}")

# ======================================================
# STEP 2: Parse HTML for our design data
# ======================================================
print("Parsing HTML for our designs...")
html_path = '/clusterfs/nilah/sergio/sermare.github.io/protein-design.html'
with open(html_path, 'r') as f:
    html = f.read()

# Extract the designs array from JavaScript
match = re.search(r'const designs = \[(.*?)\];', html, re.DOTALL)
if not match:
    raise ValueError("Could not find designs array in HTML")

designs_text = match.group(1)

# Parse each design object
our_designs = []
# Split on '  {' pattern at start of each object
blocks = re.split(r'\n\s*\{', designs_text)
for block in blocks:
    block = '{' + block if not block.strip().startswith('{') else block
    block = block.strip().rstrip(',')
    if not block or block == '{':
        continue

    d = {}
    # Extract fields
    for key in ['id', 'name', 'campaign', 'pipeline', 'stage', 'size_class', 'sequence', 'pdb_file', 'af3_flag']:
        m = re.search(rf'{key}:\s*"([^"]*)"', block)
        if m:
            d[key] = m.group(1)
        else:
            m2 = re.search(rf'{key}:\s*null', block)
            if m2:
                d[key] = None

    for key in ['binder_length', 'target_length', 'ipTM', 'pTM', 'pLDDT', 'ipSAE',
                 'af3_iptm', 'af3_ptm', 'af3_delta', 'of3_iptm', 'of3_ptm']:
        m = re.search(rf'{key}:\s*([\d.]+)', block)
        if m:
            d[key] = float(m.group(1))
        else:
            m2 = re.search(rf'{key}:\s*null', block)
            if m2:
                d[key] = None

    if 'id' in d:
        our_designs.append(d)

our_df = pd.DataFrame(our_designs)
print(f"  Our designs parsed: {len(our_df)}")

# Filter to submitted designs (those in competition CSV)
submitted_ids = set(comp['id'].values)
sub_df = our_df[our_df['id'].isin(submitted_ids)].copy().reset_index(drop=True)
print(f"  Matched to competition: {len(sub_df)}")

# Merge with competition data
merged = sub_df.merge(comp, on='id', how='inner', suffixes=('_ours', '_theirs'))
print(f"  Merged rows: {len(merged)}")

# ======================================================
# STEP 3: Feature Engineering
# ======================================================
print("Engineering features...")

# --- Amino acid properties ---
AA_WEIGHTS = {
    'A': 89.1, 'R': 174.2, 'N': 132.1, 'D': 133.1, 'C': 121.2,
    'E': 147.1, 'Q': 146.1, 'G': 75.0, 'H': 155.2, 'I': 131.2,
    'L': 131.2, 'K': 146.2, 'M': 149.2, 'F': 165.2, 'P': 115.1,
    'S': 105.1, 'T': 119.1, 'W': 204.2, 'Y': 181.2, 'V': 117.1
}

KD_HYDROPHOBICITY = {
    'I': 4.5, 'V': 4.2, 'L': 3.8, 'F': 2.8, 'C': 2.5,
    'M': 1.9, 'A': 1.8, 'G': -0.4, 'T': -0.7, 'S': -0.8,
    'W': -0.9, 'Y': -1.3, 'P': -1.6, 'H': -3.2, 'D': -3.5,
    'E': -3.5, 'N': -3.5, 'Q': -3.5, 'K': -3.9, 'R': -4.5
}

PI_VALUES = {
    'A': 6.0, 'R': 10.76, 'N': 5.41, 'D': 2.77, 'C': 5.07,
    'E': 3.22, 'Q': 5.65, 'G': 5.97, 'H': 7.59, 'I': 6.02,
    'L': 5.98, 'K': 9.74, 'M': 5.74, 'F': 5.48, 'P': 6.30,
    'S': 5.68, 'T': 5.60, 'W': 5.89, 'Y': 5.66, 'V': 5.96
}

ALL_AA = list('ACDEFGHIKLMNPQRSTVWY')
CHARGED_POS = set('RKH')
CHARGED_NEG = set('DE')
HYDROPHOBIC = set('AILMFVWP')
POLAR = set('STNQY')
AROMATIC = set('FWY')
HELIX_PROP = set('AEIKLMR')
SHEET_PROP = set('FIVWY')
DISORDER_PROP = set('PGSN')

features = {}

for idx, row in merged.iterrows():
    did = row['id']
    seq = row.get('sequence', '')
    if seq is None or not isinstance(seq, str) or len(seq) == 0:
        continue

    seq = seq.upper()
    n = len(seq)
    f = {}

    # AA composition
    for aa in ALL_AA:
        f[f'aa_{aa}'] = seq.count(aa) / n if n > 0 else 0

    # Grouped fractions
    f['frac_charged_pos'] = sum(1 for c in seq if c in CHARGED_POS) / n
    f['frac_charged_neg'] = sum(1 for c in seq if c in CHARGED_NEG) / n
    f['frac_charged'] = f['frac_charged_pos'] + f['frac_charged_neg']
    f['frac_hydrophobic'] = sum(1 for c in seq if c in HYDROPHOBIC) / n
    f['frac_polar'] = sum(1 for c in seq if c in POLAR) / n
    f['frac_aromatic'] = sum(1 for c in seq if c in AROMATIC) / n

    # Shannon entropy
    aa_counts = Counter(seq)
    probs = np.array([aa_counts[aa]/n for aa in ALL_AA if aa in aa_counts])
    probs = probs[probs > 0]
    f['shannon_entropy'] = -np.sum(probs * np.log2(probs))

    # Unique AA count
    f['unique_aa_count'] = len(set(seq))

    # Max homopolymer repeat
    max_repeat = 1
    curr_repeat = 1
    for i in range(1, n):
        if seq[i] == seq[i-1]:
            curr_repeat += 1
            max_repeat = max(max_repeat, curr_repeat)
        else:
            curr_repeat = 1
    f['max_homopolymer'] = max_repeat

    # Net charge at pH 7
    f['net_charge'] = sum(1 for c in seq if c in CHARGED_POS) - sum(1 for c in seq if c in CHARGED_NEG)
    f['charge_density'] = abs(f['net_charge']) / n

    # Propensities
    f['helix_propensity'] = sum(1 for c in seq if c in HELIX_PROP) / n
    f['sheet_propensity'] = sum(1 for c in seq if c in SHEET_PROP) / n
    f['disorder_propensity'] = sum(1 for c in seq if c in DISORDER_PROP) / n

    # Molecular weight
    f['molecular_weight'] = sum(AA_WEIGHTS.get(c, 110) for c in seq)

    # Isoelectric point (approximate mean pI)
    f['isoelectric_point'] = np.mean([PI_VALUES.get(c, 6.0) for c in seq])

    # Hydrophobicity (KD mean)
    f['hydrophobicity_kd'] = np.mean([KD_HYDROPHOBICITY.get(c, 0) for c in seq])

    # Linguistic complexity (number of unique k-mers / possible k-mers for k=2,3)
    for k in [2, 3]:
        kmers = set()
        for i in range(n - k + 1):
            kmers.add(seq[i:i+k])
        max_possible = min(20**k, n - k + 1)
        f[f'complexity_k{k}'] = len(kmers) / max_possible if max_possible > 0 else 0

    # Binder length
    f['binder_length'] = row['binder_length'] if row['binder_length'] is not None else n

    # Face / campaign
    campaign = row.get('campaign', '')
    if campaign is None:
        campaign = ''
    f['is_e2'] = 1 if 'E2' in campaign else 0
    f['is_cullin'] = 1 if 'Cullin' in campaign else 0
    f['is_boltzgen'] = 1 if 'BoltzGen' in campaign else 0

    # Wave from ID
    wave = did.split('_')[0] if did else ''
    for w in ['w1', 'w2', 'w3', 'wbg', 'wcm']:
        f[f'wave_{w}'] = 1 if wave == w else 0
    # bg_ prefix
    if did.startswith('bg_'):
        f['wave_wbg'] = 1
        f['is_boltzgen'] = 1

    # Our scoring metrics
    f['our_ipSAE'] = row['ipSAE'] if row['ipSAE'] is not None else 0
    f['our_ipTM'] = row['ipTM'] if row['ipTM'] is not None else 0
    f['our_pTM'] = row['pTM'] if row['pTM'] is not None else 0
    f['our_pLDDT'] = row['pLDDT'] if row['pLDDT'] is not None else 0

    # AF3
    af3_val = row.get('af3_iptm')
    if af3_val is not None and not (isinstance(af3_val, float) and np.isnan(af3_val)):
        f['af3_iptm'] = float(af3_val)
        f['has_af3'] = 1
    else:
        f['af3_iptm'] = 0
        f['has_af3'] = 0

    # OF3
    of3_val = row.get('of3_iptm')
    if of3_val is not None and not (isinstance(of3_val, float) and np.isnan(of3_val)):
        f['of3_iptm'] = float(of3_val)
        f['has_of3'] = 1
    else:
        f['of3_iptm'] = 0
        f['has_of3'] = 0

    features[did] = f

feat_df = pd.DataFrame.from_dict(features, orient='index')
feat_df.index.name = 'id'
feat_df = feat_df.reset_index()
print(f"  Features extracted for {len(feat_df)} designs, {len(feat_df.columns)-1} features")

# ======================================================
# STEP 3b: Structural features from Boltz-2 NPZ files
# ======================================================
print("Extracting structural features from Boltz-2 NPZ files...")

SCORING_BASE = '/clusterfs/nilah/sergio/RBX1/03_scoring'

def find_npz_path(did, metric='pae'):
    """Construct direct path to NPZ file, avoiding slow recursive glob."""
    m = re.search(r'design_(\d+)', did)
    if m is None:
        return None
    dnum_str = m.group(0)  # e.g. design_0283
    dnum = int(m.group(1))
    wave = did.split('_design_')[0] if '_design_' in did else ''

    # Map wave prefix to directory and batch size
    candidates = []
    if wave == 'w1':
        # w1 designs are in all_binders with 50 per batch (2-digit batch names)
        batch_num = dnum // 50
        batch_dir = f'pred_batch_{batch_num:02d}'
        boltz_dir = f'boltz_results_batch_{batch_num:02d}'
        candidates.append(os.path.join(SCORING_BASE, 'all_binders', batch_dir, boltz_dir, 'predictions',
                                        dnum_str, f'{metric}_{dnum_str}_model_0.npz'))
    elif wave == 'w2':
        batch_num = dnum // 100
        batch_dir = f'pred_batch_{batch_num:03d}'
        boltz_dir = f'boltz_results_batch_{batch_num:03d}'
        candidates.append(os.path.join(SCORING_BASE, 'wave2', batch_dir, boltz_dir, 'predictions',
                                        dnum_str, f'{metric}_{dnum_str}_model_0.npz'))
    elif wave == 'w3':
        batch_num = dnum // 100
        batch_dir = f'pred_batch_{batch_num:03d}'
        boltz_dir = f'boltz_results_batch_{batch_num:03d}'
        candidates.append(os.path.join(SCORING_BASE, 'wave3', batch_dir, boltz_dir, 'predictions',
                                        dnum_str, f'{metric}_{dnum_str}_model_0.npz'))
    elif wave == 'wbg':
        batch_num = dnum // 100
        batch_dir = f'pred_batch_{batch_num:03d}'
        boltz_dir = f'boltz_results_batch_{batch_num:03d}'
        candidates.append(os.path.join(SCORING_BASE, 'wave_boltzgen', batch_dir, boltz_dir, 'predictions',
                                        dnum_str, f'{metric}_{dnum_str}_model_0.npz'))
    elif wave == 'wcm':
        # wcm designs share design numbers with wave2/wave3
        for wd in ['wave2', 'wave3']:
            batch_num = dnum // 100
            batch_dir = f'pred_batch_{batch_num:03d}'
            boltz_dir = f'boltz_results_batch_{batch_num:03d}'
            candidates.append(os.path.join(SCORING_BASE, wd, batch_dir, boltz_dir, 'predictions',
                                            dnum_str, f'{metric}_{dnum_str}_model_0.npz'))
    elif wave == 'bg':
        # BoltzGen with bg_ prefix
        batch_num = dnum // 100
        batch_dir = f'pred_batch_{batch_num:03d}'
        boltz_dir = f'boltz_results_batch_{batch_num:03d}'
        candidates.append(os.path.join(SCORING_BASE, 'wave_boltzgen', batch_dir, boltz_dir, 'predictions',
                                        dnum_str, f'{metric}_{dnum_str}_model_0.npz'))

    for c in candidates:
        if os.path.exists(c):
            return c
    return None

structural_feats = {}

for did in feat_df['id'].values:
    m = re.search(r'design_(\d+)', did)
    if m is None:
        continue

    pae_path = find_npz_path(did, 'pae')
    plddt_path = find_npz_path(did, 'plddt')
    pae_files = [pae_path] if pae_path else []
    plddt_files = [plddt_path] if plddt_path else []

    sf = {}
    if pae_files:
        try:
            pae_data = np.load(pae_files[0])
            pae = list(pae_data.values())[0]  # Get the array

            # Get binder length from our data
            binder_len = int(feat_df.loc[feat_df['id'] == did, 'binder_length'].values[0])
            target_len = pae.shape[0] - binder_len

            if target_len > 0 and binder_len > 0:
                # Interface PAE: binder->target block
                binder_to_target = pae[:binder_len, binder_len:]
                target_to_binder = pae[binder_len:, :binder_len]

                sf['mean_interface_pae'] = float(np.mean(binder_to_target))
                sf['min_interface_pae'] = float(np.min(binder_to_target))
                sf['contacts_pae_lt3'] = int(np.sum(binder_to_target < 3))
                sf['contacts_pae_lt5'] = int(np.sum(binder_to_target < 5))
                sf['pae_asymmetry'] = float(np.mean(binder_to_target) - np.mean(target_to_binder))
                sf['mean_binder_pae'] = float(np.mean(pae[:binder_len, :binder_len]))
        except Exception as e:
            pass

    if plddt_files:
        try:
            plddt_data = np.load(plddt_files[0])
            plddt = list(plddt_data.values())[0]
            binder_len = int(feat_df.loc[feat_df['id'] == did, 'binder_length'].values[0])

            sf['struct_binder_plddt'] = float(np.mean(plddt[:binder_len]))
            if len(plddt) > binder_len:
                sf['struct_target_plddt'] = float(np.mean(plddt[binder_len:]))
        except Exception as e:
            pass

    if sf:
        structural_feats[did] = sf

print(f"  Structural features for {len(structural_feats)} designs")

# Merge structural features
if structural_feats:
    struct_df = pd.DataFrame.from_dict(structural_feats, orient='index')
    struct_df.index.name = 'id'
    struct_df = struct_df.reset_index()
    feat_df = feat_df.merge(struct_df, on='id', how='left')

# ======================================================
# STEP 4: Merge features with competition targets
# ======================================================
print("Merging features with competition targets...")

# Competition columns renamed
comp_renamed = comp.rename(columns={
    'BOLTZ2 IPSAE': 'their_ipSAE',
    'BOLTZ2 IPTM': 'their_ipTM',
    'BOLTZ2 LIS': 'their_LIS',
    'BOLTZ2 PDOCKQ': 'their_pDockQ',
    'SHAPE COMPLIMENTARITY BOLTZ2 BINDER SS': 'their_ShapeComp',
    'BOLTZ2 COMPLEX IPLDDT': 'their_ComplexIpLDDT',
    'BOLTZ2 COMPLEX PDE': 'their_ComplexPDE',
    'BOLTZ2 COMPLEX PLDDT': 'their_ComplexPLDDT',
    'BOLTZ2 MIN IPSAE': 'their_MinIpSAE',
    'BOLTZ2 PLDDT': 'their_PLDDT',
    'BOLTZ2 PTM': 'their_PTM',
    'BOLTZ2 PDOCKQ2': 'their_pDockQ2',
})

full = feat_df.merge(comp_renamed[['id', 'their_ipSAE', 'their_ipTM', 'their_LIS', 'their_pDockQ',
                                     'their_ShapeComp', 'their_ComplexIpLDDT', 'their_ComplexPDE',
                                     'their_ComplexPLDDT', 'their_MinIpSAE', 'their_PLDDT',
                                     'their_PTM', 'their_pDockQ2']],
                     on='id', how='inner')
print(f"  Full dataset: {len(full)} designs x {len(full.columns)} columns")

# Fill NaN with 0 for feature columns
feature_cols = [c for c in full.columns if c not in ['id'] and not c.startswith('their_')]
for c in feature_cols:
    full[c] = full[c].fillna(0)

# ======================================================
# STEP 5: Regression Analysis
# ======================================================
print("\n=== REGRESSION ANALYSIS ===")
print(f"Target: their_ipSAE")

y = full['their_ipSAE'].values
X = full[feature_cols].values
feature_names = feature_cols

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 5a. Ridge Regression
print("\n--- Ridge Regression ---")
ridge = Ridge(alpha=1.0)
ridge_cv = cross_val_score(ridge, X_scaled, y, cv=5, scoring='r2')
ridge.fit(X_scaled, y)
print(f"  CV R2: {np.mean(ridge_cv):.3f} +/- {np.std(ridge_cv):.3f}")
print(f"  Train R2: {ridge.score(X_scaled, y):.3f}")

# 5b. ElasticNet with CV
print("\n--- ElasticNet CV ---")
enet = ElasticNetCV(l1_ratio=[0.1, 0.3, 0.5, 0.7, 0.9], cv=5, max_iter=10000, random_state=42)
enet.fit(X_scaled, y)
enet_cv = cross_val_score(enet, X_scaled, y, cv=5, scoring='r2')
print(f"  CV R2: {np.mean(enet_cv):.3f} +/- {np.std(enet_cv):.3f}")
print(f"  Best l1_ratio: {enet.l1_ratio_:.2f}")
print(f"  Non-zero features: {np.sum(np.abs(enet.coef_) > 1e-6)}")

# 5c. Random Forest
print("\n--- Random Forest ---")
rf = RandomForestRegressor(n_estimators=500, max_depth=5, min_samples_leaf=3, random_state=42)
rf_cv = cross_val_score(rf, X, y, cv=5, scoring='r2')
rf.fit(X, y)
print(f"  CV R2: {np.mean(rf_cv):.3f} +/- {np.std(rf_cv):.3f}")
print(f"  Train R2: {rf.score(X, y):.3f}")

# Top features
print("\n--- Top 15 Features (Ridge absolute coefficients) ---")
ridge_imp = pd.Series(ridge.coef_, index=feature_names).abs().sort_values(ascending=False)
for i, (feat, val) in enumerate(ridge_imp.head(15).items()):
    print(f"  {i+1}. {feat}: {val:.4f} (coef={ridge.coef_[feature_names.index(feat)]:.4f})")

print("\n--- Top 15 Features (Random Forest importance) ---")
rf_imp = pd.Series(rf.feature_importances_, index=feature_names).sort_values(ascending=False)
for i, (feat, val) in enumerate(rf_imp.head(15).items()):
    print(f"  {i+1}. {feat}: {val:.4f}")

# Correlations with their other metrics
print("\n--- Correlations between our features and their ipSAE ---")
their_metrics = ['their_ipSAE', 'their_ipTM', 'their_LIS', 'their_pDockQ', 'their_ShapeComp']
our_key_features = ['our_ipSAE', 'our_ipTM', 'our_pTM', 'our_pLDDT', 'af3_iptm', 'of3_iptm',
                    'binder_length', 'frac_charged', 'frac_hydrophobic', 'helix_propensity',
                    'shannon_entropy', 'is_e2', 'is_cullin', 'is_boltzgen']

for tm in their_metrics:
    corrs = []
    for feat in our_key_features:
        if feat in full.columns and tm in full.columns:
            r, p = stats.pearsonr(full[feat], full[tm])
            corrs.append((feat, r, p))
    corrs.sort(key=lambda x: abs(x[1]), reverse=True)
    print(f"\n  {tm}:")
    for feat, r, p in corrs[:5]:
        sig = "*" if p < 0.05 else ""
        print(f"    {feat}: r={r:.3f} (p={p:.3f}){sig}")


# ======================================================
# STEP 6: Generate Plots
# ======================================================
print("\n=== GENERATING PLOTS ===")

# --- Plot 1: Full correlation heatmap ---
print("Plot 1: Full correlation heatmap...")
our_feature_subset = ['our_ipSAE', 'our_ipTM', 'our_pTM', 'our_pLDDT', 'af3_iptm', 'of3_iptm',
                       'binder_length', 'frac_charged', 'frac_charged_pos', 'frac_charged_neg',
                       'frac_hydrophobic', 'frac_polar', 'frac_aromatic',
                       'shannon_entropy', 'helix_propensity', 'sheet_propensity', 'disorder_propensity',
                       'hydrophobicity_kd', 'net_charge', 'max_homopolymer',
                       'is_e2', 'is_cullin', 'is_boltzgen']

# Add structural features if available
struct_cols = [c for c in full.columns if c.startswith('mean_interface') or c.startswith('min_interface')
               or c.startswith('contacts_') or c.startswith('struct_') or c.startswith('pae_')]
our_feature_subset.extend(struct_cols)

their_cols = [c for c in full.columns if c.startswith('their_')]
# Only keep features that exist
our_feature_subset = [c for c in our_feature_subset if c in full.columns]

corr_cols = our_feature_subset + their_cols
corr_data = full[corr_cols].astype(float)
corr_matrix = corr_data.corr()

fig, ax = plt.subplots(figsize=(20, 16))
mask = np.zeros_like(corr_matrix, dtype=bool)
sns.heatmap(corr_matrix, mask=mask, cmap='RdBu_r', center=0, vmin=-1, vmax=1,
            square=True, linewidths=0.5, ax=ax, annot=False,
            cbar_kws={'shrink': 0.6, 'label': 'Pearson r'})
ax.set_title('Feature Correlation Matrix: Our Features vs Competition Metrics', fontweight='normal', fontsize=14)
# Add a line separating our features from theirs
n_our = len(our_feature_subset)
ax.axhline(y=n_our, color='black', linewidth=2)
ax.axvline(x=n_our, color='black', linewidth=2)
plt.tight_layout()
plt.savefig(PLOT_DIR / 'post_full_correlation.png', dpi=150, bbox_inches='tight')
plt.close()

# --- Plot 2: Ridge/ElasticNet coefficients ---
print("Plot 2: Regression coefficients...")
# Combine Ridge and ElasticNet top features
ridge_coefs = pd.Series(ridge.coef_, index=feature_names)
enet_coefs = pd.Series(enet.coef_, index=feature_names)

# Get top 15 by max absolute across both
combined_abs = pd.DataFrame({'Ridge': ridge_coefs.abs(), 'ElasticNet': enet_coefs.abs()})
top15_feats = combined_abs.max(axis=1).sort_values(ascending=False).head(15).index

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Ridge
ridge_top = ridge_coefs[top15_feats].sort_values()
colors_r = ['#e74c3c' if v < 0 else '#2ecc71' for v in ridge_top]
axes[0].barh(range(len(ridge_top)), ridge_top.values, color=colors_r, edgecolor='none')
axes[0].set_yticks(range(len(ridge_top)))
axes[0].set_yticklabels(ridge_top.index, fontsize=9)
axes[0].set_xlabel('Ridge Coefficient (standardized)')
axes[0].set_title('Ridge Regression Coefficients', fontweight='normal')
axes[0].axvline(x=0, color='grey', linestyle='--', alpha=0.5)

# ElasticNet
enet_top = enet_coefs[top15_feats].sort_values()
colors_e = ['#e74c3c' if v < 0 else '#2ecc71' for v in enet_top]
axes[1].barh(range(len(enet_top)), enet_top.values, color=colors_e, edgecolor='none')
axes[1].set_yticks(range(len(enet_top)))
axes[1].set_yticklabels(enet_top.index, fontsize=9)
axes[1].set_xlabel('ElasticNet Coefficient (standardized)')
axes[1].set_title('ElasticNet CV Coefficients', fontweight='normal')
axes[1].axvline(x=0, color='grey', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig(PLOT_DIR / 'post_regression_coefs.png', dpi=150, bbox_inches='tight')
plt.close()

# --- Plot 3: Random Forest feature importance ---
print("Plot 3: RF feature importance...")
rf_top15 = rf_imp.head(15).sort_values()

fig, ax = plt.subplots(figsize=(10, 6))
colors_rf = plt.cm.viridis(np.linspace(0.3, 0.9, len(rf_top15)))
ax.barh(range(len(rf_top15)), rf_top15.values, color=colors_rf, edgecolor='none')
ax.set_yticks(range(len(rf_top15)))
ax.set_yticklabels(rf_top15.index, fontsize=10)
ax.set_xlabel('Feature Importance (MDI)')
ax.set_title('Random Forest: Top 15 Features for Predicting Competition ipSAE', fontweight='normal')
plt.tight_layout()
plt.savefig(PLOT_DIR / 'post_feature_importance_rf.png', dpi=150, bbox_inches='tight')
plt.close()

# --- Plot 4: Survivors vs Failures ---
print("Plot 4: Survivors vs Failures...")
full['outcome'] = 'intermediate'
full.loc[full['their_ipSAE'] >= 0.6, 'outcome'] = 'survivor'
full.loc[full['their_ipSAE'] < 0.3, 'outcome'] = 'failure'

survivors = full[full['outcome'] == 'survivor']
failures = full[full['outcome'] == 'failure']

n_surv = len(survivors)
n_fail = len(failures)
print(f"  Survivors (>=0.6): {n_surv}, Failures (<0.3): {n_fail}")

# Find most discriminating features (by t-test)
disc_features = []
for feat in feature_cols:
    s = survivors[feat].dropna()
    f_vals = failures[feat].dropna()
    if len(s) > 2 and len(f_vals) > 2 and s.std() + f_vals.std() > 0:
        t, p = stats.ttest_ind(s, f_vals, equal_var=False)
        disc_features.append((feat, abs(t), p))

disc_features.sort(key=lambda x: x[1], reverse=True)
top6_disc = [x[0] for x in disc_features[:6]]
top6_pvals = {x[0]: x[2] for x in disc_features[:6]}

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
palette = {'survivor': '#2ecc71', 'failure': '#e74c3c'}

for i, feat in enumerate(top6_disc):
    ax = axes[i // 3][i % 3]
    plot_data = full[full['outcome'].isin(['survivor', 'failure'])].copy()

    sns.boxplot(data=plot_data, x='outcome', y=feat, palette=palette, ax=ax,
                width=0.5, fliersize=0, boxprops=dict(alpha=0.4))
    sns.stripplot(data=plot_data, x='outcome', y=feat, palette=palette, ax=ax,
                  size=5, alpha=0.7, jitter=0.2)

    p = top6_pvals[feat]
    sig_str = f"p = {p:.1e}" if p < 0.001 else f"p = {p:.3f}"
    ax.set_title(f'{feat}\n{sig_str}', fontweight='normal', fontsize=10)
    ax.set_xlabel('')

plt.suptitle(f'Survivors (ipSAE >= 0.6, n={n_surv}) vs Failures (ipSAE < 0.3, n={n_fail})',
             fontweight='normal', fontsize=13)
plt.tight_layout()
plt.savefig(PLOT_DIR / 'post_survivors_vs_failures.png', dpi=150, bbox_inches='tight')
plt.close()

# --- Plot 5: OF3 vs their ipSAE ---
print("Plot 5: OF3 ipTM vs their ipSAE...")
of3_data = full[full['has_of3'] == 1].copy()
print(f"  Designs with OF3: {len(of3_data)}")

fig, ax = plt.subplots(figsize=(8, 7))
from matplotlib.lines import Line2D

if len(of3_data) > 3:
    r, p = stats.pearsonr(of3_data['of3_iptm'], of3_data['their_ipSAE'])

    for _, row in of3_data.iterrows():
        if row['is_boltzgen'] == 1:
            c = '#2ecc71'
        elif row['is_cullin'] == 1:
            c = '#e74c3c'
        else:
            c = '#3498db'
        ax.scatter(row['of3_iptm'], row['their_ipSAE'], c=c, s=60, alpha=0.7, edgecolors='white', linewidth=0.5)

    # Trend line
    z = np.polyfit(of3_data['of3_iptm'], of3_data['their_ipSAE'], 1)
    xline = np.linspace(of3_data['of3_iptm'].min(), of3_data['of3_iptm'].max(), 100)
    ax.plot(xline, np.polyval(z, xline), 'k--', alpha=0.5)

    ax.set_xlabel('Our OpenFold3 ipTM')
    ax.set_ylabel('Competition ipSAE')
    ax.set_title(f'OF3 ipTM vs Competition ipSAE (r = {r:.3f}, p = {p:.3f}, n = {len(of3_data)})',
                 fontweight='normal')

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#3498db', markersize=8, label='E2 Face'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#e74c3c', markersize=8, label='Cullin Face'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#2ecc71', markersize=8, label='BoltzGen'),
    ]
    ax.legend(handles=legend_elements, frameon=True, fontsize=9)
else:
    ax.text(0.5, 0.5, 'Insufficient OF3 data', transform=ax.transAxes, ha='center')

plt.tight_layout()
plt.savefig(PLOT_DIR / 'post_our_of3_vs_their_ipsae.png', dpi=150, bbox_inches='tight')
plt.close()

# --- Plot 6: Submission overview ---
print("Plot 6: Submission overview...")
fig, ax = plt.subplots(figsize=(10, 8))

for _, row in full.iterrows():
    if row['is_boltzgen'] == 1:
        c = '#2ecc71'
    elif row['is_cullin'] == 1:
        c = '#e74c3c'
    else:
        c = '#3498db'
    size = max(20, row['binder_length'] * 2)
    ax.scatter(row['our_ipSAE'], row['their_ipSAE'], c=c, s=size, alpha=0.6,
              edgecolors='white', linewidth=0.5)

# Diagonal
ax.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='Perfect agreement')
ax.axhline(y=0.6, color='green', linestyle=':', alpha=0.4, label='Survivor threshold (0.6)')
ax.axhline(y=0.3, color='red', linestyle=':', alpha=0.4, label='Failure threshold (0.3)')

# Annotate surprising designs
for _, row in full.iterrows():
    ours = row['our_ipSAE']
    theirs = row['their_ipSAE']
    # Low ours, high theirs
    if ours < 0.5 and theirs >= 0.65:
        ax.annotate(row['id'].replace('_design_', '_'), (ours, theirs),
                   fontsize=7, alpha=0.8, textcoords='offset points', xytext=(5, 5))
    # High ours, low theirs
    elif ours > 0.8 and theirs < 0.3:
        ax.annotate(row['id'].replace('_design_', '_'), (ours, theirs),
                   fontsize=7, alpha=0.8, textcoords='offset points', xytext=(5, -10))

r_ipsae, p_ipsae = stats.pearsonr(full['our_ipSAE'], full['their_ipSAE'])
ax.set_xlabel('Our Boltz-2 ipSAE')
ax.set_ylabel('Competition ipSAE')
ax.set_title(f'Our ipSAE vs Competition ipSAE (r = {r_ipsae:.3f})\nPoint size = binder length',
             fontweight='normal')

legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#3498db', markersize=8, label='E2 Face'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#e74c3c', markersize=8, label='Cullin Face'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#2ecc71', markersize=8, label='BoltzGen'),
    Line2D([0], [0], linestyle='--', color='k', alpha=0.3, label='Perfect agreement'),
    Line2D([0], [0], linestyle=':', color='green', alpha=0.4, label='Survivor (0.6)'),
    Line2D([0], [0], linestyle=':', color='red', alpha=0.4, label='Failure (0.3)'),
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

plt.tight_layout()
plt.savefig(PLOT_DIR / 'post_submission_overview.png', dpi=150, bbox_inches='tight')
plt.close()

# ======================================================
# STEP 7: Save summary stats for HTML
# ======================================================
print("\n=== SUMMARY STATS ===")
n_total = len(full)
n_survived = len(full[full['their_ipSAE'] >= 0.6])
n_failed = len(full[full['their_ipSAE'] < 0.3])
n_low_ours_high_theirs = len(full[(full['our_ipSAE'] < 0.5) & (full['their_ipSAE'] >= 0.6)])
n_high_ours_low_theirs = len(full[(full['our_ipSAE'] > 0.7) & (full['their_ipSAE'] < 0.3)])
n_low_ours_submitted = len(full[full['our_ipSAE'] < 0.5])

print(f"Total matched: {n_total}")
print(f"Survived (>=0.6): {n_survived}")
print(f"Failed (<0.3): {n_failed}")
print(f"Low ours (<0.5) submitted: {n_low_ours_submitted}")
print(f"Low ours but high theirs: {n_low_ours_high_theirs}")
print(f"High ours but low theirs: {n_high_ours_low_theirs}")

# Ridge CV R2
print(f"\nRidge CV R2: {np.mean(ridge_cv):.3f}")
print(f"ElasticNet CV R2: {np.mean(enet_cv):.3f}")
print(f"RF CV R2: {np.mean(rf_cv):.3f}")

# Surprising reversals
print("\n--- Surprising Reversals ---")
print("\nLow ours (<0.5), High theirs (>=0.6):")
reversals_up = full[(full['our_ipSAE'] < 0.5) & (full['their_ipSAE'] >= 0.6)][['id', 'our_ipSAE', 'their_ipSAE']].sort_values('their_ipSAE', ascending=False)
print(reversals_up.to_string())

print("\nHigh ours (>0.7), Low theirs (<0.3):")
reversals_down = full[(full['our_ipSAE'] > 0.7) & (full['their_ipSAE'] < 0.3)][['id', 'our_ipSAE', 'their_ipSAE']].sort_values('our_ipSAE', ascending=False)
print(reversals_down.to_string())

# Save summary to JSON for HTML generation
summary = {
    'n_total': int(n_total),
    'n_survived': int(n_survived),
    'n_failed': int(n_failed),
    'n_low_ours_submitted': int(n_low_ours_submitted),
    'n_low_ours_high_theirs': int(n_low_ours_high_theirs),
    'n_high_ours_low_theirs': int(n_high_ours_low_theirs),
    'ridge_cv_r2': float(np.mean(ridge_cv)),
    'enet_cv_r2': float(np.mean(enet_cv)),
    'rf_cv_r2': float(np.mean(rf_cv)),
    'ridge_top10': [(f, float(ridge.coef_[feature_names.index(f)])) for f in ridge_imp.head(10).index],
    'enet_nonzero': int(np.sum(np.abs(enet.coef_) > 1e-6)),
    'rf_top10': [(f, float(v)) for f, v in rf_imp.head(10).items()],
    'top6_discriminating': [(f, float(top6_pvals[f])) for f in top6_disc],
    'ipsae_corr': float(r_ipsae),
    'reversals_up': reversals_up[['id', 'our_ipSAE', 'their_ipSAE']].to_dict('records'),
    'reversals_down': reversals_down[['id', 'our_ipSAE', 'their_ipSAE']].to_dict('records'),
}

with open(PLOT_DIR / 'post_analysis_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("\nAll plots saved to data/rbx1_plots/")
print("Summary saved to data/rbx1_plots/post_analysis_summary.json")
print("DONE.")
