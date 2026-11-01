//! A narrow safe Rust boundary around TOMBSTONE's authoritative C99 engine.
//! No hashing, splice classification or canonical JSON is reimplemented here.

use std::fmt;
use std::os::raw::{c_char, c_int, c_void};
use std::ptr;

const SHA_SIZE: usize = 32;
const JSON_MAX: usize = 1024;

#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
struct EvidenceRaw {
    kind: c_int,
    before_size: usize,
    after_size: usize,
    before_sha256: [u8; SHA_SIZE],
    after_sha256: [u8; SHA_SIZE],
    deleted_size: usize,
    deleted_offset: usize,
    deleted_sha256: [u8; SHA_SIZE],
}

#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
struct ReceiptRaw {
    evidence: EvidenceRaw,
    has_previous: c_int,
    previous_hash: [u8; SHA_SIZE],
    receipt_hash: [u8; SHA_SIZE],
}

extern "C" {
    fn tb_fingerprint_abi_version() -> u32;
    fn tb_evidence_abi_version() -> u32;
    fn tb_receipt_abi_version() -> u32;
    fn tb_sha256_bytes(data: *const c_void, length: usize, out: *mut u8) -> c_int;
    fn tb_sha256_hex(digest: *const u8, out: *mut c_char) -> c_int;
    fn tb_observe_transition(
        before: *const c_void,
        before_size: usize,
        after: *const c_void,
        after_size: usize,
        out: *mut EvidenceRaw,
    ) -> c_int;
    fn tb_witness_delete(
        before: *const c_void,
        before_size: usize,
        removed: *const c_void,
        removed_size: usize,
        offset: usize,
        after: *const c_void,
        after_size: usize,
        out: *mut EvidenceRaw,
    ) -> c_int;
    fn tb_receipt_create(
        evidence: *const EvidenceRaw,
        previous: *const u8,
        out: *mut ReceiptRaw,
    ) -> c_int;
    fn tb_receipt_encode(
        receipt: *const ReceiptRaw,
        buffer: *mut c_char,
        capacity: usize,
        written: *mut usize,
    ) -> c_int;
    fn tb_receipt_parse(json: *const c_char, length: usize, out: *mut ReceiptRaw) -> c_int;
    fn tb_receipt_verify_chain(
        receipts: *const ReceiptRaw,
        count: usize,
        trusted_head: *const u8,
    ) -> c_int;
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Error {
    Native(i32),
    InvalidHex,
    InvalidEncoding,
    AbiMismatch,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Native(code) => write!(f, "TOMBSTONE C99 error {code} ({})", match code {
                1 => "argument", 2 => "length", 3 => "allocation",
                4 => "cryptography", 5 => "state", 6 => "mismatch",
                7 => "format", _ => "unknown",
            }),
            Self::InvalidHex => write!(f, "expected exactly 64 lowercase SHA-256 hex characters"),
            Self::InvalidEncoding => write!(f, "C99 returned non-UTF-8 JSON"),
            Self::AbiMismatch => write!(f, "C99 ABI version does not match Rust bindings"),
        }
    }
}
impl std::error::Error for Error {}

fn ok(code: c_int) -> Result<(), Error> {
    if code == 0 { Ok(()) } else { Err(Error::Native(code)) }
}

pub fn check_abi() -> Result<(), Error> {
    // SAFETY: the C ABI query functions take no arguments and are pure.
    let matching = unsafe {
        tb_fingerprint_abi_version() == 1
            && tb_evidence_abi_version() == 1
            && tb_receipt_abi_version() == 1
    };
    if matching { Ok(()) } else { Err(Error::AbiMismatch) }
}

pub fn sha256(bytes: &[u8]) -> Result<[u8; SHA_SIZE], Error> {
    let mut digest = [0u8; SHA_SIZE];
    // SAFETY: Rust slice supplies a valid extent; output is disjoint and 32 bytes long.
    ok(unsafe {
        tb_sha256_bytes(bytes.as_ptr().cast(), bytes.len(), digest.as_mut_ptr())
    })?;
    Ok(digest)
}

pub fn to_hex(digest: &[u8; SHA_SIZE]) -> Result<String, Error> {
    let mut result = [0u8; 65];
    // SAFETY: valid digest pointer, disjoint 65-byte writable buffer.
    ok(unsafe {
        tb_sha256_hex(digest.as_ptr(), result.as_mut_ptr().cast())
    })?;
    String::from_utf8(result[..64].to_vec()).map_err(|_| Error::InvalidEncoding)
}

/// Parse an input commitment. This is syntax validation; all cryptographic
/// verification remains exclusively in the C99 library.
pub fn parse_hex(value: &str) -> Result<[u8; SHA_SIZE], Error> {
    if value.len() != 64 { return Err(Error::InvalidHex); }
    let mut bytes = [0u8; SHA_SIZE];
    for (i, pair) in value.as_bytes().chunks_exact(2).enumerate() {
        let digit = |b: u8| -> Option<u8> {
            match b { b'0'..=b'9' => Some(b - b'0'), b'a'..=b'f' => Some(b - b'a' + 10),
                      _ => None }
        };
        bytes[i] = (digit(pair[0]).ok_or(Error::InvalidHex)? << 4)
            | digit(pair[1]).ok_or(Error::InvalidHex)?;
    }
    Ok(bytes)
}

/// Only the C99 core can create a valid classification. No public raw fields.
#[derive(Clone, Copy, Debug)]
pub struct Evidence(EvidenceRaw);

pub fn observe(before: &[u8], after: &[u8]) -> Result<Evidence, Error> {
    let mut out = EvidenceRaw::default();
    // SAFETY: both input slices are borrowed and valid; output is private and disjoint.
    ok(unsafe {
        tb_observe_transition(
            before.as_ptr().cast(), before.len(), after.as_ptr().cast(), after.len(),
            &mut out,
        )
    })?;
    Ok(Evidence(out))
}

pub fn witness_delete(
    before: &[u8], removed: &[u8], after: &[u8], offset: usize,
) -> Result<Evidence, Error> {
    let mut out = EvidenceRaw::default();
    // SAFETY: all read-only slices are valid for their lengths; output is disjoint.
    ok(unsafe {
        tb_witness_delete(
            before.as_ptr().cast(), before.len(),
            removed.as_ptr().cast(), removed.len(), offset,
            after.as_ptr().cast(), after.len(), &mut out,
        )
    })?;
    Ok(Evidence(out))
}

#[derive(Clone, Copy, Debug)]
pub struct Receipt(ReceiptRaw);

pub fn create_receipt(
    evidence: &Evidence, previous: Option<&[u8; SHA_SIZE]>,
) -> Result<Receipt, Error> {
    let mut out = ReceiptRaw::default();
    let previous_ptr = previous.map_or(ptr::null(), |bytes| bytes.as_ptr());
    // SAFETY: all input references remain live for the call; output is distinct.
    ok(unsafe {
        tb_receipt_create(&evidence.0, previous_ptr, &mut out)
    })?;
    Ok(Receipt(out))
}

pub fn parse_receipt(json: &[u8]) -> Result<Receipt, Error> {
    let mut out = ReceiptRaw::default();
    // SAFETY: a Rust slice is valid for its length; output is disjoint.
    ok(unsafe {
        tb_receipt_parse(json.as_ptr().cast(), json.len(), &mut out)
    })?;
    Ok(Receipt(out))
}

impl Receipt {
    pub fn json(&self) -> Result<String, Error> {
        let mut bytes = [0u8; JSON_MAX];
        let mut written = 0usize;
        // SAFETY: private struct and disjoint bounded output buffer; C99 returns written <= cap.
        ok(unsafe {
            tb_receipt_encode(
                &self.0, bytes.as_mut_ptr().cast(), bytes.len(), &mut written,
            )
        })?;
        if written > bytes.len() { return Err(Error::InvalidEncoding); }
        String::from_utf8(bytes[..written].to_vec()).map_err(|_| Error::InvalidEncoding)
    }

    pub fn digest(&self) -> [u8; SHA_SIZE] { self.0.receipt_hash }
}

/// Requires a genesis record followed by all immediate predecessors. With no
/// trusted head this checks local consistency, NOT historical authenticity.
pub fn verify_chain(
    receipts: &[Receipt], trusted_head: Option<&[u8; SHA_SIZE]>,
) -> Result<(), Error> {
    let native: Vec<ReceiptRaw> = receipts.iter().map(|r| r.0).collect();
    let trusted = trusted_head.map_or(ptr::null(), |value| value.as_ptr());
    // SAFETY: contiguous native array of exact repr(C) records; no mutation or retention.
    ok(unsafe {
        tb_receipt_verify_chain(native.as_ptr(), native.len(), trusted)
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    const BEFORE: &[u8] = b"1 2 3 4 5";
    const REMOVED: &[u8] = b"3 4 ";
    const AFTER: &[u8] = b"1 2 5";

    #[test]
    fn matches_known_c_vectors() {
        check_abi().unwrap();
        assert_eq!(to_hex(&sha256(b"abc").unwrap()).unwrap(),
                   "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
        assert_eq!(parse_hex(&"a".repeat(64)).unwrap(), [0xaa; 32]);
        assert!(parse_hex(&"A".repeat(64)).is_err());
    }

    #[test]
    fn phase_two_and_three_parity() {
        let evidence = witness_delete(BEFORE, REMOVED, AFTER, 4).unwrap();
        let receipt = create_receipt(&evidence, None).unwrap();
        let expected = "3917b3dc420ddb728616ee3834867664a7012aa5a4c127e56c65651f1ac4dbde";
        assert_eq!(to_hex(&receipt.digest()).unwrap(), expected);
        let decoded = parse_receipt(receipt.json().unwrap().as_bytes()).unwrap();
        verify_chain(&[decoded], Some(&parse_hex(expected).unwrap())).unwrap();
        assert!(verify_chain(&[decoded], Some(&[0u8;32])).is_err());
        assert!(witness_delete(BEFORE, b"wrong", AFTER, 4).is_err());
        let changed = observe(BEFORE, AFTER).unwrap();
        let transition = create_receipt(&changed, None).unwrap();
        assert!(transition.json().unwrap().contains("\"deleted\":null"));
    }

    #[test]
    fn original_fixture_parse_and_chain() {
        let fixtures: [&[u8]; 3] = [
            include_bytes!("../../../machine/examples/explicit-delete-v1.json"),
            include_bytes!("../../../machine/examples/observed-transition-v1.json"),
            include_bytes!("../../../machine/examples/unchanged-v1.json"),
        ];
        let receipts: Vec<Receipt> = fixtures.iter().map(|bytes| parse_receipt(bytes).unwrap()).collect();
        let expected = parse_hex("84c0b5f9e478c284553822fb95fe31a72ce71a35070e963d67c328fb777f25e6").unwrap();
        verify_chain(&receipts, Some(&expected)).unwrap();
        assert!(verify_chain(&receipts[1..], None).is_err());
    }
}


// The ABI oracle is compiled and executed against each CI target's actual
// C99 compiler. This is target-specific executed evidence, NOT a proof of
// Rust's optimizer, C compilation, allocator, linker, or operating system.
#[cfg(all(test, unix))]
mod phase15_abi_tests {
    use super::*;
    use std::collections::BTreeMap;
    use std::mem::{align_of, offset_of, size_of};
    use std::path::PathBuf;
    use std::process::Command;

    #[test]
    fn actual_target_c_layout_matches_rust_repr_c() {
        let repo = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
        let directory = std::env::temp_dir().join(format!(
            "tombstone-phase15-abi-{}-{:?}",
            std::process::id(), std::thread::current().id()
        ));
        std::fs::create_dir(&directory).unwrap();
        let executable = directory.join("c99-abi-oracle");
        let cc = std::env::var("CC").unwrap_or_else(|_| "cc".to_string());
        let compilation = Command::new(&cc)
            .arg("-std=c99").arg("-Wall").arg("-Wextra").arg("-Wpedantic").arg("-Werror")
            .arg("-I").arg(repo.join("include"))
            .arg(repo.join("tests/phase15/abi_layout.c"))
            .arg("-o").arg(&executable)
            .output().expect("C99 compiler must be available for ABI verification");
        assert!(compilation.status.success(), "C ABI oracle compilation failed: {}",
                String::from_utf8_lossy(&compilation.stderr));
        let outcome = Command::new(&executable).output().expect("run C99 ABI oracle");
        assert!(outcome.status.success(), "C99 ABI oracle failed");
        let mut observed = BTreeMap::new();
        for row in String::from_utf8(outcome.stdout).unwrap().lines() {
            let (key, value) = row.split_once('=').expect("key=value ABI row");
            assert!(observed.insert(key.to_string(), value.parse::<usize>().unwrap()).is_none(),
                    "duplicate C ABI metric {key}");
        }
        // Explicit list: additions to the oracle must also be reviewed here.
        let expected: BTreeMap<String, usize> = [
            ("size_t.size", size_of::<usize>()), ("size_t.align", align_of::<usize>()),
            ("void *.size", size_of::<*const c_void>()),
            ("void *.align", align_of::<*const c_void>()),
            ("int.size", size_of::<c_int>()), ("int.align", align_of::<c_int>()),
            ("tb_status.size", size_of::<c_int>()),
            ("tb_status.align", align_of::<c_int>()),
            ("tb_evidence_kind.size", size_of::<c_int>()),
            ("tb_evidence_kind.align", align_of::<c_int>()),
            ("tb_evidence_v1.size", size_of::<EvidenceRaw>()),
            ("tb_evidence_v1.align", align_of::<EvidenceRaw>()),
            ("tb_evidence_v1.kind", offset_of!(EvidenceRaw, kind)),
            ("tb_evidence_v1.before_size", offset_of!(EvidenceRaw, before_size)),
            ("tb_evidence_v1.after_size", offset_of!(EvidenceRaw, after_size)),
            ("tb_evidence_v1.before_sha256", offset_of!(EvidenceRaw, before_sha256)),
            ("tb_evidence_v1.after_sha256", offset_of!(EvidenceRaw, after_sha256)),
            ("tb_evidence_v1.deleted_size", offset_of!(EvidenceRaw, deleted_size)),
            ("tb_evidence_v1.deleted_offset", offset_of!(EvidenceRaw, deleted_offset)),
            ("tb_evidence_v1.deleted_sha256", offset_of!(EvidenceRaw, deleted_sha256)),
            ("tb_receipt_v1.size", size_of::<ReceiptRaw>()),
            ("tb_receipt_v1.align", align_of::<ReceiptRaw>()),
            ("tb_receipt_v1.evidence", offset_of!(ReceiptRaw, evidence)),
            ("tb_receipt_v1.has_previous", offset_of!(ReceiptRaw, has_previous)),
            ("tb_receipt_v1.previous_hash", offset_of!(ReceiptRaw, previous_hash)),
            ("tb_receipt_v1.receipt_hash", offset_of!(ReceiptRaw, receipt_hash)),
            ("TB_FINGERPRINT_ABI_VERSION", 1), ("TB_EVIDENCE_ABI_VERSION", 1),
            ("TB_RECEIPT_ABI_VERSION", 1), ("TB_SHA256_DIGEST_SIZE", SHA_SIZE),
            ("TB_RECEIPT_JSON_MAX", JSON_MAX),
            ("TB_EVIDENCE_UNCHANGED", 1), ("TB_EVIDENCE_OBSERVED_TRANSITION", 2),
            ("TB_EVIDENCE_EXPLICIT_DELETE", 3),
            ("TB_OK", 0), ("TB_ERR_ARGUMENT", 1), ("TB_ERR_LENGTH", 2),
            ("TB_ERR_MEMORY", 3), ("TB_ERR_CRYPTO", 4), ("TB_ERR_STATE", 5),
            ("TB_ERR_MISMATCH", 6), ("TB_ERR_FORMAT", 7),
        ].into_iter().map(|(k, v)| (k.to_string(), v)).collect();
        assert_eq!(observed, expected, "C99 and Rust layout/status mismatch on this target");
        std::fs::remove_dir_all(&directory).unwrap();
    }

    #[test]
    fn native_error_paths_preserve_outputs_and_status_codes() {
        let before = b"1 2 3 4 5";
        let removed = b"3 4 ";
        let after = b"1 2 5";
        let mut digest = [0xa5u8; SHA_SIZE];
        let rc = unsafe { tb_sha256_bytes(ptr::null(), 1, digest.as_mut_ptr()) };
        assert_eq!(rc, 1);
        assert_eq!(digest, [0xa5; SHA_SIZE]);

        let mut evidence = EvidenceRaw::default();
        evidence.before_size = 0x5151;
        let before_evidence = format!("{evidence:?}");
        let rc = unsafe {
            tb_witness_delete(before.as_ptr().cast(), before.len(),
                removed.as_ptr().cast(), removed.len(), 3,
                after.as_ptr().cast(), after.len(), &mut evidence)
        };
        assert_eq!(rc, 6, "false splice must propagate native mismatch");
        assert_eq!(format!("{evidence:?}"), before_evidence, "native error mutated evidence");
        assert!(matches!(witness_delete(before, removed, after, 3), Err(Error::Native(6))));

        let mut raw = ReceiptRaw::default();
        raw.has_previous = 0x5151;
        let prior = format!("{raw:?}");
        let malformed = b"{\"version\":1,\"version\":1}";
        let rc = unsafe { tb_receipt_parse(malformed.as_ptr().cast(), malformed.len(), &mut raw) };
        assert_eq!(rc, 7);
        assert_eq!(format!("{raw:?}"), prior, "parser error modified FFI receipt output");

        let good = create_receipt(&witness_delete(before, removed, after, 4).unwrap(), None).unwrap();
        let mut output = [0xa5u8; JSON_MAX];
        let mut written = 0x5151usize;
        let rc = unsafe {
            tb_receipt_encode(&good.0, output.as_mut_ptr().cast(), 1, &mut written)
        };
        assert_eq!(rc, 2);
        assert_eq!(output, [0xa5; JSON_MAX]);
        assert_eq!(written, 0x5151);
    }
}
