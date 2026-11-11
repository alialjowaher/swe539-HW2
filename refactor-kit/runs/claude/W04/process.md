# Refactoring process - W04 Long Parameter List - Claude

> Written by the LLM during the run. Keep the headings and replace every _italic guidance line_ with your own text.
> Model: Claude Opus 5.5 (claude-opus-5-5) · Mode: agent · Started: 2026-11-11 09:14

## 1. Understanding of the smell
`HelpFormatter.printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean)` (HelpFormatter.java, lines 736-753) takes 9 parameters, and the 8-parameter overload at lines 717-720 exists only to forward to it. Three of those parameters, `width`, `leftPad` and `descPad`, always travel together. They describe one concept, the page layout of the help text, and the same trio appears again in `printOptions`, `renderOptions` and `appendOptions`. That makes it a Long Parameter List built around a data clump: callers have to supply and order nine loose values, and the three layout ints have no name as a unit.

## 2. Plan
Technique: **Introduce Parameter Object** (for the width/leftPad/descPad clump), plus **Preserve Whole Object** (the new internal method takes the whole layout object, not its three values). Constraints found while reading the code, which decide the scope:
- `printHelp` (all overloads), `printOptions`, `printUsage` and `printWrapped` are public, and `renderOptions` is protected. Their signatures must stay, and they are overridable hooks, so the new internal method must keep calling the same public methods in the same order.
- `HelpFormatterTest.testRenderSince` spies on the package-private `appendOptions(A, int, Options, int, int)` and expects `renderOptions` to reach it. So `appendOptions`, `renderOptions` and `printOptions` are left as they are.
- The 8-arg and 6-arg public `printHelp` overloads already call the 9-arg overload. They keep doing so, so that a subclass overriding the 9-arg method is still called.

Steps:
1. **Create the parameter object.** Add a package-private, immutable class `HelpLayout` (new file `HelpLayout.java`, same Apache license header as the other files) with `final` fields `width`, `leftPad` and `descPad`, a constructor and package-private getters. No validation in the constructor, so exception order cannot change. Compile and test.
2. **Change Function Declaration (new internal function).** Add a private method `printHelp(PrintWriter pw, HelpLayout layout, String cmdLineSyntax, String header, Options options, String footer, boolean autoUsage)` whose body copies the 9-arg body, with each use of `width`/`leftPad`/`descPad` replaced by `layout.getWidth()`/`getLeftPad()`/`getDescPad()`. It takes the whole layout object (Preserve Whole Object) and is not called yet. Compile and test.
3. **Point the caller at the new structure.** Replace the body of the public 9-arg `printHelp` with a one-line delegate `printHelp(pw, new HelpLayout(width, leftPad, descPad), cmdLineSyntax, header, options, footer, autoUsage)`. Its signature and Javadoc stay unchanged. Compile and run `HelpFormatterTest`.
4. Run the full test suite.

## 3. Steps performed
Agent mode: every step was compiled and tested with `python kit.py test --llm "Claude" --only HelpFormatterTest`, and the full suite was run at the end.

| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | New file `HelpLayout.java`: package-private final class `HelpLayout` (final fields `width`, `leftPad`, `descPad`; package-private constructor; `getWidth()`, `getLeftPad()`, `getDescPad()`). License header byte-identical to `Char.java`. | OK | HelpFormatterTest 38/38 |
| 2 | `HelpFormatter`: added private `printHelp(PrintWriter, HelpLayout, String, String, Options, String, boolean)`, a copy of the 9-arg body that reads width/leftPad/descPad from the layout object. Not called yet. | OK | HelpFormatterTest 38/38 |
| 3 | `HelpFormatter`: body of public `printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean)` replaced by the one-line delegate `printHelp(pw, new HelpLayout(width, leftPad, descPad), cmdLineSyntax, header, options, footer, autoUsage)`. Signature and Javadoc unchanged. | OK | HelpFormatterTest 38/38 |
| 4 | No code change. Full suite run. | OK | 738 passed of 797 (59 skipped), the same as the original run |

## 4. Why behaviour is preserved
- **Same statements, same order.** The private method's body is the old 9-arg body copied as-is. The only edit is that `width`, `leftPad` and `descPad` are now read through `layout.getWidth()`, `layout.getLeftPad()` and `layout.getDescPad()`. These are plain getters of `final` fields set from exactly those arguments, so every value passed on is identical. The `cmdLineSyntax` check, the `printUsage`/`printWrapped`/`printOptions` calls and both `isEmpty` guards run in the same order with the same arguments, so the printed text and the `IllegalArgumentException("cmdLineSyntax not provided")` message do not change.
- **Exception order.** The public method now creates `new HelpLayout(...)` before the `cmdLineSyntax` check runs. The constructor only assigns three ints and has no validation, so it cannot throw. An empty or null `cmdLineSyntax` still throws the same exception first, before anything is written.
- **Overridable hooks (risky spot).** `printUsage`, `printWrapped` and `printOptions` are public and can be overridden by subclasses. The internal method still calls those same public methods, unpacking the layout at the call site, and does not go to `appendOptions` directly. A subclass override therefore runs exactly as before.
- **Public overload chain (risky spot).** The 8-arg `printHelp` and the 6-arg `printHelp(int, ..., boolean)` are left untouched. They still call the public 9-arg overload, so a subclass that overrides the 9-arg method is still reached through them. Only the 9-arg body moved, behind a one-line delegate.
- **Mockito spy test (risky spot).** `HelpFormatterTest.testRenderSince` stubs `appendOptions(sb, 50, options, 2, 5)` and expects `renderOptions` to propagate the failure. `appendOptions`, `renderOptions` and `printOptions` were not changed, so that path is still exercised exactly as before.
- **API.** No public or protected member was added, removed or changed. The new method is `private` and the new class is package-private.
- **Side effects.** The method writes to the same `PrintWriter` and does not flush (flushing stays in the 6-arg caller, as before). The only extra effect is one small short-lived `HelpLayout` allocation per call.

## 5. Deviations from the plan
None. On scope: the review sheet also lists `printOptions`, `renderOptions` and `appendOptions` as places the width/leftPad/descPad clump travels through. I deliberately did not route them through `HelpLayout`. `printOptions` (public) and `renderOptions` (protected) must keep their signatures. `appendOptions` is pinned by a Mockito stub in `testRenderSince`. Also, sending the internal `printHelp` path straight to a layout-taking options renderer would skip a subclass's `printOptions` override. "Preserve Whole Object" is applied where the whole layout object can flow without a behaviour change: the internal `printHelp` takes one `HelpLayout` instead of three ints. I did not add a factory that builds a `HelpLayout` from the formatter's own `defaultWidth`/`defaultLeftPad`/`defaultDescPad` fields, because the 6-arg overload passes its own `width` argument, not `getWidth()`, and rerouting it would skip the 9-arg override. Finish attempts: 2. Attempt 1 gave **PASS** (738/797 passed, 0 regressions, 0 API changes). Its only warning was that one italic template guidance line (the one under section 3) had not been replaced in this file. No code changed after attempt 1. Attempt 2 was run only so that REPORT.md and the log contain the completed process notes.

## 6. Observations (not changed)
- The width/leftPad/descPad data clump is still in the signatures of `printOptions(PrintWriter, int, Options, int, int)`, `renderOptions(StringBuffer, int, Options, int, int)` and the package-private `appendOptions(A, int, Options, int, int)`, for the API and test reasons given in section 5. The public 8-arg and 9-arg `printHelp` overloads keep their long parameter lists because they are public API. They are now thin delegates.
- The same three values also live in the deprecated public fields `defaultWidth`, `defaultLeftPad` and `defaultDescPad`. Once those fields can be made private (as their `@deprecated` notes plan for the next major version), they could be replaced by a single `HelpLayout` field.
- The Javadoc of the `printHelp(PrintWriter, ...)` overloads says `@throws IllegalStateException if there is no room to print a line`. Nothing in `HelpFormatter` throws `IllegalStateException`, while the `IllegalArgumentException` for an empty `cmdLineSyntax` is not documented. I copied that Javadoc as-is onto the private method so it matches its source.
- A typo in the `Builder` field comment ("dispalyed") was left as is.

## 7. Self-assessment
- Smell removed: partly to mostly. The 9-parameter method body now sits behind a private 7-parameter method that takes the layout as one named object, and the public 9-arg overload is a one-line delegate. The public 8-arg and 9-arg signatures cannot shrink without breaking the API, and the clump stays on the `printOptions`/`renderOptions`/`appendOptions` path for API, test and override-dispatch reasons.
- Expected effect on size: small increase. +1 class (`HelpLayout`: 3 fields, 1 constructor, 3 getters), +1 private method in `HelpFormatter`, and about 70 more lines overall (mostly Javadoc and the license header). The public method count is unchanged, and the parameter count on the internal path drops from 9 to 7.
- Expected effect on cohesion: `HelpFormatter` LCOM may change slightly with one more method. `HelpLayout` is fully cohesive (each getter uses one field, all set in the constructor).
- Expected effect on coupling: +1. `HelpFormatter` now depends on `HelpLayout` (CBO +1 for `HelpFormatter`). `HelpLayout` depends on nothing.
