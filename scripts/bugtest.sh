#!/bin/bash

BUGLIST=$(egrep Testcase.name $1|cut -c 15-) 
echo "BUG FILE: $1"
echo "Snapshot: $2"
cd $NOOP_HOME
COVER_TYPE=toggle
n=0
ST=0
if [ $# -eq 3 ]; then
    ST=$3
fi
for bug in $BUGLIST
do
    n=$(expr $n + 1)
    if [ $n -lt $ST ]; then
        echo "Skip Bug $n: $bug"
        continue
    fi

    echo "Testing Bug $n: $bug"

    # copy bug file to tmp
    if [ -f tmp/bin/test.bin ]; then
        echo "remove tmp/bin/test.bin"
        rm tmp/bin/test.bin
    fi
    cp errors/${bug} tmp/bin/test.bin

    # test bug    
    CMDNAME="source env.sh && python3 $BMCFUZZ_HOME/scripts/emu.py -e -dt -dc -r -s $2"
    CMDNAME="cd $NOOP_HOME && source env.sh && python3 $BMCFUZZ_HOME/scripts/emu.py -e -dt -dc -af -r -s $2 -c ${COVER_TYPE}|grep Return.code|cut -c 14-"
    echo $CMDNAME
    RET=$(eval "${CMDNAME}")
    echo "return code: $RET"
    if [ $RET -ne 0 ]; then
        echo "Bug $n: $bug failed"
        break
    fi
    echo "Bug $n: $bug passed"
done
