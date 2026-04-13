#!/usr/bin/env python3
"""
Parse the autonomous /loop conversation JSONL and produce a compact
JSON summary consumed by the Research Loop tab on the website.

Runs every 30 min via scripts/research_loop_daemon.sh. Output:
    data/research_loop.json
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

JSONL_PATH = Path(
    "/global/home/users/sergiomar10/.claude/projects/"
    "-global-scratch-users-sergiomar10-loop/"
    "2e33dbbd-95e9-47c0-ba56-f07f6284031d.jsonl"
)
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "research_loop.json"

MAX_UPDATES = 30          # most recent assistant text excerpts to keep
MAX_UPDATE_LEN = 900      # chars per excerpt


def flatten_text(content):
    """Extract plain text from an assistant message 'content' field."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    chunks = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            chunks.append(block.get("text", ""))
    return "\n".join(c for c in chunks if c).strip()


def classify(text):
    """Tag an update so the frontend can color / filter."""
    low = text.lower()
    tags = []
    if any(k in low for k in ("error", "traceback", "failed", "crash")):
        tags.append("error")
    if any(k in low for k in ("spearman", "rho", "ρ=", "auroc", "bootstrap")):
        tags.append("result")
    if any(k in low for k in ("skempi", "stab-ddg", "fireprot", "proteingym", "atlas", "bindinggym")):
        tags.append("dataset")
    if any(k in low for k in ("esm-2", "lora", "dpl", "cct", "potential", "adapter")):
        tags.append("model")
    if any(k in low for k in ("slurm", "sbatch", "squeue", "savio")):
        tags.append("infra")
    return tags or ["note"]


def parse_jsonl(path: Path):
    n_user = 0
    n_asst = 0
    first_ts = None
    last_ts = None
    recent_asst = []

    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = obj.get("timestamp")
            if ts:
                first_ts = first_ts or ts
                last_ts = ts

            msg = obj.get("message") or {}
            role = msg.get("role") or obj.get("type")
            if role == "user":
                n_user += 1
            elif role == "assistant":
                n_asst += 1
                text = flatten_text(msg.get("content"))
                if text and len(text) > 40:
                    recent_asst.append({"ts": ts, "text": text})
                    # Keep only a rolling tail to save memory.
                    if len(recent_asst) > MAX_UPDATES * 4:
                        recent_asst = recent_asst[-MAX_UPDATES * 2 :]

    # Keep the last MAX_UPDATES assistant excerpts, most recent first.
    recent_asst = recent_asst[-MAX_UPDATES:][::-1]
    for u in recent_asst:
        t = u["text"]
        if len(t) > MAX_UPDATE_LEN:
            t = t[:MAX_UPDATE_LEN].rstrip() + "…"
        u["text"] = t
        u["tags"] = classify(u["text"])

    return {
        "n_user_turns": n_user,
        "n_assistant_turns": n_asst,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "recent_updates": recent_asst,
    }


def build_payload(parsed: dict) -> dict:
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    project = {
        "title": "Δ-Potential Learning (ΔPL) for Protein Binding Affinity",
        "goal": (
            "Train a cycle-consistent ΔΔG predictor for protein–protein and "
            "protein–ligand interfaces."
        ),
        "algorithm": (
            "Δ-Potential Learning parameterizes ΔΔG as f(σ→σ′, c) = "
            "h(σ′, c) − h(σ, c), where h : Σ × C → ℝ is a learned scalar "
            "potential. This enforces anti-symmetry, transitivity, and "
            "reflexivity exactly by construction, rather than as soft "
            "penalties. Theoretical sample complexity drops from "
            "O(|Σ|²·d/ε²) to O(|Σ|·d/ε²)."
        ),
        "status": (
            "Late-stage evaluation blitz: ~13 SLURM jobs running in parallel "
            "on Savio (savio3_gpu, lowprio, savio2_gpu, co_nilah) across "
            "ProtAttBA folds, ProteinGym / BindingGym LoRA, FireProt transfer, "
            "and zero-shot ESM-2 / ESM-1v / ProtBert baselines. Six sub-agents "
            "are running in parallel for the comparison matrix (StaB-ddG env + "
            "launch, ESM-IF, SaProt, PPB-Affinity LoRA-DPL, ATLAS loader, "
            "Tsuboyama loader)."
        ),
    }

    model = {
        "name": "DPL + LoRA on ESM-2 650M",
        "backbone": "facebook/esm2_t33_650M_UR50D",
        "params_total": "655M",
        "params_trainable": "≈2.7M (0.4%) via LoRA r=16 on query + value",
        "context_dim": "1280-d per-residue ESM-2 features",
        "token_dim": "20-d AA one-hot for σ",
        "variants": [
            "DPL (anti-symmetric scalar potential, frozen or LoRA)",
            "UN (unconstrained regressor + cycle-consistency soft penalties)",
            "RES (residual head, within-family ablation)",
        ],
        "ablations": [
            "LoRA r=16 vs r=32 (r=16 wins: ρ=0.4928 vs 0.4882, data-limited)",
            "Frozen backbone vs LoRA adapter",
            "Identity-shuffle vs geometry-shuffle control (Q6)",
        ],
    }

    datasets = [
        {"name": "SKEMPI v2 + AB-Bind", "size": "n ≈ 7826–7899",
         "role": "Primary training, 5-fold GroupKFold-by-PDB, 5 seeds"},
        {"name": "StaB-ddG", "size": "1491 items / 81 test PDBs",
         "role": "External benchmark (cluster-split)"},
        {"name": "FireProt (curated + DB)", "size": "n ≥ 412",
         "role": "Stability transfer (5 dominant DMS scans)"},
        {"name": "ProteinGym binding", "size": "≈13 assays",
         "role": "LOAEO zero-shot + LoRA"},
        {"name": "BindingGym", "size": "16 PPI assays",
         "role": "Leave-one-assay-out (LOAEO)"},
        {"name": "S1131 (ProtAttBA)", "size": "7 folds",
         "role": "Cluster-split binding"},
        {"name": "SAbDab pair extractor v2", "size": "633 pairs / 97 antigens",
         "role": "Antibody-vs-antibody ΔΔG"},
        {"name": "ATLAS TCR–pMHC", "size": "697 entries / 919 point-mut records",
         "role": "Orthogonal benchmark with included structures"},
        {"name": "PPB-Affinity non-SKEMPI", "size": "≈3400 rows",
         "role": "Fresh out-of-domain evaluation"},
        {"name": "Tsuboyama / FireProt megascale", "size": "Zenodo 7992926",
         "role": "Large-scale stability transfer"},
    ]

    results = [
        {
            "title": "SKEMPI headline (5 seeds × 5-fold GKF, n=7826)",
            "metric": "Spearman ρ",
            "rows": [
                {"method": "DPL (frozen)",  "value": 0.4592},
                {"method": "UN (frozen)",   "value": 0.3513},
                {"method": "RES (frozen)",  "value": 0.4372},
                {"method": "DPL + LoRA OOF pooled", "value": 0.4856},
            ],
            "note": "Paired bootstrap Δρ vs UN = +0.091 [+0.042, +0.142], p < 0.0001",
        },
        {
            "title": "StaB-ddG head-to-head (leakage-corrected, n = 230)",
            "metric": "Spearman ρ",
            "rows": [
                {"method": "Original loose-OOF ensemble (LEAKED)", "value": 0.5918},
                {"method": "TP_LORA alone (strict)",               "value": 0.427},
                {"method": "StaB-ddG alone (strict)",              "value": 0.531},
                {"method": "Best ensemble α=0.3 (strict)",         "value": 0.573},
            ],
            "note": (
                "100% of StaB-ddG's 81 test PDBs have homologs in SKEMPI "
                "training at 30% identity — the original +0.59 was leakage. "
                "After strict matched-cluster correction the ensemble still "
                "beats StaB by Δρ = +0.042."
            ),
        },
        {
            "title": "Competitor baseline",
            "metric": "Spearman ρ",
            "rows": [
                {"method": "GearBind (Cai et al. 2024, Nat Commun) split-by-complex SKEMPI",
                 "value": 0.643},
            ],
            "note": "About +0.07 above our strict leakage-free ensemble — we may not be SOTA once GearBind is counted.",
        },
        {
            "title": "FireProt negative result",
            "metric": "DPL win-rate over UN",
            "rows": [
                {"method": "Singleton positions",       "value": "50%"},
                {"method": "Positions with >5 mutations", "value": "30%"},
            ],
            "note": (
                "DPL collapses to a 20×20 per-protein substitution matrix at "
                "dense positions (1PGA alone = 18.8% of items). DPL is a "
                "sparse-context regularizer — a principled failure mode, not a "
                "dataset quirk."
            ),
        },
    ]

    insights = [
        "Cycle-consistency as an inductive bias gives exact (not soft) ΔΔG physics constraints and measurably reduces variance on small datasets.",
        "Identity-shuffle vs geometry-shuffle controls cleanly audit whether 'geometric' tokens are secretly residue-identity detectors.",
        "Cluster leakage at 30% identity invalidates most ΔΔG leaderboards; GroupKFold-by-PDB alone is not enough.",
        "DPL helps when per-context mutations are sparse and hurts when they are dense — a clean, interpretable failure mode.",
        "ProteinTTT (Bushuiev 2024) and Singhal 2025 iterative distillation are the closest prior art; earlier TTT / FO-PRM framings had to be reworked.",
    ]

    return {
        "generated_at": now_iso,
        "jsonl_path": str(JSONL_PATH),
        "stats": {
            "user_turns": parsed["n_user_turns"],
            "assistant_turns": parsed["n_assistant_turns"],
            "first_ts": parsed["first_ts"],
            "last_ts": parsed["last_ts"],
        },
        "project": project,
        "model": model,
        "datasets": datasets,
        "results": results,
        "insights": insights,
        "recent_updates": parsed["recent_updates"],
    }


def main() -> int:
    if not JSONL_PATH.exists():
        print(f"missing jsonl: {JSONL_PATH}", file=sys.stderr)
        return 1
    parsed = parse_jsonl(JSONL_PATH)
    payload = build_payload(parsed)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    os.replace(tmp, OUT_PATH)
    print(f"wrote {OUT_PATH} "
          f"({parsed['n_assistant_turns']} asst / {parsed['n_user_turns']} user turns)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
