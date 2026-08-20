#!/bin/bash

set -eux

which wget
which gunzip
which unzip

pushd "./resources"

if [ ! -f "./jp-0.4.7-5.mod" ]; then
    wget "http://www.phontron.com/kytea/download/model/jp-0.4.7-5.mod.gz" -O "./jp-0.4.7-5.mod.gz"
    rm -f "./jp-f.4.7-5.mod"
    gunzip "./jp-0.4.7-5.mod.gz"
fi

if [ ! -d "./unidic-cwj-3.1.1" ]; then
    wget "https://ccd.ninjal.ac.jp/unidic_archive/cwj/3.1.1/unidic-cwj-3.1.1.zip" -O "./unidic-cwj-3.1.1.zip"
    rm -rf "./unidic-cwj-3.1.1"
    unzip "./unidic-cwj-3.1.1.zip"
fi

popd

pushd "./bench/sudachi-bench"
if [ ! -d "./sudachi-dictionary-20210802" ]; then
    wget "http://sudachi.s3-website-ap-northeast-1.amazonaws.com/sudachidict/sudachi-dictionary-20210802-core.zip" -O "./sudachi-dictionary-20210802-core.zip"
    rm -rf "./sudachi-dictionary-20210802"
    unzip "./sudachi-dictionary-20210802-core.zip"
fi
popd

pushd "./bench/litsea-japanese-bench"
if [ ! -f "./japanese.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.12.0/models/japanese.model" -O "./japanese.model"
fi
popd

pushd "./bench/litsea-japanese-pos-bench"
if [ ! -f "./japanese_pos.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.12.0/models/japanese_pos.model" -O "./japanese_pos.model"
fi
popd

pushd "./bench/litsea-korean-bench"
if [ ! -f "./korean.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.12.0/models/korean.model" -O "./korean.model"
fi
popd

pushd "./bench/litsea-korean-pos-bench"
if [ ! -f "./korean_pos.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.12.0/models/korean_pos.model" -O "./korean_pos.model"
fi
popd

pushd "./bench/litsea-chinese-bench"
if [ ! -f "./chinese.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.12.0/models/chinese.model" -O "./chinese.model"
fi
popd

pushd "./bench/litsea-chinese-pos-bench"
if [ ! -f "./chinese_pos.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.12.0/models/chinese_pos.model" -O "./chinese_pos.model"
fi
popd

pushd "./bench/litsea-japanese-two-stage-bench"
if [ ! -f "./japanese_two_stage.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.12.0/models/japanese_two_stage.model" -O "./japanese_two_stage.model"
fi
popd

pushd "./bench/litsea-korean-two-stage-bench"
if [ ! -f "./korean_two_stage.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.12.0/models/korean_two_stage.model" -O "./korean_two_stage.model"
fi
popd

pushd "./bench/litsea-chinese-two-stage-bench"
if [ ! -f "./chinese_two_stage.model" ]; then
    wget "https://raw.githubusercontent.com/mosuka/litsea/v0.12.0/models/chinese_two_stage.model" -O "./chinese_two_stage.model"
fi
popd

pushd "./bench/lindera-ipadic-bench"
if [ ! -d "./lindera-ipadic" ]; then
    wget "https://github.com/lindera/lindera/releases/download/v5.3.0/lindera-ipadic-5.3.0.zip" -O "./lindera-ipadic-5.3.0.zip"
    unzip "./lindera-ipadic-5.3.0.zip"
fi
popd

pushd "./bench/lindera-unidic-bench"
if [ ! -d "./lindera-unidic" ]; then
    wget "https://github.com/lindera/lindera/releases/download/v5.3.0/lindera-unidic-5.3.0.zip" -O "./lindera-unidic-5.3.0.zip"
    unzip "./lindera-unidic-5.3.0.zip"
fi
popd

pushd "./bench/lindera-cc-cedict-bench"
if [ ! -d "./lindera-cc-cedict" ]; then
    wget "https://github.com/lindera/lindera/releases/download/v5.3.0/lindera-cc-cedict-5.3.0.zip" -O "./lindera-cc-cedict-5.3.0.zip"
    unzip "./lindera-cc-cedict-5.3.0.zip"
fi
popd

pushd "./bench/lindera-jieba-bench"
if [ ! -d "./lindera-jieba" ]; then
    wget "https://github.com/lindera/lindera/releases/download/v5.3.0/lindera-jieba-5.3.0.zip" -O "./lindera-jieba-5.3.0.zip"
    unzip "./lindera-jieba-5.3.0.zip"
fi
popd

pushd "./bench/lindera-ko-dic-bench"
if [ ! -d "./lindera-ko-dic" ]; then
    wget "https://github.com/lindera/lindera/releases/download/v5.3.0/lindera-ko-dic-5.3.0.zip" -O "./lindera-ko-dic-5.3.0.zip"
    unzip "./lindera-ko-dic-5.3.0.zip"
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
