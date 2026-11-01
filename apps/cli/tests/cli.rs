use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Output, Stdio};

fn root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}
fn fixture(path: &str) -> String {
    root().join(path).to_string_lossy().into_owned()
}
fn command(args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_tombstone")).args(args).output().unwrap()
}
fn string(output: &[u8]) -> String { String::from_utf8(output.to_vec()).unwrap() }

#[test]
fn hashes_binary_stdin_and_pipe_safe_output() {
    let mut child = Command::new(env!("CARGO_BIN_EXE_tombstone"))
        .args(["hash", "-"])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn().unwrap();
    child.stdin.take().unwrap().write_all(b"abc").unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(out.status.success(), "{:?}", out.status);
    assert_eq!(string(&out.stdout), concat!(
        "{\"sha256\":\"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad\",",
        "\"size\":3}\n",
    ));
    assert!(out.stderr.is_empty());
}

#[test]
fn exact_canonical_receipt_matches_phase_three_fixture() {
    let before = fixture("tests/fixtures/before.txt");
    let removed = fixture("tests/fixtures/deleted.txt");
    let after = fixture("tests/fixtures/after.txt");
    let out = command(&["delete", &before, &removed, &after, "4"]);
    assert!(out.status.success(), "{}", string(&out.stderr));
    let expected = std::fs::read(fixture("machine/examples/explicit-delete-v1.json")).unwrap();
    let canonical = tombstone_ffi::parse_receipt(&expected).unwrap().json().unwrap();
    assert_eq!(string(&out.stdout), format!("{canonical}\n"));
    assert!(!string(&out.stdout).contains("1 2 3 4 5"));

    let observed = command(&["observe", &before, &after]);
    assert!(observed.status.success(), "{}", string(&observed.stderr));
    assert!(string(&observed.stdout).contains("\"kind\":\"observed-transition\""));
    assert!(string(&observed.stdout).contains("\"deleted\":null"));
}

#[test]
fn verify_and_chain_accept_original_golden_receipts() {
    let a = fixture("machine/examples/explicit-delete-v1.json");
    let b = fixture("machine/examples/observed-transition-v1.json");
    let c = fixture("machine/examples/unchanged-v1.json");
    let expected = "84c0b5f9e478c284553822fb95fe31a72ce71a35070e963d67c328fb777f25e6";
    let single = command(&["verify", &b]);
    assert!(single.status.success(), "{}", string(&single.stderr));
    assert!(string(&single.stdout).contains("\"self_hash_valid\":true"));
    assert!(!string(&single.stdout).contains("chain_valid"));

    let all = command(&["verify-chain", &a, &b, &c, "--trusted-head", expected]);
    assert!(all.status.success(), "{}", string(&all.stderr));
    assert_eq!(string(&all.stdout), format!(
        "{{\"chain_valid\":true,\"count\":3,\"head\":\"{expected}\",\"trusted_head_checked\":true}}\n"
    ));
    let bad = command(&["verify-chain", &a, &c, &b]);
    assert_eq!(bad.status.code(), Some(3));
    assert!(bad.stdout.is_empty());

    let wrong_head = "0".repeat(64);
    let wrong = command(&["verify-chain", &a, &b, &c, "--trusted-head", &wrong_head]);
    assert_eq!(wrong.status.code(), Some(3));
    assert!(wrong.stdout.is_empty());
}

#[test]
fn invalid_splices_and_arguments_have_no_stdout() {
    let before = fixture("tests/fixtures/before.txt");
    let removed = fixture("tests/fixtures/deleted.txt");
    let after = fixture("tests/fixtures/after.txt");
    let mismatched = command(&["delete", &before, &removed, &after, "3"]);
    assert_eq!(mismatched.status.code(), Some(3));
    assert!(mismatched.stdout.is_empty());
    let invalid = command(&["delete", &before, &removed, &after, "4", "--previous", "BAD"]);
    assert_eq!(invalid.status.code(), Some(2));
    assert!(invalid.stdout.is_empty());
    let too_many_stdin = command(&["observe", "-", "-"]);
    assert_eq!(too_many_stdin.status.code(), Some(2));
    assert!(too_many_stdin.stdout.is_empty());
    let no_files = command(&["verify-chain"]);
    assert_eq!(no_files.status.code(), Some(2));
    assert!(no_files.stdout.is_empty());
}

#[test]
fn malformed_json_is_rejected_in_c99() {
    let mut child = Command::new(env!("CARGO_BIN_EXE_tombstone"))
        .args(["verify", "-"])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn().unwrap();
    child.stdin.take().unwrap().write_all(b"{\"version\":1,\"version\":1}").unwrap();
    let result = child.wait_with_output().unwrap();
    assert_eq!(result.status.code(), Some(3));
    assert!(result.stdout.is_empty());
    assert!(!result.stderr.is_empty());
}

#[cfg(unix)]
#[test]
fn non_utf8_arguments_are_rejected_without_disclosing_paths() {
    use std::ffi::OsString;
    use std::os::unix::ffi::OsStringExt;

    // Exact P1 regression: the supplied Unix filename contains a raw 0xff.
    // The prior env::args() panicked (status 101) and printed the pathname.
    let sensitive = OsString::from_vec(b"/tmp/private-customer-\xff".to_vec());
    let result = Command::new(env!("CARGO_BIN_EXE_tombstone"))
        .arg("hash")
        .arg(&sensitive)
        .output()
        .unwrap();
    assert_eq!(result.status.code(), Some(2));
    assert!(result.stdout.is_empty());
    assert_eq!(
        result.stderr,
        b"tombstone: command arguments must be valid UTF-8\n"
    );

    // Apply the same path-independent behavior to invalid option values.
    let bad_option = OsString::from_vec(b"private-anchor-\xff".to_vec());
    let result = Command::new(env!("CARGO_BIN_EXE_tombstone"))
        .arg("observe")
        .arg(fixture("tests/fixtures/before.txt"))
        .arg(fixture("tests/fixtures/after.txt"))
        .arg("--previous")
        .arg(bad_option)
        .output()
        .unwrap();
    assert_eq!(result.status.code(), Some(2));
    assert!(result.stdout.is_empty());
    assert_eq!(
        result.stderr,
        b"tombstone: command arguments must be valid UTF-8\n"
    );
}


#[test]
fn phase15_exact_64_mib_file_cap_and_no_data_on_failure() {
    use std::fs::OpenOptions;
    use std::time::{SystemTime, UNIX_EPOCH};

    const LIMIT: u64 = 64 * 1024 * 1024;
    let nonce = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
    let path = std::env::temp_dir().join(format!(
        "tombstone-phase15-cap-{}-{nonce}", std::process::id()
    ));
    // Sparse local fixture: allocates no persistent user data or huge in-memory Vec.
    let file = OpenOptions::new().create_new(true).write(true).open(&path).unwrap();
    let at_limit = (|| {
        file.set_len(LIMIT).unwrap();
        let valid = Command::new(env!("CARGO_BIN_EXE_tombstone"))
            .args(["hash"]).arg(&path).output().unwrap();
        assert_eq!(valid.status.code(), Some(0), "exactly 64 MiB must remain legal");
        assert!(valid.stderr.is_empty());
        assert!(string(&valid.stdout).contains("\"size\":67108864}"));
        assert!(!string(&valid.stdout).contains("private"));

        file.set_len(LIMIT + 1).unwrap();
        for op in ["hash", "verify"] {
            let invalid = Command::new(env!("CARGO_BIN_EXE_tombstone"))
                .arg(op).arg(&path).output().unwrap();
            assert_eq!(invalid.status.code(), Some(2), "oversize {op} must fail before C99");
            assert!(invalid.stdout.is_empty(), "oversize {op} emitted success JSON");
            assert_eq!(invalid.stderr, b"tombstone: input exceeds 64 MiB limit\n");
        }
    })();
    std::fs::remove_file(&path).unwrap();
    at_limit
}
