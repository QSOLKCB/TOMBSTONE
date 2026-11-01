//! Terminal-independent workflows. All evidence and cryptographic decisions
//! are delegated to tombstone-ffi, which delegates to the original C99 core.
//! No user paths or removed plaintext are placed in display/error results.
use std::fs::{File, OpenOptions};
use std::io::{Read, Write};
use std::path::Path;
use tombstone_ffi as engine;

pub const INPUT_LIMIT: u64 = 64 * 1024 * 1024;
pub const RECEIPT_LIMIT: u64 = 16 * 1024;
pub const MAX_CHAIN: usize = 64;

#[derive(Clone, Debug)]
pub struct Report {
    pub title: String,
    pub lines: Vec<String>,
    pub export_json: Option<String>,
}

fn problem(message: &str) -> String { message.to_owned() }

fn read_file(path: &str, limit: u64) -> Result<Vec<u8>, String> {
    if path.is_empty() { return Err(problem("A file path is required.")); }
    let file = File::open(Path::new(path))
        .map_err(|_| problem("Could not open input file (path hidden)."))?;
    let mut data = Vec::new();
    file.take(limit + 1).read_to_end(&mut data)
        .map_err(|_| problem("Could not read input file (path hidden)."))?;
    if data.len() as u64 > limit { return Err(problem("Input exceeds the configured size limit.")); }
    Ok(data)
}

pub fn fingerprint(path: &str) -> Result<Report, String> {
    let input = read_file(path, INPUT_LIMIT)?;
    let digest = engine::sha256(&input).map_err(|e| e.to_string())?;
    let hex = engine::to_hex(&digest).map_err(|e| e.to_string())?;
    Ok(Report {
        title: "SHA-256 fingerprint".into(),
        lines: vec!["C99 SHA-256 of caller-selected file bytes".into(),
                    format!("Size: {} bytes", input.len()),
                    format!("SHA-256: {hex}"),
                    "This does not witness deletion.".into()],
        export_json: None,
    })
}

fn receipt_report(title: &str, receipt: engine::Receipt) -> Result<Report, String> {
    let json = receipt.json().map_err(|e| e.to_string())?;
    let hash = engine::to_hex(&receipt.digest()).map_err(|e| e.to_string())?;
    Ok(Report {
        title: title.into(),
        lines: vec![format!("Receipt hash: {hash}"),
                    "C99-generated canonical v1 JSON (without filename or plaintext):".into(),
                    json.clone(),
                    "A verified splice does not prove a historical edit.".into()],
        export_json: Some(json),
    })
}

fn previous(hash: Option<&str>) -> Result<Option<[u8; 32]>, String> {
    hash.map(|value| engine::parse_hex(value).map_err(|e| e.to_string())).transpose()
}

pub fn observe(before: &str, after: &str, prior: Option<&str>) -> Result<Report, String> {
    let b = read_file(before, INPUT_LIMIT)?;
    let a = read_file(after, INPUT_LIMIT)?;
    let evidence = engine::observe(&b, &a).map_err(|e| e.to_string())?;
    let previous_hash = previous(prior)?;
    let receipt = engine::create_receipt(&evidence, previous_hash.as_ref()).map_err(|e| e.to_string())?;
    receipt_report("Observed transition receipt", receipt)
}

pub fn witness(before: &str, removed: &str, after: &str, offset: &str,
               prior: Option<&str>) -> Result<Report, String> {
    if offset.is_empty() || !offset.bytes().all(|b| b.is_ascii_digit()) ||
        (offset.len() > 1 && offset.starts_with('0')) {
        return Err(problem("Offset must be a nonnegative decimal byte index."));
    }
    let n: usize = offset.parse().map_err(|_| problem("Offset exceeds platform limits."))?;
    let b = read_file(before, INPUT_LIMIT)?;
    let d = read_file(removed, INPUT_LIMIT)?;
    let a = read_file(after, INPUT_LIMIT)?;
    let evidence = engine::witness_delete(&b, &d, &a, n).map_err(|e| e.to_string())?;
    let previous_hash = previous(prior)?;
    let receipt = engine::create_receipt(&evidence, previous_hash.as_ref()).map_err(|e| e.to_string())?;
    receipt_report("Verified supplied splice receipt", receipt)
}

pub fn inspect(path: &str) -> Result<Report, String> {
    let raw = read_file(path, RECEIPT_LIMIT)?;
    let receipt = engine::parse_receipt(&raw).map_err(|e| e.to_string())?;
    receipt_report("Receipt self-hash valid (chain not checked)", receipt)
}

pub fn chain(paths: &[String], trusted_head: Option<&str>) -> Result<Report, String> {
    if paths.is_empty() || paths.len() > MAX_CHAIN {
        return Err(problem("Specify 1 to 64 ordered receipt files."));
    }
    let trusted = match trusted_head {
        Some(hex) => Some(engine::parse_hex(hex).map_err(|e| e.to_string())?),
        None => None,
    };
    let mut receipts = Vec::with_capacity(paths.len());
    for path in paths {
        let json = read_file(path, RECEIPT_LIMIT)?;
        receipts.push(engine::parse_receipt(&json).map_err(|e| e.to_string())?);
    }
    engine::verify_chain(&receipts, trusted.as_ref()).map_err(|e| e.to_string())?;
    let last = receipts.last().ok_or_else(|| problem("Chain is empty."))?;
    let head = engine::to_hex(&last.digest()).map_err(|e| e.to_string())?;
    let label = if trusted.is_some() {
        "Externally supplied trusted head MATCHED."
    } else {
        "Local consistency only. NOT independently anchored."
    };
    Ok(Report {
        title: "Receipt chain verified by C99".into(),
        lines: vec![format!("Checked receipts (genesis to head): {}", receipts.len()),
                    format!("Final receipt SHA-256: {head}"),
                    label.into(),
                    "A consistent chain does not prove a real-world deletion.".into()],
        export_json: None,
    })
}

/// Never overwrite: export is an explicit opt-in and writes only C99 canonical
/// receipt JSON plus LF. The file path is never included in an error message.
pub fn export_receipt(json: &str, path: &str) -> Result<(), String> {
    if path.is_empty() { return Err(problem("An output path is required.")); }
    let receipt = engine::parse_receipt(json.as_bytes()).map_err(|e| e.to_string())?;
    let canonical = receipt.json().map_err(|e| e.to_string())?;
    if canonical != json {
        return Err(problem("Only canonical C99 receipts may be exported."));
    }
    let mut options = OpenOptions::new();
    options.write(true).create_new(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.mode(0o600);
    }
    let mut output = options.open(Path::new(path))
        .map_err(|_| problem("Could not create a new receipt file (existing files are never overwritten)."))?;
    output.write_all(canonical.as_bytes())
        .and_then(|_| output.write_all(b"\n"))
        .and_then(|_| output.flush())
        .map_err(|_| problem("Could not write complete receipt; inspect/remove any partial output manually."))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    fn fixture(name: &str) -> String {
        format!("{}/../../{}", env!("CARGO_MANIFEST_DIR"), name)
    }
    #[test]
    fn verified_witness_matches_goldens() {
        let r = witness(
            &fixture("tests/fixtures/before.txt"),
            &fixture("tests/fixtures/deleted.txt"),
            &fixture("tests/fixtures/after.txt"), "4", None).unwrap();
        let expected = engine::parse_receipt(
            &std::fs::read(fixture("machine/examples/explicit-delete-v1.json")).unwrap()
        ).unwrap().json().unwrap();
        assert_eq!(r.export_json.as_deref(), Some(expected.as_str()));
        assert!(!r.lines.join(" ").contains("1 2 3 4 5"));
        assert!(witness(
            &fixture("tests/fixtures/before.txt"),
            &fixture("tests/fixtures/deleted.txt"),
            &fixture("tests/fixtures/after.txt"), "3", None).is_err());
    }
    #[test]
    fn observation_is_not_a_deletion() {
        let r = observe(&fixture("tests/fixtures/before.txt"),
                        &fixture("tests/fixtures/after.txt"), None).unwrap();
        assert!(r.export_json.unwrap().contains("\"deleted\":null"));
    }
    #[test]
    fn anchored_chain_and_reordered_rejection() {
        let a = fixture("machine/examples/explicit-delete-v1.json");
        let b = fixture("machine/examples/observed-transition-v1.json");
        let c = fixture("machine/examples/unchanged-v1.json");
        let head = "84c0b5f9e478c284553822fb95fe31a72ce71a35070e963d67c328fb777f25e6";
        let result = chain(&[a.clone(), b.clone(), c.clone()], Some(head)).unwrap();
        assert!(result.lines.join(" ").contains("trusted head MATCHED"));
        assert!(chain(&[a.clone(), c.clone(), b.clone()], None).is_err());
        assert!(chain(&[a,b,c], Some(&"0".repeat(64))).is_err());
        assert!(chain(&[], None).is_err());
    }
    #[test]
    fn inspect_and_invalid_offsets() {
        let report = inspect(&fixture("machine/examples/explicit-delete-v1.json")).unwrap();
        assert!(report.title.contains("self-hash valid"));
        for invalid in ["", "04", "-1", "184467440737095516160"] {
            assert!(witness("unused", "unused", "unused", invalid, None).is_err());
        }
    }
    #[test]
    fn generated_receipts_accept_untrusted_caller_supplied_predecessors() {
        let after = fixture("tests/fixtures/after.txt");
        let initial = observe(&after, &after, None).unwrap();
        let hash = engine::parse_receipt(initial.export_json.as_ref().unwrap().as_bytes())
            .unwrap().digest();
        let prev = engine::to_hex(&hash).unwrap();
        let next = observe(&after, &after, Some(&prev)).unwrap();
        assert!(next.export_json.as_ref().unwrap().contains(&prev));
        assert!(observe(&after, &after, Some("INVALID")).is_err());
        // Caller still must check full chain; a previous digest is not authentication.
    }
    #[test]
    fn file_and_error_privacy() {
        let missing = "/tmp/private-customer-not-in-filesystem";
        let err = inspect(missing).unwrap_err();
        assert!(!err.contains(missing));
        assert!(fingerprint(missing).is_err());
    }
}
