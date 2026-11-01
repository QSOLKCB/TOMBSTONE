use std::process::Command;

#[test]
fn help_is_noninteractive() {
    let result = Command::new(env!("CARGO_BIN_EXE_tombstone-tui"))
        .arg("--help").output().unwrap();
    assert_eq!(result.status.code(), Some(0));
    assert!(String::from_utf8_lossy(&result.stdout).contains("TOMBSTONE"));
}

#[test]
fn disconnected_terminal_fails_cleanly() {
    let result = Command::new(env!("CARGO_BIN_EXE_tombstone-tui"))
        .output().unwrap();
    assert_eq!(result.status.code(), Some(2));
    assert!(result.stdout.is_empty());
    assert!(String::from_utf8_lossy(&result.stderr).contains("interactive terminal"));
}

#[cfg(unix)]
#[test]
fn non_utf8_argument_is_sanitized() {
    use std::ffi::OsString;
    use std::os::unix::ffi::OsStringExt;
    let name = OsString::from_vec(b"/tmp/private-\xff".to_vec());
    let result = Command::new(env!("CARGO_BIN_EXE_tombstone-tui")).arg(name).output().unwrap();
    assert_eq!(result.status.code(), Some(2));
    assert!(result.stdout.is_empty());
    assert!(!result.stderr.contains(&0xff));
}
