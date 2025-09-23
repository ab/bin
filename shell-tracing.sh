#!/bin/bash
#
# set __log_performance=1 to enable
#
# see analysis script in oneoffs/shell_trace_report.py
#
# or try otel-cli for a different take on this


#export OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317

#TRACEPARENT=$(/opt/homebrew/bin/otel-cli span -n start -s bashrc --tp-print \
#    | grep ^TRACEPARENT | cut -f2 -d=)
#export TRACEPARENT

perf::conf_write() {
    set -x
    tee ~/.bash_tracing_conf <<EOM
# Config for ~/bin/shell-tracing.sh
__log_performance=1
__log_threshold=0.75 # seconds
EOM
    set +x
}

perf::start() {
    __log_performance=1
    __log_threshold=${__log_threshold-0.5}
    __log_start="${__log_start-$EPOCHREALTIME}"
    __log_span_start=()
    __log_span=()
    __log_span_count=0
    __log_span_ids=()
    __log_file=$(mktemp "/tmp/bash.perf.json.$(date +%s).XXXXXX")
    echo >"$__log_file" '{ "spans": ['
}
perf::cleanup() {
    local span
    for span in "${__log_span[@]}"; do
        echo >&2 "Warning: spans still open: $span"
    done
    # stupid json hack to avoid needing JSON5 w/ commas
    echo >>"$__log_file" "  {}"
    echo >>"$__log_file" "] }"

    local total
    total=$(bc -l <<< "$EPOCHREALTIME - $__log_start")

    if (( $(bc -l <<< "$total > $__log_threshold") )); then
        echo >&2 "perf: total time (ms) $total exceeds threshold ($__log_threshold)"
        echo >&2 "perf: see full report in $__log_file"
        echo >&2

        if [ -x "$HOME/bin/oneoffs/shell_trace_report.py" ]; then
            echo >&2 "+ $HOME/bin/oneoffs/shell_trace_report.py $__log_file"
            "$HOME/bin/oneoffs/shell_trace_report.py" "$__log_file"
        fi
    else
        rm "$__log_file"
    fi
    unset __log_threshold __log_start __log_span_start __log_span __log_span_count __log_span_ids __log_file
}

span_start() {
    if [ -z "${__log_performance-}" ]; then
        return
    fi

    local now span_id
    now=$EPOCHREALTIME
    ((++__log_span_count))
    span_id=$(printf "%03d" "$__log_span_count")
    __log_span_start+=("$now")
    __log_span+=("$*")
    __log_span_ids+=("$span_id")

    local span_name
    span_name="$*"

    if [[ $span_name == *\"* ]]; then
        echo >&2 "Span name cannot contain \": '$span_name'"
        return 1
    fi
}
span_end() {
    if [ -z "${__log_performance-}" ]; then
        return
    fi
    local now span_start span_name span_id

    now=$EPOCHREALTIME
    span_id="${__log_span_ids[-1]}"
    span_name="${__log_span[-1]}"
    span_start="${__log_span_start[-1]}"

    unset "__log_span_ids[-1]"
    unset "__log_span[-1]"
    unset "__log_span_start[-1]"

    local parent=
    if [ "${#__log_span_ids[@]}" -ge 1 ]; then
        parent="${__log_span_ids[-1]}"
    fi

    #/opt/homebrew/bin/otel-cli span -n "$span_name" -s bashrc --start "$span_start" --end "$now"

    cat >>"$__log_file" <<EOM
  {"span_id": "$span_id", "span_name": "$span_name", "parent": "$parent", "start": $span_start, "end": $now},
EOM
}
