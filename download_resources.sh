#!/bin/bash

set -eux

which wget
which gunzip
which unzip

# Checks "<sha256>  <file>" lines read from stdin, with sha256sum (GNU
# coreutils on Linux) or shasum (macOS).
sha256_check() {
    if command -v sha256sum > /dev/null; then
        sha256sum -c -
    else
        shasum -a 256 -c -
    fi
}

pushd "./resources"

# The original URL (http://www.phontron.com/kytea/download/model/) now returns
# an HTML page, so fetch the model from the Wayback Machine's copy of it. The
# checksum rejects a truncated or different file. That download is slow, so an
# archive that an earlier run already fetched and that passes the checksum is
# reused. `wget -c` is not used: when the file is already complete, the Wayback
# Machine answers the range request with a redirect loop.
if [ ! -f "./jp-0.4.7-5.mod" ]; then
    if [ ! -f "./jp-0.4.7-5.mod.gz" ] || ! echo "963a311bb75e1685a585a2364172c9c6705a894c31f65c4c4d4d227254fb1fd4  ./jp-0.4.7-5.mod.gz" | sha256_check; then
        wget --tries=5 "https://web.archive.org/web/20250824162500id_/http://www.phontron.com/kytea/download/model/jp-0.4.7-5.mod.gz" -O "./jp-0.4.7-5.mod.gz"
        echo "963a311bb75e1685a585a2364172c9c6705a894c31f65c4c4d4d227254fb1fd4  ./jp-0.4.7-5.mod.gz" | sha256_check
    fi
    gunzip "./jp-0.4.7-5.mod.gz"
fi

if [ ! -d "./unidic-cwj-3.1.1" ]; then
    wget "https://ccd.ninjal.ac.jp/unidic_archive/cwj/3.1.1/unidic-cwj-3.1.1.zip" -O "./unidic-cwj-3.1.1.zip"
    rm -rf "./unidic-cwj-3.1.1"
    unzip "./unidic-cwj-3.1.1.zip"
fi

if [ ! -d "./unidic-cwj-202512" ]; then
    wget "https://clrd.ninjal.ac.jp/unidic_archive/2512/unidic-cwj-202512.zip" -O "./unidic-cwj-202512.zip"
    rm -rf "./unidic-cwj-202512"
    # Unlike the 3.1.1 archive, this one has no top-level directory.
    unzip "./unidic-cwj-202512.zip" -d "./unidic-cwj-202512"
fi

# mecab-ko-dic, the Korean dictionary for MeCab that lindera's ko-dic is built
# from. compile_all.sh compiles it in place.
if [ ! -d "./mecab-ko-dic-2.1.1-20180720" ]; then
    wget "https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/mecab-ko-dic-2.1.1-20180720.tar.gz" -O "./mecab-ko-dic-2.1.1-20180720.tar.gz"
    echo "fd62d3d6d8fa85145528065fabad4d7cb20f6b2201e71be4081a4e9701a5b330  ./mecab-ko-dic-2.1.1-20180720.tar.gz" | sha256_check
    tar -xzf "./mecab-ko-dic-2.1.1-20180720.tar.gz"
fi

# Gold-standard data for segmentation.py (see segment_all.sh), all at UD's tag
# r2.19: the parallel UD treebanks (PUD) of Japanese, Chinese and English,
# under CC BY-SA 3.0, and the test set of UD_Korean-Kaist, under CC BY-SA 4.0.
# They are fetched here rather than committed, and checked against their
# SHA-256.
mkdir -p "./gold"
fetch_gold() {
    local url="$1" sum="$2"
    local file="./gold/$(basename "$url")"
    if [ ! -f "$file" ]; then
        wget "$url" -O "$file"
        echo "$sum  $file" | sha256_check
    fi
}
fetch_gold "https://raw.githubusercontent.com/UniversalDependencies/UD_Japanese-PUD/r2.19/ja_pud-ud-test.conllu" 7ac51383189bdf5513102f9f8ac7ee1b967d5449f8c2dc1a9108fa21a8f1a688
fetch_gold "https://raw.githubusercontent.com/UniversalDependencies/UD_Korean-Kaist/r2.19/ko_kaist-ud-test.conllu" b4134e421b74791df11d07da9fd19873ac2682c192214e81f47f9b2fa0b56892
fetch_gold "https://raw.githubusercontent.com/UniversalDependencies/UD_Chinese-PUD/r2.19/zh_pud-ud-test.conllu" 38ad4f76224567a275f3492a87a9b7ed91690b8f0959ee4eabac0ae022d6cf41
fetch_gold "https://raw.githubusercontent.com/UniversalDependencies/UD_English-PUD/r2.19/en_pud-ud-test.conllu" befc5e901b58732f2308b1aac5cdd804d938362ab31c9fe400c61c28e8e155d8

if [ ! -f "./wagahaiwa_nekodearu.txt" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.16.0/resources/wagahaiwa_nekodearu.txt" -O "./wagahaiwa_nekodearu.txt"
fi

if [ ! -f "./mujeong.txt" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.16.0/resources/mujeong.txt" -O "./mujeong.txt"
fi

if [ ! -f "./rulin_waishi.txt" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.16.0/resources/rulin_waishi.txt" -O "./rulin_waishi.txt"
fi

if [ ! -f "./pride_and_prejudice.txt" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.16.0/resources/pride_and_prejudice.txt" -O "./pride_and_prejudice.txt"
fi

popd

pushd "./thirdparty"
# mecab-ko is MeCab 0.996 modified for Korean. Unlike the original MeCab, it
# reads the left-space-penalty-factor that mecab-ko-dic's dicrc sets.
# 0.996-ko-0.9.2 (2015) is its last release.
if [ ! -d "./mecab-ko" ]; then
    wget "https://bitbucket.org/eunjeon/mecab-ko/downloads/mecab-0.996-ko-0.9.2.tar.gz" -O "./mecab-0.996-ko-0.9.2.tar.gz"
    echo "d0e0f696fc33c2183307d4eb87ec3b17845f90b81bf843bd0981e574ee3c38cb  ./mecab-0.996-ko-0.9.2.tar.gz" | sha256_check
    mkdir "./mecab-ko"
    tar -xzf "./mecab-0.996-ko-0.9.2.tar.gz" -C "./mecab-ko" --strip-components=1
fi
popd

pushd "./bench/sudachi-bench"
# Sudachi (Java) 0.8.2 and sudachi.rs 0.7.0 read only the V1 dictionary format,
# which is distributed under sudachidict/v1/. Both benches use this dictionary.
if [ ! -d "./sudachi-dictionary-20261015" ]; then
    wget "http://sudachi.s3-website-ap-northeast-1.amazonaws.com/sudachidict/v1/sudachi-dictionary-20261015-core.zip" -O "./sudachi-dictionary-20261015-core.zip"
    rm -rf "./sudachi-dictionary-20261015"
    unzip "./sudachi-dictionary-20261015-core.zip"
fi
popd

pushd "./bench/litsea-japanese-bench"
if [ ! -f "./japanese.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.16.0/models/japanese.model" -O "./japanese.model"
fi
popd

pushd "./bench/litsea-korean-bench"
if [ ! -f "./korean.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.16.0/models/korean.model" -O "./korean.model"
fi
popd

pushd "./bench/litsea-chinese-bench"
if [ ! -f "./chinese.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.16.0/models/chinese.model" -O "./chinese.model"
fi
popd

pushd "./bench/litsea-japanese-two-stage-bench"
if [ ! -f "./japanese_pos.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.16.0/models/japanese_pos.model" -O "./japanese_pos.model"
fi
popd

pushd "./bench/litsea-korean-two-stage-bench"
if [ ! -f "./korean_pos.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.16.0/models/korean_pos.model" -O "./korean_pos.model"
fi
popd

pushd "./bench/litsea-chinese-two-stage-bench"
if [ ! -f "./chinese_pos.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.16.0/models/chinese_pos.model" -O "./chinese_pos.model"
fi
popd

pushd "./bench/litsea-english-bench"
if [ ! -f "./english.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.16.0/models/english.model" -O "./english.model"
fi
popd

pushd "./bench/litsea-english-two-stage-bench"
if [ ! -f "./english_pos.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.16.0/models/english_pos.model" -O "./english_pos.model"
fi
popd

pushd "./bench/lindera-ipadic-bench"
if [ ! -d "./lindera-ipadic" ]; then
    wget "https://github.com/lindera/lindera/releases/download/v7.0.0/lindera-ipadic-7.0.0.zip" -O "./lindera-ipadic-7.0.0.zip"
    unzip "./lindera-ipadic-7.0.0.zip"
fi
popd

pushd "./bench/lindera-unidic-bench"
if [ ! -d "./lindera-unidic" ]; then
    wget "https://github.com/lindera/lindera/releases/download/v7.0.0/lindera-unidic-7.0.0.zip" -O "./lindera-unidic-7.0.0.zip"
    unzip "./lindera-unidic-7.0.0.zip"
fi
popd

pushd "./bench/lindera-sudachidict-bench"
if [ ! -d "./lindera-sudachidict" ]; then
    wget "https://github.com/lindera/lindera/releases/download/v7.0.0/lindera-sudachidict-7.0.0.zip" -O "./lindera-sudachidict-7.0.0.zip"
    unzip "./lindera-sudachidict-7.0.0.zip"
fi
popd

pushd "./bench/lindera-unidic-cwj-bench"
if [ ! -d "./lindera-unidic-cwj" ]; then
    wget "https://github.com/lindera/lindera/releases/download/v7.0.0/lindera-unidic-cwj-7.0.0.zip" -O "./lindera-unidic-cwj-7.0.0.zip"
    unzip "./lindera-unidic-cwj-7.0.0.zip"
fi
popd

pushd "./bench/lindera-unidic-csj-bench"
if [ ! -d "./lindera-unidic-csj" ]; then
    wget "https://github.com/lindera/lindera/releases/download/v7.0.0/lindera-unidic-csj-7.0.0.zip" -O "./lindera-unidic-csj-7.0.0.zip"
    unzip "./lindera-unidic-csj-7.0.0.zip"
fi
popd

pushd "./bench/lindera-cc-cedict-bench"
if [ ! -d "./lindera-cc-cedict" ]; then
    wget "https://github.com/lindera/lindera/releases/download/v7.0.0/lindera-cc-cedict-7.0.0.zip" -O "./lindera-cc-cedict-7.0.0.zip"
    unzip "./lindera-cc-cedict-7.0.0.zip"
fi
popd

pushd "./bench/lindera-jieba-bench"
if [ ! -d "./lindera-jieba" ]; then
    wget "https://github.com/lindera/lindera/releases/download/v7.0.0/lindera-jieba-7.0.0.zip" -O "./lindera-jieba-7.0.0.zip"
    unzip "./lindera-jieba-7.0.0.zip"
fi
popd

pushd "./bench/lindera-ko-dic-bench"
if [ ! -d "./lindera-ko-dic" ]; then
    wget "https://github.com/lindera/lindera/releases/download/v7.0.0/lindera-ko-dic-7.0.0.zip" -O "./lindera-ko-dic-7.0.0.zip"
    unzip "./lindera-ko-dic-7.0.0.zip"
fi
popd

pushd "./bench/vibrato-bench"
if [ ! -d "ipadic-mecab-2_7_0" ]; then
    wget https://github.com/daac-tools/vibrato/releases/download/v0.5.0/ipadic-mecab-2_7_0.tar.xz
    tar -xf ipadic-mecab-2_7_0.tar.xz
fi
if [ ! -d "unidic-cwj-3_1_1" ]; then
    wget https://github.com/daac-tools/vibrato/releases/download/v0.5.0/unidic-cwj-3_1_1.tar.xz
    tar -xf unidic-cwj-3_1_1.tar.xz
fi
if [ ! -d "unidic-cwj-3_1_1+compact-dual" ]; then
    wget https://github.com/daac-tools/vibrato/releases/download/v0.5.0/unidic-cwj-3_1_1+compact-dual.tar.xz
    tar -xf unidic-cwj-3_1_1+compact-dual.tar.xz
fi
popd
