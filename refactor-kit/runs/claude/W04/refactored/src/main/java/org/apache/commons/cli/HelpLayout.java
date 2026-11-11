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
