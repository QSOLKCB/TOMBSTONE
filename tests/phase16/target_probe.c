/* SPDX-License-Identifier: Apache-2.0 */
/* Phase 16: executable C99 platform observation, never a hardware proof.
 * Deliberately abort unsupported models rather than silently extrapolate.
 */
#include "tombstone/receipt.h"
#include <limits.h>
#include <stdint.h>
#include <stdio.h>

#if CHAR_BIT != 8
#error "Phase 16 supports only eight-bit char targets"
#endif
#if !defined(UINT32_MAX) || !defined(UINT64_MAX) || !defined(UINTPTR_MAX)
#error "Phase 16 requires exact-width uint32_t, uint64_t and uintptr_t"
#endif

int main(void)
{
    const uint32_t one = 1u;
    const unsigned char *bytes = (const unsigned char *)&one;
    const char *endian = bytes[0] == 1u ? "little" :
                         bytes[sizeof(one) - 1u] == 1u ? "big" : "unknown";
    if (sizeof(void *) != 8u || sizeof(size_t) != 8u ||
        sizeof(uint32_t) != 4u || sizeof(uint64_t) != 8u ||
        UINTPTR_MAX != UINT64_MAX || bytes[0] != 1u ||
        sizeof(tb_status) != sizeof(int) ||
        sizeof(tb_evidence_kind) != sizeof(int) ||
        TB_FINGERPRINT_ABI_VERSION != 1u ||
        TB_EVIDENCE_ABI_VERSION != 1u ||
        TB_RECEIPT_ABI_VERSION != 1u) {
        fputs("FAIL: unsupported target representation\n", stderr);
        return 2;
    }
    printf("format=tombstone.phase16.target-observation\n");
    printf("char_bit=%u\n", (unsigned)CHAR_BIT);
    printf("pointer_bits=%zu\n", sizeof(void *) * CHAR_BIT);
    printf("size_t_bits=%zu\n", sizeof(size_t) * CHAR_BIT);
    printf("uint32_bits=%zu\n", sizeof(uint32_t) * CHAR_BIT);
    printf("uint64_bits=%zu\n", sizeof(uint64_t) * CHAR_BIT);
    printf("endianness=%s\n", endian);
    printf("status_enum_bytes=%zu\n", sizeof(tb_status));
    printf("evidence_enum_bytes=%zu\n", sizeof(tb_evidence_kind));
    printf("fingerprint_abi=%u\n", TB_FINGERPRINT_ABI_VERSION);
    printf("evidence_abi=%u\n", TB_EVIDENCE_ABI_VERSION);
    printf("receipt_abi=%u\n", TB_RECEIPT_ABI_VERSION);
    return 0;
}
