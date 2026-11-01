use std::process::Command;

fn main() {
    println!("cargo:rerun-if-changed=build.rs");
    // Rust calls GTK4's stable C API directly, with no new Rust crates.
    // Only a deliberately selected GUI build needs native GTK libraries.
    let status = Command::new("pkg-config")
        .args(["--exists", "gtk4 >= 4.6"])
        .status()
        .expect("pkg-config required for optional GTK4 build");
    assert!(
        status.success(),
        "GTK4 development libraries >= 4.6 required (Ubuntu: libgtk-4-dev)"
    );
    // Explicitly requested linker libraries; GTK's pkg-config may also
    // return extra transitive libraries, but our FFI uses these four APIs.
    for lib in ["gtk-4", "gio-2.0", "gobject-2.0", "glib-2.0"] {
        println!("cargo:rustc-link-lib={lib}");
    }
}
