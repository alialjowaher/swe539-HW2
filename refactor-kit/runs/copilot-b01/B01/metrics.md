# Metrics - B01 Feature Envy - Copilot-B01

Measured with **CK** (`com.github.mauricioaniche:ck:0.7.0`) on the whole `src/main/java` tree. Before = `698b238276` (original), after = `99b5beacf7` (branch `refactor/B01`). Measured 2026-11-10 21:25 by `python kit.py metrics`.

**Classes counted:** the top-level class of every affected file (the smell's target files plus the source files the run changed), plus any other class in those files that holds a target member, is new or removed, or whose CK metrics changed.

Affected files: `HelpFormatter.java`, `Option.java`, `OptionGroup.java`

## Summary (these values are written to the Metrics sheet)

| Metric | Measure | Before | After | Change |
|---|---|---:|---:|---:|
| Size | LOC (CK loc), sum over the counted classes | 845 | 844 | -1 |
| Cohesion | LCOM* (CK lcom*, Henderson-Sellers; 0 = cohesive, 1 = no cohesion), mean over the counted classes | 0.8739 | 0.8742 | +0.0003 |
| Coupling | CBO (CK cbo), sum over the counted classes | 18 | 18 | 0 |

## Per class (before → after)

| Class | Counted | loc | wmc | cbo | rfc | lcom | lcom* | tcc | methods |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HelpFormatter | yes | 425 → 415 | 121 → 119 | 9 | 77 | 1092 | 0.9549 | 0 | 49 |
| HelpFormatter$Builder | no | 24 | 6 | 3 | 4 | 4 | 0.65 | 0 | 5 |
| HelpFormatter$OptionComparator | no | 6 | 1 | 1 | 2 | 0 | 1 | - | 1 |
| Option | yes | 357 → 373 | 86 → 92 | 6 | 37 | 836 → 897 | 0.889 → 0.8898 | 0 | 53 → 55 |
| Option$Builder | no | 98 | 27 | 5 | 7 | 146 | 0.8755 | 0 | 21 |
| OptionGroup | yes | 63 → 56 | 17 | 3 | 15 → 16 | 22 | 0.7778 | 0 | 9 |

## Per method: target members and every new, removed or changed method (before → after)

| Class | Method | Status | loc | CC (wmc) | params | cbo |
|---|---|---|---:|---:|---:|---:|
| HelpFormatter | `getDescription(Option)` | target | 4 → 3 | 2 → 1 | 1 | 1 |
| HelpFormatter | `appendOption(StringBuilder, Option, boolean)` | target | 18 → 13 | 9 | 3 | 2 |
| HelpFormatter | `appendOptions(A, int, Options, int, int)` | target | 66 → 62 | 20 → 19 | 5 | 4 |
| Option | `getDescriptionOrEmpty()` | new | - → 3 | - → 2 | - → 0 | - → 0 |
| Option | `toLabel(String, String)` | new | - → 13 | - → 4 | - → 2 | - → 0 |
| OptionGroup | `toString()` | target | 25 → 18 | 5 | 0 | 2 |

## What the CK measures mean

- **loc**: lines of code without blank lines and comments. **wmc**: for a class, the sum of the cyclomatic complexity (CC) of its methods; for a method, its CC.
- **cbo**: number of other types a class (or method) depends on. **rfc**: number of distinct methods a class can invoke (response for a class).
- **lcom**: CK's raw lack of cohesion of methods (pairs of methods sharing no field); it grows with the number of methods and CK itself calls it unreliable. **lcom\***: Henderson-Sellers' normalised version, 0 = fully cohesive, 1 = no cohesion (lower is better). **tcc**: tight class cohesion, higher is better.
- An Extract Method usually *adds* a little class loc (new signatures) and raises lcom/lcom\* (more methods) even when the long method itself becomes much simpler; the per-method table shows that effect.
