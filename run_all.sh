#!/bin/bash

set -eux

which mvn

# Runs a command via `/usr/bin/time -v`, passing through the command's own
# stdout/stderr as before, then emits a MaxRSS-<name> line derived from
# time's "Maximum resident set size" report so stats.py can aggregate it
# the same way it already does for the Elapsed-<name> lines.
measure_rss() {
    local name="$1"
    shift
    local logfile
    logfile=$(mktemp)
    /usr/bin/time -v "$@" 2>"$logfile"
    cat "$logfile" >&2
    awk -v name="$name" '/Maximum resident set size/ { print "MaxRSS-" name ": " $NF " [KB]" }' "$logfile"
    rm -f "$logfile"
}

INPUT_DATA="./resources/wagahaiwa_nekodearu.txt"
INPUT_DATA_KO="./resources/mujeong.txt"
INPUT_DATA_ZH="./resources/rulin_waishi.txt"

# iter=0 is a warm-up to avoid unfair results due to lazy loading.
for i in $(seq 0 100)
do
    echo "iter" $i

    measure_rss "vaporetto" ./bench/vaporetto-bench/target/release/vaporetto-bench < $INPUT_DATA

    LD_LIBRARY_PATH=$PWD/thirdparty/kytea/tmpusr/lib measure_rss "kytea" ./bench/kytea-bench/a.out -model "./resources/jp-0.4.7-5.mod" < $INPUT_DATA

    LD_LIBRARY_PATH=$PWD/thirdparty/mecab/tmpusr/lib measure_rss "mecab-ipadic-2_7_0" ./bench/mecab-ipadic-2_7_0-bench/a.out < $INPUT_DATA

    LD_LIBRARY_PATH=$PWD/thirdparty/mecab/tmpusr/lib measure_rss "mecab-unidic-3_1_1" ./bench/mecab-unidic-3_1_1-bench/a.out < $INPUT_DATA

    pushd ./bench/kuromoji-bench
    measure_rss "kuromoji" mvn exec:java -Dexec.mainClass=kuromoji_bench.App < ../../$INPUT_DATA
    popd

    measure_rss "lindera-ipadic" ./bench/lindera-ipadic-bench/target/release/lindera-ipadic-bench < $INPUT_DATA

    measure_rss "lindera-unidic" ./bench/lindera-unidic-bench/target/release/lindera-unidic-bench < $INPUT_DATA

    measure_rss "lindera-cc-cedict" ./bench/lindera-cc-cedict-bench/target/release/lindera-cc-cedict-bench < $INPUT_DATA_ZH

    measure_rss "lindera-jieba" ./bench/lindera-jieba-bench/target/release/lindera-jieba-bench < $INPUT_DATA_ZH

    measure_rss "lindera-ko-dic" ./bench/lindera-ko-dic-bench/target/release/lindera-ko-dic-bench < $INPUT_DATA_KO

    pushd ./bench/sudachi-bench
    measure_rss "sudachi" mvn exec:java -Dexec.mainClass=sudachi_bench.App < ../../$INPUT_DATA
    popd

    measure_rss "sudachi.rs" ./bench/sudachirs-bench/target/release/sudachirs-bench < $INPUT_DATA

    measure_rss "rust-tinysegmenter" ./bench/rust-tinysegmenter-bench/target/release/rust-tinysegmenter-bench < $INPUT_DATA

    measure_rss "litsea-japanese" ./bench/litsea-japanese-bench/target/release/litsea-japanese-bench < $INPUT_DATA

    measure_rss "litsea-japanese-pos" ./bench/litsea-japanese-pos-bench/target/release/litsea-japanese-pos-bench < $INPUT_DATA

    measure_rss "litsea-korean" ./bench/litsea-korean-bench/target/release/litsea-korean-bench < $INPUT_DATA_KO

    measure_rss "litsea-korean-pos" ./bench/litsea-korean-pos-bench/target/release/litsea-korean-pos-bench < $INPUT_DATA_KO

    measure_rss "litsea-chinese" ./bench/litsea-chinese-bench/target/release/litsea-chinese-bench < $INPUT_DATA_ZH

    measure_rss "litsea-chinese-pos" ./bench/litsea-chinese-pos-bench/target/release/litsea-chinese-pos-bench < $INPUT_DATA_ZH

    measure_rss "litsea-japanese-two-stage" ./bench/litsea-japanese-two-stage-bench/target/release/litsea-japanese-two-stage-bench < $INPUT_DATA

    measure_rss "litsea-korean-two-stage" ./bench/litsea-korean-two-stage-bench/target/release/litsea-korean-two-stage-bench < $INPUT_DATA_KO

    measure_rss "litsea-chinese-two-stage" ./bench/litsea-chinese-two-stage-bench/target/release/litsea-chinese-two-stage-bench < $INPUT_DATA_ZH

    measure_rss "vibrato-ipadic-mecab-2_7_0" ./bench/vibrato-bench/target/release/vibrato-bench --dictname="ipadic-mecab-2_7_0" < $INPUT_DATA

    measure_rss "vibrato-unidic-cwj-3_1_1" ./bench/vibrato-bench/target/release/vibrato-bench --dictname="unidic-cwj-3_1_1" < $INPUT_DATA

    measure_rss "vibrato-unidic-cwj-3_1_1+compact-dual" ./bench/vibrato-bench/target/release/vibrato-bench --dictname="unidic-cwj-3_1_1+compact-dual" < $INPUT_DATA
done
