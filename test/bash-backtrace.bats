#!/usr/bin/env bats
set -u

setup() {
    cd "$BATS_TEST_DIRNAME"
    bats_load_library "bats-assert"
    bats_load_library "bats-support"
}

@test "bash-backtrace rejects non-Bash shells" {
    run dash -c '. "$1"' dash ../bash-backtrace.sh

    assert_failure
    assert_output "Error: this script only works in bash"
}

@test "bash-backtrace does not affect successful commands" {
    run bash -c 'source "$1"; printf ready' bash ../bash-backtrace.sh

    assert_success
    assert_output ready
}

@test "bash-backtrace reports nested function frames and source" {
    run bash bash-backtrace-fixture.sh ../bash-backtrace.sh

    assert_failure 1
    assert_line "Traceback (most recent call last):"
    assert_line '  File "bash-backtrace-fixture.sh", line 7, in outer'
    assert_line "    inner"
    assert_line '  File "bash-backtrace-fixture.sh", line 11, in inner'
    assert_line "    cat /nonexistent"
    assert_line "Command exited with status 1"
}
