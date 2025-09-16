#!/usr/bin/env bats
set -u

setup() {
    cd "$BATS_TEST_DIRNAME"
    bats_load_library "bats-assert"
    bats_load_library "bats-support"
}

no_stderr() {
    "$@" 2>/dev/null
}

@test "myip" {
    run no_stderr ../myip
    assert_success
    assert_output --regexp "^(\d+\.\d+\.\d+\.\d+|[0-9a-f:]+)$"
}
