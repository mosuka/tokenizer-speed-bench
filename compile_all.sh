#!/bin/bash

set -eux

which patch
which cargo
which autoreconf
which libtool
which make
which mvn

# Build thirdparty libraries

pushd "./thirdparty/mecab/mecab"
./configure --prefix=$(cd .. && pwd)/tmpusr --libdir=$(cd .. && pwd)/tmpusr/lib
make
make install
popd

pushd "./thirdparty/mecab/mecab-ipadic"
./configure --with-charset=utf8 --prefix=$(cd .. && pwd)/tmpusr --with-mecab-config=../mecab/mecab-config
make
make install
popd

pushd "./thirdparty/kytea"
# Homebrew installs GNU libtool's libtoolize as glibtoolize on macOS, and
# /usr/bin/libtool there is Apple's unrelated tool.
if [ "$(uname)" = "Darwin" ]; then
    which glibtoolize
    LIBTOOLIZE=glibtoolize autoreconf -i
else
    autoreconf -i
fi
./configure --prefix=$(pwd)/tmpusr --libdir=$(pwd)/tmpusr/lib
make
make install
popd

pushd "./thirdparty/mecab-ko"
./configure --prefix=$(pwd)/tmpusr --libdir=$(pwd)/tmpusr/lib
make
make install
popd

# Compile mecab-ko-dic in place with mecab-ko's mecab-dict-index. The release
# has no aclocal.m4, so after `./configure` its Makefile tries to regenerate
# the build system with automake 1.11 and fails; this runs the command of its
# Makefile directly instead. The mecab-dict-index of mecab-ko and of the
# original MeCab write the same files, and both mecab-ko-dic benches read them.
pushd "./resources/mecab-ko-dic-2.1.1-20180720"
../../thirdparty/mecab-ko/tmpusr/libexec/mecab/mecab-dict-index -d . -o . -f UTF-8 -t UTF-8
popd

# Build benches

pushd "./bench/vaporetto-bench"
cargo build --release
popd

pushd "./bench/kytea-bench"
LIBRARY_PATH=$(cd ../.. && pwd)/thirdparty/kytea/tmpusr/lib g++ -std=c++11 -O3 ./main.cc -I../../thirdparty/kytea/tmpusr/include -lkytea
popd

pushd "./bench/mecab-ipadic-2_7_0-bench"
LIBRARY_PATH=$(cd ../.. && pwd)/thirdparty/mecab/tmpusr/lib g++ -std=c++11 -O3 ./main.cc -I../../thirdparty/mecab/tmpusr/include -lmecab
popd

pushd "./bench/mecab-unidic-3_1_1-bench"
LIBRARY_PATH=$(cd ../.. && pwd)/thirdparty/mecab/tmpusr/lib g++ -std=c++11 -O3 ./main.cc -I../../thirdparty/mecab/tmpusr/include -lmecab
popd

pushd "./bench/mecab-unidic-202512-bench"
LIBRARY_PATH=$(cd ../.. && pwd)/thirdparty/mecab/tmpusr/lib g++ -std=c++11 -O3 ./main.cc -I../../thirdparty/mecab/tmpusr/include -lmecab
popd

pushd "./bench/mecab-ko-dic-2_1_1-bench"
LIBRARY_PATH=$(cd ../.. && pwd)/thirdparty/mecab/tmpusr/lib g++ -std=c++11 -O3 ./main.cc -I../../thirdparty/mecab/tmpusr/include -lmecab
popd

pushd "./bench/mecab-ko-ko-dic-2_1_1-bench"
LIBRARY_PATH=$(cd ../.. && pwd)/thirdparty/mecab-ko/tmpusr/lib g++ -std=c++11 -O3 ./main.cc -I../../thirdparty/mecab-ko/tmpusr/include -lmecab
popd

pushd "./bench/kuromoji-bench"
mvn compile
# Resolve the runtime classpath once here so run_all.sh can launch the JVM
# directly with `java -cp`, instead of going through `mvn exec:java`, which
# would run in the same JVM as Maven itself and inflate the measured RSS.
mvn dependency:build-classpath -Dmdep.outputFile=classpath.txt
popd

pushd "./bench/lindera-ipadic-bench"
cargo build --release
popd

pushd "./bench/lindera-unidic-bench"
cargo build --release
popd

pushd "./bench/lindera-sudachidict-bench"
cargo build --release
popd

pushd "./bench/lindera-unidic-cwj-bench"
cargo build --release
popd

pushd "./bench/lindera-unidic-csj-bench"
cargo build --release
popd

pushd "./bench/lindera-cc-cedict-bench"
cargo build --release
popd

pushd "./bench/lindera-jieba-bench"
cargo build --release
popd

pushd "./bench/lindera-ko-dic-bench"
cargo build --release
popd

pushd "./bench/sudachi-bench"
mvn compile
mvn dependency:build-classpath -Dmdep.outputFile=classpath.txt
popd

pushd "./bench/sudachirs-bench"
cargo build --release
popd

pushd "./bench/rust-tinysegmenter-bench"
cargo build --release
popd

pushd "./bench/litsea-japanese-bench"
cargo build --release
popd

pushd "./bench/litsea-korean-bench"
cargo build --release
popd

pushd "./bench/litsea-chinese-bench"
cargo build --release
popd

pushd "./bench/litsea-japanese-two-stage-bench"
cargo build --release
popd

pushd "./bench/litsea-korean-two-stage-bench"
cargo build --release
popd

pushd "./bench/litsea-chinese-two-stage-bench"
cargo build --release
popd

pushd "./bench/litsea-english-bench"
cargo build --release
popd

pushd "./bench/litsea-english-two-stage-bench"
cargo build --release
popd

pushd "./bench/vibrato-bench"
cargo build --release
popd

# alyze's build script downloads the dictionaries of the enabled features from
# its GitHub release, checks their SHA-256 and embeds them in the executable.
pushd "./bench/alyze-kuromoji-bench"
cargo build --release
popd

pushd "./bench/alyze-nori-bench"
cargo build --release
popd

pushd "./bench/alyze-smartcn-bench"
cargo build --release
popd

pushd "./bench/alyze-uax29-bench"
cargo build --release
popd
