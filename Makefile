# TOMBSTONE Phases 1-3: C99 SHA-256, witnessed splices, canonical receipts.
CC = cc
AR = ar
PKG_CONFIG ?= pkg-config
SHA256_BACKEND ?= openssl
ifeq ($(SHA256_BACKEND),hacl)
BUILD_DIR ?= build/hacl
FINGERPRINT_SOURCE := src/crypto/fingerprint_hacl.c
HACL_COMPAT_FLAGS := -Wno-pedantic
EXTRA_OBJ := $(BUILD_DIR)/hacl_sha2.o
HASH_LIBS :=
HACL_ROOT := vendor/hacl-star
HACL_INC := -I$(HACL_ROOT)/dist/gcc-compatible -I$(HACL_ROOT)/dist/karamel/include -I$(HACL_ROOT)/dist/karamel/krmllib/dist/minimal
else ifeq ($(SHA256_BACKEND),openssl)
BUILD_DIR ?= build
FINGERPRINT_SOURCE := src/crypto/fingerprint.c
EXTRA_OBJ :=
HASH_LIBS = $(OPENSSL_LIBS)
else
$(error Unsupported SHA256_BACKEND: $(SHA256_BACKEND))
endif
CPPFLAGS ?=
CFLAGS ?= -O2 -std=c99 -Wall -Wextra -Wpedantic -Werror
LDFLAGS ?=
OPENSSL_CFLAGS := $(shell $(PKG_CONFIG) --cflags openssl)
OPENSSL_LIBS := $(shell $(PKG_CONFIG) --libs openssl)

LIB := $(BUILD_DIR)/libtombstone.a
OBJ := $(BUILD_DIR)/fingerprint.o $(BUILD_DIR)/deletion.o $(BUILD_DIR)/receipt.o $(EXTRA_OBJ)
TEST_UNIT := $(BUILD_DIR)/test_fingerprint $(BUILD_DIR)/test_deletion $(BUILD_DIR)/test_receipt
TEST_INTEGRATION := $(BUILD_DIR)/test_public_link $(BUILD_DIR)/test_deletion_link
TESTS := $(TEST_UNIT) $(TEST_INTEGRATION)

.PHONY: all test clean docs-check sanitizer-test reproducibility rust-test rust-build tui-build gtk-test gtk-build fuzz
all: $(LIB)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/fingerprint.o: $(FINGERPRINT_SOURCE) include/tombstone/fingerprint.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(if $(filter hacl,$(SHA256_BACKEND)),-D_DEFAULT_SOURCE -Wno-pedantic,) $(OPENSSL_CFLAGS) $(HACL_INC) -Iinclude -c $< -o $@

$(BUILD_DIR)/hacl_sha2.o: $(HACL_ROOT)/dist/gcc-compatible/Hacl_Hash_SHA2.c | $(BUILD_DIR)
	$(CC) -O2 -std=c99 -D_DEFAULT_SOURCE $(HACL_INC) -c $< -o $@

$(BUILD_DIR)/deletion.o: src/core/deletion.c include/tombstone/deletion.h include/tombstone/fingerprint.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude -c $< -o $@

$(BUILD_DIR)/receipt.o: src/encoding/receipt.c include/tombstone/receipt.h include/tombstone/deletion.h include/tombstone/fingerprint.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude -c $< -o $@

$(LIB): $(OBJ)
	$(AR) rcsD $@ $^

$(BUILD_DIR)/test_fingerprint: tests/unit/test_fingerprint.c $(LIB)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude $< $(LIB) $(LDFLAGS) $(HASH_LIBS) -o $@

$(BUILD_DIR)/test_deletion: tests/unit/test_deletion.c $(LIB)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude $< $(LIB) $(LDFLAGS) $(HASH_LIBS) -o $@

$(BUILD_DIR)/test_public_link: tests/integration/test_public_link.c $(LIB)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude $< $(LIB) $(LDFLAGS) $(HASH_LIBS) -o $@

$(BUILD_DIR)/test_deletion_link: tests/integration/test_deletion_link.c $(LIB)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude $< $(LIB) $(LDFLAGS) $(HASH_LIBS) -o $@

$(BUILD_DIR)/test_receipt: tests/unit/test_receipt.c $(LIB)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude $< $(LIB) $(LDFLAGS) $(HASH_LIBS) -o $@

test: $(TESTS)
	$(BUILD_DIR)/test_fingerprint
	$(BUILD_DIR)/test_deletion
	$(BUILD_DIR)/test_receipt
	$(BUILD_DIR)/test_public_link
	$(BUILD_DIR)/test_deletion_link

sanitizer-test:
	$(MAKE) BUILD_DIR=build/sanitize CFLAGS="-O1 -g -std=c99 -Wall -Wextra -Wpedantic -Werror -fno-omit-frame-pointer -fsanitize=address,undefined" LDFLAGS="-fsanitize=address,undefined" test

reproducibility:
	sh tools/check_reproducible.sh

docs-check:
	python3 tools/check_docs.py

rust-test:
	cargo test --workspace --offline --locked

rust-build:
	cargo build -p tombstone-cli --release --offline --locked

tui-build:
	cargo build -p tombstone-tui --release --offline --locked

gtk-test:
	cargo test --manifest-path apps/gtk/Cargo.toml --offline --locked

gtk-build:
	cargo build --manifest-path apps/gtk/Cargo.toml --release --offline --locked

fuzz:
	sh tools/run_fuzz.sh

clean:
	rm -rf build
