#!/usr/bin/env bats
set -u

setup() {
    export REAL_TMUX="$(command -v tmux)"
    export TEST_SOCKET="test-parallel-$$-$BATS_TEST_NUMBER"
    mkdir "$BATS_TEST_TMPDIR/bin"
    ln -s "$BATS_TEST_DIRNAME/tmux-parallel-tmux" "$BATS_TEST_TMPDIR/bin/tmux"
    export PATH="$BATS_TEST_TMPDIR/bin:$PATH"
    export OUTPUT="$BATS_TEST_TMPDIR/output"
}

teardown() {
    "$REAL_TMUX" -L "$TEST_SOCKET" kill-server 2>/dev/null || true
}

@test "tmux-parallel passes each argument intact and keeps panes open" {
    run "$BATS_TEST_DIRNAME/../tmux-parallel" sh -c 'printf "%s\n" "$1" >> "$OUTPUT"' ignored -- "a b" "it's fine"
    [ "$status" -eq 0 ]
    for attempt in 1 2 3 4 5 6 7 8 9 10; do
        [ -f "$OUTPUT" ] && [ "$(wc -l < "$OUTPUT")" -eq 2 ] && break
        sleep 0.1
    done
    [ "$(<"$OUTPUT")" = $'a b\nit\x27s fine' ]
    [ "$("$REAL_TMUX" -L "$TEST_SOCKET" list-panes -a -F '#{pane_id}' | wc -l | tr -d ' ')" -eq 2 ]
}

@test "tmux-parallel runs independent shell commands" {
    run "$BATS_TEST_DIRNAME/../tmux-parallel" -- "printf one > '$OUTPUT'" "printf two > '$OUTPUT.two'"
    [ "$status" -eq 0 ]
    for attempt in 1 2 3 4 5 6 7 8 9 10; do
        [ -f "$OUTPUT" ] && [ -f "$OUTPUT.two" ] && break
        sleep 0.1
    done
    [ "$(<"$OUTPUT")" = one ]
    [ "$(<"$OUTPUT.two")" = two ]
}

@test "tmux-parallel -w runs jobs in separate windows and keeps them open" {
    run "$BATS_TEST_DIRNAME/../tmux-parallel" -w -- 'true' 'true'
    [ "$status" -eq 0 ]
    [ "$("$REAL_TMUX" -L "$TEST_SOCKET" list-windows -a -F '#{window_id}' | wc -l | tr -d ' ')" -eq 2 ]
    [ "$("$REAL_TMUX" -L "$TEST_SOCKET" list-panes -a -F '#{pane_id}' | wc -l | tr -d ' ')" -eq 2 ]
}

@test "tmux-parallel continues in new windows when panes cannot be split" {
    export TEST_SESSION_HEIGHT=2
    run "$BATS_TEST_DIRNAME/../tmux-parallel" --script 'echo "$1" >> "$OUTPUT"' -- one two three
    [ "$status" -eq 0 ]
    [[ "$output" == *'continuing in a new window'* ]]
    for attempt in 1 2 3 4 5 6 7 8 9 10; do
        [ -f "$OUTPUT" ] && [ "$(wc -l < "$OUTPUT")" -eq 3 ] && break
        sleep 0.1
    done
    [ "$(sort "$OUTPUT")" = $'one\nthree\ntwo' ]
    [ "$("$REAL_TMUX" -L "$TEST_SOCKET" list-windows -a -F '#{window_id}' | wc -l | tr -d ' ')" -eq 3 ]
    [ "$("$REAL_TMUX" -L "$TEST_SOCKET" list-panes -a -F '#{pane_id}' | wc -l | tr -d ' ')" -eq 3 ]
}

@test "tmux-parallel script jobs show their arguments in window names and pane headings" {
    run "$BATS_TEST_DIRNAME/../tmux-parallel" -w --script 'echo "$1" >> "$OUTPUT"' -- aws/dev aws/dev-2
    [ "$status" -eq 0 ]
    for attempt in 1 2 3 4 5 6 7 8 9 10; do
        [ -f "$OUTPUT" ] && [ "$(wc -l < "$OUTPUT")" -eq 2 ] && break
        sleep 0.1
    done
    [ "$(wc -l < "$OUTPUT")" -eq 2 ]
    [ "$("$REAL_TMUX" -L "$TEST_SOCKET" list-windows -a -F '#{window_name}')" = $'aws/dev\naws/dev-2' ]
    for pane in $("$REAL_TMUX" -L "$TEST_SOCKET" list-panes -a -F '#{pane_id}'); do
        name=$("$REAL_TMUX" -L "$TEST_SOCKET" display-message -p -t "$pane" '#{window_name}')
        contents=$("$REAL_TMUX" -L "$TEST_SOCKET" capture-pane -p -J -t "$pane")
        [[ "$contents" == *"+ [$name] echo \"\$1\" >> \"\$OUTPUT\""* ]]
    done
}

@test "tmux-parallel preserves trailing newlines in arguments" {
    run "$BATS_TEST_DIRNAME/../tmux-parallel" sh -c 'printf "%s" "$1" > "$OUTPUT"' ignored -- $'ends\n'
    [ "$status" -eq 0 ]
    for attempt in 1 2 3 4 5 6 7 8 9 10; do
        if [ -f "$OUTPUT" ] && [ "$(od -An -tx1 "$OUTPUT" | tr -d ' \n')" = 656e64730a ]; then
            break
        fi
        sleep 0.1
    done
    [ "$(od -An -tx1 "$OUTPUT" | tr -d ' \n')" = 656e64730a ]
}

@test "tmux-parallel requires jobs" {
    run "$BATS_TEST_DIRNAME/../tmux-parallel" --
    [ "$status" -eq 1 ]
}
