#!/usr/bin/env python3
"""Generate a modular calculate_hash proof from exactly unchanged receipt.c.

Provider calls are EXTERNAL ASSUMPTIONS with a proof-only private state
footprint; this does not prove their internals, allocation or SHA correctness.
No actual code paths are replaced or mocked. The only C declaration added is
a proof-only abstract byte representing inaccessible private provider state.
"""
import argparse
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("phase18_overlay",ROOT/"tools/phase18_wp_overlay.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
INCLUDES="#include <string.h>\n"
# Explicitly overapproximates effects visible to caller: separate private
# provider state; the actual heap layout and lifetime remain unproved.
MODEL=r"""/* Proof-only model of externally owned SHA state, NOT a provider implementation.
 * The real provider may modify its private context; no caller input or
 * unrelated buffer may be modified under these assumed contracts.
 */
static unsigned char model_private_provider_state;
/*@
  requires \valid(out_ctx);
  assigns *out_ctx, model_private_provider_state;
  ensures \result == TB_OK || \result == TB_ERR_MEMORY ||
          \result == TB_ERR_CRYPTO || \result == TB_ERR_STATE;
  ensures \result == TB_OK ==> *out_ctx != \null;
*/
tb_status tb_sha256_new(tb_sha256_ctx **out_ctx);
/*@
  requires ctx != \null;
  requires length == 0 || \valid_read(((const unsigned char *)data)+(0 .. length-1));
  assigns model_private_provider_state;
  ensures \result == TB_OK || \result == TB_ERR_CRYPTO ||
          \result == TB_ERR_MEMORY || \result == TB_ERR_STATE;
*/
tb_status tb_sha256_update(tb_sha256_ctx *ctx,const void *data,size_t length);
/*@
  requires ctx != \null;
  requires \valid(out+(0 .. 31));
  assigns out[0 .. 31], model_private_provider_state;
  ensures \result == TB_OK || \result == TB_ERR_CRYPTO ||
          \result == TB_ERR_MEMORY || \result == TB_ERR_STATE;
*/
tb_status tb_sha256_final(tb_sha256_ctx *ctx,unsigned char out[32]);
/*@
  assigns model_private_provider_state;
*/
void tb_sha256_free(tb_sha256_ctx *ctx);
"""
FORMAT=r"""/*@
  requires \valid_read(r);
  requires capacity > 0;
  requires \valid(buffer+(0 .. capacity-1));
  requires \valid(size);
  requires \separated(r,buffer+(0 .. capacity-1),size);
  assigns buffer[0 .. capacity-1], *size;
  ensures \result == TB_OK || \result == TB_ERR_CRYPTO ||
          \result == TB_ERR_LENGTH;
  ensures \result == TB_OK ==> *size < capacity;
*/
"""
GOOD=r"""/*@
  requires \valid_read(r);
  assigns \nothing;
  ensures \result == 0 || \result == 1;
*/
"""
def render():
    b=m.SOURCE.read_bytes()
    if m.git_blob(b)!=m.EXPECTED_BLOB:raise ValueError("source drift")
    source=b.decode("utf-8")
    rendered=m.render(source)
    if source.count(INCLUDES)!=1:raise ValueError("includes changed")
    rendered=rendered.replace(INCLUDES,INCLUDES+MODEL,1)
    insert={
        "static int good_receipt(const tb_receipt_v1 *r)":GOOD,
        "static tb_status format_json(const tb_receipt_v1 *r, int with_hash,":FORMAT
    }
    for marker,contract in insert.items():
        if source.count(marker)!=1:raise ValueError("missing private production helper")
        rendered=rendered.replace(marker,contract+marker,1)
    stripped=rendered.replace(MODEL,"",1)
    for fragment in list(m.ANNOTATIONS.values())+list(insert.values()):
        stripped=stripped.replace(fragment,"",1)
    if stripped!=source:raise ValueError("not exact original production source")
    return rendered

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(render(),encoding="utf-8")
    print("PASS: unchanged real calculate_hash body, modular provider/formatter assumptions declared")
    print("LIMIT: private state abstraction, provider allocation, libc and SHA correctness NOT proved")
if __name__=="__main__":main()
