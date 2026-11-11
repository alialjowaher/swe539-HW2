# Metrics - W04 Long Parameter List - Copilot

Measured with **CK** (`com.github.mauricioaniche:ck:0.7.0`) on the whole `src/main/java` tree. Before = `698b238276` (original), after = `462dc8c7fb` (branch `refactor/W04`). Measured 2026-11-10 21:10 by `python kit.py metrics`.

**Classes counted:** the top-level class of every affected file (the smell's target files plus the source files the run changed), plus any other class in those files that holds a target member, is new or removed, or whose CK metrics changed.

Affected files: `HelpFormatter.java`

## Summary (these values are written to the Metrics sheet)

| Metric | Measure | Before | After | Change |
|---|---|---:|---:|---:|
| Size | LOC (CK loc), sum over the counted classes | 425 | 457 | +32 |
| Cohesion | LCOM* (CK lcom*, Henderson-Sellers; 0 = cohesive, 1 = no cohesion), mean over the counted classes | 0.9549 | 0.4792 | -0.4757 |
| Coupling | CBO (CK cbo), sum over the counted classes | 9 | 10 | +1 |

## Per class (before → after)

| Class | Counted | loc | wmc | cbo | rfc | lcom | lcom* | tcc | methods |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HelpFormatter | yes | 425 → 447 | 121 → 125 | 9 → 10 | 77 → 80 | 1092 → 1294 | 0.9549 → 0.9583 | 0 | 49 → 53 |
| HelpFormatter$Builder | no | 24 | 6 | 3 | 4 | 4 | 0.65 | 0 | 5 |
| HelpFormatter$Layout | yes | - → 10 | - → 1 | - → 0 | - → 0 | - → 0 | - → 0 | - → -1 | - → 1 |
| HelpFormatter$OptionComparator | no | 6 | 1 | 1 | 2 | 0 | 1 | - | 1 |

## Per method: target members and every new, removed or changed method (before → after)

| Class | Method | Status | loc | CC (wmc) | params | cbo |
|---|---|---|---:|---:|---:|---:|
| HelpFormatter | `appendOptions(A, int, Options, int, int)` | target | 66 → 3 | 20 → 1 | 5 | 4 |
| HelpFormatter | `appendOptions(A, Options, Layout)` | target | - → 66 | - → 20 | - → 3 | - → 5 |
| HelpFormatter | `printHelp(PrintWriter, int, String, String, Options, int, int, String)` | target | 3 | 1 | 8 | 2 |
| HelpFormatter | `printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean)` | target | 18 → 3 | 7 → 1 | 9 | 3 |
| HelpFormatter | `printHelp(PrintWriter, String, String, Options, String, boolean, Layout)` | new | - → 18 | - → 7 | - → 7 | - → 4 |
| HelpFormatter | `printOptions(PrintWriter, int, Options, int, int)` | target | 8 → 3 | 2 → 1 | 5 | 2 → 3 |
| HelpFormatter | `printOptions(PrintWriter, Options, Layout)` | target | - → 8 | - → 2 | - → 3 | - → 3 |
| HelpFormatter | `renderOptions(StringBuffer, int, Options, int, int)` | target | 8 → 3 | 2 → 1 | 5 | 2 → 3 |
| HelpFormatter | `renderOptions(StringBuffer, Options, Layout)` | target | - → 8 | - → 2 | - → 3 | - → 3 |
| HelpFormatter$Layout | `Layout(int, int, int)` | new | - → 5 | - → 1 | - → 3 | - → 0 |

## What the CK measures mean

- **loc**: lines of code without blank lines and comments. **wmc**: for a class, the sum of the cyclomatic complexity (CC) of its methods; for a method, its CC.
- **cbo**: number of other types a class (or method) depends on. **rfc**: number of distinct methods a class can invoke (response for a class).
- **lcom**: CK's raw lack of cohesion of methods (pairs of methods sharing no field); it grows with the number of methods and CK itself calls it unreliable. **lcom\***: Henderson-Sellers' normalised version, 0 = fully cohesive, 1 = no cohesion (lower is better). **tcc**: tight class cohesion, higher is better.
- An Extract Method usually *adds* a little class loc (new signatures) and raises lcom/lcom\* (more methods) even when the long method itself becomes much simpler; the per-method table shows that effect.
