# Refactoring report - B02 Shotgun Surgery - Copilot

| | |
|---|---|
| Smell | B02 - Shotgun Surgery (Between classes) |
| Class / member | Options, DefaultParser, Parser, MissingOptionException - Options.requiredOpts / addOption / addOptionGroup / getRequiredOptions; DefaultParser.expectedOpts / updateRequiredOptions / checkRequiredOptions; Parser.requiredOptions / updateRequiredOptions / checkRequiredOptions; MissingOptionException (lines Options 52–54, 72–77, 138–140, 273–275; DefaultParser 179, 278–283, 708, 760–775; Parser 41, 48–53, 306, 314–329; MissingOptionException 35–83) |
| Refactoring applied | Extract Class + Move Method + Move Field |
| LLM / model | Copilot - Copilot SDK in VS Code (2026-11-10) |
| Mode | agent |
| Code base | rel/commons-cli-1.9.0 (698b238276) -> branch `refactor/B02` commit 2ee4dd7058 |
| Verdict | **PASS** |
| Original tests | 738 passed of 797 (59 skipped) |
| Refactored tests | 738 passed of 797 (59 skipped) - regressions: 0 |
| Test files modified | No |
| Public/protected API | 0 removed or changed, 0 added |
| Files changed | src/main/java/org/apache/commons/cli/DefaultParser.java (+7 -19)<br>src/main/java/org/apache/commons/cli/Options.java (+5 -10)<br>src/main/java/org/apache/commons/cli/Parser.java (+7 -19)<br>src/main/java/org/apache/commons/cli/RequiredOptions.java (+78 -0) |
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

### [changed] `Options.java` > `Options#requiredOpts` (lines 51-54)

```java
    /** A map of the required options */
    // N.B. This can contain either a String (addOption) or an OptionGroup (addOptionGroup)
    // TODO this seems wrong
    private final List<Object> requiredOpts = new ArrayList<>();
```

### [changed] `Options.java` > `Options.addOption(Option)` (lines 59-80)

```java
    /**
     * Adds an option instance
     *
     * @param opt the option that is to be added
     * @return the resulting Options instance
     */
    public Options addOption(final Option opt) {
        final String key = opt.getKey();
        // add it to the long option list
        if (opt.hasLongOpt()) {
            longOpts.put(opt.getLongOpt(), opt);
        }
        // if the option is required add it to the required list
        if (opt.isRequired()) {
            if (requiredOpts.contains(key)) {
                requiredOpts.remove(requiredOpts.indexOf(key));
            }
            requiredOpts.add(key);
        }
        shortOpts.put(key, opt);
        return this;
    }
```

### [changed] `Options.java` > `Options.addOptionGroup(OptionGroup)` (lines 131-150)

```java
    /**
     * Adds the specified option group.
     *
     * @param group the OptionGroup that is to be added
     * @return the resulting Options instance
     */
    public Options addOptionGroup(final OptionGroup group) {
        if (group.isRequired()) {
            requiredOpts.add(group);
        }
        for (final Option option : group.getOptions()) {
            // an Option cannot be required if it is in an
            // OptionGroup, either the group is required or
            // nothing is required
            option.setRequired(false);
            addOption(option);
            optionGroups.put(option.getKey(), group);
        }
        return this;
    }
```

### [changed] `Options.java` > `Options.getRequiredOptions()` (lines 268-275)

```java
    /**
     * Gets the required options.
     *
     * @return read-only List of required options
     */
    public List<?> getRequiredOptions() {
        return Collections.unmodifiableList(requiredOpts);
    }
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
> Model: Copilot SDK in VS Code (2026-11-10) · Mode: agent · Started: 2026-11-10 21:02

### 1. Understanding of the smell
Required-option state and its update/checking logic was duplicated across `Options`, `Parser`, and `DefaultParser`, while `MissingOptionException` consumed the resulting mixed list. This shotgun surgery meant that changing required-option tracking required coordinated edits in several classes, including near-identical parser methods.

### 2. Plan
1. Extract a package-private `RequiredOptions` class that owns the required-elements list, adding methods for registration, marking an option/group seen, and checking that all elements are present.
2. Move `Options` required-list storage and registration operations into the tracker while keeping `getRequiredOptions()` as the same read-only ordered-list API; run `OptionsTest`.
3. Move both parsers’ required state and update/check bodies to tracker delegates, retaining the protected fields/methods and their list views; run parser and option-group tests.
4. Run the full suite and record any unrelated baseline blocker without changing other smells.

### 3. Steps performed
| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | Added package-private `RequiredOptions` with required-list ownership, registration, `markSeen`, and `checkAllPresent`. | Passed as part of Maven test compile | `OptionsTest`: 15 passed |
| 2 | `Options` delegates required option/group registration and ordered read-only contents to `RequiredOptions`. | Passed | `OptionsTest`: 15 passed |
| 3 | `Parser` and `DefaultParser` delegate required state updates and checks while retaining compatibility fields/methods. | Passed | `DefaultParserTest`, `BasicParserTest`, `GnuParserTest`, `PosixParserTest`, `OptionGroupTest`: 226 passed, 59 skipped |
| 4 | Full regression run. | Passed compilation | 737 passed, 1 unrelated failure, 59 skipped (`HelpFormatterTest#testRenderSince`) |

### 4. Why behaviour is preserved
`RequiredOptions` uses the same list insertion/removal rules, so `Options.getRequiredOptions()` retains its contents and order. Parser compatibility fields and protected methods remain present and delegate to the same mutable tracked list. `checkAllPresent()` still constructs `MissingOptionException` from that list, preserving the exception API, exact singular/plural wording, element `toString()` values, and ordering; group selection still occurs through `OptionGroup.setSelected`.

### 5. Deviations from the plan
The full suite exposed a pre-existing/unrelated `HelpFormatterTest#testRenderSince` failure (`Expected UncheckedIOException to be thrown, but nothing was thrown`) in an already modified `HelpFormatter.java`; that file was not changed. Per the run instruction, `finish` and metrics were not run.

### 6. Observations (not changed)
The working tree already contained unrelated `HelpFormatter.java` changes, and its `testRenderSince` regression remains outside B02. No source under `src/test/` was modified.

### 7. Self-assessment
- Smell removed: yes; required-option tracking is centralized in `RequiredOptions`.
- Expected effect on size: duplicated parser logic and state handling are reduced.
- Expected effect on cohesion: parsers no longer own the required-option tracking concern.
- Expected effect on coupling: parsers depend on one tracker abstraction rather than duplicating list/group mechanics, while compatibility delegates preserve existing callers.

## 5. Refactored code (after refactoring)

_The same members after the refactoring, plus any new members or files. Full files: `refactored/`; diff: `changes.patch`._

### [new] `DefaultParser.java` > `DefaultParser#requiredOptions` (lines 181-182)

```java
    /** Tracks required options during parsing. */
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
        requiredOptions = new RequiredOptions(options.getRequiredOptions());
        expectedOpts = requiredOptions.getOptions();
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

### [changed] `Options.java` > `Options#requiredOpts` (lines 51-52)

```java
    /** The required options. */
    private final RequiredOptions requiredOpts = new RequiredOptions();
```

### [changed] `Options.java` > `Options.addOption(Option)` (lines 57-75)

```java
    /**
     * Adds an option instance
     *
     * @param opt the option that is to be added
     * @return the resulting Options instance
     */
    public Options addOption(final Option opt) {
        final String key = opt.getKey();
        // add it to the long option list
        if (opt.hasLongOpt()) {
            longOpts.put(opt.getLongOpt(), opt);
        }
        // if the option is required add it to the required list
        if (opt.isRequired()) {
            requiredOpts.addOption(key);
        }
        shortOpts.put(key, opt);
        return this;
    }
```

### [changed] `Options.java` > `Options.addOptionGroup(OptionGroup)` (lines 126-145)

```java
    /**
     * Adds the specified option group.
     *
     * @param group the OptionGroup that is to be added
     * @return the resulting Options instance
     */
    public Options addOptionGroup(final OptionGroup group) {
        if (group.isRequired()) {
            requiredOpts.addGroup(group);
        }
        for (final Option option : group.getOptions()) {
            // an Option cannot be required if it is in an
            // OptionGroup, either the group is required or
            // nothing is required
            option.setRequired(false);
            addOption(option);
            optionGroups.put(option.getKey(), group);
        }
        return this;
    }
```

### [changed] `Options.java` > `Options.getRequiredOptions()` (lines 263-270)

```java
    /**
     * Gets the required options.
     *
     * @return read-only List of required options
     */
    public List<?> getRequiredOptions() {
        return Collections.unmodifiableList(requiredOpts.getOptions());
    }
```

### [new] `Parser.java` > `Parser#requiredOptionsTracker` (lines 43-44)

```java
    /** Tracks required options during parsing. */
    private RequiredOptions requiredOptionsTracker;
```

### [changed] `Parser.java` > `Parser.checkRequiredOptions()` (lines 46-53)

```java
    /**
     * Throws a {@link MissingOptionException} if all of the required options are not present.
     *
     * @throws MissingOptionException if any of the required Options are not present.
     */
    protected void checkRequiredOptions() throws MissingOptionException {
        requiredOptionsTracker.checkAllPresent();
    }
```

### [changed] `Parser.java` > `Parser.setOptions(Options)` (lines 299-308)

```java
    /**
     * Sets the options.
     *
     * @param options the options.
     */
    protected void setOptions(final Options options) {
        this.options = options;
        requiredOptionsTracker = new RequiredOptions(options.getRequiredOptions());
        this.requiredOptions = requiredOptionsTracker.getOptions();
    }
```

### [changed] `Parser.java` > `Parser.updateRequiredOptions(Option)` (lines 310-317)

```java
    /**
     * Removes the option or its group from the list of expected elements.
     *
     * @param opt
     */
    private void updateRequiredOptions(final Option opt) throws ParseException {
        requiredOptionsTracker.markSeen(opt, getOptions().getOptionGroup(opt));
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

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

/** Tracks required options and option groups during parsing. */
final class RequiredOptions implements Serializable {
    private static final long serialVersionUID = 1L;

    private final List<Object> options;

    /** Creates an empty required-options tracker. */
    RequiredOptions() {
        options = new ArrayList<>();
    }

    /** Creates a tracker initialized with the supplied required elements. */
    RequiredOptions(final Collection<?> requiredOptions) {
        options = new ArrayList<>(requiredOptions);
    }

    /** Adds a required option key, preserving the original replacement order. */
    void addOption(final String key) {
        if (options.contains(key)) {
            options.remove(options.indexOf(key));
        }
        options.add(key);
    }

    /** Adds a required option group. */
    void addGroup(final OptionGroup group) {
        options.add(group);
    }

    /** Marks an option and its group as present. */
    void markSeen(final Option option, final OptionGroup group) throws AlreadySelectedException {
        if (option.isRequired()) {
            options.remove(option.getKey());
        }
        if (group != null) {
            if (group.isRequired()) {
                options.remove(group);
            }
            group.setSelected(option);
        }
    }

    /** Throws if required options remain. */
    void checkAllPresent() throws MissingOptionException {
        if (!options.isEmpty()) {
            throw new MissingOptionException(options);
        }
    }

    /** Gets the mutable tracked elements. */
    List<Object> getOptions() {
        return options;
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
