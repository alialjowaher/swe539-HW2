# Metrics - B02 Shotgun Surgery - Gemini

Measured with **CK** (`com.github.mauricioaniche:ck:0.7.0`) on the whole `src/main/java` tree. Before = `698b238276` (original), after = `f7ce874c69` (branch `refactor/B02`). Measured 2026-11-11 15:09 by `python kit.py metrics`.

**Classes counted:** the top-level class of every affected file (the smell's target files plus the source files the run changed), plus any other class in those files that holds a target member, is new or removed, or whose CK metrics changed.

Affected files: `DefaultParser.java`, `MissingOptionException.java`, `Options.java`, `Parser.java`, `RequiredOptions.java`

## Summary (these values are written to the Metrics sheet)

| Metric | Measure | Before | After | Change |
|---|---|---:|---:|---:|
| Size | LOC (CK loc), sum over the counted classes | 676 | 681 | +5 |
| Cohesion | LCOM* (CK lcom*, Henderson-Sellers; 0 = cohesive, 1 = no cohesion), mean over the counted classes | 0.7285 | 0.5751 | -0.1534 |
| Coupling | CBO (CK cbo), sum over the counted classes | 32 | 34 | +2 |

## Per class (before → after)

| Class | Counted | loc | wmc | cbo | rfc | lcom | lcom* | tcc | methods |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DefaultParser | yes | 377 → 368 | 121 → 117 | 14 → 13 | 78 → 76 | 149 | 0.7968 → 0.8094 | 0 | 31 |
| DefaultParser$Builder | no | 22 | 5 | 3 | 0 | 4 | 0.6 | 0 | 5 |
| MissingOptionException | yes | 27 | 7 | 2 | 8 | 0 | 0.625 | 0 | 4 |
| Options | yes | 113 | 29 | 4 | 36 | 93 | 0.8 | 0 | 18 |
| Parser | yes | 159 → 148 | 51 → 48 | 12 → 11 | 49 → 45 | 30 → 20 | 0.6923 → 0.641 | 0 | 13 |
| RequiredOptions | yes | - → 25 | - → 8 | - → 4 | - → 7 | - → 0 | - → 0 | - → 0 | - → 4 |

## Per method: target members and every new, removed or changed method (before → after)

| Class | Method | Status | loc | CC (wmc) | params | cbo |
|---|---|---|---:|---:|---:|---:|
| DefaultParser | `checkRequiredOptions()` | target | 5 → 3 | 2 → 1 | 0 | 1 |
| DefaultParser | `parse(Options, String[], Properties, boolean)` | target | 20 → 21 | 4 | 4 | 6 |
| DefaultParser | `updateRequiredOptions(Option)` | target | 12 → 3 | 4 → 1 | 1 | 3 |
| Options | `addOption(Option)` | target | 14 | 4 | 1 | 2 |
| Options | `addOptionGroup(OptionGroup)` | target | 11 | 3 | 1 | 3 |
| Options | `getRequiredOptions()` | target | 3 | 1 | 0 | 0 |
| Parser | `checkRequiredOptions()` | target | 5 → 3 | 2 → 1 | 0 | 2 → 1 |
| Parser | `getRequiredOptions()` | target | 3 | 1 → 2 | 0 | 0 → 1 |
| Parser | `setOptions(Options)` | target | 4 | 1 | 1 | 2 |
| Parser | `updateRequiredOptions(Option)` | target | 12 → 3 | 4 → 1 | 1 | 4 |
| RequiredOptions | `RequiredOptions(Options)` | new | - → 3 | - → 1 | - → 1 | - → 1 |
| RequiredOptions | `checkAllPresent()` | new | - → 5 | - → 2 | - → 0 | - → 1 |
| RequiredOptions | `getExpectedOptions()` | new | - → 3 | - → 1 | - → 0 | - → 0 |
| RequiredOptions | `markSeen(Option, OptionGroup)` | new | - → 11 | - → 4 | - → 2 | - → 2 |

## What the CK measures mean

- **loc**: lines of code without blank lines and comments. **wmc**: for a class, the sum of the cyclomatic complexity (CC) of its methods; for a method, its CC.
- **cbo**: number of other types a class (or method) depends on. **rfc**: number of distinct methods a class can invoke (response for a class).
- **lcom**: CK's raw lack of cohesion of methods (pairs of methods sharing no field); it grows with the number of methods and CK itself calls it unreliable. **lcom\***: Henderson-Sellers' normalised version, 0 = fully cohesive, 1 = no cohesion (lower is better). **tcc**: tight class cohesion, higher is better.
- An Extract Method usually *adds* a little class loc (new signatures) and raises lcom/lcom\* (more methods) even when the long method itself becomes much simpler; the per-method table shows that effect.
