/* SPDX-License-Identifier: Apache-2.0 */
/* Deliberate UB: used ONLY to validate the UBSan fail-fast test gate.
 * Never link this into the TOMBSTONE engine or release binaries.
 */
#include <limits.h>
int main(void)
{
    volatile int max = INT_MAX;
    volatile int one = 1;
    volatile int overflow = max + one;
    (void)overflow;
    return 0;
}
