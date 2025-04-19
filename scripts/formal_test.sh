#!/bin/bash

BIN_DIR=$BMCFUZZ_HOME/Formal/coverTasks/hexbin
BIN_LIST=$(ls $BIN_DIR)
COVER_TYPE=toggle

echo "Running formal tests for $COVER_TYPE coverage" > $NOOP_HOME/tmp/fuzz.log

FUZZ_CMD="source env.sh && $NOOP_HOME/build/fuzzer -c firrtl.$COVER_TYPE --"
EXTRA_CMD=" -I 300 -C 300 --fuzz-id 0 >> $NOOP_HOME/tmp/fuzz.log 2>&1"

mkdir -p $NOOP_HOME/tmp
mkdir -p $NOOP_HOME/tmp/fuzz

for BIN in $BIN_LIST; do
    BIN_BASE=$(basename "${BIN}")
    echo "Running $BIN" >> $NOOP_HOME/tmp/fuzz.log
    echo "Running $BIN"
    CMD="$FUZZ_CMD $BIN_DIR/$BIN $EXTRA_CMD"
    echo $CMD >> $NOOP_HOME/tmp/fuzz.log

    $(eval $CMD)

    mv $NOOP_HOME/tmp/sim_run_cover_points.csv $NOOP_HOME/tmp/fuzz/$BIN_BASE.csv
done

