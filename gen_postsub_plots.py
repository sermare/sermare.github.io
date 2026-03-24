#!/usr/bin/env python3
"""Generate Post-Submission tab plots for protein-design.html."""
import csv, re, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import Ridge

os.chdir('/clusterfs/nilah/sergio/sermare.github.io')
outdir = 'data/rbx1_plots'

# ---------- Load their data ----------
with open('/global/scratch/users/sergiomar10/adapty_clean.csv') as f:
    reader = csv.DictReader(f)
    their_raw = list(reader)

# Deduplicate (some ids appear twice in CSV)
their = {}
for r in their_raw:
    their[r['id']] = r

print(f"Their unique designs: {len(their)}")

# ---------- Load our data from HTML ----------
with open('protein-design.html') as f:
    html = f.read()

merged = []
for tid, tvals in their.items():
    idx = html.find(f'id: "{tid}"')
    if idx == -1:
        print(f"  NOT FOUND in HTML: {tid}")
        continue
    entry = html[idx:html.find('},', idx)]

    def gf(k):
        fm = re.search(rf'(?<!\w){k}:\s*([\d.]+)', entry)
        return float(fm.group(1)) if fm else None
    def gs(k):
        fm = re.search(rf'{k}:\s*"([^"]+)"', entry)
        return fm.group(1) if fm else None

    def safe_float(val):
        if val is None or val == '':
            return None
        try:
            return float(val)
        except:
            return None

    merged.append({
        'id': tid,
        'their_ipsae': safe_float(tvals.get('BOLTZ2 IPSAE')),
        'their_min_ipsae': safe_float(tvals.get('BOLTZ2 MIN IPSAE')),
        'their_iptm': safe_float(tvals.get('BOLTZ2 IPTM')),
        'their_ptm': safe_float(tvals.get('BOLTZ2 PTM')),
        'their_plddt': safe_float(tvals.get('BOLTZ2 PLDDT')),
        'their_lis': safe_float(tvals.get('BOLTZ2 LIS')),
        'their_pdockq': safe_float(tvals.get('BOLTZ2 PDOCKQ')),
        'their_pdockq2': safe_float(tvals.get('BOLTZ2 PDOCKQ2')),
        'their_shape': safe_float(tvals.get('SHAPE COMPLIMENTARITY BOLTZ2 BINDER SS')),
        'their_complex_iplddt': safe_float(tvals.get('BOLTZ2 COMPLEX IPLDDT')),
        'their_complex_pde': safe_float(tvals.get('BOLTZ2 COMPLEX PDE')),
        'their_complex_plddt': safe_float(tvals.get('BOLTZ2 COMPLEX PLDDT')),
        'our_ipsae': gf('ipSAE'),
        'our_iptm': gf('ipTM'),
        'our_ptm': gf('pTM'),
        'our_plddt': gf('pLDDT'),
        'our_af3': gf('af3_iptm'),
        'our_of3': gf('of3_iptm'),
        'campaign': gs('campaign') or '',
        'pipeline': gs('pipeline') or '',
    })

print(f"Merged designs: {len(merged)}")

# Pipeline color mapping
def get_color(m):
    if 'BoltzGen' in m.get('pipeline', ''):
        return '#2ca02c'
    elif 'Cullin' in m.get('campaign', ''):
        return '#d62728'
    else:
        return '#1f77b4'

def get_label(m):
    if 'BoltzGen' in m.get('pipeline', ''):
        return 'BoltzGen'
    elif 'Cullin' in m.get('campaign', ''):
        return 'Cullin Face'
    else:
        return 'E2 Face'

# ---------- Style defaults ----------
plt.rcParams.update({
    'font.weight': 'normal',
    'axes.labelweight': 'normal',
    'axes.titleweight': 'normal',
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'savefig.facecolor': 'white',
    'font.size': 12,
})


# ======== PLOT 1: Our vs Their ipSAE ========
fig, ax = plt.subplots(figsize=(7, 6))
valid = [m for m in merged if m['our_ipsae'] is not None and m['their_ipsae'] is not None]
x = np.array([m['our_ipsae'] for m in valid])
y = np.array([m['their_ipsae'] for m in valid])
colors = [get_color(m) for m in valid]
labels = [get_label(m) for m in valid]

# Plot by group for legend
for grp, c in [('E2 Face', '#1f77b4'), ('Cullin Face', '#d62728'), ('BoltzGen', '#2ca02c')]:
    mask = [l == grp for l in labels]
    if any(mask):
        xg = x[mask]
        yg = y[mask]
        ax.scatter(xg, yg, c=c, label=grp, alpha=0.7, s=50, edgecolors='white', linewidth=0.5)

# Ridge regression
ridge = Ridge(alpha=1.0)
ridge.fit(x.reshape(-1, 1), y)
xline = np.linspace(x.min(), x.max(), 100)
yline = ridge.predict(xline.reshape(-1, 1))
ax.plot(xline, yline, 'k--', linewidth=1.5, alpha=0.7)

# Pearson r
r, p = stats.pearsonr(x, y)
ax.text(0.05, 0.95, f'Pearson r = {r:.3f}\np = {p:.2e}\nn = {len(valid)}',
        transform=ax.transAxes, fontsize=11, verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.8))

# Diagonal reference
mn, mx = min(x.min(), y.min()), max(x.max(), y.max())
ax.plot([mn, mx], [mn, mx], 'gray', linewidth=0.8, alpha=0.5, linestyle=':')

ax.set_xlabel('Our Boltz-2 ipSAE')
ax.set_ylabel('Competition Boltz-2 ipSAE')
ax.set_title('Our vs Competition ipSAE Scores')
ax.legend(fontsize=10)
plt.tight_layout()
fig.savefig(f'{outdir}/post_our_vs_their_ipsae.png', dpi=150)
plt.close()
print("Plot 1 done")


# ======== PLOT 2: Our vs Their ipTM ========
fig, ax = plt.subplots(figsize=(7, 6))
valid = [m for m in merged if m['our_iptm'] is not None and m['their_iptm'] is not None]
x = np.array([m['our_iptm'] for m in valid])
y = np.array([m['their_iptm'] for m in valid])
colors = [get_color(m) for m in valid]
labels = [get_label(m) for m in valid]

for grp, c in [('E2 Face', '#1f77b4'), ('Cullin Face', '#d62728'), ('BoltzGen', '#2ca02c')]:
    mask = [l == grp for l in labels]
    if any(mask):
        xg = x[mask]
        yg = y[mask]
        ax.scatter(xg, yg, c=c, label=grp, alpha=0.7, s=50, edgecolors='white', linewidth=0.5)

ridge = Ridge(alpha=1.0)
ridge.fit(x.reshape(-1, 1), y)
xline = np.linspace(x.min(), x.max(), 100)
yline = ridge.predict(xline.reshape(-1, 1))
ax.plot(xline, yline, 'k--', linewidth=1.5, alpha=0.7)

r, p = stats.pearsonr(x, y)
ax.text(0.05, 0.95, f'Pearson r = {r:.3f}\np = {p:.2e}\nn = {len(valid)}',
        transform=ax.transAxes, fontsize=11, verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.8))

mn, mx = min(x.min(), y.min()), max(x.max(), y.max())
ax.plot([mn, mx], [mn, mx], 'gray', linewidth=0.8, alpha=0.5, linestyle=':')

ax.set_xlabel('Our Boltz-2 ipTM')
ax.set_ylabel('Competition Boltz-2 ipTM')
ax.set_title('Our vs Competition ipTM Scores')
ax.legend(fontsize=10)
plt.tight_layout()
fig.savefig(f'{outdir}/post_our_vs_their_iptm.png', dpi=150)
plt.close()
print("Plot 2 done")


# ======== PLOT 3: Correlation heatmap of their 12 metrics ========
their_metric_keys = [
    ('BOLTZ2 IPSAE', 'ipSAE'),
    ('BOLTZ2 MIN IPSAE', 'Min ipSAE'),
    ('BOLTZ2 IPTM', 'ipTM'),
    ('BOLTZ2 PTM', 'PTM'),
    ('BOLTZ2 PLDDT', 'pLDDT'),
    ('BOLTZ2 COMPLEX IPLDDT', 'Complex ipLDDT'),
    ('BOLTZ2 COMPLEX PDE', 'Complex PDE'),
    ('BOLTZ2 COMPLEX PLDDT', 'Complex pLDDT'),
    ('BOLTZ2 LIS', 'LIS'),
    ('BOLTZ2 PDOCKQ', 'pDockQ'),
    ('BOLTZ2 PDOCKQ2', 'pDockQ2'),
    ('SHAPE COMPLIMENTARITY BOLTZ2 BINDER SS', 'Shape Comp.'),
]

# Build matrix from their raw unique data
metric_data = {}
for csv_key, label in their_metric_keys:
    vals = []
    for tid, tvals in their.items():
        v = tvals.get(csv_key, '')
        try:
            vals.append(float(v))
        except:
            vals.append(np.nan)
    metric_data[label] = vals

labels_list = [lbl for _, lbl in their_metric_keys]
n_metrics = len(labels_list)
corr_matrix = np.zeros((n_metrics, n_metrics))
for i, li in enumerate(labels_list):
    for j, lj in enumerate(labels_list):
        a = np.array(metric_data[li])
        b = np.array(metric_data[lj])
        mask = ~(np.isnan(a) | np.isnan(b))
        if mask.sum() > 2:
            corr_matrix[i, j] = np.corrcoef(a[mask], b[mask])[0, 1]
        else:
            corr_matrix[i, j] = np.nan

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
ax.set_xticks(range(n_metrics))
ax.set_yticks(range(n_metrics))
ax.set_xticklabels(labels_list, rotation=45, ha='right', fontsize=9)
ax.set_yticklabels(labels_list, fontsize=9)
ax.set_title('Competition Metric Correlations (12 Boltz-2 Metrics)')

# Add correlation values
for i in range(n_metrics):
    for j in range(n_metrics):
        v = corr_matrix[i, j]
        if not np.isnan(v):
            color = 'white' if abs(v) > 0.6 else 'black'
            ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=7, color=color)

plt.colorbar(im, ax=ax, shrink=0.8, label='Pearson r')
plt.tight_layout()
fig.savefig(f'{outdir}/post_their_metrics_heatmap.png', dpi=150)
plt.close()
print("Plot 3 done")


# ======== PLOT 4: Distribution of their ipSAE ========
fig, ax = plt.subplots(figsize=(7, 5))
ipsae_vals = [m['their_ipsae'] for m in merged if m['their_ipsae'] is not None]
ipsae_arr = np.array(ipsae_vals)

ax.hist(ipsae_arr, bins=20, color='#4c72b0', alpha=0.7, edgecolor='white')
ax.axvline(0.5, color='orange', linestyle='--', linewidth=1.5, label=f'>0.5: {(ipsae_arr > 0.5).sum()} designs')
ax.axvline(0.7, color='red', linestyle='--', linewidth=1.5, label=f'>0.7: {(ipsae_arr > 0.7).sum()} designs')
ax.set_xlabel('Competition Boltz-2 ipSAE')
ax.set_ylabel('Count')
ax.set_title('Distribution of Competition ipSAE for Our 83 Designs')
ax.legend(fontsize=10)

# Add summary text
median_val = np.median(ipsae_arr)
mean_val = np.mean(ipsae_arr)
ax.text(0.95, 0.95, f'Mean = {mean_val:.3f}\nMedian = {median_val:.3f}\nn = {len(ipsae_vals)}',
        transform=ax.transAxes, fontsize=10, verticalalignment='top', ha='right',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.8))

plt.tight_layout()
fig.savefig(f'{outdir}/post_their_ipsae_distribution.png', dpi=150)
plt.close()
print("Plot 4 done")


# ======== PLOT 5: Which of our metrics predict their ipSAE ========
fig, ax = plt.subplots(figsize=(7, 5))

our_metrics = [
    ('our_ipsae', 'Our ipSAE'),
    ('our_iptm', 'Our ipTM'),
    ('our_plddt', 'Our pLDDT'),
    ('our_ptm', 'Our pTM'),
    ('our_af3', 'AF3 ipTM'),
    ('our_of3', 'OF3 ipTM'),
]

correlations = []
metric_labels = []
for key, label in our_metrics:
    valid = [(m[key], m['their_ipsae']) for m in merged
             if m[key] is not None and m['their_ipsae'] is not None]
    if len(valid) >= 3:
        a = np.array([v[0] for v in valid])
        b = np.array([v[1] for v in valid])
        r, p = stats.pearsonr(a, b)
        correlations.append(r)
        metric_labels.append(f'{label}\n(n={len(valid)})')
    else:
        correlations.append(0)
        metric_labels.append(f'{label}\n(n<3)')

colors_bar = ['#2ca02c' if c > 0.5 else '#ff7f0e' if c > 0.3 else '#d62728' for c in correlations]
bars = ax.barh(range(len(correlations)), correlations, color=colors_bar, alpha=0.8, edgecolor='white')
ax.set_yticks(range(len(metric_labels)))
ax.set_yticklabels(metric_labels, fontsize=10)
ax.set_xlabel('Pearson r with Competition ipSAE')
ax.set_title('Which of Our Metrics Best Predicts Competition Scoring?')
ax.axvline(0, color='gray', linewidth=0.5)

# Add values on bars
for i, (bar, val) in enumerate(zip(bars, correlations)):
    ax.text(val + 0.02 if val >= 0 else val - 0.02, i, f'{val:.3f}',
            va='center', ha='left' if val >= 0 else 'right', fontsize=10)

plt.tight_layout()
fig.savefig(f'{outdir}/post_which_predict_their_ipsae.png', dpi=150)
plt.close()
print("Plot 5 done")

# Print summary stats for the HTML
print("\n--- Summary Stats ---")
print(f"Total matched: {len(merged)}")
above_05 = sum(1 for m in merged if m['their_ipsae'] is not None and m['their_ipsae'] > 0.5)
above_07 = sum(1 for m in merged if m['their_ipsae'] is not None and m['their_ipsae'] > 0.7)
print(f"Above 0.5 ipSAE: {above_05}")
print(f"Above 0.7 ipSAE: {above_07}")

# Correlation summary
for key, label in our_metrics:
    valid = [(m[key], m['their_ipsae']) for m in merged
             if m[key] is not None and m['their_ipsae'] is not None]
    if len(valid) >= 3:
        a = np.array([v[0] for v in valid])
        b = np.array([v[1] for v in valid])
        r, p = stats.pearsonr(a, b)
        print(f"  {label}: r={r:.3f}, p={p:.2e}, n={len(valid)}")

# ipSAE correlation
valid_ipsae = [m for m in merged if m['our_ipsae'] is not None and m['their_ipsae'] is not None]
our_arr = np.array([m['our_ipsae'] for m in valid_ipsae])
their_arr = np.array([m['their_ipsae'] for m in valid_ipsae])
r, _ = stats.pearsonr(our_arr, their_arr)
mean_delta = np.mean(our_arr - their_arr)
print(f"\nipSAE: Our mean={our_arr.mean():.3f}, Their mean={their_arr.mean():.3f}, mean delta={mean_delta:.3f}")
print(f"ipSAE correlation: r={r:.3f}")

valid_iptm = [m for m in merged if m['our_iptm'] is not None and m['their_iptm'] is not None]
our_iptm_arr = np.array([m['our_iptm'] for m in valid_iptm])
their_iptm_arr = np.array([m['their_iptm'] for m in valid_iptm])
r_iptm, _ = stats.pearsonr(our_iptm_arr, their_iptm_arr)
mean_delta_iptm = np.mean(our_iptm_arr - their_iptm_arr)
print(f"ipTM: Our mean={our_iptm_arr.mean():.3f}, Their mean={their_iptm_arr.mean():.3f}, mean delta={mean_delta_iptm:.3f}")
print(f"ipTM correlation: r={r_iptm:.3f}")

print("\nAll plots saved successfully!")
