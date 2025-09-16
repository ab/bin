#!/usr/bin/env bats
set -u

setup() {
    cd "$BATS_TEST_DIRNAME"
    bats_load_library "bats-assert"
    bats_load_library "bats-support"
}

@test "total empty" {
    run ../total /dev/null
    assert_success
    assert_output 0
}

@test "total empty stdin" {
    run ../total </dev/null
    assert_success
    assert_output 0
}

@test "nonexistent file" {
    run ../total /nonexistent/doesnotexist
    assert_output --regexp "No such file or directory"
    assert_failure
}

@test "multiple files" {
    run ../total <(echo -e '1\n2') <(echo -e '3\n4')
    assert_success
    assert_output 10
}


@test "seq" {
    run ../total <(seq 1 10)
    assert_success
    assert_output 55
}

@test "seq reverse" {
    run ../total <<<"$(seq 10 -1 1)"
    assert_success
    assert_output 55
}

@test "decimal exact" {
    run ../total <<EOM
1.1
2.2
EOM
    assert_success
    assert_output '3.3'
}

@test "decimals sum to 1" {
    run ../total <<EOM
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
0.1
EOM
    assert_success
    assert_output '1.0'
}

@test "decimals sum to 0" {
    run ../total <<EOM
0.1
0.1
0.1
-0.3
EOM
    assert_success
    assert_output '0.0'
}

@test "decimal and int" {
    run ../total <<EOM
248
89.53
149.66
EOM
    assert_success
    assert_output '487.19'
}

@test "python docs example" {
    run ../total <<EOM
-0.10430216751806065
-266310978.67179024
143401161448607.16
-143401161400469.7
266262841.31058735
-0.003244936839808227
EOM
    assert_success
    assert_output '-0.008749994357908227'
}

@test "invalid input" {
    run ../total <<EOM
123
foo
456
EOM
    assert_failure 2
    assert_output "Invalid number: 'foo'"
}
