# Refactoring report - B02 Shotgun Surgery - Gemini

| | |
|---|---|
| Smell | B02 - Shotgun Surgery (Between classes) |
| Class / member | Options, DefaultParser, Parser, MissingOptionException - Options.requiredOpts / addOption / addOptionGroup / getRequiredOptions; DefaultParser.expectedOpts / updateRequiredOptions / checkRequiredOptions; Parser.requiredOptions / updateRequiredOptions / checkRequiredOptions; MissingOptionException (lines Options 52–54, 72–77, 138–140, 273–275; DefaultParser 179, 278–283, 708, 760–775; Parser 41, 48–53, 306, 314–329; MissingOptionException 35–83) |
| Refactoring applied | Extract Class + Move Method + Move Field |
| LLM / model | Gemini - Gemini 3.1 Pro |
| Mode | agent |
| Code base | rel/commons-cli-1.9.0 (698b238276) -> branch `refactor/B02` commit f7ce874c69 |
| Verdict | **PASS** |
| Original tests | 738 passed of 797 (59 skipped) |
| Refactored tests | 738 passed of 797 (59 skipped) - regressions: 0 |
| Test files modified | No |
| Public/protected API | 0 removed or changed, 0 added |
| Files changed | src/main/java/org/apache/commons/cli/DefaultParser.java (+7 -19)<br>src/main/java/org/apache/commons/cli/Parser.java (+6 -23)<br>src/main/java/org/apache/commons/cli/RequiredOptions.java (+78 -0) |
| Finish attempts | 1 |

## 1. Smell (from the review sheet)

**Evidence.** Tracking of required options and groups is spread over 4 classes. Options keeps them in a List<Object> that mixes String keys and OptionGroup objects (its own comment: "TODO this seems wrong"). Both parsers copy it into raw List fields, and each has its own near-identical updateRequiredOptions and checkRequiredOptions (Type III clones). MissingOptionException takes a raw List and builds its message from each element's toString(). Changing how a required option is identified or reported means editing Options, DefaultParser, Parser and MissingOptionException together. The same two parsers also duplicate properties handling (Parser.processProperties 264–297 vs DefaultParser.handleProperties 434–463).

**Technique:** Extract Class + Move Method + Move Field

_Source: review sheet suggestion (column 'Suggested refactoring')._

**How (outline):** Create a package-private class (e.g. RequiredOptions) that owns the 'still expected' list, with markSeen(Option, OptionGroup) and checkAllPresent() (throws MissingOptionException). Move the updateRequiredOptions / checkRequiredOptions bodies from both parsers into it, and move the expectedOpts / requiredOptions state there. Keep the protected members as delegates, and keep Options.getRequiredOptions() and MissingOptionException.getMissingOptions() returning the same contents.

**Risks to watch:** Medium. Protected members (DefaultParser.expectedOpts, checkRequiredOptions; Parser.getRequiredOptions) are subclass API. Tests assert exact messages such as "Missing required options: b, c" (AbstractParserTestCase 398, OptionsTest 276), so element order must be preserved.

**Expected effect on metrics:** Size: duplicated logic removed from 2 parsers. Cohesion: parsers lose a side concern (LCOM drops). Coupling: parsers depend on one tracker instead of OptionGroup + MissingOptionException + Options internals (parser CBO may drop by 1–2), but the system gains one class.


## 2. Original code (before refactoring)

_Every member the refactoring changed or removed, as it was in the original code. Full files: `original/`._

### [changed] `DefaultParser.java` > `DefaultParser.checkRequiredOptions()` (lines 273-283)

```java
    /**
     * Throws a {@link MissingOptionException} if all of the required options are not present.
     *
     * @throws MissingOptionException if any of the required Options are not present.
     */
    protected void checkRequiredOptions() throws MissingOptionException {
        // if there are required options that have not been processed
        if (!expectedOpts.isEmpty()) {
            throw new MissingOptionException(expectedOpts);
        }
    }
```

### [changed] `DefaultParser.java` > `DefaultParser.parse(Options,String[],Properties,boolean)` (lines 689-725)

```java
    /**
     * Parses the arguments according to the specified options and properties.
     *
     * @param options the specified Options
     * @param arguments the command line arguments
     * @param properties command line option name-value pairs
     * @param stopAtNonOption if {@code true} an unrecognized argument stops the parsing and the remaining arguments
     *        are added to the {@link CommandLine}s args list. If {@code false} an unrecognized argument triggers a
     *        ParseException.
     *
     * @return the list of atomic option and value tokens
     * @throws ParseException if there are any problems encountered while parsing the command line tokens.
     */
    public CommandLine parse(final Options options, final String[] arguments, final Properties properties, final boolean stopAtNonOption)
        throws ParseException {
        this.options = options;
        this.stopAtNonOption = stopAtNonOption;
        skipParsing = false;
        currentOption = null;
        expectedOpts = new ArrayList<>(options.getRequiredOptions());
        // clear the data from the groups
        for (final OptionGroup group : options.getOptionGroups()) {
            group.setSelected(null);
        }
        cmd = CommandLine.builder().setDeprecatedHandler(deprecatedHandler).build();
        if (arguments != null) {
            for (final String argument : arguments) {
                handleToken(argument);
            }
        }
        // check the arguments of the last option
        checkRequiredArgs();
        // add the default options
        handleProperties(properties);
        checkRequiredOptions();
        return cmd;
    }
```

### [changed] `DefaultParser.java` > `DefaultParser.updateRequiredOptions(Option)` (lines 755-775)

```java
    /**
     * Removes the option or its group from the list of expected elements.
     *
     * @param option
     */
    private void updateRequiredOptions(final Option option) throws AlreadySelectedException {
        if (option.isRequired()) {
            expectedOpts.remove(option.getKey());
        }

        // if the option is in an OptionGroup make that option the selected option of the group
        if (options.getOptionGroup(option) != null) {
            final OptionGroup group = options.getOptionGroup(option);

            if (group.isRequired()) {
                expectedOpts.remove(group);
            }

            group.setSelected(option);
        }
    }
```

### [changed] `Parser.java` > `(package & imports)` (lines 1-25)

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

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Enumeration;
import java.util.List;
import java.util.ListIterator;
import java.util.Properties;
```

### [changed] `Parser.java` > `Parser#requiredOptions` (lines 40-41)

```java
    /** List of required options strings */
    private List requiredOptions;
```

### [changed] `Parser.java` > `Parser.checkRequiredOptions()` (lines 43-53)

```java
    /**
     * Throws a {@link MissingOptionException} if all of the required options are not present.
     *
     * @throws MissingOptionException if any of the required Options are not present.
     */
    protected void checkRequiredOptions() throws MissingOptionException {
        // if there are required options that have not been processed
        if (!getRequiredOptions().isEmpty()) {
            throw new MissingOptionException(getRequiredOptions());
        }
    }
```

### [changed] `Parser.java` > `Parser.getRequiredOptions()` (lines 75-82)

```java
    /**
     * Gets the required options.
     *
     * @return the required options.
     */
    protected List getRequiredOptions() {
        return requiredOptions;
    }
```

### [changed] `Parser.java` > `Parser.setOptions(Options)` (lines 299-307)

```java
    /**
     * Sets the options.
     *
     * @param options the options.
     */
    protected void setOptions(final Options options) {
        this.options = options;
        this.requiredOptions = new ArrayList<>(options.getRequiredOptions());
    }
```

### [changed] `Parser.java` > `Parser.updateRequiredOptions(Option)` (lines 309-329)

```java
    /**
     * Removes the option or its group from the list of expected elements.
     *
     * @param opt
     */
    private void updateRequiredOptions(final Option opt) throws ParseException {
        // if the option is a required option remove the option from
        // the requiredOptions list
        if (opt.isRequired()) {
            getRequiredOptions().remove(opt.getKey());
        }
        // if the option is in an OptionGroup make that option the selected
        // option of the group
        if (getOptions().getOptionGroup(opt) != null) {
            final OptionGroup group = getOptions().getOptionGroup(opt);
            if (group.isRequired()) {
                getRequiredOptions().remove(group);
            }
            group.setSelected(opt);
        }
    }
```

## 3. Original tests (on the untouched code)

- Result: **738 passed of 797 (59 skipped)**
- Log: `tests_original.log`

## 4. Refactoring process

> Written by the LLM during the run. Keep the headings and replace every _italic guidance line_ with your own text.
> Model: Gemini 3.1 Pro · Mode: agent · Started: 2026-11-11 11:53

### 1. Understanding of the smell
Tracking of required options and option groups during command-line parsing is scattered and duplicated across `Options` (lines 52–54, 72–77, 138–140, 273–275), `DefaultParser` (lines 179, 278–283, 708, 760–775), `Parser` (lines 41, 48–53, 80–82, 304–329), and `MissingOptionException` (lines 35–83). Both `DefaultParser` and `Parser` copy `options.getRequiredOptions()` into raw `List` fields (`expectedOpts` and `requiredOptions`) and maintain near-identical Type III clones of `updateRequiredOptions(Option)` and `checkRequiredOptions()`. Because this state and logic are duplicated across classes, any change to how required options and groups are tracked or validated requires parallel edits in multiple classes (Shotgun Surgery).

### 2. Plan
1. **Extract Class (`RequiredOptions`):** Create a package-private class `RequiredOptions` in `org.apache.commons.cli` that owns the mutable per-parse list of still-expected required options/groups (copied from `options.getRequiredOptions()`), and move the duplicated tracking and validation logic into `markSeen(Option, OptionGroup)` and `checkAllPresent()`. Provide package-private `getExpectedOptions()` to expose the backing list for protected subclass delegates. Compile and run `OptionsTest`.
2. **Move Field and Move Method in `DefaultParser`:** Add a private `RequiredOptions requiredOptions` field in `DefaultParser`, initialize it in `parse(Options, String[], Properties, boolean)` while keeping `protected List expectedOpts` pointing to its backing list, and replace the bodies of `checkRequiredOptions()` and `updateRequiredOptions(Option)` with delegation calls to `requiredOptions.checkAllPresent()` and `requiredOptions.markSeen(option, options.getOptionGroup(option))`. Compile and run `DefaultParserTest` and `OptionGroupTest`.
3. **Move Field and Move Method in `Parser`:** Replace `private List requiredOptions` in `Parser` with `private RequiredOptions requiredOptions`, initialize it in `setOptions(Options)`, update `protected List getRequiredOptions()` to delegate to `requiredOptions.getExpectedOptions()`, and replace the bodies of `checkRequiredOptions()` and `updateRequiredOptions(Option)` with delegation calls to `requiredOptions.checkAllPresent()` and `requiredOptions.markSeen(opt, getOptions().getOptionGroup(opt))`. Compile and run `BasicParserTest`, `GnuParserTest`, `PosixParserTest`, and the full test suite.

### 3. Steps performed

| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | Added `RequiredOptions.java` (`RequiredOptions` constructor, `checkAllPresent()`, `getExpectedOptions()`, `markSeen(Option, OptionGroup)`) | OK | `OptionsTest` 15/15 passed |
| 2 | Updated `DefaultParser.java` (`#requiredOptions`, `checkRequiredOptions()`, `parse(Options,String[],Properties,boolean)`, `updateRequiredOptions(Option)`) | OK | `DefaultParserTest` 74/74, `OptionGroupTest` 13/13 passed |
| 3 | Updated `Parser.java` (`#requiredOptions`, `checkRequiredOptions()`, `getRequiredOptions()`, `setOptions(Options)`, `updateRequiredOptions(Option)`) | OK | `BasicParserTest` 39/66, `GnuParserTest` 44/66, `PosixParserTest` 56/66, full suite 738/797 passed |

### 4. Why behaviour is preserved
- **Identical list initialization and ordering:** `RequiredOptions` initializes its backing list with `new ArrayList<>(options.getRequiredOptions())`, preserving the exact insertion order of String option keys and `OptionGroup` instances so `MissingOptionException` messages and `getMissingOptions()` contents are byte-for-byte identical.
- **Identical removal and group-selection sequence:** `RequiredOptions.markSeen(Option, OptionGroup)` removes `option.getKey()` when `option.isRequired()`, then if `group != null`, removes `group` when `group.isRequired()` and calls `group.setSelected(option)` — matching the exact statement order and exception behaviour (`AlreadySelectedException`) of both parsers.
- **Protected API and live backing list preserved:** `DefaultParser.expectedOpts` and `Parser.getRequiredOptions()` return the same live mutable `List` managed by `RequiredOptions`, and `Parser.getRequiredOptions()` still returns `null` before `setOptions` is called. Both `checkRequiredOptions()` methods remain `protected` and delegate to `requiredOptions.checkAllPresent()`.

### 5. Deviations from the plan
None

### 6. Observations (not changed)
- `Options.requiredOpts` still mixes `String` keys and `OptionGroup` instances in a single `List<Object>` (as noted by its existing `// TODO this seems wrong` comment), because `Options.getRequiredOptions()` and `MissingOptionException.getMissingOptions()` are part of the public API contract and tests assert their exact elements.
- `DefaultParser.handleProperties` and `Parser.processProperties` also contain duplicated logic for default option properties, which was left untouched as out of scope for this refactoring.

### 7. Self-assessment
- Smell removed: partly — the duplicated per-parse required-options state and the Type III clones of `updateRequiredOptions` and `checkRequiredOptions` in `DefaultParser` and `Parser` are consolidated into `RequiredOptions`, while the heterogeneous `List` representation in `Options.getRequiredOptions()` and `MissingOptionException.getMissingOptions()` is retained to preserve public/protected API contracts.
- Expected effect on size: Duplicated lines in `DefaultParser` and `Parser` decrease, with a modest net LOC increase across the package due to the new `RequiredOptions` class and its Javadoc.
- Expected effect on cohesion: Mean cohesion improves (LCOM* decreases) because `RequiredOptions` is a single-purpose cohesive class (LCOM* = 0) and `Parser` sheds direct manipulation of the raw list.
- Expected effect on coupling: `DefaultParser` and `Parser` each lose direct coupling to `MissingOptionException` (or `ArrayList` in `Parser`), while coupling to `RequiredOptions` is added and `RequiredOptions` itself contributes its own CBO to the sum.

## 5. Refactored code (after refactoring)

_The same members after the refactoring, plus any new members or files. Full files: `refactored/`; diff: `changes.patch`._

### [new] `DefaultParser.java` > `DefaultParser#requiredOptions` (lines 181-182)

```java
    /** Tracker for the required options and groups expected during parsing. */
    private RequiredOptions requiredOptions;
```

### [changed] `DefaultParser.java` > `DefaultParser.checkRequiredOptions()` (lines 276-283)

```java
    /**
     * Throws a {@link MissingOptionException} if all of the required options are not present.
     *
     * @throws MissingOptionException if any of the required Options are not present.
     */
    protected void checkRequiredOptions() throws MissingOptionException {
        requiredOptions.checkAllPresent();
    }
```

### [changed] `DefaultParser.java` > `DefaultParser.parse(Options,String[],Properties,boolean)` (lines 689-726)

```java
    /**
     * Parses the arguments according to the specified options and properties.
     *
     * @param options the specified Options
     * @param arguments the command line arguments
     * @param properties command line option name-value pairs
     * @param stopAtNonOption if {@code true} an unrecognized argument stops the parsing and the remaining arguments
     *        are added to the {@link CommandLine}s args list. If {@code false} an unrecognized argument triggers a
     *        ParseException.
     *
     * @return the list of atomic option and value tokens
     * @throws ParseException if there are any problems encountered while parsing the command line tokens.
     */
    public CommandLine parse(final Options options, final String[] arguments, final Properties properties, final boolean stopAtNonOption)
        throws ParseException {
        this.options = options;
        this.stopAtNonOption = stopAtNonOption;
        skipParsing = false;
        currentOption = null;
        requiredOptions = new RequiredOptions(options);
        expectedOpts = requiredOptions.getExpectedOptions();
        // clear the data from the groups
        for (final OptionGroup group : options.getOptionGroups()) {
            group.setSelected(null);
        }
        cmd = CommandLine.builder().setDeprecatedHandler(deprecatedHandler).build();
        if (arguments != null) {
            for (final String argument : arguments) {
                handleToken(argument);
            }
        }
        // check the arguments of the last option
        checkRequiredArgs();
        // add the default options
        handleProperties(properties);
        checkRequiredOptions();
        return cmd;
    }
```

### [changed] `DefaultParser.java` > `DefaultParser.updateRequiredOptions(Option)` (lines 756-763)

```java
    /**
     * Removes the option or its group from the list of expected elements.
     *
     * @param option
     */
    private void updateRequiredOptions(final Option option) throws AlreadySelectedException {
        requiredOptions.markSeen(option, options.getOptionGroup(option));
    }
```

### [changed] `Parser.java` > `(package & imports)` (lines 1-24)

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

import java.util.Arrays;
import java.util.Enumeration;
import java.util.List;
import java.util.ListIterator;
import java.util.Properties;
```

### [changed] `Parser.java` > `Parser#requiredOptions` (lines 39-40)

```java
    /** Tracker of required options and option groups */
    private RequiredOptions requiredOptions;
```

### [changed] `Parser.java` > `Parser.checkRequiredOptions()` (lines 42-49)

```java
    /**
     * Throws a {@link MissingOptionException} if all of the required options are not present.
     *
     * @throws MissingOptionException if any of the required Options are not present.
     */
    protected void checkRequiredOptions() throws MissingOptionException {
        requiredOptions.checkAllPresent();
    }
```

### [changed] `Parser.java` > `Parser.getRequiredOptions()` (lines 71-78)

```java
    /**
     * Gets the required options.
     *
     * @return the required options.
     */
    protected List getRequiredOptions() {
        return requiredOptions == null ? null : requiredOptions.getExpectedOptions();
    }
```

### [changed] `Parser.java` > `Parser.setOptions(Options)` (lines 295-303)

```java
    /**
     * Sets the options.
     *
     * @param options the options.
     */
    protected void setOptions(final Options options) {
        this.options = options;
        this.requiredOptions = new RequiredOptions(options);
    }
```

### [changed] `Parser.java` > `Parser.updateRequiredOptions(Option)` (lines 305-312)

```java
    /**
     * Removes the option or its group from the list of expected elements.
     *
     * @param opt
     */
    private void updateRequiredOptions(final Option opt) throws ParseException {
        requiredOptions.markSeen(opt, getOptions().getOptionGroup(opt));
    }
```

### [new file] `RequiredOptions.java` > `(whole file)` (lines 1-79)

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

import java.util.ArrayList;
import java.util.List;

/**
 * Tracks the required options and option groups that are still expected during command-line parsing.
 */
final class RequiredOptions {

    /** The list of required option keys and required OptionGroup instances still expected. */
    private final List<Object> expectedOpts;

    /**
     * Constructs a new tracker initialized with the required options from {@code options}.
     *
     * @param options the Options being parsed
     */
    RequiredOptions(final Options options) {
        this.expectedOpts = new ArrayList<>(options.getRequiredOptions());
    }

    /**
     * Throws a {@link MissingOptionException} if any required options or option groups have not been seen.
     *
     * @throws MissingOptionException if any required options are still missing
     */
    void checkAllPresent() throws MissingOptionException {
        if (!expectedOpts.isEmpty()) {
            throw new MissingOptionException(expectedOpts);
        }
    }

    /**
     * Gets the live mutable list of still-expected options and groups for subclass compatibility.
     *
     * @return the list of still-expected required options and groups
     */
    List<Object> getExpectedOptions() {
        return expectedOpts;
    }

    /**
     * Records that {@code option} (and its enclosing {@code group}, if any) has been seen during parsing.
     *
     * @param option the option that was matched
     * @param group the OptionGroup containing {@code option}, or {@code null} if none
     * @throws AlreadySelectedException if another option in {@code group} was already selected
     */
    void markSeen(final Option option, final OptionGroup group) throws AlreadySelectedException {
        if (option.isRequired()) {
            expectedOpts.remove(option.getKey());
        }
        if (group != null) {
            if (group.isRequired()) {
                expectedOpts.remove(group);
            }
            group.setSelected(option);
        }
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
