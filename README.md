# Tuning as Optimisation

A framework for evaluating musical tuning systems as solutions to explicit optimisation problems, with MIDI-based harmonic analysis and a similarity metric for comparing compositions.

Companion code for the paper:

> **Tuning as Optimisation: A Quantitative Analysis of Equal and Non-Equal Temperaments**
> William Odumosu, (2026)
> [doi.org/10.5281/zenodo.19026923](https://doi.org/10.5281/zenodo.19026923)

## What this does

Most discussions of musical temperament describe 12-tone equal temperament (12-TET) as the "best compromise" without ever specifying what is being optimised. This tool makes the comparison precise.

Given a set of just-intonation targets, it:

- Computes interval-specific approximation errors for any n-TET system
- Aggregates errors under L1, L2, and L-infinity norms with configurable weighting schemes
- Parses MIDI files to extract harmonic content and induce piece-specific weights
- Evaluates temperaments under those induced weights
- Compares pieces via a cosine-similarity-based harmonic similarity metric

## Setup

```
pip install mido numpy
```

## Usage

### Evaluate temperament errors

```
python tuning_framework.py errors
```

Prints interval-by-interval errors and aggregate scores for 12-TET, 19-TET, and 31-TET under uniform, fifth-prioritised, third-prioritised, and triadic weightings.

You can also specify custom values of n:

```
python tuning_framework.py errors 12 19 31 53
```

### Analyse a MIDI file

```
python tuning_framework.py analyse bach_bwv846.mid
```

Extracts the harmonic weight vector from the piece and evaluates 12-TET, 19-TET, and 31-TET under the induced weights. Output includes the normalised weight for each interval and the aggregate E1, E2, and E-infinity scores.

### Compare two pieces

```
python tuning_framework.py compare piece_a.mid piece_b.mid
```

Computes cosine similarity between the harmonic weight vectors of two MIDI files. A result of 100% means identical harmonic profiles; lower values mean the pieces make different demands on the tuning system.

## Example output

```
$ python tuning_framework.py analyse bach_bwv846.mid

Harmonic weight vector for: bach_bwv846.mid
-------------------------------------------------------
   m2 (Minor second    ): 0.0231  ##
   M2 (Major second    ): 0.0601  ######
   m3 (Minor third     ): 0.1898  ##################
   M3 (Major third     ): 0.1474  ##############
   P4 (Perfect fourth  ): 0.1102  ###########
   TT (Tritone         ): 0.0566  #####
   P5 (Perfect fifth   ): 0.1484  ##############
   m6 (Minor sixth     ): 0.0778  #######
   M6 (Major sixth     ): 0.1163  ###########
   m7 (Minor seventh   ): 0.0596  #####
   M7 (Major seventh   ): 0.0107  #

Temperament evaluation (piece-induced weights):
   TET          E1            E2     E_inf
------------------------------------------
 12-TET    69441.73    1002097.31     17.60
 19-TET    38669.11     374899.90     14.58
 31-TET    30700.22     205444.36     11.14
```

## How it works

**Interval errors**: For an n-TET system with step size 1200/n cents, each just-intonation target is approximated by the nearest available step. The error is the absolute difference in cents.

**Loss functions**: Individual errors are aggregated using weighted L1 (total impurity), weighted L2 (penalises large deviations), or L-infinity (worst single interval).

**Weighting schemes**: Four predefined schemes (uniform, fifth-prioritised, third-prioritised, triadic) reflect different musical traditions. The MIDI analyser induces weights directly from a piece's harmonic content.

**Harmonic similarity**: Two pieces are compared by computing cosine similarity between their normalised weight vectors. This captures whether they make similar demands on the tuning system, independent of length or key.

## File structure

```
tuning_framework.py    Main implementation (framework, MIDI analysis, similarity)
requirements.txt       Python dependencies
bach_bwv846.mid        Example MIDI file (Bach WTC I, Prelude in C major)
```

## Citation

```bibtex
@misc{odumosu2026tuning,
  author    = {Odumosu, William},
  title     = {Tuning as Optimisation: A Quantitative Analysis of Equal and Non-Equal Temperaments},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.19026923}
}
```

## License

CC BY 4.0
