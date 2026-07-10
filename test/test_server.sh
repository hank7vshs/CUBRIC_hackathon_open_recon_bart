#!/bin/bash
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE

set -e

# Help string
show_help() {
    echo "Usage: $0 [--speed <fast|slow|all>] [--mode <i2i_invertcontrast|r2ci_bart|all>] [<error-margin> <OR-module> <data> <ref-reco> <reco-speed: [fast/slow]>]"
    echo
    echo "You must provide five parameters as arguments. <data> is looked up in data/ unless a subfolder prefix is given (e.g. ref/file.h5). <ref> is looked up in ref/ unless a subfolder prefix is given."
    echo
    echo "Alternatively, you can OMIT the PARAMETERS and the script will try to source a tests file for default values."
    echo "Set TESTS_FILE to override (default: tests.sh)."
    echo
    echo "Options:"
    echo "  -h                       Show this help message"
    echo "  --speed <fast|slow|all>  Only run tests matching the given speed (default: all)"
    echo "  --mode  <i2i_invertcontrast|r2ci_bart|all>   Only run tests matching the given OR module (default: all)"
}

# Check for help flag
if [[ "$1" == "-h" ]];
then
    show_help
    exit 0
fi

# Parse --speed and --mode options
SPEED_FILTER="all"
MODE_FILTER="all"
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --speed)
            if [[ -z "$2" || ( "$2" != "fast" && "$2" != "slow" && "$2" != "all" ) ]]; then
                echo "Error: --speed requires 'fast', 'slow', or 'all' as argument."
                show_help
                exit 1
            fi
            SPEED_FILTER="$2"
            shift 2
            ;;
        --mode)
            if [[ -z "$2" || ( "$2" != "i2i_invertcontrast" && "$2" != "r2ci_bart" && "$2" != "all" ) ]]; then
                echo "Error: --mode requires 'i2i_invertcontrast', 'r2ci_bart', or 'all' as argument."
                show_help
                exit 1
            fi
            MODE_FILTER="$2"
            shift 2
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done
set -- "${ARGS[@]+"${ARGS[@]}"}"

# Default tests file (can be overridden by setting TESTS_FILE before calling the script)
TESTS_FILE="${TESTS_FILE:-$(dirname "${BASH_SOURCE[0]}")/tests.sh}"

# Check if five arguments are provided
if [[ $# -ne 5 ]];
then
    if [[ -f "${TESTS_FILE}" ]];
    then
        echo "Load all tests."
        source "${TESTS_FILE}"
    else
        echo "Error: File ${TESTS_FILE} not found and insufficient arguments provided."
        show_help
        exit 1
    fi
else
    TESTS=("$1 $2 $3 $4 $5")
    echo -e "Custom test:\t${TESTS[0]}"
fi

# Filter tests by speed
if [[ "$SPEED_FILTER" != "all" ]]; then
    echo "Filtering tests by speed: $SPEED_FILTER"
    FILTERED_TESTS=()
    for t in "${TESTS[@]}"; do
        set -- $t
        if [[ "$5" == "$SPEED_FILTER" ]]; then
            FILTERED_TESTS+=("$t")
        fi
    done
    TESTS=("${FILTERED_TESTS[@]+"${FILTERED_TESTS[@]}"}")
    if [[ ${#TESTS[@]} -eq 0 ]]; then
        echo "No tests found matching speed: $SPEED_FILTER"
        exit 0
    fi
fi

# Filter tests by mode
if [[ "$MODE_FILTER" != "all" ]]; then
    echo "Filtering tests by mode: $MODE_FILTER"
    FILTERED_TESTS=()
    for t in "${TESTS[@]}"; do
        set -- $t
        if [[ "$2" == "$MODE_FILTER" ]]; then
            FILTERED_TESTS+=("$t")
        fi
    done
    TESTS=("${FILTERED_TESTS[@]+"${FILTERED_TESTS[@]}"}")
    if [[ ${#TESTS[@]} -eq 0 ]]; then
        echo "No tests found matching mode: $MODE_FILTER"
        exit 0
    fi
fi

MAIN_DIR=".."

run_test()
{
    EPS=$1
    OR_MODULE=$2
    DATA=$3
    REF=$4
    SPEED=$5
    UI_DATA=${6:-}

    # Resolve DATA and REF: if the value already contains a '/' treat it as a path
    # relative to the test/ directory; otherwise apply the default folder prefix.
    if [[ "${DATA}" == */* ]]; then
        DATA_PATH="${MAIN_DIR}/test/${DATA}"
    else
        DATA_PATH="${MAIN_DIR}/test/data/${DATA}"
    fi
    if [[ "${REF}" == */* ]]; then
        REF_PATH="${MAIN_DIR}/test/${REF}"
    else
        REF_PATH="${MAIN_DIR}/test/ref/${REF}"
    fi

    # Resolve UI_DATA: bare filename is looked up in test/data/ (without .json extension).
    # client.py appends .json itself, so we pass the path without extension.
    if [[ -n "${UI_DATA}" ]]; then
        UI_DATA_ARG="${MAIN_DIR}/test/data/${UI_DATA}"
    else
        UI_DATA_ARG=""
    fi

    # Remove stale output before starting to avoid reading previous results
    [ -f ${MAIN_DIR}/client/out.h5 ] && rm ${MAIN_DIR}/client/out.h5

    # Start server
    (
        cd ${MAIN_DIR}/server

        ./run_server.sh "${OR_MODULE}" > /dev/null 2>&1
    ) &
    PID1=$!

    # Run client — pass optional UI data override via -u if provided
    (
        cd ${MAIN_DIR}/client

        if [[ -n "${UI_DATA_ARG}" ]]; then
            python3 client.py ${DATA_PATH} -u "${UI_DATA_ARG}" > /dev/null 2>&1
        else
            python3 client.py ${DATA_PATH} > /dev/null 2>&1
        fi
    ) &
    PID2=$!

    # Wait for both processes to finish
    wait $PID1
    wait $PID2

    if [ ! -f  "${REF_PATH}" ]
    then 
        echo -e "\e[31m✖ Reference not found!\e[0m"
        exit 1
    fi

    if [ ! -f  "${MAIN_DIR}/client/out.h5" ]
    then
        echo -e "\e[31m✖ Reconstructed file could not be found!\e[0m"
        exit 1
    fi

    # Test NRMSE of the absolute difference of the complex datasets
    python3 "$(dirname "${BASH_SOURCE[0]}")/scripts/nrmse_test.py" $EPS "${MAIN_DIR}/client/out.h5" "${REF_PATH}"
}
export -f run_test


echo "Start testing..."

for t in "${TESTS[@]}"
do
    set -- $t
    echo -e "\nRunning Test:\n${t}"
    run_test $1 $2 $3 $4 $5 ${6:-}
done
