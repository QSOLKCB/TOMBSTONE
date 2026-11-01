# TOMBSTONE Phases 1-3: C99 SHA-256, witnessed splices, canonical receipts.
CC = cc
AR = ar
PKG_CONFIG ?= pkg-config
BUILD_DIR ?= build
CPPFLAGS ?=
CFLAGS ?= -O2 -std=c99 -Wall -Wextra -Wpedantic -Werror
LDFLAGS ?=
OPENSSL_CFLAGS := $(shell $(PKG_CONFIG) --cflags openssl)
OPENSSL_LIBS := $(shell $(PKG_CONFIG) --libs openssl)

LIB := $(BUILD_DIR)/libtombstone.a
OBJ := $(BUILD_DIR)/fingerprint.o $(BUILD_DIR)/deletion.o $(BUILD_DIR)/receipt.o
TEST_UNIT := $(BUILD_DIR)/test_fingerprint $(BUILD_DIR)/test_deletion $(BUILD_DIR)/test_receipt
TEST_INTEGRATION := $(BUILD_DIR)/test_public_link $(BUILD_DIR)/test_deletion_link
TESTS := $(TEST_UNIT) $(TEST_INTEGRATION)

.PHONY: all test clean docs-check sanitizer-test reproducibility
all: $(LIB)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/fingerprint.o: src/crypto/fingerprint.c include/tombstone/fingerprint.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude -c $< -o $@

$(BUILD_DIR)/deletion.o: src/core/deletion.c include/tombstone/deletion.h include/tombstone/fingerprint.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude -c $< -o $@

$(BUILD_DIR)/receipt.o: src/encoding/receipt.c include/tombstone/receipt.h include/tombstone/deletion.h include/tombstone/fingerprint.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude -c $< -o $@

$(LIB): $(OBJ)
	$(AR) rcsD $@ $^

$(BUILD_DIR)/test_fingerprint: tests/unit/test_fingerprint.c $(LIB)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude $< $(LIB) $(LDFLAGS) $(OPENSSL_LIBS) -o $@

$(BUILD_DIR)/test_deletion: tests/unit/test_deletion.c $(LIB)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude $< $(LIB) $(LDFLAGS) $(OPENSSL_LIBS) -o $@

$(BUILD_DIR)/test_public_link: tests/integration/test_public_link.c $(LIB)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude $< $(LIB) $(LDFLAGS) $(OPENSSL_LIBS) -o $@

$(BUILD_DIR)/test_deletion_link: tests/integration/test_deletion_link.c $(LIB)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude $< $(LIB) $(LDFLAGS) $(OPENSSL_LIBS) -o $@

$(BUILD_DIR)/test_receipt: tests/unit/test_receipt.c $(LIB)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude $< $(LIB) $(LDFLAGS) $(OPENSSL_LIBS) -o $@

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

clean:
	rm -rf build
