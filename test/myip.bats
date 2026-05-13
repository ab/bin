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

# Note: this test assumes a working IPv4 and IPv6 connection!

@test "myip IPv4" {
    run ../myip -4 -q
    assert_success
    assert_output --regexp "^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$"
}
@test "myip IPv4 HTTP" {
    run ../myip -4 -q --http
    assert_success
    assert_output --regexp "^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$"
}

@test "myip IPv6" {
    run ../myip -6 -q
    assert_success
    assert_output --regexp "^([a-f0-9:]+:+)+[a-f0-9]+$"
}

@test "myip IPv6 HTTP" {
    run ../myip -6 -q --http
    assert_success
    assert_output --regexp "^([a-f0-9:]+:+)+[a-f0-9]+$"
}

@test "myip default" {
    run ../myip -q
    assert_success

    nl=$'\n'
    expected="^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$nl([a-f0-9:]+:+)+[a-f0-9]+$"
    assert_output --regexp "$expected"
}
