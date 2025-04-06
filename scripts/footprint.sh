#!bin/bash

CORPUS_DIR=$LINEARIZED_CORPUS
OUT_DIR=$FOOTPRINTS_CORPUS
FUZZER=$NOOP_HOME/build/fuzzer
LOG_FILE=$BMCFUZZ_HOME/scripts/logs/script.log

CORPUS_BIN=$(ls ${CORPUS_DIR}/$1*.bin)

echo "Log Init" > ${LOG_FILE}

if [ -d ${OUT_DIR} ]; then
    echo "remove ${OUT_DIR}" >> ${LOG_FILE}
    rm -r ${OUT_DIR}
fi
mkdir -p ${OUT_DIR}

for bin in $CORPUS_BIN
do
    BINFILE=$(basename "${bin}")
    echo "Dump footprint from ${BINFILE}" >> ${LOG_FILE}
    FILENAME="${BINFILE%%.*}"
    MFP_FILE="${OUT_DIR}/${FILENAME}.mfp"
    CMDNAME="${FUZZER} --auto-exit -- ${bin} -I 10000 -C 10000 --no-diff --dump-footprint ${MFP_FILE} >> ${LOG_FILE}"
    echo $CMDNAME
    $(eval $CMDNAME)
	# OUTSTR=$(eval "${CMDNAME}" 2>&1)
    # echo $OUTSTR
done
