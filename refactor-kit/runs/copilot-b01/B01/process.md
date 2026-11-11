# Refactoring process - B01 Feature Envy - Copilot-B01

> Written by the LLM during the run. Keep the headings and replace every _italic guidance line_ with your own text.
> Model: Copilot SDK in VS Code (2026-11-10) · Mode: agent · Started: 2026-11-10 21:19

## 1. Understanding of the smell
HelpFormatter builds option labels and reads option descriptions in several places, while OptionGroup.toString repeats the same label construction. These methods make many decisions from Option's fields, so the display behavior is feature envy of Option. The relevant code is HelpFormatter.appendOption, appendOptions, and getDescription, plus OptionGroup.toString.

## 2. Plan
1. Extract the option label and null-safe description behavior into package-private methods on Option, and make HelpFormatter.getDescription delegate to the new description accessor.
2. Move the extracted label logic into Option usage from HelpFormatter.appendOption and appendOptions, preserving hard-coded usage prefixes and configured table prefixes.
3. Replace OptionGroup.toString's label construction with Option's package-private label method, using the null-safe description accessor without changing spacing.


## 3. Steps performed
| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | Added package-private Option.toLabel and Option.getDescriptionOrEmpty; delegated HelpFormatter.getDescription. | Passed via targeted Maven run | HelpFormatterTest, OptionGroupTest, OptionTest: 72/72 passed |
| 2 | Replaced HelpFormatter usage and table label construction with Option.toLabel, retaining hard-coded usage prefixes and configured table prefixes. | Passed via targeted Maven run | HelpFormatterTest, OptionGroupTest, OptionTest: 72/72 passed |
| 3 | Replaced OptionGroup.toString label and description reads with the Option methods while retaining its existing spacing. | Passed via targeted Maven run | HelpFormatterTest, OptionGroupTest, OptionTest: 72/72 passed |

## 4. Why behaviour is preserved
The new label method applies the same short-versus-long selection and comma formatting as the original callers. HelpFormatter.appendOption still uses literal "-" and "--", while appendOptions still passes the formatter's configured prefixes, so custom table prefixes and usage output remain distinct. The description accessor returns the same description or an empty string; callers preserve the original null checks and spacing, including OptionGroup's empty-description case.

## 5. Deviations from the plan
None.

## 6. Observations (not changed)
None.

## 7. Self-assessment
- Smell removed: yes; option label and null-safe description behavior now reside on Option.
- Expected effect on size: small reduction in duplicated label and description logic in the client classes.
- Expected effect on cohesion: HelpFormatter and OptionGroup become more focused on rendering and grouping.
- Expected effect on coupling: fewer message sends from HelpFormatter and OptionGroup to Option for label and description details; class-level coupling remains.
