# Refactoring report - W04 Long Parameter List - Claude

| | |
|---|---|
| Smell | W04 - Long Parameter List (Within class) |
| Class / member | HelpFormatter - printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean) (lines 736–753 (also 717–720)) |
| Refactoring applied | Introduce Parameter Object; Preserve Whole Object |
| LLM / model | Claude - Claude Opus 5.5 (claude-opus-5-5) |
| Mode | agent |
| Code base | rel/commons-cli-1.9.0 (698b238276) -> branch `refactor/W04` commit 0500c0a4d6 |
| Verdict | **PASS** |
| Original tests | 738 passed of 797 (59 skipped) |
| Refactored tests | 738 passed of 797 (59 skipped) - regressions: 0 |
| Test files modified | No |
| Public/protected API | 0 removed or changed, 0 added |
| Files changed | src/main/java/org/apache/commons/cli/HelpFormatter.java (+22 -5)<br>src/main/java/org/apache/commons/cli/HelpLayout.java (+74 -0) |
| Finish attempts | 2 |

## 1. Smell (from the review sheet)

**Evidence.** 9 parameters (the overload at 717–720 has 8). Three of them, width / leftPad / descPad, travel together through printHelp (717, 736), printOptions (815), renderOptions (918) and appendOptions (407), while the class already stores the same values as fields (defaultWidth, defaultLeftPad, defaultDescPad).

**Technique:** Introduce Parameter Object; Preserve Whole Object

_Source: review sheet suggestion (column 'Suggested refactoring')._

**How (outline):** Add a small value class for the layout (width, leftPad, descPad) and route the long overloads through one internal method that takes it. Keep every public printHelp overload as a one-line delegate so the public API does not change.

**Risks to watch:** Medium. Public API: the existing overloads must stay. Output is pinned by HelpFormatterTest.

**Expected effect on metrics:** Size: parameter count on the internal path drops; public method count unchanged. Coupling: +1 (new parameter class).


## 2. Original code (before refactoring)

_Every member the refactoring changed or removed, as it was in the original code. Full files: `original/`._

### [changed] `HelpFormatter.java` > `HelpFormatter.printHelp(PrintWriter,int,String,String,Options,int,int,String,boolean)` (lines 722-753)

```java
    /**
     * Prints the help for {@code options} with the specified command line syntax.
     *
     * @param pw the writer to which the help will be written
     * @param width the number of characters to be displayed on each line
     * @param cmdLineSyntax the syntax for this application
     * @param header the banner to display at the beginning of the help
     * @param options the Options instance
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     * @param footer the banner to display at the end of the help
     * @param autoUsage whether to print an automatically generated usage statement
     * @throws IllegalStateException if there is no room to print a line
     */
    public void printHelp(final PrintWriter pw, final int width, final String cmdLineSyntax, final String header, final Options options, final int leftPad,
        final int descPad, final String footer, final boolean autoUsage) {
        if (Util.isEmpty(cmdLineSyntax)) {
            throw new IllegalArgumentException("cmdLineSyntax not provided");
        }
        if (autoUsage) {
            printUsage(pw, width, cmdLineSyntax, options);
        } else {
            printUsage(pw, width, cmdLineSyntax);
        }
        if (header != null && !header.isEmpty()) {
            printWrapped(pw, width, header);
        }
        printOptions(pw, width, options, leftPad, descPad);
        if (footer != null && !footer.isEmpty()) {
            printWrapped(pw, width, footer);
        }
    }
```

## 3. Original tests (on the untouched code)

- Result: **738 passed of 797 (59 skipped)**
- Log: `tests_original.log`

## 4. Refactoring process

> Written by the LLM during the run. Keep the headings and replace every _italic guidance line_ with your own text.
> Model: Claude Opus 5.5 (claude-opus-5-5) · Mode: agent · Started: 2026-11-11 09:14

### 1. Understanding of the smell
`HelpFormatter.printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean)` (HelpFormatter.java, lines 736-753) takes 9 parameters, and the 8-parameter overload at lines 717-720 exists only to forward to it. Three of those parameters, `width`, `leftPad` and `descPad`, always travel together. They describe one concept, the page layout of the help text, and the same trio appears again in `printOptions`, `renderOptions` and `appendOptions`. That makes it a Long Parameter List built around a data clump: callers have to supply and order nine loose values, and the three layout ints have no name as a unit.

### 2. Plan
Technique: **Introduce Parameter Object** (for the width/leftPad/descPad clump), plus **Preserve Whole Object** (the new internal method takes the whole layout object, not its three values). Constraints found while reading the code, which decide the scope:
- `printHelp` (all overloads), `printOptions`, `printUsage` and `printWrapped` are public, and `renderOptions` is protected. Their signatures must stay, and they are overridable hooks, so the new internal method must keep calling the same public methods in the same order.
- `HelpFormatterTest.testRenderSince` spies on the package-private `appendOptions(A, int, Options, int, int)` and expects `renderOptions` to reach it. So `appendOptions`, `renderOptions` and `printOptions` are left as they are.
- The 8-arg and 6-arg public `printHelp` overloads already call the 9-arg overload. They keep doing so, so that a subclass overriding the 9-arg method is still called.

Steps:
1. **Create the parameter object.** Add a package-private, immutable class `HelpLayout` (new file `HelpLayout.java`, same Apache license header as the other files) with `final` fields `width`, `leftPad` and `descPad`, a constructor and package-private getters. No validation in the constructor, so exception order cannot change. Compile and test.
2. **Change Function Declaration (new internal function).** Add a private method `printHelp(PrintWriter pw, HelpLayout layout, String cmdLineSyntax, String header, Options options, String footer, boolean autoUsage)` whose body copies the 9-arg body, with each use of `width`/`leftPad`/`descPad` replaced by `layout.getWidth()`/`getLeftPad()`/`getDescPad()`. It takes the whole layout object (Preserve Whole Object) and is not called yet. Compile and test.
3. **Point the caller at the new structure.** Replace the body of the public 9-arg `printHelp` with a one-line delegate `printHelp(pw, new HelpLayout(width, leftPad, descPad), cmdLineSyntax, header, options, footer, autoUsage)`. Its signature and Javadoc stay unchanged. Compile and run `HelpFormatterTest`.
4. Run the full test suite.

### 3. Steps performed
Agent mode: every step was compiled and tested with `python kit.py test --llm "Claude" --only HelpFormatterTest`, and the full suite was run at the end.

| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | New file `HelpLayout.java`: package-private final class `HelpLayout` (final fields `width`, `leftPad`, `descPad`; package-private constructor; `getWidth()`, `getLeftPad()`, `getDescPad()`). License header byte-identical to `Char.java`. | OK | HelpFormatterTest 38/38 |
| 2 | `HelpFormatter`: added private `printHelp(PrintWriter, HelpLayout, String, String, Options, String, boolean)`, a copy of the 9-arg body that reads width/leftPad/descPad from the layout object. Not called yet. | OK | HelpFormatterTest 38/38 |
| 3 | `HelpFormatter`: body of public `printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean)` replaced by the one-line delegate `printHelp(pw, new HelpLayout(width, leftPad, descPad), cmdLineSyntax, header, options, footer, autoUsage)`. Signature and Javadoc unchanged. | OK | HelpFormatterTest 38/38 |
| 4 | No code change. Full suite run. | OK | 738 passed of 797 (59 skipped), the same as the original run |

### 4. Why behaviour is preserved
- **Same statements, same order.** The private method's body is the old 9-arg body copied as-is. The only edit is that `width`, `leftPad` and `descPad` are now read through `layout.getWidth()`, `layout.getLeftPad()` and `layout.getDescPad()`. These are plain getters of `final` fields set from exactly those arguments, so every value passed on is identical. The `cmdLineSyntax` check, the `printUsage`/`printWrapped`/`printOptions` calls and both `isEmpty` guards run in the same order with the same arguments, so the printed text and the `IllegalArgumentException("cmdLineSyntax not provided")` message do not change.
- **Exception order.** The public method now creates `new HelpLayout(...)` before the `cmdLineSyntax` check runs. The constructor only assigns three ints and has no validation, so it cannot throw. An empty or null `cmdLineSyntax` still throws the same exception first, before anything is written.
- **Overridable hooks (risky spot).** `printUsage`, `printWrapped` and `printOptions` are public and can be overridden by subclasses. The internal method still calls those same public methods, unpacking the layout at the call site, and does not go to `appendOptions` directly. A subclass override therefore runs exactly as before.
- **Public overload chain (risky spot).** The 8-arg `printHelp` and the 6-arg `printHelp(int, ..., boolean)` are left untouched. They still call the public 9-arg overload, so a subclass that overrides the 9-arg method is still reached through them. Only the 9-arg body moved, behind a one-line delegate.
- **Mockito spy test (risky spot).** `HelpFormatterTest.testRenderSince` stubs `appendOptions(sb, 50, options, 2, 5)` and expects `renderOptions` to propagate the failure. `appendOptions`, `renderOptions` and `printOptions` were not changed, so that path is still exercised exactly as before.
- **API.** No public or protected member was added, removed or changed. The new method is `private` and the new class is package-private.
- **Side effects.** The method writes to the same `PrintWriter` and does not flush (flushing stays in the 6-arg caller, as before). The only extra effect is one small short-lived `HelpLayout` allocation per call.

### 5. Deviations from the plan
None. On scope: the review sheet also lists `printOptions`, `renderOptions` and `appendOptions` as places the width/leftPad/descPad clump travels through. I deliberately did not route them through `HelpLayout`. `printOptions` (public) and `renderOptions` (protected) must keep their signatures. `appendOptions` is pinned by a Mockito stub in `testRenderSince`. Also, sending the internal `printHelp` path straight to a layout-taking options renderer would skip a subclass's `printOptions` override. "Preserve Whole Object" is applied where the whole layout object can flow without a behaviour change: the internal `printHelp` takes one `HelpLayout` instead of three ints. I did not add a factory that builds a `HelpLayout` from the formatter's own `defaultWidth`/`defaultLeftPad`/`defaultDescPad` fields, because the 6-arg overload passes its own `width` argument, not `getWidth()`, and rerouting it would skip the 9-arg override. Finish attempts: 2. Attempt 1 gave **PASS** (738/797 passed, 0 regressions, 0 API changes). Its only warning was that one italic template guidance line (the one under section 3) had not been replaced in this file. No code changed after attempt 1. Attempt 2 was run only so that REPORT.md and the log contain the completed process notes.

### 6. Observations (not changed)
- The width/leftPad/descPad data clump is still in the signatures of `printOptions(PrintWriter, int, Options, int, int)`, `renderOptions(StringBuffer, int, Options, int, int)` and the package-private `appendOptions(A, int, Options, int, int)`, for the API and test reasons given in section 5. The public 8-arg and 9-arg `printHelp` overloads keep their long parameter lists because they are public API. They are now thin delegates.
- The same three values also live in the deprecated public fields `defaultWidth`, `defaultLeftPad` and `defaultDescPad`. Once those fields can be made private (as their `@deprecated` notes plan for the next major version), they could be replaced by a single `HelpLayout` field.
- The Javadoc of the `printHelp(PrintWriter, ...)` overloads says `@throws IllegalStateException if there is no room to print a line`. Nothing in `HelpFormatter` throws `IllegalStateException`, while the `IllegalArgumentException` for an empty `cmdLineSyntax` is not documented. I copied that Javadoc as-is onto the private method so it matches its source.
- A typo in the `Builder` field comment ("dispalyed") was left as is.

### 7. Self-assessment
- Smell removed: partly to mostly. The 9-parameter method body now sits behind a private 7-parameter method that takes the layout as one named object, and the public 9-arg overload is a one-line delegate. The public 8-arg and 9-arg signatures cannot shrink without breaking the API, and the clump stays on the `printOptions`/`renderOptions`/`appendOptions` path for API, test and override-dispatch reasons.
- Expected effect on size: small increase. +1 class (`HelpLayout`: 3 fields, 1 constructor, 3 getters), +1 private method in `HelpFormatter`, and about 70 more lines overall (mostly Javadoc and the license header). The public method count is unchanged, and the parameter count on the internal path drops from 9 to 7.
- Expected effect on cohesion: `HelpFormatter` LCOM may change slightly with one more method. `HelpLayout` is fully cohesive (each getter uses one field, all set in the constructor).
- Expected effect on coupling: +1. `HelpFormatter` now depends on `HelpLayout` (CBO +1 for `HelpFormatter`). `HelpLayout` depends on nothing.

## 5. Refactored code (after refactoring)

_The same members after the refactoring, plus any new members or files. Full files: `refactored/`; diff: `changes.patch`._

### [changed] `HelpFormatter.java` > `HelpFormatter.printHelp(PrintWriter,int,String,String,Options,int,int,String,boolean)` (lines 722-739)

```java
    /**
     * Prints the help for {@code options} with the specified command line syntax.
     *
     * @param pw the writer to which the help will be written
     * @param width the number of characters to be displayed on each line
     * @param cmdLineSyntax the syntax for this application
     * @param header the banner to display at the beginning of the help
     * @param options the Options instance
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     * @param footer the banner to display at the end of the help
     * @param autoUsage whether to print an automatically generated usage statement
     * @throws IllegalStateException if there is no room to print a line
     */
    public void printHelp(final PrintWriter pw, final int width, final String cmdLineSyntax, final String header, final Options options, final int leftPad,
        final int descPad, final String footer, final boolean autoUsage) {
        printHelp(pw, new HelpLayout(width, leftPad, descPad), cmdLineSyntax, header, options, footer, autoUsage);
    }
```

### [new] `HelpFormatter.java` > `HelpFormatter.printHelp(PrintWriter,HelpLayout,String,String,Options,String,boolean)` (lines 741-770)

```java
    /**
     * Prints the help for {@code options} with the specified command line syntax, using the given page layout.
     *
     * @param pw the writer to which the help will be written
     * @param layout the line width, left padding and description padding to use
     * @param cmdLineSyntax the syntax for this application
     * @param header the banner to display at the beginning of the help
     * @param options the Options instance
     * @param footer the banner to display at the end of the help
     * @param autoUsage whether to print an automatically generated usage statement
     * @throws IllegalStateException if there is no room to print a line
     */
    private void printHelp(final PrintWriter pw, final HelpLayout layout, final String cmdLineSyntax, final String header, final Options options,
        final String footer, final boolean autoUsage) {
        if (Util.isEmpty(cmdLineSyntax)) {
            throw new IllegalArgumentException("cmdLineSyntax not provided");
        }
        if (autoUsage) {
            printUsage(pw, layout.getWidth(), cmdLineSyntax, options);
        } else {
            printUsage(pw, layout.getWidth(), cmdLineSyntax);
        }
        if (header != null && !header.isEmpty()) {
            printWrapped(pw, layout.getWidth(), header);
        }
        printOptions(pw, layout.getWidth(), options, layout.getLeftPad(), layout.getDescPad());
        if (footer != null && !footer.isEmpty()) {
            printWrapped(pw, layout.getWidth(), footer);
        }
    }
```

### [new file] `HelpLayout.java` > `(whole file)` (lines 1-75)

```java
/*
  Licensed to the Apache Software Foundation (ASF) under one or more
  contributor license agreements.  See the NOTICE file distributed with
  this work for additional information regarding copyright ownership.
  The ASF licenses this file to You under the Apache License, Version 2.0
  (the "License"); you may not use this file except in compliance with
  the License.  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
 */

package org.apache.commons.cli;

/**
 * Package-private, immutable layout of a help page: the line width, the left padding and the description padding used by
 * {@link HelpFormatter} when it prints help.
 */
final class HelpLayout {

    /** The number of characters to be displayed on each line. */
    private final int width;

    /** The number of characters of padding to be prefixed to each line. */
    private final int leftPad;

    /** The number of characters of padding to be prefixed to each description line. */
    private final int descPad;

    /**
     * Constructs a new layout.
     *
     * @param width the number of characters to be displayed on each line
     * @param leftPad the number of characters of padding to be prefixed to each line
     * @param descPad the number of characters of padding to be prefixed to each description line
     */
    HelpLayout(final int width, final int leftPad, final int descPad) {
        this.width = width;
        this.leftPad = leftPad;
        this.descPad = descPad;
    }

    /**
     * Gets the number of characters of padding to be prefixed to each description line.
     *
     * @return the description padding
     */
    int getDescPad() {
        return descPad;
    }

    /**
     * Gets the number of characters of padding to be prefixed to each line.
     *
     * @return the left padding
     */
    int getLeftPad() {
        return leftPad;
    }

    /**
     * Gets the number of characters to be displayed on each line.
     *
     * @return the line width
     */
    int getWidth() {
        return width;
    }
}
```

## 6. Original tests on the refactored code

- Result: **738 passed of 797 (59 skipped)**
- Regressions (passed before, not now): **0**
- Log: `tests_refactored.log`

| Test class | Original (passed/total) | Refactored (passed/total) |
|---|---|---|
| AlreadySelectedExceptionTest | 1/1 | 1/1 |
| ApplicationTest | 5/5 | 5/5 |
| ArgumentIsOptionTest | 3/3 | 3/3 |
| BasicParserTest | 39/66 | 39/66 |
| BugCLI133Test | 1/1 | 1/1 |
| BugCLI13Test | 1/1 | 1/1 |
| BugCLI148Test | 2/2 | 2/2 |
| BugCLI162Test | 4/4 | 4/4 |
| BugCLI18Test | 1/1 | 1/1 |
| BugCLI252Test | 2/2 | 2/2 |
| BugCLI265Test | 3/3 | 3/3 |
| BugCLI266Test | 2/2 | 2/2 |
| BugCLI312Test | 3/3 | 3/3 |
| BugCLI325Test | 1/1 | 1/1 |
| BugCLI71Test | 4/4 | 4/4 |
| BugsTest | 13/13 | 13/13 |
| CommandLineTest | 121/121 | 121/121 |
| ConverterTests | 14/14 | 14/14 |
| DefaultParserTest | 74/74 | 74/74 |
| DeprecatedAttributesTest | 4/4 | 4/4 |
| DisablePartialMatchingTest | 2/2 | 2/2 |
| GnuParserTest | 44/66 | 44/66 |
| HelpFormatterTest | 38/38 | 38/38 |
| OptionBuilderTest | 9/9 | 9/9 |
| OptionGroupTest | 13/13 | 13/13 |
| OptionTest | 21/21 | 21/21 |
| OptionValidatorTest | 115/115 | 115/115 |
| OptionsTest | 15/15 | 15/15 |
| ParseExceptionTest | 1/1 | 1/1 |
| PatternOptionBuilderTest | 10/10 | 10/10 |
| PosixParserTest | 56/66 | 56/66 |
| SolrCliTest | 1/1 | 1/1 |
| SolrCreateToolTest | 2/2 | 2/2 |
| TypeHandlerTest | 63/63 | 63/63 |
| UnrecognizedOptionExceptionTest | 1/1 | 1/1 |
| UtilTest | 2/2 | 2/2 |
| ValueTest | 40/40 | 40/40 |
| ValuesTest | 7/7 | 7/7 |

## 7. Checks

- Test files untouched: yes
- Other non-source files changed: none
- Public/protected API removed or changed: 0
- Public/protected API added: 0

## 8. Files in this run folder

| File | What it is |
|---|---|
| `PROMPT_master.md` | the unified prompt (master copy at start) |
| `TASK.md / CHAT_PROMPT.md` | the run-specific task given to the LLM (agent / chat mode) |
| `response*.md` | the LLM's reply / transcript (saved by you) |
| `process.md` | the refactoring process written by the LLM |
| `original/` | original versions of every involved file |
| `original_smell_location.java.txt` | original code of the smell location |
| `refactored/` | refactored versions of every changed file |
| `changes.patch` | unified diff against the original |
| `code_changes.json` | member-by-member before/after |
| `tests_original.json/.log` | original test suite on the original code |
| `tests_refactored.json/.log` | original test suite on the refactored code |
| `api_original.txt / api_refactored.txt / api_diff.txt` | public/protected API comparison |
| `run.json` | run metadata |
