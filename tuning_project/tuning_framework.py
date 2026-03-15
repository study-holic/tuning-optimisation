"""
Tuning as Optimisation: Framework and MIDI Analysis Tool
========================================================

A complete implementation of the temperament evaluation framework,
MIDI-based weight induction, and harmonic similarity metric described in:

    "Tuning as Optimisation: A Quantitative Analysis of Equal and 
     Non-Equal Temperaments" — William Odumosu, 2026.

Usage:
    python tuning_framework.py analyse <file.mid>
    python tuning_framework.py compare <a.mid> <b.mid>

Dependencies:
    pip install mido numpy
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from collections import Counter


# =========================================================
# Core definitions
# =========================================================

def cents(ratio: float) -> float:
    """Convert a frequency ratio to cents."""
    return 1200.0 * math.log(ratio, 2)


@dataclass(frozen=True)
class Target:
    name: str       # e.g. "M3"
    full_name: str  # e.g. "Major third"
    ratio: float    # e.g. 5/4
    semitones: int  # interval in semitones (for MIDI matching)


TARGETS = [
    Target("m2", "Minor second",    16/15, 1),
    Target("M2", "Major second",    9/8,   2),
    Target("m3", "Minor third",     6/5,   3),
    Target("M3", "Major third",     5/4,   4),
    Target("P4", "Perfect fourth",  4/3,   5),
    Target("TT", "Tritone",         7/5,   6),
    Target("P5", "Perfect fifth",   3/2,   7),
    Target("m6", "Minor sixth",     8/5,   8),
    Target("M6", "Major sixth",     5/3,   9),
    Target("m7", "Minor seventh",   9/5,  10),
    Target("M7", "Major seventh",  15/8,  11),
]

TARGET_NAMES = [t.name for t in TARGETS]


# =========================================================
# Temperament evaluation
# =========================================================

def nearest_et(c_just: float, n: int) -> Tuple[int, float]:
    """Find nearest n-TET step to a just-intonation value."""
    step = 1200.0 / n
    k = round(c_just / step)
    return k, k * step


def compute_errors(n: int) -> List[Tuple[str, float, int, float, float]]:
    """Compute interval errors for n-TET."""
    rows = []
    for t in TARGETS:
        c_just = cents(t.ratio)
        k, c_et = nearest_et(c_just, n)
        err = abs(c_et - c_just)
        rows.append((t.name, c_just, k, c_et, err))
    return rows


def aggregate(rows, weights: Dict[str, float] = None):
    """Compute E1, E2, E_inf under given weights."""
    if weights is None:
        weights = {}
    errors = []
    for name, c_just, k, c_et, err in rows:
        w = weights.get(name, 1.0)
        errors.append((w, err))
    E1 = sum(w * err for w, err in errors)
    E2 = sum(w * (err ** 2) for w, err in errors)
    Einf = max(err for _, err in errors)
    return E1, E2, Einf


# Predefined weighting schemes
WEIGHT_UNIFORM = {}
WEIGHT_FIFTHS = {"P4": 4.0, "P5": 4.0}
WEIGHT_THIRDS = {"m3": 4.0, "M3": 4.0}
WEIGHT_TRIADIC = {
    "m3": 3.0, "M3": 3.0, "P4": 3.0,
    "P5": 3.0, "m6": 3.0, "M6": 3.0
}


# =========================================================
# MIDI analysis and weight induction
# =========================================================

def extract_intervals_from_midi(
    midi_path: str,
    time_resolution: float = 0.05
) -> Counter:
    """
    Parse a MIDI file and extract interval content.
    
    At each time step, identify all sounding notes,
    compute all pairwise intervals (mod 12 semitones),
    and accumulate counts.
    """
    import mido
    mid = mido.MidiFile(midi_path)
    
    interval_counts = Counter()
    events = []
    
    for track in mid.tracks:
        tick = 0
        for msg in track:
            tick += msg.time
            events.append((tick, msg))
    
    events.sort(key=lambda x: x[0])
    
    ticks_per_beat = mid.ticks_per_beat
    current_notes = {}
    event_idx = 0
    max_tick = max(t for t, _ in events) if events else 0
    tick_step = int(ticks_per_beat * time_resolution * 2)
    if tick_step < 1:
        tick_step = 1
    
    for sample_tick in range(0, max_tick + 1, tick_step):
        while event_idx < len(events) and events[event_idx][0] <= sample_tick:
            _, msg = events[event_idx]
            if msg.type == 'note_on' and msg.velocity > 0:
                current_notes[msg.note] = msg.velocity
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                current_notes.pop(msg.note, None)
            event_idx += 1
        
        pitches = sorted(current_notes.keys())
        if len(pitches) >= 2:
            for i in range(len(pitches)):
                for j in range(i + 1, len(pitches)):
                    interval = (pitches[j] - pitches[i]) % 12
                    if 1 <= interval <= 11:
                        interval_counts[interval] += 1
    
    return interval_counts


def induce_weights(
    interval_counts: Counter,
    normalise: bool = True
) -> Dict[str, float]:
    """Convert interval semitone counts to target weights."""
    weights = {}
    for t in TARGETS:
        count = interval_counts.get(t.semitones, 0)
        weights[t.name] = float(count)
    
    if normalise and sum(weights.values()) > 0:
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}
    
    return weights


def analyse_midi(midi_path: str, temperaments=(12, 19, 31)):
    """Full pipeline: MIDI -> intervals -> weights -> evaluation."""
    counts = extract_intervals_from_midi(midi_path)
    weights = induce_weights(counts, normalise=False)
    norm_weights = induce_weights(counts, normalise=True)
    
    results = {"weights": norm_weights, "raw_counts": dict(counts)}
    
    for n in temperaments:
        rows = compute_errors(n)
        E1, E2, Einf = aggregate(rows, weights)
        results[f"{n}-TET"] = {"E1": E1, "E2": E2, "Einf": Einf}
    
    return results


# =========================================================
# Harmonic similarity
# =========================================================

def harmonic_weight_vector(midi_path: str) -> np.ndarray:
    """Extract normalised harmonic weight vector from a MIDI file."""
    counts = extract_intervals_from_midi(midi_path)
    weights = induce_weights(counts, normalise=True)
    return np.array([weights.get(t.name, 0.0) for t in TARGETS])


def harmonic_similarity(path_a: str, path_b: str) -> float:
    """
    Cosine similarity between harmonic weight vectors.
    Returns a value in [0, 1].
    """
    va = harmonic_weight_vector(path_a)
    vb = harmonic_weight_vector(path_b)
    
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(np.dot(va, vb) / (norm_a * norm_b))


def similarity_percentage(path_a: str, path_b: str) -> str:
    """Human-readable similarity."""
    s = harmonic_similarity(path_a, path_b)
    return f"{s * 100:.1f}% harmonically similar"


# =========================================================
# CLI
# =========================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Tuning as Optimisation — Framework & MIDI Analysis Tool")
        print("=" * 55)
        print()
        print("Usage:")
        print("  python tuning_framework.py analyse <file.mid>")
        print("  python tuning_framework.py compare <a.mid> <b.mid>")
        print("  python tuning_framework.py errors [n]")
        print()
        print("Commands:")
        print("  analyse  — Extract harmonic weights and evaluate temperaments")
        print("  compare  — Compute harmonic similarity between two pieces")
        print("  errors   — Print interval errors for n-TET (default: 12, 19, 31)")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "analyse" and len(sys.argv) >= 3:
        path = sys.argv[2]
        results = analyse_midi(path)
        
        print(f"\nHarmonic weight vector for: {path}")
        print("-" * 55)
        for name in TARGET_NAMES:
            t = next(t for t in TARGETS if t.name == name)
            w = results["weights"].get(name, 0)
            bar = "#" * int(w * 100)
            print(f"  {name:>3s} ({t.full_name:<16s}): {w:.4f}  {bar}")
        
        print(f"\nTemperament evaluation (piece-induced weights):")
        print(f"{'TET':>6s}  {'E1':>10s}  {'E2':>12s}  {'E_inf':>8s}")
        print("-" * 42)
        for n in [12, 19, 31]:
            r = results[f"{n}-TET"]
            print(f"{n:>3d}-TET  {r['E1']:>10.2f}  {r['E2']:>12.2f}  {r['Einf']:>8.2f}")
    
    elif command == "compare" and len(sys.argv) >= 4:
        path_a, path_b = sys.argv[2], sys.argv[3]
        va = harmonic_weight_vector(path_a)
        vb = harmonic_weight_vector(path_b)
        
        print(f"\nComparing harmonic profiles:")
        print(f"  A: {path_a}")
        print(f"  B: {path_b}")
        print()
        print(f"  {'Interval':>10s}  {'A':>8s}  {'B':>8s}")
        print("  " + "-" * 30)
        for i, t in enumerate(TARGETS):
            print(f"  {t.name:>10s}  {va[i]:>8.4f}  {vb[i]:>8.4f}")
        print()
        print(f"  Result: {similarity_percentage(path_a, path_b)}")
    
    elif command == "errors":
        ns = [int(x) for x in sys.argv[2:]] if len(sys.argv) > 2 else [12, 19, 31]
        for n in ns:
            rows = compute_errors(n)
            print(f"\n=== {n}-TET (step = {1200/n:.2f} cents) ===")
            print(f"{'Interval':>10s}  {'Just':>8s}  {'Steps':>5s}  {'Tempered':>8s}  {'Error':>8s}")
            print("-" * 45)
            for name, c_just, k, c_et, err in rows:
                print(f"{name:>10s}  {c_just:>8.2f}  {k:>5d}  {c_et:>8.2f}  {err:>8.2f}")
            
            print(f"\nAggregate errors:")
            for label, W in [("uniform", WEIGHT_UNIFORM), ("fifths", WEIGHT_FIFTHS),
                             ("thirds", WEIGHT_THIRDS), ("triadic", WEIGHT_TRIADIC)]:
                E1, E2, Einf = aggregate(rows, W)
                print(f"  {label:>8s}: E1={E1:.2f}, E2={E2:.2f}, Einf={Einf:.2f}")
    
    else:
        print("Unknown command. Use 'analyse', 'compare', or 'errors'.")
