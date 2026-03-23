#!/usr/bin/env python3
"""Generate pipeline analysis plots for protein-design.html"""

import re, os, json, warnings
warnings.filterwarnings('ignore')

os.chdir('/clusterfs/nilah/sergio/sermare.github.io')

# ── Extract designs ──────────────────────────────────────────────────
with open('protein-design.html') as f:
    content = f.read()

designs = []
for m in re.finditer(r'id: "([^"]+)"', content):
    s = m.start()
    e = content.find('},', s)
    if e == -1 or e - s > 2000:
        continue
    en = content[s:e]

    def gf(k):
        fm = re.search(rf'(?<!\w){k}:\s*([\d.]+)', en)
        return float(fm.group(1)) if fm else None

    def gs(k):
        fm = re.search(rf'{k}:\s*"([^"]+)"', en)
        return fm.group(1) if fm else None

    seq = gs('sequence') or ''
    d = {
        'id': m.group(1),
        'boltz_iptm': gf('ipTM'),
        'boltz_ptm': gf('pTM'),
        'boltz_plddt': gf('pLDDT'),
        'ipsae': gf('ipSAE'),
        'of3_iptm': gf('of3_iptm'),
        'of3_ptm': gf('of3_ptm'),
        'af3_iptm': gf('af3_iptm'),
        'af3_ptm': gf('af3_ptm'),
        'af3_flag': gs('af3_flag'),
        'campaign': gs('campaign') or '',
        'pipeline': gs('pipeline') or '',
        'binder_length': gf('binder_length') or len(seq),
        'sequence': seq,
    }

    c = d['campaign'].lower()
    pid = d['id'].lower()
    if pid.startswith('wbg_') or 'boltzgen' in c or 'bg_' in c:
        d['face'] = 'BoltzGen'
    elif pid.startswith('wcm_') or 'cul' in c:
        d['face'] = 'Cullin'
    else:
        d['face'] = 'E2'

    bl = d['binder_length'] or 0
    if bl < 55:
        d['size'] = '<55 AA'
    elif bl < 66:
        d['size'] = '55-65 AA'
    elif bl < 100:
        d['size'] = '66-99 AA'
    else:
        d['size'] = '100+ AA'

    if 'beta' in c:
        d['model'] = 'Beta'
    elif 'boltzgen' in c or 'bg_' in c or pid.startswith('wbg_'):
        d['model'] = 'BoltzGen'
    else:
        d['model'] = 'Base'

    designs.append(d)

print(f"Extracted {len(designs)} designs")
print(f"  with AF3: {sum(1 for d in designs if d['af3_iptm'] is not None)}")
print(f"  with OF3: {sum(1 for d in designs if d['of3_iptm'] is not None)}")
print(f"  faces: { {f: sum(1 for d in designs if d['face']==f) for f in ['E2','Cullin','BoltzGen']} }")

# ── Plotting setup ───────────────────────────────────────────────────
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from sklearn.linear_model import Ridge
from matplotlib.gridspec import GridSpec

plt.rcParams.update({
    'figure.facecolor': 'white', 'axes.facecolor': 'white', 'font.size': 11,
    'font.weight': 'normal', 'axes.labelweight': 'normal', 'axes.titleweight': 'normal',
    'axes.grid': True, 'grid.alpha': 0.15,
    'axes.spines.top': False, 'axes.spines.right': False
})

palette = {'E2': '#2171B5', 'Cullin': '#CB181D', 'BoltzGen': '#238B45'}
outdir = 'data/rbx1_plots'
os.makedirs(outdir, exist_ok=True)

# ── Helper: scatter with boxplot marginals ───────────────────────────
def scatter_with_marginals(data_list, xkey, ykey, xlabel, ylabel, title, fname,
                           label_top=5, add_diagonal=True):
    """
    data_list: list of dicts with xkey, ykey, 'face', 'id'
    """
    fig = plt.figure(figsize=(9, 8))
    gs = GridSpec(5, 5, hspace=0.05, wspace=0.05)
    ax_main = fig.add_subplot(gs[1:, :-1])
    ax_top = fig.add_subplot(gs[0, :-1], sharex=ax_main)
    ax_right = fig.add_subplot(gs[1:, -1], sharey=ax_main)

    # Scatter
    face_counts = {}
    for face, color in palette.items():
        pts = [d for d in data_list if d['face'] == face]
        face_counts[face] = len(pts)
        if pts:
            xs = [d[xkey] for d in pts]
            ys = [d[ykey] for d in pts]
            ax_main.scatter(xs, ys, c=color, alpha=0.65, s=50, edgecolors='white',
                           linewidth=0.5, label=f"{face} (n={len(pts)})", zorder=3)

    # Label top designs by ykey
    sorted_pts = sorted(data_list, key=lambda d: d[ykey] if d[ykey] else 0, reverse=True)
    for d in sorted_pts[:label_top]:
        short_id = d['id'].replace('design_', '').replace('w2_', '').replace('w1_', '').replace('w3_', '').replace('wbg_', 'bg_').replace('wcm_', 'cm_')
        ax_main.annotate(short_id, (d[xkey], d[ykey]), fontsize=7, alpha=0.7,
                        xytext=(5, 5), textcoords='offset points')

    # Ridge regression
    xs_all = np.array([d[xkey] for d in data_list])
    ys_all = np.array([d[ykey] for d in data_list])
    if len(xs_all) > 3:
        ridge = Ridge(alpha=1.0)
        ridge.fit(xs_all.reshape(-1, 1), ys_all)
        xline = np.linspace(xs_all.min(), xs_all.max(), 100)
        yline = ridge.predict(xline.reshape(-1, 1))
        ax_main.plot(xline, yline, color='darkorange', linewidth=2, alpha=0.8, zorder=4)

        r_val, _ = stats.pearsonr(xs_all, ys_all)
        rho_val, _ = stats.spearmanr(xs_all, ys_all)
        ax_main.text(0.03, 0.97, f"Pearson r = {r_val:.2f}\nSpearman ρ = {rho_val:.2f}",
                    transform=ax_main.transAxes, fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    # Diagonal
    if add_diagonal:
        lims = [min(xs_all.min(), ys_all.min()), max(xs_all.max(), ys_all.max())]
        ax_main.plot(lims, lims, '--', color='gray', alpha=0.5, zorder=1)

    ax_main.set_xlabel(xlabel)
    ax_main.set_ylabel(ylabel)
    ax_main.legend(fontsize=9, loc='lower right')

    # Top marginal: boxplots
    faces_with_data = []
    for i, (face, color) in enumerate(palette.items()):
        vals = [d[xkey] for d in data_list if d['face'] == face and d[xkey] is not None]
        if vals:
            faces_with_data.append((i, face, color, vals))
            bp = ax_top.boxplot([vals], positions=[i], widths=0.6, patch_artist=True, vert=True)
            bp['boxes'][0].set_facecolor(color)
            bp['boxes'][0].set_alpha(0.6)
            for element in ['whiskers', 'caps', 'medians']:
                for line in bp[element]:
                    line.set_color(color)
                    line.set_alpha(0.8)
            for flier in bp['fliers']:
                flier.set_markeredgecolor(color)

    ax_top.set_xticks(range(len(palette)))
    ax_top.set_xticklabels([])
    ax_top.tick_params(axis='x', labelbottom=False)
    ax_top.spines['top'].set_visible(False)
    ax_top.spines['right'].set_visible(False)
    ax_top.set_ylabel(xlabel, fontsize=9)
    ax_top.grid(True, alpha=0.15)

    # Right marginal: boxplots
    for i, (face, color) in enumerate(palette.items()):
        vals = [d[ykey] for d in data_list if d['face'] == face and d[ykey] is not None]
        if vals:
            bp = ax_right.boxplot([vals], positions=[i], widths=0.6, patch_artist=True, vert=False)
            bp['boxes'][0].set_facecolor(color)
            bp['boxes'][0].set_alpha(0.6)
            for element in ['whiskers', 'caps', 'medians']:
                for line in bp[element]:
                    line.set_color(color)
                    line.set_alpha(0.8)
            for flier in bp['fliers']:
                flier.set_markeredgecolor(color)

    ax_right.set_yticks(range(len(palette)))
    ax_right.set_yticklabels([])
    ax_right.tick_params(axis='y', labelleft=False)
    ax_right.spines['top'].set_visible(False)
    ax_right.spines['right'].set_visible(False)
    ax_right.set_xlabel(ylabel, fontsize=9)
    ax_right.grid(True, alpha=0.15)

    fig.suptitle(title, fontsize=14, fontweight='normal', y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(f'{outdir}/{fname}', dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved {fname}")

    return face_counts, (r_val if len(xs_all) > 3 else None), (rho_val if len(xs_all) > 3 else None)


# ═══════════════════════════════════════════════════════════════════════
# PLOT 1: Boltz vs AF3
# ═══════════════════════════════════════════════════════════════════════
print("\n--- Section 1: Scoring Bias ---")
af3_data = [d for d in designs if d['af3_iptm'] is not None and d['boltz_iptm'] is not None]
print(f"AF3 validated designs: {len(af3_data)}")
fc1, r1, rho1 = scatter_with_marginals(
    af3_data, 'boltz_iptm', 'af3_iptm',
    'Boltz-2 ipTM', 'AF3 ipTM',
    f'Boltz-2 does not predict AF3 validation (n={len(af3_data)})',
    'pipe_boltz_vs_af3.png', label_top=5
)

# ═══════════════════════════════════════════════════════════════════════
# PLOT 2: AF3 vs OF3
# ═══════════════════════════════════════════════════════════════════════
af3_of3_data = [d for d in designs if d['af3_iptm'] is not None and d['of3_iptm'] is not None]
print(f"AF3+OF3 designs: {len(af3_of3_data)}")
fc2, r2, rho2 = scatter_with_marginals(
    af3_of3_data, 'af3_iptm', 'of3_iptm',
    'AF3 ipTM', 'OF3 ipTM',
    f'AF3 correlates with OF3 (n={len(af3_of3_data)})',
    'pipe_af3_vs_of3.png', label_top=5
)

# ═══════════════════════════════════════════════════════════════════════
# PLOT 3: Boltz vs OF3
# ═══════════════════════════════════════════════════════════════════════
of3_data = [d for d in designs if d['of3_iptm'] is not None and d['boltz_iptm'] is not None]
print(f"OF3 designs: {len(of3_data)}")
fc3, r3, rho3 = scatter_with_marginals(
    of3_data, 'boltz_iptm', 'of3_iptm',
    'Boltz-2 ipTM', 'OF3 ipTM',
    f'Boltz-2 vs OF3 (n={len(of3_data)})',
    'pipe_boltz_vs_of3.png', label_top=5
)

# ═══════════════════════════════════════════════════════════════════════
# PLOT 4: ipSAE by face (boxplot + swarm)
# ═══════════════════════════════════════════════════════════════════════
print("\n--- Section 2: Performance by Target ---")
fig, ax = plt.subplots(figsize=(7, 5))
face_vals = {}
for face in ['E2', 'Cullin', 'BoltzGen']:
    vals = [d['ipsae'] for d in designs if d['face'] == face and d['ipsae'] is not None]
    face_vals[face] = vals

positions = range(len(palette))
for i, (face, color) in enumerate(palette.items()):
    vals = face_vals[face]
    if not vals:
        continue
    bp = ax.boxplot([vals], positions=[i], widths=0.5, patch_artist=True, vert=True)
    bp['boxes'][0].set_facecolor(color)
    bp['boxes'][0].set_alpha(0.5)
    for el in ['whiskers', 'caps', 'medians']:
        for line in bp[el]:
            line.set_color(color)
    # Swarm (jittered points, downsampled)
    np.random.seed(42)
    show = vals if len(vals) <= 300 else list(np.random.choice(vals, 300, replace=False))
    jitter = np.random.normal(0, 0.08, len(show))
    ax.scatter(i + jitter, show, c=color, alpha=0.2, s=10, zorder=2)
    # Mean
    mean_val = np.mean(vals)
    ax.annotate(f'μ={mean_val:.3f}\nn={len(vals)}', (i, mean_val),
               fontsize=9, ha='center', va='bottom', xytext=(0, 8),
               textcoords='offset points')

# T-tests
faces_list = list(palette.keys())
for i in range(len(faces_list)):
    for j in range(i+1, len(faces_list)):
        v1, v2 = face_vals[faces_list[i]], face_vals[faces_list[j]]
        if v1 and v2:
            t, p = stats.ttest_ind(v1, v2)
            y_max = max(max(v1), max(v2))
            ax.plot([i, j], [y_max + 0.02*(j-i+1), y_max + 0.02*(j-i+1)], 'k-', linewidth=0.8)
            ax.text((i+j)/2, y_max + 0.02*(j-i+1) + 0.005, f'p={p:.1e}', ha='center', fontsize=8)

ax.set_xticks(range(len(palette)))
ax.set_xticklabels(list(palette.keys()))
ax.set_ylabel('ipSAE')
ax.set_title('ipSAE by Target Face', fontweight='normal')
fig.tight_layout()
fig.savefig(f'{outdir}/pipe_ipsae_by_face.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("  Saved pipe_ipsae_by_face.png")

# ═══════════════════════════════════════════════════════════════════════
# PLOT 5: Metrics by face (1x4)
# ═══════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 4, figsize=(16, 4))
metrics = [('ipsae', 'ipSAE'), ('boltz_iptm', 'Boltz ipTM'), ('boltz_plddt', 'Boltz pLDDT'), ('boltz_ptm', 'Boltz pTM')]
for ax, (mkey, mlabel) in zip(axes, metrics):
    for i, (face, color) in enumerate(palette.items()):
        vals = [d[mkey] for d in designs if d['face'] == face and d[mkey] is not None]
        if vals:
            bp = ax.boxplot([vals], positions=[i], widths=0.5, patch_artist=True, vert=True)
            bp['boxes'][0].set_facecolor(color)
            bp['boxes'][0].set_alpha(0.5)
            for el in ['whiskers', 'caps', 'medians']:
                for line in bp[el]:
                    line.set_color(color)
    ax.set_xticks(range(len(palette)))
    ax.set_xticklabels(list(palette.keys()), fontsize=9)
    ax.set_title(mlabel, fontweight='normal', fontsize=11)
fig.suptitle('Metrics by Target Face', fontweight='normal', fontsize=13)
fig.tight_layout()
fig.savefig(f'{outdir}/pipe_metrics_by_face.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("  Saved pipe_metrics_by_face.png")

# ═══════════════════════════════════════════════════════════════════════
# PLOT 6: ipSAE by size
# ═══════════════════════════════════════════════════════════════════════
print("\n--- Section 3: Performance by Size ---")
size_order = ['<55 AA', '55-65 AA', '66-99 AA', '100+ AA']
fig, ax = plt.subplots(figsize=(8, 5))
for i, sz in enumerate(size_order):
    vals = [d['ipsae'] for d in designs if d['size'] == sz and d['ipsae'] is not None]
    if vals:
        bp = ax.boxplot([vals], positions=[i], widths=0.5, patch_artist=True, vert=True)
        bp['boxes'][0].set_facecolor('#6baed6')
        bp['boxes'][0].set_alpha(0.6)
        ax.annotate(f'μ={np.mean(vals):.3f}\nn={len(vals)}', (i, np.mean(vals)),
                   fontsize=9, ha='center', va='bottom', xytext=(0, 8),
                   textcoords='offset points')
ax.set_xticks(range(len(size_order)))
ax.set_xticklabels(size_order)
ax.set_ylabel('ipSAE')
ax.set_title('ipSAE by Binder Size', fontweight='normal')
fig.tight_layout()
fig.savefig(f'{outdir}/pipe_ipsae_by_size.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("  Saved pipe_ipsae_by_size.png")

# ═══════════════════════════════════════════════════════════════════════
# PLOT 7: ipTM vs length
# ═══════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
for face, color in palette.items():
    pts = [d for d in designs if d['face'] == face and d['boltz_iptm'] is not None and d['binder_length']]
    if pts:
        ax.scatter([d['binder_length'] for d in pts], [d['boltz_iptm'] for d in pts],
                  c=color, alpha=0.15, s=12, label=f'{face} (n={len(pts)})')
ax.set_xlabel('Binder Length (AA)')
ax.set_ylabel('Boltz-2 ipTM')
ax.set_title('Boltz-2 ipTM vs Binder Length', fontweight='normal')
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(f'{outdir}/pipe_iptm_vs_length.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("  Saved pipe_iptm_vs_length.png")

# ═══════════════════════════════════════════════════════════════════════
# PLOT 8: ipSAE by model
# ═══════════════════════════════════════════════════════════════════════
print("\n--- Section 4: Performance by Model ---")
model_order = ['Base', 'Beta', 'BoltzGen']
model_colors = {'Base': '#2171B5', 'Beta': '#6A51A3', 'BoltzGen': '#238B45'}
fig, ax = plt.subplots(figsize=(7, 5))
for i, mdl in enumerate(model_order):
    vals = [d['ipsae'] for d in designs if d['model'] == mdl and d['ipsae'] is not None]
    if vals:
        bp = ax.boxplot([vals], positions=[i], widths=0.5, patch_artist=True, vert=True)
        bp['boxes'][0].set_facecolor(model_colors[mdl])
        bp['boxes'][0].set_alpha(0.5)
        for el in ['whiskers', 'caps', 'medians']:
            for line in bp[el]:
                line.set_color(model_colors[mdl])
        ax.annotate(f'μ={np.mean(vals):.3f}\nn={len(vals)}', (i, np.mean(vals)),
                   fontsize=9, ha='center', va='bottom', xytext=(0, 8),
                   textcoords='offset points')
ax.set_xticks(range(len(model_order)))
ax.set_xticklabels(model_order)
ax.set_ylabel('ipSAE')
ax.set_title('ipSAE by Model Checkpoint', fontweight='normal')
fig.tight_layout()
fig.savefig(f'{outdir}/pipe_ipsae_by_model.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("  Saved pipe_ipsae_by_model.png")

# ═══════════════════════════════════════════════════════════════════════
# PLOT 9: Hit rate by face (ipSAE thresholds)
# ═══════════════════════════════════════════════════════════════════════
print("\n--- Section 5: Hit Rates ---")
thresholds = np.arange(0, 1.01, 0.05)
fig, ax = plt.subplots(figsize=(8, 5))
for face, color in palette.items():
    vals = [d['ipsae'] for d in designs if d['face'] == face and d['ipsae'] is not None]
    if vals:
        rates = [sum(1 for v in vals if v >= t) / len(vals) for t in thresholds]
        ax.plot(thresholds, rates, color=color, linewidth=2, label=f'{face} (n={len(vals)})', marker='o', markersize=3)
ax.set_xlabel('ipSAE Threshold')
ax.set_ylabel('Hit Rate (fraction above threshold)')
ax.set_title('Hit Rate by Target Face (ipSAE)', fontweight='normal')
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(f'{outdir}/pipe_hitrate_ipsae.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("  Saved pipe_hitrate_ipsae.png")

# ═══════════════════════════════════════════════════════════════════════
# PLOT 10: Hit rate by face (OF3 thresholds)
# ═══════════════════════════════════════════════════════════════════════
thresholds_of3 = np.arange(0, 1.01, 0.05)
fig, ax = plt.subplots(figsize=(8, 5))
for face, color in palette.items():
    vals = [d['of3_iptm'] for d in designs if d['face'] == face and d['of3_iptm'] is not None]
    if vals:
        rates = [sum(1 for v in vals if v >= t) / len(vals) for t in thresholds_of3]
        ax.plot(thresholds_of3, rates, color=color, linewidth=2, label=f'{face} (n={len(vals)})', marker='o', markersize=3)
ax.set_xlabel('OF3 ipTM Threshold')
ax.set_ylabel('Hit Rate (fraction above threshold)')
ax.set_title('Hit Rate by Target Face (OF3 ipTM)', fontweight='normal')
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(f'{outdir}/pipe_hitrate_of3.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("  Saved pipe_hitrate_of3.png")

# ═══════════════════════════════════════════════════════════════════════
# PLOT 11: Three-method comparison (top 20 by OF3)
# ═══════════════════════════════════════════════════════════════════════
print("\n--- Section 6: Three-method ---")
three_data = [d for d in designs if d['of3_iptm'] is not None and d['boltz_iptm'] is not None]
three_data.sort(key=lambda d: d['of3_iptm'], reverse=True)
top20 = three_data[:20]

fig, ax = plt.subplots(figsize=(14, 5))
x = np.arange(len(top20))
w = 0.25
for i, d in enumerate(top20):
    ax.bar(i - w, d['boltz_iptm'] or 0, w, color='#2171B5', alpha=0.5, label='Boltz-2' if i == 0 else '')
    ax.bar(i, d['of3_iptm'] or 0, w, color='#CB181D', alpha=0.8, label='OF3' if i == 0 else '')
    af3 = d['af3_iptm']
    if af3 is not None:
        ax.bar(i + w, af3, w, color='#238B45', alpha=0.8, label='AF3' if i == 0 else '')
    else:
        ax.bar(i + w, 0, w, color='#238B45', alpha=0.15, label='AF3 (no data)' if i == 0 else '')

short_ids = []
for d in top20:
    sid = d['id'].replace('design_', '').replace('w2_', '').replace('w1_', '').replace('w3_', '').replace('wbg_', 'bg_').replace('wcm_', 'cm_')
    short_ids.append(sid)

ax.set_xticks(x)
ax.set_xticklabels(short_ids, rotation=45, ha='right', fontsize=8)
ax.set_ylabel('ipTM')
ax.set_title('Top 20 by OF3: Boltz-2 / OF3 / AF3 Comparison', fontweight='normal')
ax.legend(fontsize=9, loc='upper right')
fig.tight_layout()
fig.savefig(f'{outdir}/pipe_three_method.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("  Saved pipe_three_method.png")

# ═══════════════════════════════════════════════════════════════════════
# Save stats for HTML legends
# ═══════════════════════════════════════════════════════════════════════
plot_stats = {
    'n_total': len(designs),
    'n_af3': len(af3_data),
    'n_af3_of3': len(af3_of3_data),
    'n_of3': len(of3_data),
    'fc1': fc1, 'r1': f"{r1:.2f}" if r1 else "N/A", 'rho1': f"{rho1:.2f}" if rho1 else "N/A",
    'fc2': fc2, 'r2': f"{r2:.2f}" if r2 else "N/A", 'rho2': f"{rho2:.2f}" if rho2 else "N/A",
    'fc3': fc3, 'r3': f"{r3:.2f}" if r3 else "N/A", 'rho3': f"{rho3:.2f}" if rho3 else "N/A",
    'face_n': {f: sum(1 for d in designs if d['face'] == f) for f in palette},
    'face_ipsae_mean': {f: f"{np.mean([d['ipsae'] for d in designs if d['face']==f and d['ipsae'] is not None]):.3f}" for f in palette},
}
with open(f'{outdir}/pipe_stats.json', 'w') as f:
    json.dump(plot_stats, f, indent=2)

print(f"\nStats: {json.dumps(plot_stats, indent=2)}")
print("\nAll plots generated successfully!")
