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
