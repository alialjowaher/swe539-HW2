# Refactoring report - W04 Long Parameter List - Gemini

| | |
|---|---|
| Smell | W04 - Long Parameter List (Within class) |
| Class / member | HelpFormatter - printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean) (lines 736–753 (also 717–720)) |
| Refactoring applied | Introduce Parameter Object; Preserve Whole Object |
| LLM / model | Gemini - Gemini 3.1 Pro |
| Mode | agent |
| Code base | rel/commons-cli-1.9.0 (698b238276) -> branch `refactor/W04` commit ccac47bb9c |
| Verdict | **PASS** |
| Original tests | 738 passed of 797 (59 skipped) |
| Refactored tests | 738 passed of 797 (59 skipped) - regressions: 0 |
| Test files modified | No |
| Public/protected API | 0 removed or changed, 0 added |
| Files changed | src/main/java/org/apache/commons/cli/HelpFormatter.java (+43 -15)<br>src/main/java/org/apache/commons/cli/HelpLayout.java (+73 -0) |
| Finish attempts | 1 |

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
> Model: Gemini 3.1 Pro · Mode: agent · Started: 2026-11-11 10:05

### 1. Understanding of the smell
In `HelpFormatter.java`, `printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean)` (lines 736–753) takes 9 parameters, and its overload at lines 717–720 takes 8 parameters. Three of those parameters (`width`, `leftPad`, and `descPad`) form a recurring data clump representing layout dimensions that travel together through `printHelp`, `printOptions` (line 815), `renderOptions` (line 918), and `appendOptions` (line 407), even though `HelpFormatter` already holds default values for these three layout properties (`defaultWidth`, `defaultLeftPad`, `defaultDescPad`). This makes the parameter lists overly long and harder to read and maintain (Long Parameter List).

### 2. Plan
1. **Introduce Parameter Object (`HelpLayout`):** Create a package-private immutable value class `HelpLayout` in `org.apache.commons.cli` encapsulating `width`, `leftPad`, and `descPad` with final fields, a constructor, and package-private getters (`getWidth()`, `getLeftPad()`, `getDescPad()`). Compile and run `HelpFormatterTest`.
2. **Change Function Declaration / Preserve Whole Object on `printHelp` and `printOptions`:** Add an internal helper `printOptions(PrintWriter, Options, HelpLayout)` that preserves the whole `HelpLayout` object and delegates to the public 5-argument `printOptions` (preserving subclass override hooks), and add a private `printHelp(PrintWriter, HelpLayout, String, String, Options, String, boolean)` method that accepts `HelpLayout` instead of the three separate layout integers. Compile and run `HelpFormatterTest`.
3. **Route the long `printHelp` overload through the parameter-object method:** Replace the body of the 9-parameter `printHelp` overload with a one-line delegation call `printHelp(pw, new HelpLayout(width, leftPad, descPad), cmdLineSyntax, header, options, footer, autoUsage)` (while the 8-parameter `printHelp` overload remains a one-line delegate to the 9-parameter overload). Compile and run `HelpFormatterTest` and the full test suite.

### 3. Steps performed

| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | Added `HelpLayout.java` (`HelpLayout` constructor, `getWidth()`, `getLeftPad()`, `getDescPad()`) | OK | `HelpFormatterTest` 38/38 passed |
| 2 | Added private `HelpFormatter.printHelp(PrintWriter, HelpLayout, String, String, Options, String, boolean)` and private `HelpFormatter.printOptions(PrintWriter, Options, HelpLayout)` | OK | `HelpFormatterTest` 38/38 passed |
| 3 | Updated `HelpFormatter.printHelp(PrintWriter, int, String, String, Options, int, int, String, boolean)` to delegate to the `HelpLayout` overload | OK | `HelpFormatterTest` 38/38 passed; full suite 738/797 passed (59 skipped) |

### 4. Why behaviour is preserved
- **Public and protected API unchanged:** Every existing `printHelp`, `printOptions`, and `renderOptions` overload retains its exact signature, visibility, and modifiers.
- **Identical control flow and exceptions:** `new HelpLayout(width, leftPad, descPad)` performs only three field assignments and cannot throw; `printHelp(PrintWriter, HelpLayout, ...)` immediately checks `Util.isEmpty(cmdLineSyntax)` and throws the same `IllegalArgumentException("cmdLineSyntax not provided")` when empty, then invokes `printUsage`, `printWrapped`, and `printOptions` in the exact same order with the exact same `width`, `leftPad`, and `descPad` values.
- **Subclass and Mockito spy compatibility:** `printOptions(PrintWriter, Options, HelpLayout)` delegates to the public `printOptions(PrintWriter, int, Options, int, int)`, ensuring any subclass override of `printOptions`, `renderOptions`, or package-private `appendOptions` (such as the Mockito spy in `HelpFormatterTest.testRenderSince`) continues to be invoked identically.

### 5. Deviations from the plan
None

### 6. Observations (not changed)
- The Javadoc on the 8-argument and 9-argument `printHelp(PrintWriter, ...)` methods declares `@throws IllegalStateException if there is no room to print a line`, which is never thrown, while omitting `@throws IllegalArgumentException` when `cmdLineSyntax` is null or empty.
- `HelpFormatter` still stores mutable default layout fields (`defaultWidth`, `defaultLeftPad`, `defaultDescPad`), which are noted in a `Builder` TODO for 2.0 immutability.

### 7. Self-assessment
- Smell removed: partly — the internal `printHelp` implementation and `printOptions` call path now accept a `HelpLayout` parameter object (reducing the internal `printHelp` parameter count from 9 to 7 and grouping the `width`/`leftPad`/`descPad` clump), while the public 8- and 9-parameter `printHelp` overloads and `printOptions`/`renderOptions`/`appendOptions` signatures remain in place as required to preserve the public/protected API and test spies.
- Expected effect on size: Slight increase in total LOC due to the new `HelpLayout` parameter class and delegating methods, while reducing parameter count on the internal `printHelp` method from 9 to 7.
- Expected effect on cohesion: Improved mean cohesion (lower LCOM*) across the affected classes because `HelpLayout` is a cohesive value class encapsulating the three layout fields.
- Expected effect on coupling: Slight increase (+1 CBO on `HelpFormatter`) due to the reference to the new `HelpLayout` parameter object class.

## 5. Refactored code (after refactoring)

_The same members after the refactoring, plus any new members or files. Full files: `refactored/`; diff: `changes.patch`._

### [new] `HelpFormatter.java` > `HelpFormatter.printHelp(PrintWriter,HelpLayout,String,String,Options,String,boolean)` (lines 703-732)

```java
    /**
     * Prints the help for {@code options} with the specified command line syntax and layout.
     *
     * @param pw the writer to which the help will be written
     * @param layout the layout configuration (width, leftPad, descPad)
     * @param cmdLineSyntax the syntax for this application
     * @param header the banner to display at the beginning of the help
     * @param options the Options instance
     * @param footer the banner to display at the end of the help
     * @param autoUsage whether to print an automatically generated usage statement
     */
    private void printHelp(final PrintWriter pw, final HelpLayout layout, final String cmdLineSyntax, final String header, final Options options,
        final String footer, final boolean autoUsage) {
        if (Util.isEmpty(cmdLineSyntax)) {
            throw new IllegalArgumentException("cmdLineSyntax not provided");
        }
        final int width = layout.getWidth();
        if (autoUsage) {
            printUsage(pw, width, cmdLineSyntax, options);
        } else {
            printUsage(pw, width, cmdLineSyntax);
        }
        if (header != null && !header.isEmpty()) {
            printWrapped(pw, width, header);
        }
        printOptions(pw, options, layout);
        if (footer != null && !footer.isEmpty()) {
            printWrapped(pw, width, footer);
        }
    }
```

### [changed] `HelpFormatter.java` > `HelpFormatter.printHelp(PrintWriter,int,String,String,Options,int,int,String,boolean)` (lines 753-770)

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

### [new] `HelpFormatter.java` > `HelpFormatter.printOptions(PrintWriter,Options,HelpLayout)` (lines 822-831)

```java
    /**
     * Prints the help for the specified Options to the specified writer using the given layout.
     *
     * @param pw The PrintWriter to write the help to
     * @param options The command line Options
     * @param layout The layout configuration
     */
    private void printOptions(final PrintWriter pw, final Options options, final HelpLayout layout) {
        printOptions(pw, layout.getWidth(), options, layout.getLeftPad(), layout.getDescPad());
    }
```

### [new file] `HelpLayout.java` > `(whole file)` (lines 1-74)

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
 * Encapsulates layout dimensions (width, left padding, and description padding) for {@link HelpFormatter}.
 */
final class HelpLayout {

    /** The number of characters to display per line. */
    private final int width;

    /** The number of characters of padding to be prefixed to each line. */
    private final int leftPad;

    /** The number of characters of padding to be prefixed to each description line. */
    private final int descPad;

    /**
     * Constructs a new layout configuration.
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
     * Gets the description padding.
     *
     * @return the number of characters of padding prefixed to each description line
     */
    int getDescPad() {
        return descPad;
    }

    /**
     * Gets the left padding.
     *
     * @return the number of characters of padding prefixed to each line
     */
    int getLeftPad() {
        return leftPad;
    }

    /**
     * Gets the line width.
     *
     * @return the number of characters displayed per line
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
