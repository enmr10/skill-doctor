# Scoring reference

Quick tuning guide for the thresholds.

## Default thresholds

| Knob | Default | Effect of raising it |
|------|---------|----------------------|
| `--merge-at` | 0.55 | Fewer, more confident MERGE recommendations |
| `--disambig-at` | 0.30 | Fewer DISAMBIGUATE noise items |
| `--collision-critical` | 0.55 | Fewer CRITICAL overlap issues |
| `--collision-high` | 0.38 | Fewer HIGH overlap issues |
| `--vague-threshold` | 0.50 | Only the vaguest descriptions flagged |

## Recommended profiles

**Strict (publishing a public pack):**
```
--collision-high 0.30 --disambig-at 0.25 --vague-threshold 0.4 --fail-on high
```

**Relaxed (large personal library, reduce noise):**
```
--collision-high 0.45 --disambig-at 0.40 --merge-at 0.65
```

**CI gate (block merges that add collisions):**
```
python3 -m scripts ./skills --format json --fail-on critical --quiet
```

## Reading the heatmap

The ASCII heatmap uses ` .:-=+*#%@` from light (0.0) to dark (0.9+). A dark
off-diagonal cell = a colliding pair. Dense dark blocks = a confusable cluster.

## Interpreting the health score

- 90–100: clean library
- 70–89: minor boundaries to add
- 50–69: real collisions; fix top clusters
- < 50: structural overlap; consider merging skill families

The score normalizes lightly by library size so a 100-skill pack isn't punished
for having more pairs than a 10-skill pack. Treat it as a trend, not a grade.
