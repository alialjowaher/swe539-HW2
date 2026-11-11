# Refactoring process - B02 Shotgun Surgery - Copilot

> Written by the LLM during the run. Keep the headings and replace every _italic guidance line_ with your own text.
> Model: Copilot SDK in VS Code (2026-11-10) · Mode: agent · Started: 2026-11-10 21:02

## 1. Understanding of the smell
Required-option state and its update/checking logic was duplicated across `Options`, `Parser`, and `DefaultParser`, while `MissingOptionException` consumed the resulting mixed list. This shotgun surgery meant that changing required-option tracking required coordinated edits in several classes, including near-identical parser methods.

## 2. Plan
1. Extract a package-private `RequiredOptions` class that owns the required-elements list, adding methods for registration, marking an option/group seen, and checking that all elements are present.
2. Move `Options` required-list storage and registration operations into the tracker while keeping `getRequiredOptions()` as the same read-only ordered-list API; run `OptionsTest`.
3. Move both parsers’ required state and update/check bodies to tracker delegates, retaining the protected fields/methods and their list views; run parser and option-group tests.
4. Run the full suite and record any unrelated baseline blocker without changing other smells.

## 3. Steps performed
| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | Added package-private `RequiredOptions` with required-list ownership, registration, `markSeen`, and `checkAllPresent`. | Passed as part of Maven test compile | `OptionsTest`: 15 passed |
| 2 | `Options` delegates required option/group registration and ordered read-only contents to `RequiredOptions`. | Passed | `OptionsTest`: 15 passed |
| 3 | `Parser` and `DefaultParser` delegate required state updates and checks while retaining compatibility fields/methods. | Passed | `DefaultParserTest`, `BasicParserTest`, `GnuParserTest`, `PosixParserTest`, `OptionGroupTest`: 226 passed, 59 skipped |
| 4 | Full regression run on the isolated B02 workspace. | Passed compilation | Initial run: 737 passed, 1 unrelated failure, 59 skipped. The required `finish` rerun after isolating B02 from W04 passed: 738 passed, 59 skipped, 0 failures. |

## 4. Why behaviour is preserved
`RequiredOptions` uses the same list insertion/removal rules, so `Options.getRequiredOptions()` retains its contents and order. Parser compatibility fields and protected methods remain present and delegate to the same mutable tracked list. `checkAllPresent()` still constructs `MissingOptionException` from that list, preserving the exception API, exact singular/plural wording, element `toString()` values, and ordering; group selection still occurs through `OptionGroup.setSelected`.

## 5. Deviations from the plan
The initial full suite was run while the shared workspace still contained W04 changes, which caused the `HelpFormatterTest#testRenderSince` failure. The workspace was then rebuilt from the original 1.9.0 tag with only the B02 patch; `finish` reran the original suite successfully with 738 passed and zero regressions. After `finish`, `python kit.py metrics --smell B02 --llm "Copilot"` measured the committed before/after snapshots and wrote `metrics.md` and the Metrics sheet.

## 6. Observations (not changed)
The initial shared-workspace failure demonstrated why the B02 run was rebuilt in isolation; no `HelpFormatter.java` change is part of B02. No source under `src/test/` was modified.

## 7. Self-assessment
- Smell removed: yes; required-option tracking is centralized in `RequiredOptions`.
- Expected effect on size: duplicated parser logic and state handling are reduced.
- Expected effect on cohesion: parsers no longer own the required-option tracking concern.
- Expected effect on coupling: parsers depend on one tracker abstraction rather than duplicating list/group mechanics, while compatibility delegates preserve existing callers.
