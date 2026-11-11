# TASK - refactor smell B02 (Shotgun Surgery) in Apache Commons CLI 1.9.0

| | |
|---|---|
| Run | Gemini · Gemini 3.1 Pro · mode: agent · started 2026-11-11 11:53 |
| Workspace (edit only here) | `workspace/gemini/commons-cli` |
| Branch | `refactor/B02`, created from `rel/commons-cli-1.9.0` (commit 698b238276) |
| Your process notes | `runs/gemini/B02/process.md` |
| Original code saved in | `runs/gemini/B02/original/` |

## 1. The smell

| Field | Value |
|---|---|
| ID | B02 |
| Smell type | Between classes |
| Code smell | Shotgun Surgery |
| Class(es) | Options, DefaultParser, Parser, MissingOptionException |
| Method / member | Options.requiredOpts / addOption / addOptionGroup / getRequiredOptions; DefaultParser.expectedOpts / updateRequiredOptions / checkRequiredOptions; Parser.requiredOptions / updateRequiredOptions / checkRequiredOptions; MissingOptionException |
| Lines (1.9.0) | Options 52–54, 72–77, 138–140, 273–275; DefaultParser 179, 278–283, 708, 760–775; Parser 41, 48–53, 306, 314–329; MissingOptionException 35–83 |
| Priority |  |

**Evidence.** Tracking of required options and groups is spread over 4 classes. Options keeps them in a List<Object> that mixes String keys and OptionGroup objects (its own comment: "TODO this seems wrong"). Both parsers copy it into raw List fields, and each has its own near-identical updateRequiredOptions and checkRequiredOptions (Type III clones). MissingOptionException takes a raw List and builds its message from each element's toString(). Changing how a required option is identified or reported means editing Options, DefaultParser, Parser and MissingOptionException together. The same two parsers also duplicate properties handling (Parser.processProperties 264–297 vs DefaultParser.handleProperties 434–463).


## 2. The refactoring to apply

**Technique:** Extract Class + Move Method + Move Field

_Source: review sheet suggestion (column 'Suggested refactoring')._

**How (outline):** Create a package-private class (e.g. RequiredOptions) that owns the 'still expected' list, with markSeen(Option, OptionGroup) and checkAllPresent() (throws MissingOptionException). Move the updateRequiredOptions / checkRequiredOptions bodies from both parsers into it, and move the expectedOpts / requiredOptions state there. Keep the protected members as delegates, and keep Options.getRequiredOptions() and MissingOptionException.getMissingOptions() returning the same contents.

**Risks to watch:** Medium. Protected members (DefaultParser.expectedOpts, checkRequiredOptions; Parser.getRequiredOptions) are subclass API. Tests assert exact messages such as "Missing required options: b, c" (AbstractParserTestCase 398, OptionsTest 276), so element order must be preserved.

**Expected effect on metrics:** Size: duplicated logic removed from 2 parsers. Cohesion: parsers lose a side concern (LCOM drops). Coupling: parsers depend on one tracker instead of OptionGroup + MissingOptionException + Options internals (parser CBO may drop by 1–2), but the system gains one class.


Apply **this** technique and nothing else. If you believe it cannot be applied without breaking a rule below, stop, explain why in process.md section 5, and run `finish` without making a different refactoring.

## 3. Where the code is (original, before refactoring)

- `src/main/java/org/apache/commons/cli/Options.java` > `Options#requiredOpts` (lines 51-54)
- `src/main/java/org/apache/commons/cli/Options.java` > `Options.addOption(Option)` (lines 59-80)
- `src/main/java/org/apache/commons/cli/Options.java` > `Options.addOptionGroup(OptionGroup)` (lines 131-150)
- `src/main/java/org/apache/commons/cli/Options.java` > `Options.getRequiredOptions()` (lines 268-275)
- `src/main/java/org/apache/commons/cli/DefaultParser.java` > `DefaultParser#expectedOpts` (lines 178-179)
- `src/main/java/org/apache/commons/cli/DefaultParser.java` > `DefaultParser.checkRequiredOptions()` (lines 273-283)
- `src/main/java/org/apache/commons/cli/DefaultParser.java` > `DefaultParser.parse(Options,String[],Properties,boolean)` (lines 689-725)
- `src/main/java/org/apache/commons/cli/DefaultParser.java` > `DefaultParser.updateRequiredOptions(Option)` (lines 755-775)
- `src/main/java/org/apache/commons/cli/Parser.java` > `Parser#requiredOptions` (lines 40-41)
- `src/main/java/org/apache/commons/cli/Parser.java` > `Parser.checkRequiredOptions()` (lines 43-53)
- `src/main/java/org/apache/commons/cli/Parser.java` > `Parser.getRequiredOptions()` (lines 75-82)
- `src/main/java/org/apache/commons/cli/Parser.java` > `Parser.setOptions(Options)` (lines 299-307)
- `src/main/java/org/apache/commons/cli/Parser.java` > `Parser.updateRequiredOptions(Option)` (lines 309-329)
- `src/main/java/org/apache/commons/cli/MissingOptionException.java` - whole file (lines 1-85)

Most relevant test classes: OptionsTest, DefaultParserTest, BasicParserTest, GnuParserTest, PosixParserTest, OptionGroupTest

#### `Options.java` > `Options#requiredOpts` (lines 51-54)

```java
    /** A map of the required options */
    // N.B. This can contain either a String (addOption) or an OptionGroup (addOptionGroup)
    // TODO this seems wrong
    private final List<Object> requiredOpts = new ArrayList<>();
```

#### `Options.java` > `Options.addOption(Option)` (lines 59-80)

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

#### `Options.java` > `Options.addOptionGroup(OptionGroup)` (lines 131-150)

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

#### `Options.java` > `Options.getRequiredOptions()` (lines 268-275)

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

#### `DefaultParser.java` > `DefaultParser#expectedOpts` (lines 178-179)

```java
    /** The required options and groups expected to be found when parsing the command line. */
    protected List expectedOpts;
```

#### `DefaultParser.java` > `DefaultParser.checkRequiredOptions()` (lines 273-283)

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

#### `DefaultParser.java` > `DefaultParser.parse(Options,String[],Properties,boolean)` (lines 689-725)

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

#### `DefaultParser.java` > `DefaultParser.updateRequiredOptions(Option)` (lines 755-775)

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

#### `Parser.java` > `Parser#requiredOptions` (lines 40-41)

```java
    /** List of required options strings */
    private List requiredOptions;
```

#### `Parser.java` > `Parser.checkRequiredOptions()` (lines 43-53)

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

#### `Parser.java` > `Parser.getRequiredOptions()` (lines 75-82)

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

#### `Parser.java` > `Parser.setOptions(Options)` (lines 299-307)

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

#### `Parser.java` > `Parser.updateRequiredOptions(Option)` (lines 309-329)

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

#### `src/main/java/org/apache/commons/cli/MissingOptionException.java` (whole file, 85 lines - open it in the workspace)


## 4. Rules (non-negotiable)

1. **One smell, one technique.** Change only what is needed to remove smell B02 with the technique given in "The refactoring to apply". No other refactorings, renames, reformatting, comment edits or improvements anywhere else.
2. **Behaviour must not change.** Same return values, same printed text (including spaces, line breaks and order), same exceptions and messages, same side effects. If the existing code looks wrong, keep its behaviour and note it under "Observations" in the process notes. Fixing bugs is out of scope.
3. **The original tests are the judge, so don't touch them.** Do not modify, add, delete, skip or disable anything under `src/test/`.
4. **Keep the public and protected API.** Do not remove, rename or change the signature, visibility or modifiers of any public or protected class, constructor, method or field. If the technique moves or renames one, keep the old one and make it delegate to the new one. New members should be `private` or package-private unless the technique needs otherwise.
5. **Java 8, no new dependencies.** Do not edit `pom.xml` or any build file. Use only Java 8 language features and APIs (no `var`, records, switch expressions, text blocks, `List.of`, `String.isBlank`, ...).
6. **New classes** go in package `org.apache.commons.cli` under `src/main/java`, start with the same Apache License header as the existing files, have a class Javadoc, and are package-private unless they must be public.
7. **Keep the house style:** 4-space indentation; `final` on parameters and locals, as in the surrounding code; a short Javadoc on every new method.
8. **Small steps.** Compile and run the tests after every step. If a step breaks a test, undo or fix that step before moving on; don't pile changes on top of a failure.
9. **Stay in your lane.** Edit only inside your own workspace clone (`workspace/gemini/commons-cli`). Don't commit, push or switch branches; `kit.py` does that. Don't open other LLMs' folders under `runs/` or `workspace/`. Don't edit the kit or the Excel files by hand, or anything in the run folder except `process.md`; `kit.py` writes them. You **are allowed** to run `python kit.py metrics --smell B02 --llm "<your LLM name>"` after your last `finish`: it measures size, cohesion and coupling before and after with CK and fills your run's row of the Excel **Metrics** sheet.


## 5. Definition of done

- `python kit.py test --llm "Gemini"` shows the same number of passing tests as the original run (see `runs/gemini/B02/tests_original.json`).
- No file under `src/test/` changed, and no public or protected API was removed or changed.
- The smell is addressed with the technique in section 2, and nothing else changed.
- `process.md` is complete: every _italic guidance line_ has been replaced.
- `python kit.py finish --smell B02 --llm "Gemini"` has run and printed a verdict.

## 6. Commands

| Purpose | Command |
|---|---|
| Quick test (one class) | `python kit.py test --llm "Gemini" --only OptionsTest` |
| Full test suite | `python kit.py test --llm "Gemini"` |
| Finish the run | `python kit.py finish --smell B02 --llm "Gemini"` |
