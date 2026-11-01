//! GTK desktop uses precisely the Phase 5 workflows (Rust -> C99).
//! These tests require GTK libraries for linking but no display server.
use tombstone_tui as flow;
use std::fs;
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

fn fixture(name: &str) -> String {
    format!("{}/../../{}", env!("CARGO_MANIFEST_DIR"), name)
}

#[test]
fn gtk_workflow_witness_matches_the_c99_golden_receipt() {
    let report = flow::witness(
        &fixture("tests/fixtures/before.txt"),
        &fixture("tests/fixtures/deleted.txt"),
        &fixture("tests/fixtures/after.txt"), "4", None,
    ).unwrap();
    let golden = fs::read(fixture("machine/examples/explicit-delete-v1.json")).unwrap();
    let canonical = tombstone_ffi::parse_receipt(&golden).unwrap().json().unwrap();
    assert_eq!(report.export_json.as_deref(), Some(canonical.as_str()));
    assert!(!canonical.contains("1 2 3 4 5"));
}

#[test]
fn gtk_workflow_enforces_observed_not_deleted_and_validates_chain() {
    let report = flow::observe(
        &fixture("tests/fixtures/before.txt"),
        &fixture("tests/fixtures/after.txt"), None,
    ).unwrap();
    assert!(report.export_json.unwrap().contains("\"deleted\":null"));

    let chain = [
        fixture("machine/examples/explicit-delete-v1.json"),
        fixture("machine/examples/observed-transition-v1.json"),
        fixture("machine/examples/unchanged-v1.json"),
    ];
    let expected = "84c0b5f9e478c284553822fb95fe31a72ce71a35070e963d67c328fb777f25e6";
    flow::chain(&chain, Some(expected)).unwrap();
    assert!(flow::chain(&[chain[1].clone(), chain[0].clone()], None).is_err());
    assert!(flow::chain(&chain, Some(&"0".repeat(64))).is_err());
}

#[test]
fn receipt_export_never_overwrites() {
    let report = flow::inspect(&fixture("machine/examples/explicit-delete-v1.json")).unwrap();
    let json = report.export_json.unwrap();
    let nanos = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
    let path = std::env::temp_dir().join(format!(
        "tombstone-gtk-{}-{nanos}.json", std::process::id()
    ));
    let name = path.to_str().unwrap();
    flow::export_receipt(&json, name).unwrap();
    assert!(flow::export_receipt(&json, name).is_err());
    assert_eq!(fs::read(&path).unwrap(), format!("{json}\n").as_bytes());
    fs::remove_file(&path).unwrap();
}

#[test]
fn gtk_help_without_display_and_invalid_arguments_are_sanitized() {
    let help = Command::new(env!("CARGO_BIN_EXE_tombstone-gtk"))
        .arg("--help").output().unwrap();
    assert!(help.status.success());
    assert!(String::from_utf8_lossy(&help.stdout).contains("GTK4"));
    let bad = Command::new(env!("CARGO_BIN_EXE_tombstone-gtk"))
        .arg("--unknown").output().unwrap();
    assert_eq!(bad.status.code(), Some(2));
    assert!(bad.stdout.is_empty());
}

#[cfg(unix)]
#[test]
fn gtk_non_utf8_argument_does_not_leak_path() {
    use std::ffi::OsString;
    use std::os::unix::ffi::OsStringExt;
    let private = OsString::from_vec(b"/tmp/private-customer-\xff".to_vec());
    let result = Command::new(env!("CARGO_BIN_EXE_tombstone-gtk"))
        .arg(private).output().unwrap();
    assert_eq!(result.status.code(), Some(2));
    assert!(result.stdout.is_empty());
    assert!(!String::from_utf8_lossy(&result.stderr).contains("private-customer"));
}
