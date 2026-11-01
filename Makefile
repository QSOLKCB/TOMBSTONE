# TOMBSTONE Phase 1: C99-only SHA-256 fingerprint engine (OpenSSL EVP).
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
OBJ := $(BUILD_DIR)/fingerprint.o
TEST_UNIT := $(BUILD_DIR)/test_fingerprint
TEST_INTEGRATION := $(BUILD_DIR)/test_public_link

.PHONY: all test clean docs-check sanitizer-test reproducibility
all: $(LIB)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(OBJ): src/crypto/fingerprint.c include/tombstone/fingerprint.h | $(BUILD_DIR)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude -c $< -o $@

$(LIB): $(OBJ)
	$(AR) rcsD $@ $^

$(TEST_UNIT): tests/unit/test_fingerprint.c $(LIB)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude $< $(LIB) $(LDFLAGS) $(OPENSSL_LIBS) -o $@

$(TEST_INTEGRATION): tests/integration/test_public_link.c $(LIB)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(OPENSSL_CFLAGS) -Iinclude $< $(LIB) $(LDFLAGS) $(OPENSSL_LIBS) -o $@

test: $(TEST_UNIT) $(TEST_INTEGRATION)
	$(TEST_UNIT)
	$(TEST_INTEGRATION)

sanitizer-test:
	$(MAKE) BUILD_DIR=build/sanitize CFLAGS="-O1 -g -std=c99 -Wall -Wextra -Wpedantic -Werror -fno-omit-frame-pointer -fsanitize=address,undefined" LDFLAGS="-fsanitize=address,undefined" test

reproducibility:
	sh tools/check_reproducible.sh

docs-check:
	python3 tools/check_docs.py

clean:
	rm -rf build
