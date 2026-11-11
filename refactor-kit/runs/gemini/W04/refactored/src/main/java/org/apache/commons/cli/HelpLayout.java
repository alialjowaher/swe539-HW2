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
