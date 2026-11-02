#!/usr/bin/env python3
"""Actual validator/formatter bodies; versioned refinement of Phase 19.

Formatting libc calls have explicit, fixed-format, fixed-arity external
contracts. These are not implementations or a proof of libc/canonical JSON.
Every original C byte survives stripping the registered proof fragments.
"""
import argparse
from pathlib import Path

import phase19_bridge_overlay as bridge

ROOT = Path(__file__).resolve().parents[1]
PREDICATES = r"""/*@
  predicate p20_zero{L}(unsigned char *p) =
    \forall integer k; 0 <= k < 32 ==> p[k] == 0;
  predicate p20_equal{L}(unsigned char *a, unsigned char *b) =
    \forall integer k; 0 <= k < 32 ==> a[k] == b[k];
  predicate p20_evidence{L}(tb_evidence_v1 *e) =
    e->before_size <= TB_EVIDENCE_MAX_BYTES &&
    e->after_size <= TB_EVIDENCE_MAX_BYTES &&
    e->deleted_size <= TB_EVIDENCE_MAX_BYTES &&
    e->deleted_offset <= TB_EVIDENCE_MAX_BYTES &&
    ((e->kind == TB_EVIDENCE_UNCHANGED &&
      e->before_size == e->after_size && p20_equal(&e->before_sha256[0],&e->after_sha256[0]) &&
      e->deleted_size == 0 && e->deleted_offset == 0 && p20_zero(&e->deleted_sha256[0])) ||
     (e->kind == TB_EVIDENCE_OBSERVED_TRANSITION &&
      (e->before_size != e->after_size || !p20_equal(&e->before_sha256[0],&e->after_sha256[0])) &&
      e->deleted_size == 0 && e->deleted_offset == 0 && p20_zero(&e->deleted_sha256[0])) ||
     (e->kind == TB_EVIDENCE_EXPLICIT_DELETE &&
      0 < e->deleted_size <= e->before_size &&
      e->after_size == (integer)e->before_size - e->deleted_size &&
      e->deleted_offset <= (integer)e->before_size - e->deleted_size));
  predicate p20_receipt{L}(tb_receipt_v1 *r) =
    (r->has_previous == 0 || r->has_previous == 1) &&
    (r->has_previous != 0 || p20_zero(&r->previous_hash[0])) && p20_evidence(&r->evidence);
  predicate p20_cstr{L}(char *s, integer bound) =
    \exists integer k; 0 <= k < bound && \valid_read(s+(0 .. k)) && s[k] == '\0';
  predicate p20_text{L}(char *a, char *b, integer n) =
    \valid_read(a+(0 .. n-1)) && \valid_read(b+(0 .. n-1)) &&
    (\forall integer k; 0 <= k < n ==> a[k] == b[k]);
*/
"""
ZERO = r"""/*@
  requires \valid_read(p+(0 .. 31));
  assigns \nothing;
  ensures \result == 0 || \result == 1;
  ensures zero_equivalence: \result == 1 <==> p20_zero(p);
*/
"""
ZERO_LOOP = r"""    /*@
      loop invariant 0 <= i <= 32;
      loop invariant \forall integer k; 0 <= k < i ==> p[k] == 0;
      loop assigns i;
      loop variant 32 - i;
    */
"""
EVIDENCE = r"""/*@
  requires \valid_read(e);
  assigns \nothing;
  ensures \result == 0 || \result == 1;
  ensures evidence_equivalence: \result == 1 <==> p20_evidence(e);
*/
"""
GOOD_MARKER = "static int good_receipt(const tb_receipt_v1 *r)"
FORMAT_MARKER = "static tb_status format_json(const tb_receipt_v1 *r, int with_hash,"
GOOD = bridge.p19.GOOD.replace("*/", r"""  ensures receipt_equivalence: \result == 1 <==> p20_receipt(r);
*/""")
FORMAT = bridge.p19.FORMAT.replace("*/", r"""  ensures size_on_error: \result != TB_OK ==> *size == \old(*size);
  ensures terminated: \result == TB_OK ==> buffer[*size] == '\0';
  ensures input_unchanged: \forall integer k; 0 <= k < sizeof(*r) ==>
    ((const unsigned char *)r)[k] == \old(((const unsigned char *)r)[k]);
*/""")
HEX = r"""/*@
  requires \valid_read(digest+(0 .. 31));
  requires \valid(out+(0 .. 64));
  requires \separated(digest+(0 .. 31), out+(0 .. 64));
  assigns out[0 .. 64];
  ensures \result == TB_OK;
  ensures nul_terminated: out[64] == '\0';
*/
"""
HEX32 = r"""/*@
  requires \valid_read(d+(0 .. 31));
  requires \valid(b+(0 .. 64));
  requires \separated(d+(0 .. 31), b+(0 .. 64));
  assigns b[0 .. 64];
  ensures \result == 1;
  ensures b[64] == '\0';
  ensures p20_cstr(b,65);
*/
"""

# These are the exact literal formats at the four pinned call sites. The
# contract checks bytes, not pointer identity/string-literal interning.
LIBC = r"""/* External fixed-format libc premises, not a libc implementation. */
static const char p20_fmt_deleted[] __attribute__((unused)) =
  "{\"offset\":%" PRIu64 ",\"sha256\":\"%s\",\"size\":%" PRIu64 "}";
static const char p20_fmt_previous[] __attribute__((unused)) = "\"%s\"";
static const char p20_fmt_hash[] __attribute__((unused)) = ",\"receipt_hash\":\"%s\"";
static const char p20_fmt_receipt[] __attribute__((unused)) =
  "{\"after\":{\"sha256\":\"%s\",\"size\":%" PRIu64 "},"
  "\"before\":{\"sha256\":\"%s\",\"size\":%" PRIu64 "},"
  "\"deleted\":%s,\"format\":\"tombstone.receipt\","
  "\"kind\":\"%s\",\"previous_receipt_hash\":%s%s,\"version\":1}";
/*@
  requires n > 0 && \valid(dst+(0 .. n-1));
  requires p20_text(fmt,&p20_fmt_deleted[0],sizeof(p20_fmt_deleted));
  requires p20_cstr(hex,65);
  requires \separated(dst+(0 .. n-1), fmt+(..), hex+(..));
  assigns dst[0 .. n-1];
  ensures 0 <= \result < n ==> dst[\result] == '\0';
*/
extern int p20_snprintf_deleted(char *dst,size_t n,const char *fmt,
                                uint64_t offset,const char *hex,uint64_t size);
/*@
  requires n > 0 && \valid(dst+(0 .. n-1));
  requires p20_text(fmt,&p20_fmt_previous[0],sizeof(p20_fmt_previous)) ||
           p20_text(fmt,&p20_fmt_hash[0],sizeof(p20_fmt_hash));
  requires p20_cstr(hex,65);
  requires \separated(dst+(0 .. n-1), fmt+(..), hex+(..));
  assigns dst[0 .. n-1];
  ensures 0 <= \result < n ==> dst[\result] == '\0';
*/
extern int p20_snprintf_string(char *dst,size_t n,const char *fmt,const char *hex);
/*@
  requires n > 0 && \valid(dst+(0 .. n-1));
  requires p20_text(fmt,&p20_fmt_receipt[0],sizeof(p20_fmt_receipt));
  requires p20_cstr(after,65) && p20_cstr(before,65);
  requires p20_cstr(deleted,192) && p20_cstr(kind,20);
  requires p20_cstr(previous,96) && p20_cstr(own,96);
  requires \separated(dst+(0 .. n-1), fmt+(..), after+(..), before+(..),
                      deleted+(..), kind+(..), previous+(..), own+(..));
  assigns dst[0 .. n-1];
  ensures 0 <= \result < n ==> dst[\result] == '\0';
*/
extern int p20_snprintf_receipt(char *dst,size_t n,const char *fmt,
  const char *after,uint64_t after_size,const char *before,uint64_t before_size,
  const char *deleted,const char *kind,const char *previous,const char *own);
/*@
  requires n == 5;
  requires \valid(((unsigned char *)dst)+(0 .. n-1));
  requires \valid_read(((const unsigned char *)src)+(0 .. n-1));
  requires \separated(((unsigned char *)dst)+(0 .. n-1),
                       ((const unsigned char *)src)+(0 .. n-1));
  assigns ((unsigned char *)dst)[0 .. n-1];
  ensures \forall integer k; 0 <= k < n ==>
    ((unsigned char *)dst)[k] == \old(((const unsigned char *)src)[k]);
  ensures \forall integer k; 0 <= k < n ==>
    ((char *)dst)[k] == \old(((const char *)src)[k]);
*/
extern void *p20_memcpy(void *dst,const void *src,size_t n);
#define memcpy p20_memcpy
#define P20_PICK(_1,_2,_3,_4,_5,_6,_7,_8,_9,_10,_11,NAME,...) NAME
#define snprintf(...) P20_PICK(__VA_ARGS__,p20_snprintf_receipt,p20_bad10,p20_bad9,p20_bad8,p20_bad7,p20_snprintf_deleted,p20_bad5,p20_snprintf_string,p20_bad3,p20_bad2,p20_bad1)(__VA_ARGS__)
"""
# Expand only the four finite, fixed-format byte equalities. The sizeof guard
# deliberately rejects a different PRIu64 expansion instead of silently
# interpreting that target's format as this 64-bit proof model's format.
FORMAT_LENGTHS = {"deleted":40,"previous":5,"hash":21,"receipt":168}
for _name,_length in FORMAT_LENGTHS.items():
    _table="p20_fmt_"+_name
    _original=f"p20_text(fmt,&{_table}[0],sizeof({_table}))"
    _checks=[f"sizeof({_table}) == {_length}",
             f"\\valid_read(fmt+(0 .. {_length-1}))",
             f"\\valid_read(&{_table}[0]+(0 .. {_length-1}))"]
    _checks += [f"fmt[{i}] == {_table}[{i}]" for i in range(_length)]
    LIBC=LIBC.replace(_original,"("+" &&\n           ".join(_checks)+")")

DECL = HEX + "tb_status tb_sha256_hex(const unsigned char digest[TB_SHA256_DIGEST_SIZE],\n                        char out[TB_SHA256_HEX_SIZE]);\n"
EXTRA = {
    "static int zero32(const unsigned char *p)": ZERO,
    "    for (i = 0; i < 32u; ++i) if (p[i]) return 0;": ZERO_LOOP,
    "static int good_evidence(const tb_evidence_v1 *e)": EVIDENCE,
    "static int hex32(const unsigned char *d, char b[TB_SHA256_HEX_SIZE])": HEX32,
}

def frame_assertions(label):
    return r"""    /*@ assert p20_size_LABEL: *size == \at(*size,Pre); */
    /*@ assert p20_input_LABEL: \forall integer j; 0 <= j < sizeof(*r) ==>
      ((const unsigned char *)r)[j] == \at(((const unsigned char *)r)[j],Pre); */
""".replace("LABEL",label)


def string_assertion(label, pairs):
    # Ghost lengths retain the actual terminator witnesses. Both the witness
    # and the original existential assertion are checked goals, not premises.
    lengths = {"dfield":"p20_dlen", "pfield":"p20_plen",
               "hfield":"p20_hlen", "kind":"p20_klen"}
    return "".join(f"    /*@ assert p20_witness_{label}_{name}: "
                   f"0 <= {lengths.get(name,'64')} < {bound} && "
                   f"{name}[{lengths.get(name,'64')}] == '\\0'; */\n"
                   f"    /*@ assert p20_string_{label}_{name}: "
                   f"p20_cstr(&{name}[0],{bound}); */\n"
                   for name,bound in pairs)


HEX_STRINGS = [(name,65) for name in ("before","after","deleted","prev","own")]
FORMAT_HINTS = {
    "    if (!hex32(e->before_sha256,before) || !hex32(e->after_sha256,after) ||":
        r"""    /*@ ghost int p20_dlen=4, p20_plen=4, p20_hlen=0, p20_klen=0; */
    /*@ assert p20_receipt_output_separation: \forall integer j;
      0 <= j < sizeof(*r) ==> \separated(((const unsigned char *)r)+j,
                                         buffer+(0 .. capacity-1)); */
    /*@ assert p20_receipt_size_separation: \forall integer j;
      0 <= j < sizeof(*r) ==> \separated(((const unsigned char *)r)+j,size); */
""",
    "    if (e->kind == TB_EVIDENCE_EXPLICIT_DELETE) {":
        r"""    /*@ assert p20_literal_bytes: p20_fmt_deleted[0] == '{' &&
      p20_fmt_previous[0] == '"' && p20_fmt_hash[0] == ',' && p20_fmt_receipt[0] == '{'; */
""" + frame_assertions("hex") + string_assertion("hex",HEX_STRINGS),
    "        if (k < 0 || (size_t)k >= sizeof(dfield)) return TB_ERR_LENGTH;":
        frame_assertions("deleted_call"),
    "    if (r->has_previous) {":
        frame_assertions("deleted") + string_assertion("deleted",HEX_STRINGS+[("dfield",192),("kind",20)]),
    "        if (k < 0 || (size_t)k >= sizeof(pfield)) return TB_ERR_LENGTH;":
        frame_assertions("previous_call"),
    "    if (with_hash) {":
        frame_assertions("previous") + string_assertion("previous",[("before",65),("after",65),("own",65),("dfield",192),("kind",20),("pfield",96)]),
    "        if (k < 0 || (size_t)k >= sizeof(hfield)) return TB_ERR_LENGTH;":
        frame_assertions("own_call"),
    "    k = snprintf(buffer,capacity,":
        frame_assertions("own") + string_assertion("own",[("before",65),("after",65),("dfield",192),("kind",20),("pfield",96),("hfield",96)]),
    "    if (k < 0 || (size_t)k >= capacity) return TB_ERR_LENGTH;":
        frame_assertions("final_call"),
    "    *size = (size_t)k;":
        r"""    /*@ assert p20_final_length: 0 <= k < capacity; */
    /*@ assert p20_final_nul: buffer[k] == '\0'; */
    /*@ assert p20_final_size_separation: \separated(buffer+k,size); */
""",
}

# These are proof assertions after existing statements, not assumed facts or
# replacement implementations. Every assertion is part of the WP inventory.
FORMAT_AFTER = {
    '        kind = "explicit-delete";\n':
        r"""        /*@ ghost p20_klen=15; */
        /*@ assert p20_kind_deleted_nul: kind[15] == '\0'; */
        /*@ assert p20_kind_deleted_string: p20_cstr(kind,20); */
        /*@ assert p20_kind_deleted_separation:
          \separated(buffer+(0 .. capacity-1),kind+(..)); */
""",
    '        kind = e->kind == TB_EVIDENCE_UNCHANGED ? "unchanged" : "observed-transition";\n':
        r"""        /*@ ghost p20_klen=e->kind == TB_EVIDENCE_UNCHANGED ? 9 : 19; */
        /*@ assert p20_kind_other_nul:
          kind[e->kind == TB_EVIDENCE_UNCHANGED ? 9 : 19] == '\0'; */
        /*@ assert p20_kind_other_string: p20_cstr(kind,20); */
        /*@ assert p20_kind_other_separation:
          \separated(buffer+(0 .. capacity-1),kind+(..)); */
""",
    '        memcpy(dfield,"null",5);\n':
        r"""        /*@ assert p20_deleted_null_byte: dfield[4] == 0; */
        /*@ assert p20_deleted_null_string: p20_cstr(&dfield[0],192); */
""",
    '    } else memcpy(pfield,"null",5);\n':
        r"""    /*@ assert p20_previous_null_byte:
      r->has_previous == 0 ==> pfield[4] == 0; */
""",
    '    *size = (size_t)k;\n':
        r"""    /*@ assert p20_input_returned: \forall integer j; 0 <= j < sizeof(*r) ==>
      ((const unsigned char *)r)[j] == \at(((const unsigned char *)r)[j],Pre); */
""",
}
for _field in ("dfield","pfield","hfield"):
    FORMAT_AFTER[f"        if (k < 0 || (size_t)k >= sizeof({_field})) return TB_ERR_LENGTH;\n"] = (
        f"        /*@ ghost p20_{_field[0]}len=k; */\n"
        f"        /*@ assert p20_{_field}_length: 0 <= k < sizeof({_field}); */\n"
        f"        /*@ assert p20_{_field}_nul: {_field}[k] == '\\0'; */\n"
        f"        /*@ assert p20_{_field}_string: p20_cstr(&{_field}[0],sizeof({_field})); */\n"
    )


def strip(text):
    for fragment in (PREDICATES, LIBC, DECL, *EXTRA.values(),
                     *FORMAT_HINTS.values(), *FORMAT_AFTER.values()):
        if text.count(fragment) != 1:
            raise ValueError("missing/duplicate Phase 20 proof fragment")
        text = text.replace(fragment,"",1)
    text = text.replace(GOOD,bridge.p19.GOOD,1).replace(FORMAT,bridge.p19.FORMAT,1)
    return bridge.strip(text)


def render():
    source = bridge.render()
    text = source.replace(bridge.p19.GOOD,GOOD,1).replace(bridge.p19.FORMAT,FORMAT,1)
    text = text.replace(bridge.eq.BEFORE,bridge.eq.BEFORE+PREDICATES+LIBC+DECL,1)
    for marker, contract in EXTRA.items():
        if text.count(marker) != 1:
            raise ValueError("actual source marker drift")
        text = text.replace(marker,contract+marker,1)
    start=text.index(FORMAT_MARKER)
    end=text.index("static tb_status calculate_hash(",start)
    body=text[start:end]
    for marker, assertion in FORMAT_HINTS.items():
        if body.count(marker) != 1:
            raise ValueError("formatter assertion site drift")
        body=body.replace(marker,assertion+marker,1)
    for marker, assertion in FORMAT_AFTER.items():
        if body.count(marker) != 1:
            raise ValueError("formatter post-statement assertion site drift")
        body=body.replace(marker,marker+assertion,1)
    text=text[:start]+body+text[end:]
    if strip(text) != bridge.p18.SOURCE.read_text():
        raise ValueError("receipt source bytes changed")
    return text


HEX_BLOBS = {"openssl":"5d9e60f88305fd108405908269a023cdff8cb8ee",
             "hacl":"a66d6a2aeb0064fbde04bd2fef34dface64e1c61"}
HEX_LOOP = r"""    /*@
      loop invariant 0 <= i <= 32;
      loop assigns i,out[0 .. 63];
      loop variant 32-i;
    */
"""


def render_hex(backend):
    path = ROOT / ("src/crypto/fingerprint.c" if backend == "openssl" else "src/crypto/fingerprint_hacl.c")
    data = path.read_bytes()
    if bridge.p18.git_blob(data) != HEX_BLOBS[backend]:
        raise ValueError("actual provider source drift")
    source = data.decode()
    body = source[source.index("tb_status tb_sha256_hex("):]
    marker = "    for (i = 0u;" if backend == "openssl" else "    for (i = 0;"
    if body.count(marker) != 1:
        raise ValueError("actual hex loop marker drift")
    overlay = HEX + body.replace(marker,HEX_LOOP+marker,1)
    if overlay.replace(HEX,"",1).replace(HEX_LOOP,"",1) != body:
        raise ValueError("hex body changed")
    return '#include "tombstone/fingerprint.h"\n' + overlay


MUTANTS = {
    "accept-invalid": ("good_receipt", "    return (r->has_previous == 0 || r->has_previous == 1) &&",
                       "    return 1;\n    return (r->has_previous == 0 || r->has_previous == 1) &&"),
    "bad-size": ("format_json", "    *size = (size_t)k;", "    *size = capacity;"),
    "error-size": ("format_json", "        if (k < 0 || (size_t)k >= sizeof(dfield)) return TB_ERR_LENGTH;",
                   "        if (k < 0 || (size_t)k >= sizeof(dfield)) { *size = 0; return TB_ERR_LENGTH; }"),
}


def mutant(name):
    source = render()
    _, old, new = MUTANTS[name]
    if source.count(old) != 1:
        raise ValueError("ambiguous mutation site")
    return source.replace(old,new,1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output",required=True,type=Path)
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--hex-backend",choices=HEX_BLOBS)
    choice.add_argument("--mutant",choices=MUTANTS)
    args = parser.parse_args()
    text = render_hex(args.hex_backend) if args.hex_backend else mutant(args.mutant) if args.mutant else render()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(text)
    print("GENERATED: exact production body with explicit external libc premises")
