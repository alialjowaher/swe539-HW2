# Metrics - W01 Long Method - Gemini

Measured with **CK** (`com.github.mauricioaniche:ck:0.7.0`) on the whole `src/main/java` tree. Before = `698b238276` (original), after = `d1fd3cfe9c` (branch `refactor/W01`). Measured 2026-11-10 13:22 by `python kit.py metrics`.

**Classes counted:** the top-level class of every affected file (the smell's target files plus the source files the run changed), plus any other class in those files that holds a target member, is new or removed, or whose CK metrics changed.

Affected files: `HelpFormatter.java`

## Summary (these values are written to the Metrics sheet)

| Metric | Measure | Before | After | Change |
|---|---|---:|---:|---:|
| Size | LOC (CK loc), sum over the counted classes | 425 | 435 | +10 |
| Cohesion | LCOM* (CK lcom*, Henderson-Sellers; 0 = cohesive, 1 = no cohesion), mean over the counted classes | 0.9549 | 0.9567 | +0.0018 |
| Coupling | CBO (CK cbo), sum over the counted classes | 9 | 9 | 0 |

## Per class (before → after)

| Class | Counted | loc | wmc | cbo | rfc | lcom | lcom* | tcc | methods |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HelpFormatter | yes | 425 → 435 | 121 → 124 | 9 | 77 → 80 | 1092 → 1234 | 0.9549 → 0.9567 | 0 | 49 → 52 |
| HelpFormatter$Builder | no | 24 | 6 | 3 | 4 | 4 | 0.65 | 0 | 5 |
| HelpFormatter$OptionComparator | no | 6 | 1 | 1 | 2 | 0 | 1 | - | 1 |

## Per method: target members and every new, removed or changed method (before → after)

| Class | Method | Status | loc | CC (wmc) | params | cbo |
|---|---|---|---:|---:|---:|---:|
| HelpFormatter | `appendOptionRow(A, int, int, Option, StringBuilder, int, int, String, String)` | new | - → 18 | - → 7 | - → 9 | - → 3 |
| HelpFormatter | `appendOptions(A, int, Options, int, int)` | target | 66 → 29 | 20 → 7 | 5 | 4 |
| HelpFormatter | `appendSinceHeader(A, int, int, int, int, int, String)` | new | - → 6 | - → 1 | - → 7 | - → 2 |
| HelpFormatter | `buildOptionLabel(Option, String)` | new | - → 23 | - → 8 | - → 2 | - → 2 |

## What the CK measures mean

- **loc**: lines of code without blank lines and comments. **wmc**: for a class, the sum of the cyclomatic complexity (CC) of its methods; for a method, its CC.
- **cbo**: number of other types a class (or method) depends on. **rfc**: number of distinct methods a class can invoke (response for a class).
- **lcom**: CK's raw lack of cohesion of methods (pairs of methods sharing no field); it grows with the number of methods and CK itself calls it unreliable. **lcom\***: Henderson-Sellers' normalised version, 0 = fully cohesive, 1 = no cohesion (lower is better). **tcc**: tight class cohesion, higher is better.
- An Extract Method usually *adds* a little class loc (new signatures) and raises lcom/lcom\* (more methods) even when the long method itself becomes much simpler; the per-method table shows that effect.
