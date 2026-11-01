#!/usr/bin/env python3
"""Phase 19: exact-source, annotation-only equal32 proof overlay.

This is a real-function proof, not a substitute equal32 implementation.
The external memcmp semantic contract is explicitly ASSUMED, not proved.
"""
import argparse
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"tools/phase18_wp_overlay.py"
spec=importlib.util.spec_from_file_location("phase18_overlay",path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
EXPECTED=module.EXPECTED_BLOB
BEFORE='#include <string.h>\n'
EXT=r"""/* Phase 19 proof-only external-call alias. The REAL equal32 C body is
 * byte-for-byte unchanged; the preprocessor binds its memcmp call to an
 * independently assumed specification, not Frama-C libc string.h contracts
 * containing currently unsupported danglingness predicates.
 * This does NOT prove real libc memcmp. It MUST be separately refined.
 */
#define memcmp phase19_memcmp
/*@
  requires n == 32;
  requires \valid_read(((const unsigned char*)s1)+(0 .. n-1));
  requires \valid_read(((const unsigned char*)s2)+(0 .. n-1));
  assigns \nothing;
  ensures \result == 0 <==>
    (\forall integer i; 0 <= i < 32 ==>
      ((const unsigned char*)s1)[i] == ((const unsigned char*)s2)[i]);
*/
extern int phase19_memcmp(const void *s1, const void *s2, size_t n);
"""
def render() -> str:
    data=module.SOURCE.read_bytes()
    assert module.git_blob(data)==EXPECTED,"source identity changed"
    original=data.decode("utf-8")
    base=module.render(original)
    assert original.count(BEFORE)==1
    result=base.replace(BEFORE,BEFORE+EXT,1)
    assert result.replace(EXT,"",1)==base
    result=result.replace(EXT,"",1)
    for item in module.ANNOTATIONS.values():
        result=result.replace(item,"",1)
    assert result==original,"verification annotations must strip to production C99"
    return base.replace(BEFORE,BEFORE+EXT,1)

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--output",required=True,type=Path)
    args=arg.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(render(),encoding="utf-8")
    print("PASS: Phase 19 actual equal32 body, exact unchanged C99 and explicit memcmp contract")
    print("LIMIT: libc memcmp implementation and runtime are external assumptions")

if __name__=="__main__":main()
