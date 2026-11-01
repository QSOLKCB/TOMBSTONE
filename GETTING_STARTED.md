# Getting started — Phase 4 Rust CLI and C99 engine

TOMBSTONE can now fingerprint raw bytes, verify caller-supplied deletion-splice relationships, produce canonical JSON receipts, and validate receipt chains. The new Rust command uses the **existing C99 engine** through a narrow FFI boundary. It never erases, deletes or alters files.

## Ubuntu dependencies

\`\`\`sh
sudo apt-get install build-essential pkg-config libssl-dev python3 cargo rustc
git clone https://github.com/QSOLKCB/TOMBSTONE.git
cd TOMBSTONE
\`\`\`

## Native and Rust checks

\`\`\`sh
make test
make sanitizer-test
make reproducibility
make docs-check
cargo test --workspace --locked --offline
cargo build -p tombstone-cli --release --locked --offline
\`\`\`

Run the completed binary:

\`\`\`sh
target/release/tombstone hash tests/fixtures/before.txt
target/release/tombstone observe tests/fixtures/before.txt tests/fixtures/after.txt
target/release/tombstone delete tests/fixtures/before.txt tests/fixtures/deleted.txt tests/fixtures/after.txt 4

target/release/tombstone verify-chain \
    machine/examples/explicit-delete-v1.json \
    machine/examples/observed-transition-v1.json \
    machine/examples/unchanged-v1.json
\`\`\`

The last command verifies **local chain consistency only**. Supply \`--trusted-head\` with an independently known final SHA-256 to check an external commitment. The original golden fixtures are public synthetic test data. No real deleted information is retained by TOMBSTONE receipts.

Read [docs/CLI.md](docs/CLI.md) for commands, exact stdout/exit contracts and security limits, and [SECURITY.md](SECURITY.md) for the distinction between a witnessed splice and real-world erasure. The TUI and GTK are not yet implemented.
