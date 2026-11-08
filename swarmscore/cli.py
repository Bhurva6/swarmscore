#!/usr/bin/env python3
"""Score a transcript: swarmscore <transcript.jsonl> [--window 1800] [--step 900]

Prints a per-window risk table and every fired flag with its evidence.
"""

from __future__ import annotations

import argparse
import sys

from .features import make_windows, window_features
from .ingest import read_jsonl
from .score import score_window, band_for
from .detect import detect_all


def main(argv=None):
    p = argparse.ArgumentParser(prog="swarmscore")
    p.add_argument("transcript", help="JSONL transcript in the canonical schema (see ingest.py)")
    p.add_argument("--window", type=float, default=1800, help="window size in seconds")
    p.add_argument("--step", type=float, default=900, help="window step in seconds")
    p.add_argument("--min-score", type=float, default=0.0, help="only print windows at or above this score")
    args = p.parse_args(argv)

    events = list(read_jsonl(args.transcript))
    if not events:
        print("no events found", file=sys.stderr)
        return 1

    wins = make_windows(events, args.window, args.step)
    print(f"{len(events)} events, {len(wins)} windows (window={args.window}s step={args.step}s)\n")
    worst = 0.0
    for w in wins:
        feats = window_features(w)
        sc, contrib = score_window(feats)
        worst = max(worst, sc)
        if sc < args.min_score:
            continue
        band = band_for(sc)
        print(f"[{band:8s}] {sc:5.1f}  window {w.start:.0f}..{w.end:.0f}  "
              f"({feats['events']:.0f} events, {feats['agents']:.0f} agents)")
        if contrib:
            top = sorted(contrib.items(), key=lambda kv: -kv[1])[:4]
            print("           why: " + ", ".join(f"{k}={v}" for k, v in top))
        for flag in detect_all(feats):
            print(f"           flag: {flag.name} ({flag.severity}) - {flag.detail}")
    print(f"\nworst window score: {worst:.1f} ({band_for(worst)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
