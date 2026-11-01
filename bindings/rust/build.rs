use std::env;
use std::path::{Path, PathBuf};
use std::process::Command;

fn run(program: &str, args: &[&str]) {
    let status = Command::new(program)
        .args(args)
        .status()
        .unwrap_or_else(|error| panic!("could not launch {program}: {error}"));
    assert!(status.success(), "{program} failed with {status}");
}

fn compile(compiler: &str, root: &Path, out: &Path, source: &str, name: &str) {
    let include = root.join("include");
    let src = root.join(source);
    let obj = out.join(name);
    run(
        compiler,
        &[
            "-std=c99",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-Werror",
            "-I",
            include.to_str().expect("UTF-8 include path"),
            "-c",
            src.to_str().expect("UTF-8 C path"),
            "-o",
            obj.to_str().expect("UTF-8 object path"),
        ],
    );
}

fn main() {
    let root = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap()).join("../..");
    let out = PathBuf::from(env::var("OUT_DIR").unwrap());
    let cc = env::var("CC").unwrap_or_else(|_| "cc".to_string());
    let ar = env::var("AR").unwrap_or_else(|_| "ar".to_string());

    let backend = env::var("TOMBSTONE_SHA256_BACKEND").unwrap_or_else(|_| "openssl".to_string());
    assert!(backend == "openssl" || backend == "hacl", "unsupported SHA-256 backend");
    if backend == "openssl" {
        run("pkg-config", &["--exists", "openssl"]);
    }
    println!("cargo:rerun-if-env-changed=TOMBSTONE_SHA256_BACKEND");
    for path in [
        "src/crypto/fingerprint.c",
        "src/core/deletion.c",
        "src/encoding/receipt.c",
        "include/tombstone/fingerprint.h",
        "include/tombstone/deletion.h",
        "include/tombstone/receipt.h",
    ] {
        println!("cargo:rerun-if-changed={}", root.join(path).display());
    }
    println!("cargo:rerun-if-env-changed=CC");
    println!("cargo:rerun-if-env-changed=AR");

    if backend == "openssl" {
        compile(&cc, &root, &out, "src/crypto/fingerprint.c", "fingerprint.o");
    } else {
        println!("cargo:rerun-if-changed={}", root.join("src/crypto/fingerprint_hacl.c").display());
        println!("cargo:rerun-if-changed={}", root.join("vendor/hacl-star/dist/gcc-compatible/Hacl_Hash_SHA2.c").display());
        let hacl_inc = root.join("vendor/hacl-star/dist/gcc-compatible");
        let krml_inc = root.join("vendor/hacl-star/dist/karamel/include");
        let uint128_inc = root.join("vendor/hacl-star/dist/karamel/krmllib/dist/minimal");
        let compile_hacl = |source: &str, object: &str| {
            run(
                &cc,
                &[
                    "-std=c99", "-O2",
                    "-I", root.join("include").to_str().expect("UTF-8 include").to_owned().as_str(),
                    "-I", hacl_inc.to_str().expect("UTF-8 HACL path"),
                    "-I", krml_inc.to_str().expect("UTF-8 KaRaMeL path"),
                    "-I", uint128_inc.to_str().expect("UTF-8 uint128 path"),
                    "-c", root.join(source).to_str().expect("UTF-8 source").to_owned().as_str(),
                    "-o", out.join(object).to_str().expect("UTF-8 object").to_owned().as_str(),
                ],
            );
        };
        compile_hacl("src/crypto/fingerprint_hacl.c", "fingerprint.o");
        compile_hacl("vendor/hacl-star/dist/gcc-compatible/Hacl_Hash_SHA2.c", "hacl_sha2.o");
    }
    compile(&cc, &root, &out, "src/core/deletion.c", "deletion.o");
    compile(&cc, &root, &out, "src/encoding/receipt.c", "receipt.o");

    let archive = out.join("libtombstone_native.a");
    let native_objects = ["fingerprint.o", "deletion.o", "receipt.o"];
    let mut args = vec!["rcsD".to_string(), archive.to_str().expect("UTF-8 archive").to_owned()];
    for entry in native_objects { args.push(out.join(entry).to_str().expect("UTF-8 object").to_owned()); }
    if backend == "hacl" { args.push(out.join("hacl_sha2.o").to_str().expect("UTF-8 object").to_owned()); }
    let refs: Vec<&str> = args.iter().map(String::as_str).collect();
    run(&ar, &refs);
    println!("cargo:rustc-link-search=native={}", out.display());
    println!("cargo:rustc-link-lib=static=tombstone_native");
    if backend == "openssl" { println!("cargo:rustc-link-lib=crypto"); }
}
