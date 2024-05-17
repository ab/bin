#!/usr/bin/env bats
set -u

setup() {
    cd "$BATS_TEST_DIRNAME"
    bats_load_library "bats-assert"
    bats_load_library "bats-support"
}

@test "help exits 0" {
    ../choice --help
    ../choice -h
}

@test "single choice" {
    run ../choice freedom
    assert_success
    assert_output freedom
}

@test "single choice, stdin" {
    run ../choice <<< "one"
    assert_success
    assert_output one
}

@test "flip a coin" {
    run ../choice heads tails
    assert_output --regexp '^(heads|tails)$'
    assert_success
}

@test "pick a number 0-9, stdin" {
    run ../choice <<< "$(seq 0 9)"
    assert_output -e '^[0-9]$'
    assert_success
}

choice_with_nulls() {
    echo -e 'New\nYork\0San\nFrancisco' | ../choice -0
}

@test "test with nulls" {
    run choice_with_nulls
    assert_success
    [[ "$output" == $(echo -e "New\nYork") || "$output" == $(echo -e "San\nFrancisco") ]]
}

@test "test with newlines" {
    run ../choice <<< "$(echo -e 'New York\nSan Francisco')"
    assert_output -e '^(New York|San Francisco)$'
    assert_success
}

@test "can't combine -0 and args" {
    run ../choice -0 foo bar </dev/null
    assert_failure
}

@test "empty input" {
    run ../choice </dev/null
    assert_failure
    assert_line "choice: error: Must provide at least one choice (stdin was empty)"
}
