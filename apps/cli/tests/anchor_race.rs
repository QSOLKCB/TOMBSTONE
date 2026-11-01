// SPDX-License-Identifier: Apache-2.0
// Exact Phase 16 regression: a pathname check and a subsequent blocking
// open can be raced using renameat2(RENAME_EXCHANGE) with a FIFO or symlink.
// No new crates, no privileged capabilities, and a hard child timeout.
#![cfg(target_os = "linux")]

use std::ffi::CString;
use std::fs;
use std::os::raw::{c_char, c_int};
use std::os::unix::ffi::OsStrExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

const AT_FDCWD: c_int = -100;
const RENAME_EXCHANGE: u32 = 2;
const GOOD_HEAD: &str = "84c0b5f9e478c284553822fb95fe31a72ce71a35070e963d67c328fb777f25e6";

extern "C" {
    fn mkfifo(path: *const c_char, mode: u32) -> c_int;
    fn renameat2(
        olddirfd: c_int,
        oldpath: *const c_char,
        newdirfd: c_int,
        newpath: *const c_char,
        flags: u32,
    ) -> c_int;
}

fn cpath(path: &Path) -> CString {
    CString::new(path.as_os_str().as_bytes()).unwrap()
}

fn receipt(path: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..").join(path)
}

fn run_exchange_test(swap_kind: &str) {
    let nonce = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
    let directory = std::env::temp_dir().join(format!(
        "tombstone-phase16-renameat2-{}-{nonce}-{swap_kind}", std::process::id()
    ));
    fs::create_dir(&directory).unwrap();
    let anchor = directory.join("anchor");
    let swap = directory.join("swap");
    fs::write(&anchor, format!("{GOOD_HEAD}\n")).unwrap();
    if swap_kind == "fifo" {
        let name = cpath(&swap);
        assert_eq!(unsafe { mkfifo(name.as_ptr(), 0o600) }, 0,
                   "mkfifo failed: {:?}", std::io::Error::last_os_error());
    } else {
        let wrong = directory.join("wrong-head");
        fs::write(&wrong, "0".repeat(64)).unwrap();
        std::os::unix::fs::symlink(wrong, &swap).unwrap();
    }

    let stop = Arc::new(AtomicBool::new(false));
    let swaps = Arc::new(AtomicUsize::new(0));
    let worker_stop = Arc::clone(&stop);
    let worker_swaps = Arc::clone(&swaps);
    let lhs = cpath(&anchor);
    let rhs = cpath(&swap);
    let worker = thread::spawn(move || -> Result<(), String> {
        while !worker_stop.load(Ordering::Relaxed) {
            let result = unsafe {
                renameat2(AT_FDCWD, lhs.as_ptr(), AT_FDCWD, rhs.as_ptr(), RENAME_EXCHANGE)
            };
            if result != 0 {
                return Err(format!("renameat2 failed: {}", std::io::Error::last_os_error()));
            }
            worker_swaps.fetch_add(1, Ordering::Relaxed);
            thread::yield_now();
        }
        Ok(())
    });

    let receipts = [
        receipt("machine/examples/explicit-delete-v1.json"),
        receipt("machine/examples/observed-transition-v1.json"),
        receipt("machine/examples/unchanged-v1.json"),
    ];
    let mut failure = None;
    let mut rejected = 0usize;
    for iteration in 0..80 {
        let mut child = Command::new(env!("CARGO_BIN_EXE_tombstone"))
            .arg("verify-chain")
            .arg(&receipts[0]).arg(&receipts[1]).arg(&receipts[2])
            .arg("--trusted-head-file").arg(&anchor)
            .stdout(Stdio::piped()).stderr(Stdio::piped())
            .spawn().unwrap();
        let start = Instant::now();
        let mut timeout = false;
        loop {
            if child.try_wait().unwrap().is_some() { break; }
            if start.elapsed() > Duration::from_secs(2) {
                // Without O_NONBLOCK this can hang in open(FIFO) indefinitely.
                let _ = child.kill();
                timeout = true;
                break;
            }
            thread::sleep(Duration::from_millis(5));
        }
        let output = child.wait_with_output().unwrap();
        if timeout {
            failure = Some(format!("{swap_kind}: iteration {iteration} blocked during anchor open"));
            break;
        }
        match output.status.code() {
            Some(0) => {
                if !output.stderr.is_empty()
                    || !String::from_utf8_lossy(&output.stdout).contains("\"trusted_head_checked\":true")
                {
                    failure = Some("successful chain verification has incorrect output".into());
                    break;
                }
            }
            Some(2 | 4) => {
                rejected += 1;
                if !output.stdout.is_empty()
                    || !output.stderr.starts_with(b"tombstone: ")
                    || output.stderr.windows(anchor.as_os_str().as_bytes().len())
                        .any(|span| span == anchor.as_os_str().as_bytes())
                {
                    failure = Some("anchor error leaked success output or path".into());
                    break;
                }
            }
            other => {
                failure = Some(format!(
                    "{swap_kind}: unexpected status {other:?} (may have followed a symlink)"
                ));
                break;
            }
        }
    }
    stop.store(true, Ordering::Relaxed);
    let worker_result = worker.join().unwrap();
    fs::remove_dir_all(&directory).unwrap();
    assert!(worker_result.is_ok(), "{worker_result:?}");
    assert!(failure.is_none(), "{failure:?}");
    assert!(swaps.load(Ordering::Relaxed) > 0, "rename exchange did not execute");
    assert!(rejected > 0, "no invalid anchor was actually observed during exchange");
}

#[test]
fn exchanged_fifo_anchor_never_blocks_the_cli() {
    run_exchange_test("fifo");
}

#[test]
fn exchanged_symlink_anchor_is_never_followed() {
    run_exchange_test("symlink");
}
