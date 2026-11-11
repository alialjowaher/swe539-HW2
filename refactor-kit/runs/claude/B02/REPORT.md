# Refactoring report - B02 Shotgun Surgery - Claude

| | |
|---|---|
| Smell | B02 - Shotgun Surgery (Between classes) |
| Class / member | Options, DefaultParser, Parser, MissingOptionException - Options.requiredOpts / addOption / addOptionGroup / getRequiredOptions; DefaultParser.expectedOpts / updateRequiredOptions / checkRequiredOptions; Parser.requiredOptions / updateRequiredOptions / checkRequiredOptions; MissingOptionException (lines Options 52–54, 72–77, 138–140, 273–275; DefaultParser 179, 278–283, 708, 760–775; Parser 41, 48–53, 306, 314–329; MissingOptionException 35–83) |
| Refactoring applied | Extract Class + Move Method + Move Field |
| LLM / model | Claude - Claude Opus 5.5 (claude-opus-5-5) |
| Mode | agent |
| Code base | rel/commons-cli-1.9.0 (698b238276) -> branch `refactor/B02` commit 53c8b76a8e |
| Verdict | **PASS** |
| Original tests | 738 passed of 797 (59 skipped) |
| Refactored tests | 738 passed of 797 (59 skipped) - regressions: 0 |
| Test files modified | No |
| Public/protected API | 0 removed or changed, 0 added |
| Files changed | src/main/java/org/apache/commons/cli/DefaultParser.java (+7 -28)<br>src/main/java/org/apache/commons/cli/Parser.java (+7 -33)<br>src/main/java/org/apache/commons/cli/RequiredOptions.java (+87 -0) |
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

### [changed] `DefaultParser.java` > `DefaultParser.handleOption(Option)` (lines 420-427)

```java
    private void handleOption(final Option option) throws ParseException {
        // check the previous option before handling the next one
        checkRequiredArgs();
        final Option copy = (Option) option.clone();
        updateRequiredOptions(copy);
        cmd.addOption(copy);
        currentOption = copy.hasArg() ? copy : null;
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

### [removed] `DefaultParser.java` > `DefaultParser.updateRequiredOptions(Option)` (lines 755-775)

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

### [changed] `Parser.java` > `Parser.processOption(String,ListIterator<String>)` (lines 232-256)

```java
    /**
     * Process the Option specified by {@code arg} using the values retrieved from the specified iterator
     * {@code iter}.
     *
     * @param arg The String value representing an Option
     * @param iter The iterator over the flattened command line arguments.
     * @throws ParseException if {@code arg} does not represent an Option
     */
    protected void processOption(final String arg, final ListIterator<String> iter) throws ParseException {
        final boolean hasOption = getOptions().hasOption(arg);
        // if there is no option throw an UnrecognizedOptionException
        if (!hasOption) {
            throw new UnrecognizedOptionException("Unrecognized option: " + arg, arg);
        }
        // get the option represented by arg
        final Option opt = (Option) getOptions().getOption(arg).clone();
        // update the required options and groups
        updateRequiredOptions(opt);
        // if the option takes an argument value
        if (opt.hasArg()) {
            processArgs(opt, iter);
        }
        // set the option on the command line
        cmd.addOption(opt);
    }
```

### [changed] `Parser.java` > `Parser.processProperties(Properties)` (lines 258-297)

```java
    /**
     * Sets the values of Options using the values in {@code properties}.
     *
     * @param properties The value properties to be processed.
     * @throws ParseException if there are any problems encountered while processing the properties.
     */
    protected void processProperties(final Properties properties) throws ParseException {
        if (properties == null) {
            return;
        }
        for (final Enumeration<?> e = properties.propertyNames(); e.hasMoreElements();) {
            final String option = e.nextElement().toString();
            final Option opt = options.getOption(option);
            if (opt == null) {
                throw new UnrecognizedOptionException("Default option wasn't defined", option);
            }
            // if the option is part of a group, check if another option of the group has been selected
            final OptionGroup group = options.getOptionGroup(opt);
            final boolean selected = group != null && group.isSelected();
            if (!cmd.hasOption(option) && !selected) {
                // get the value from the properties instance
                final String value = properties.getProperty(option);
                if (opt.hasArg()) {
                    if (Util.isEmpty(opt.getValues())) {
                        try {
                            opt.processValue(value);
                        } catch (final RuntimeException exp) { // NOPMD
                            // if we cannot add the value don't worry about it
                        }
                    }
                } else if (!("yes".equalsIgnoreCase(value) || "true".equalsIgnoreCase(value) || "1".equalsIgnoreCase(value))) {
                    // if the value is not yes, true or 1 then don't add the
                    // option to the CommandLine
                    continue;
                }
                cmd.addOption(opt);
                updateRequiredOptions(opt);
            }
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

### [removed] `Parser.java` > `Parser.updateRequiredOptions(Option)` (lines 309-329)

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
> Model: Claude Opus 5.5 (claude-opus-5-5) · Mode: agent · Started: 2026-11-11 09:21

### 1. Understanding of the smell
The bookkeeping of "required options and groups that have not been seen yet" has no home of its own. `Options` builds the mixed String/OptionGroup list (`requiredOpts`, lines 51-54, filled in `addOption` 72-77 and `addOptionGroup` 138-140), and then each parser copies it into its own raw `List` field (`DefaultParser.expectedOpts` line 179 / 708, `Parser.requiredOptions` line 41 / 306) and carries a near-identical private `updateRequiredOptions` (DefaultParser 760-775, Parser 314-329) and protected `checkRequiredOptions` (DefaultParser 278-283, Parser 48-53) that interpret the list and build a `MissingOptionException` (which formats each element via `toString()`, lines 35-49). Any change in how a required option is identified, ticked off or reported therefore needs coordinated edits in Options, DefaultParser, Parser and MissingOptionException at once, which is Shotgun Surgery; the two parser copies are Type III clones of the same logic.

### 2. Plan
Technique: Extract Class + Move Field + Move Method. The new class owns the per-parse "still expected" list; both parsers delegate to it; the protected members stay and delegate. `Options` and `MissingOptionException` keep their code and contents (the outline asks to keep `Options.getRequiredOptions()` and `MissingOptionException.getMissingOptions()` returning the same contents), so element order and messages cannot change.

1. **Extract Class (empty shell).** Create package-private `final class RequiredOptions` in `org.apache.commons.cli` (licence header, class Javadoc). Add the moved state as `private final List<Object> expected`, filled by a constructor `RequiredOptions(final Options options)` with `new ArrayList<>(options.getRequiredOptions())` (the exact copy both parsers do today), and a package-private accessor `getExpected()` that returns the live list (not a copy). Nothing uses it yet. Compile + test (OptionsTest).
2. **Move Method `updateRequiredOptions` (copy body).** Add `void markSeen(final Option option, final OptionGroup group) throws AlreadySelectedException` with the body of the parsers' `updateRequiredOptions`, statement order unchanged: remove `option.getKey()` if the option is required; then, if `group != null`, remove the group if it is required and call `group.setSelected(option)`. Add `void checkAllPresent() throws MissingOptionException` with the body of `checkRequiredOptions` (throws `new MissingOptionException(expected)` with the live list when it is not empty). Still unused. Compile + test (OptionsTest).
3. **Move Field + Move Method in `DefaultParser`.** Add `private RequiredOptions requiredOptions`. In `parse(...)` replace `expectedOpts = new ArrayList<>(options.getRequiredOptions())` (same position) with creating the tracker and pointing the kept protected field `expectedOpts` at the tracker's live list. Make protected `checkRequiredOptions()` delegate to `requiredOptions.checkAllPresent()`. Replace the private `updateRequiredOptions(copy)` call in `handleOption` with `requiredOptions.markSeen(copy, options.getOptionGroup(copy))` and delete the now-unused private method (the `ArrayList` import stays: `getMatchingLongOptions` still uses it). Compile + test (DefaultParserTest, then OptionGroupTest).
4. **Move Field + Move Method in `Parser`.** Change the private field `requiredOptions` from `List` to `RequiredOptions`; `setOptions(...)` creates the tracker; protected `getRequiredOptions()` delegates to `requiredOptions.getExpected()` (returns `null` when `setOptions` has not run yet, as today); protected `checkRequiredOptions()` delegates to `requiredOptions.checkAllPresent()`. Replace the two private `updateRequiredOptions(opt)` calls (`processOption`, `processProperties`) with `requiredOptions.markSeen(opt, getOptions().getOptionGroup(opt))` and delete the private method. Remove the unused `ArrayList` import. Compile + test (BasicParserTest, GnuParserTest, PosixParserTest).
5. **Full suite.** `python kit.py test --llm "Claude"`; must show 738 passed / 0 failed / 59 skipped, like `tests_original.json`.

### 3. Steps performed
| # | What changed (files / members) | Compile | Tests |
|---|---|---|---|
| 1 | Extract Class: new package-private `RequiredOptions.java` with moved field `expected` (`List<Object>`), constructor `RequiredOptions(Options)` (copies `options.getRequiredOptions()`), accessor `getExpected()` returning the live list. Unused yet. | OK | OptionsTest 15/15 |
| 2 | Move Method (copy): `RequiredOptions.markSeen(Option, OptionGroup)` = body of both `updateRequiredOptions`, same statement order; `RequiredOptions.checkAllPresent()` = body of both `checkRequiredOptions`, throws `MissingOptionException(expected)` with the live list. Unused yet. | OK | OptionsTest 15/15 |
| 3 | `DefaultParser`: new private field `requiredOptions`; `parse(...)` creates the tracker at the same spot and sets the kept protected `expectedOpts` to the tracker's live list; protected `checkRequiredOptions()` delegates to `checkAllPresent()`; `handleOption` calls `requiredOptions.markSeen(copy, options.getOptionGroup(copy))`; private `updateRequiredOptions` deleted. `ArrayList` import kept (still used by `getMatchingLongOptions`). | OK | DefaultParserTest 74/74, OptionGroupTest 13/13 |
| 4 | `Parser`: private field `requiredOptions` changed from raw `List` to `RequiredOptions`; `setOptions` creates the tracker; protected `getRequiredOptions()` delegates to `getExpected()` (null-guarded); protected `checkRequiredOptions()` delegates to `checkAllPresent()`; `processOption` and `processProperties` call `requiredOptions.markSeen(opt, getOptions().getOptionGroup(opt))`; private `updateRequiredOptions` deleted; unused `ArrayList` import removed. | OK | BasicParserTest 39/66 (27 skipped), GnuParserTest 44/66 (22 skipped), PosixParserTest 56/66 (10 skipped) - same as baseline |
| 5 | Full suite. | OK | 738 passed of 797 (59 skipped), 0 failures - same as `tests_original.json` |

### 4. Why behaviour is preserved
- **Same contents and order of the expected list.** `RequiredOptions` builds its list with exactly the expression both parsers used (`new ArrayList<>(options.getRequiredOptions())`), at the same moment (DefaultParser: same line position inside `parse`, before the groups are cleared; Parser: inside `setOptions`). `Options` was not touched, so the list still holds `String` keys and `OptionGroup` objects in insertion order.
- **Same exception, same message, same `getMissingOptions()` object.** `checkAllPresent()` is the old body verbatim: `if (!expected.isEmpty()) throw new MissingOptionException(expected)`. It passes the live list (not a copy), as both originals did, so `MissingOptionException` (unchanged) produces the same text, e.g. "Missing required options: b, c", and `getMissingOptions()` returns the same list instance with the same elements and order.
- **Same removal/selection side effects and order.** `markSeen` keeps the original statement order: remove the key if the option is required, then (if in a group) remove the group if the group is required, then `group.setSelected(option)`. So if `setSelected` throws `AlreadySelectedException`, the list is left in exactly the same state as before. `List.remove(Object)` is still the method called (a `String` key and an `OptionGroup`, never `remove(int)`). The group is now looked up once at the call site instead of twice inside the method; `Options.getOptionGroup` is a plain map lookup (`optionGroups.get(opt.getKey())`) with no side effects, so this is not observable. Parser still uses the overridable `getOptions()` for that lookup and DefaultParser still uses the `options` field, matching each original.
- **Exceptions declared.** `markSeen` throws `AlreadySelectedException`, the same as the old DefaultParser method and a subtype of the `ParseException` the old Parser method declared; all call sites already declare `ParseException`.
- **Protected API kept.** `DefaultParser.expectedOpts` (protected field) stays and, after `parse` starts, references the tracker's live list, so a subclass that reads it or adds/removes elements sees and affects the same list as before. `DefaultParser.checkRequiredOptions()`, `Parser.checkRequiredOptions()`, `Parser.getRequiredOptions()` and `Parser.setOptions()` keep their signatures and now delegate. `Parser.getRequiredOptions()` returns `null` before `setOptions` runs, as the old field did (null guard). `checkRequiredOptions()` before any parse still fails with a `NullPointerException`, as before. Only private members were removed (`updateRequiredOptions` x2, the old raw `List` field in Parser), and `RequiredOptions` is package-private.
- **Handled risk (subclass hooks, by design of the outline).** Before, a subclass that *reassigned* `DefaultParser.expectedOpts` to a different list in the middle of a parse, or *overrode* `Parser.getRequiredOptions()` to return another list, changed which list `checkRequiredOptions` and the removal code worked on. Now both use the tracker's own list. Mutating the list in place still works exactly as before. Nothing in the library or in `src/test` reassigns that field or overrides that getter (grep checked), and the outline explicitly asks for the state and the bodies to move into the new class with the protected members as delegates, so I kept this design and flag it for the reviewer.

### 5. Deviations from the plan
None. (One plan detail was corrected before editing: DefaultParser keeps its `ArrayList` import because `getMatchingLongOptions` still uses it; only Parser's import became unused and was removed.)

### 6. Observations (not changed)
- `Options.requiredOpts` is still a `List<Object>` mixing `String` keys and `OptionGroup` objects (with its own "TODO this seems wrong"), and `MissingOptionException` still formats each element with `toString()`. Changing either would change `Options.getRequiredOptions()` / `getMissingOptions()` contents or the message, which the outline says to keep, so they were left alone.
- `Options.addOption` dedups required keys with `contains` + `remove(indexOf)` (moving a re-added key to the end), but `addOptionGroup` adds a required group every time it is called, so adding the same required group twice lists it twice in the "Missing required options" message. Left as is.
- Raw types remain in the protected API (`DefaultParser.expectedOpts`, `Parser.getRequiredOptions()`, `MissingOptionException(List)` / `getMissingOptions()`); they cannot be generified without changing signatures.
- `MissingOptionException` keeps a reference to the parser's live list, so code that mutates that list after the exception is thrown (e.g. a subclass through `expectedOpts`) changes what the exception reports (unchanged behaviour).
- The two parsers still duplicate properties handling (`Parser.processProperties` vs `DefaultParser.handleProperties`), with small differences: Parser swallows `RuntimeException` from `processValue` and adds the option before ticking it off, while DefaultParser strips quotes and goes through `handleOption`. This is a separate duplication and was not refactored.
- `DefaultParser.parse` and `Parser.parse` clear the selected option of every group (`group.setSelected(null)`), i.e. they mutate the caller's shared `Options` object; this is parsing state stored outside the parser.

### 7. Self-assessment
- Smell removed: partly. The parser-side part of the Shotgun Surgery is gone: the "still expected" state and the logic that ticks options/groups off and throws `MissingOptionException` now live in one class (`RequiredOptions`) instead of two cloned copies in `DefaultParser` and `Parser`, so changing how a required option is ticked off or reported touches one class. The mixed String/OptionGroup list built by `Options` and the `toString()`-based message in `MissingOptionException` remain, as the outline requires their contents to stay the same.
- Expected effect on size: DefaultParser and Parser each lose one private method and a few lines (about -28 and -26 lines); one new small class (~87 lines with Javadoc) is added, so total LOC rises slightly while the duplicated logic exists only once. DefaultParser gains one private field.
- Expected effect on cohesion: better for both parsers (a side concern and its method leave; LCOM should drop or stay the same). `RequiredOptions` is highly cohesive (every method uses its single field).
- Expected effect on coupling: `Parser` and `DefaultParser` no longer construct `MissingOptionException` or hold the raw list logic; they now call `RequiredOptions` instead. They still name `MissingOptionException` in the `throws` clause of `checkRequiredOptions()` and still use `OptionGroup` elsewhere, so their CBO should stay about the same or rise by 1 (the new `RequiredOptions` dependency). `RequiredOptions` adds one new class coupled to `Options`, `Option`, `OptionGroup`, `MissingOptionException` and `AlreadySelectedException`.

## 5. Refactored code (after refactoring)

_The same members after the refactoring, plus any new members or files. Full files: `refactored/`; diff: `changes.patch`._

### [new] `DefaultParser.java` > `DefaultParser#requiredOptions` (lines 181-182)

```java
    /** Tracks the required options and groups not found yet; {@link #expectedOpts} is its live list. */
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

### [changed] `DefaultParser.java` > `DefaultParser.handleOption(Option)` (lines 420-427)

```java
    private void handleOption(final Option option) throws ParseException {
        // check the previous option before handling the next one
        checkRequiredArgs();
        final Option copy = (Option) option.clone();
        requiredOptions.markSeen(copy, options.getOptionGroup(copy));
        cmd.addOption(copy);
        currentOption = copy.hasArg() ? copy : null;
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
        expectedOpts = requiredOptions.getExpected();
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
    /** Tracks the required options and groups not found yet. */
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
        return requiredOptions == null ? null : requiredOptions.getExpected();
    }
```

### [changed] `Parser.java` > `Parser.processOption(String,ListIterator<String>)` (lines 228-252)

```java
    /**
     * Process the Option specified by {@code arg} using the values retrieved from the specified iterator
     * {@code iter}.
     *
     * @param arg The String value representing an Option
     * @param iter The iterator over the flattened command line arguments.
     * @throws ParseException if {@code arg} does not represent an Option
     */
    protected void processOption(final String arg, final ListIterator<String> iter) throws ParseException {
        final boolean hasOption = getOptions().hasOption(arg);
        // if there is no option throw an UnrecognizedOptionException
        if (!hasOption) {
            throw new UnrecognizedOptionException("Unrecognized option: " + arg, arg);
        }
        // get the option represented by arg
        final Option opt = (Option) getOptions().getOption(arg).clone();
        // update the required options and groups
        requiredOptions.markSeen(opt, getOptions().getOptionGroup(opt));
        // if the option takes an argument value
        if (opt.hasArg()) {
            processArgs(opt, iter);
        }
        // set the option on the command line
        cmd.addOption(opt);
    }
```

### [changed] `Parser.java` > `Parser.processProperties(Properties)` (lines 254-293)

```java
    /**
     * Sets the values of Options using the values in {@code properties}.
     *
     * @param properties The value properties to be processed.
     * @throws ParseException if there are any problems encountered while processing the properties.
     */
    protected void processProperties(final Properties properties) throws ParseException {
        if (properties == null) {
            return;
        }
        for (final Enumeration<?> e = properties.propertyNames(); e.hasMoreElements();) {
            final String option = e.nextElement().toString();
            final Option opt = options.getOption(option);
            if (opt == null) {
                throw new UnrecognizedOptionException("Default option wasn't defined", option);
            }
            // if the option is part of a group, check if another option of the group has been selected
            final OptionGroup group = options.getOptionGroup(opt);
            final boolean selected = group != null && group.isSelected();
            if (!cmd.hasOption(option) && !selected) {
                // get the value from the properties instance
                final String value = properties.getProperty(option);
                if (opt.hasArg()) {
                    if (Util.isEmpty(opt.getValues())) {
                        try {
                            opt.processValue(value);
                        } catch (final RuntimeException exp) { // NOPMD
                            // if we cannot add the value don't worry about it
                        }
                    }
                } else if (!("yes".equalsIgnoreCase(value) || "true".equalsIgnoreCase(value) || "1".equalsIgnoreCase(value))) {
                    // if the value is not yes, true or 1 then don't add the
                    // option to the CommandLine
                    continue;
                }
                cmd.addOption(opt);
                requiredOptions.markSeen(opt, getOptions().getOptionGroup(opt));
            }
        }
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

### [new file] `RequiredOptions.java` > `(whole file)` (lines 1-88)

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
 * Tracks, for one parse, the required options and required option groups that have not been found yet on the command
 * line.
 * <p>
 * The expected elements are the ones returned by {@link Options#getRequiredOptions()}: {@code String} keys for required
 * options and {@link OptionGroup} instances for required groups, in the same order.
 * </p>
 */
final class RequiredOptions {

    /** The required options and groups still expected to be found when parsing the command line. */
    private final List<Object> expected;

    /**
     * Constructs a new instance expecting all the required options and groups of the specified options.
     *
     * @param options the options being parsed.
     */
    RequiredOptions(final Options options) {
        this.expected = new ArrayList<>(options.getRequiredOptions());
    }

    /**
     * Throws a {@link MissingOptionException} if all of the required options are not present.
     *
     * @throws MissingOptionException if any of the required Options are not present.
     */
    void checkAllPresent() throws MissingOptionException {
        // if there are required options that have not been processed
        if (!expected.isEmpty()) {
            throw new MissingOptionException(expected);
        }
    }

    /**
     * Gets the live list of the required options and groups not found yet.
     *
     * @return the required options and groups still expected.
     */
    List<Object> getExpected() {
        return expected;
    }

    /**
     * Removes the option or its group from the list of expected elements, and makes the option the selected option of
     * its group.
     *
     * @param option the option found on the command line.
     * @param group the group of the option, or {@code null} if the option is not in a group.
     * @throws AlreadySelectedException if another option of the group has already been selected.
     */
    void markSeen(final Option option, final OptionGroup group) throws AlreadySelectedException {
        // if the option is a required option remove the option from the expected list
        if (option.isRequired()) {
            expected.remove(option.getKey());
        }
        // if the option is in an OptionGroup make that option the selected option of the group
        if (group != null) {
            if (group.isRequired()) {
                expected.remove(group);
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
