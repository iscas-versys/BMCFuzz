EXP_DIR=$1

XFUZZ_LOG=$EXP_DIR/xfuzz.log
PATHFUZZ_LOG=$EXP_DIR/pathfuzz.log
HYPFUZZ_LOG=$EXP_DIR/hypfuzz.log
BMCFUZZ_LOG=$EXP_DIR/bmcfuzz.log

CMD="python3 $BMCFUZZ_HOME/scripts/experiment.py -g"

mkdir -p $NOOP_HOME/tmp/exp

if [ -f $XFUZZ_LOG ]; then
    cp $XFUZZ_LOG $NOOP_HOME/tmp/exp/xfuzz.log
    CMD="$CMD -ax"
fi
if [ -f $PATHFUZZ_LOG ]; then
    cp $PATHFUZZ_LOG $NOOP_HOME/tmp/exp/pathfuzz.log
    CMD="$CMD -ap"
fi
if [ -f $HYPFUZZ_LOG ]; then
    cp $HYPFUZZ_LOG $NOOP_HOME/tmp/exp/hypfuzz.log
    CMD="$CMD -ah"
fi
if [ -f $BMCFUZZ_LOG ]; then
    cp $BMCFUZZ_LOG $NOOP_HOME/tmp/exp/bmcfuzz.log
    CMD="$CMD -ab"
fi

echo $CMD
RET=$(eval "${CMD}")
echo "$RET"

cp $NOOP_HOME/tmp/exp/output.png $EXP_DIR/output.png
cp $NOOP_HOME/tmp/exp/output_full.png $EXP_DIR/output_full.png
echo "Graphs generated in $EXP_DIR"
