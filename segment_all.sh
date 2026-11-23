#!/bin/bash
# Write the segmentation of every series and print the agreement and accuracy
# tables in Markdown. Run from the repository root after
# ./download_resources.sh and ./compile_all.sh, e.g.
#   ./segment_all.sh | tee ./accuracy
#
# Each series runs once on each input, through run_all.sh with SEGMENT_DIR,
# so it uses the same command and options as its speed row. The tokens go to
# ./tokens/<input>/<series>.txt, and segmentation.py scores them.

set -eux

GOLD="$PWD/resources/gold"
TOKENS="$PWD/tokens"

# -B: segmentation.py loads stats.py, and should not write __pycache__.
python3 -B ./segmentation.py text "$GOLD" "$TOKENS/text"

# The speed corpora, for the agreement with the reference implementations.
SEGMENT_DIR="$TOKENS/corpus" ./run_all.sh >&2

# The parallel UD treebanks, one per language.
SEGMENT_DIR="$TOKENS/pud" \
    INPUT_DATA="$TOKENS/text/ja_pud.txt" \
    INPUT_DATA_KO="$TOKENS/text/ko_pud.txt" \
    INPUT_DATA_ZH="$TOKENS/text/zh_pud.txt" \
    INPUT_DATA_EN="$TOKENS/text/en_pud.txt" \
    ./run_all.sh >&2

# KLUE-DP dev, for the Korean series; the other series get no input.
SEGMENT_DIR="$TOKENS/klue" \
    INPUT_DATA=/dev/null \
    INPUT_DATA_KO="$TOKENS/text/klue_dp_dev.txt" \
    INPUT_DATA_ZH=/dev/null \
    INPUT_DATA_EN=/dev/null \
    ./run_all.sh >&2

python3 -B ./segmentation.py report "$GOLD" "$TOKENS"
