# Benchmarking of various tokenizers

English | [日本語](README_ja.md)

This repository contains benchmarking tools of various tokenizers.

## Overview

To perform benchmarking, you have to run the following two steps.

### Preparation

The following commands prepare resources (e.g. model data) and compile source codes.

```sh
% git submodule update --init
% ./download_resources.sh
% ./compile_all.sh
```

The scripts run on Linux and on macOS (the mecab-ko build has been checked
only on Linux); the results below are measured on Linux. Install Rust and the
following packages before running the commands above. On Ubuntu,
`libtool-bin` provides the `libtool` command that `./compile_all.sh` checks
for, and `time` provides the `/usr/bin/time` that `./run_all.sh` uses to
measure peak memory.

```sh
% sudo apt install build-essential patch autoconf automake \
    libtool libtool-bin default-jdk-headless maven \
    wget unzip xz-utils time
```

On macOS, install Rust, a JDK and the Xcode Command Line Tools, plus the
following tools from Homebrew. On Windows, run the scripts in WSL.

```sh
% brew install wget autoconf automake libtool maven
```

### Measurement

To measure the speed of each tokenizer, run the following commands.
If you stop `./run_all.sh` in the middle, `./stats.py` will calculate
statistics from available results.

```sh
% ./run_all.sh | tee ./results
% ./stats.py < ./results
```

`./run_all.sh` runs every tokenizer for 1 warm-up iteration and 100 measured
iterations. Set `ITERATIONS` to measure fewer iterations for a rough comparison.

```sh
% ITERATIONS=10 ./run_all.sh | tee ./results
```

## Results

Measured 2026-11-23 on the following environment.

* Machine: GMKtec EVO-X2, AMD Ryzen AI MAX+ 395 (16 cores, 32 threads)
* Memory: 126GiB
* OS: Ubuntu 26.04.1 LTS (Linux 7.0.0-43-generic), CPU frequency governor
  `performance`
* Toolchains: rustc 1.99.1, OpenJDK 25.0.5.1, Apache Maven 3.9.12,
  g++ 15.2.0

The results up to 2026-11-11 were measured on a MacBook Air (Apple M4,
macOS 27.2) with lindera 6.2.0, and those up to 2026-09-29 on another machine
(Intel Core i7-1185G7, Ubuntu 24.04) with older versions, so neither is
comparable with these.

Each tokenizer segmented its corpus 100 times (after 1 warm-up iteration,
excluded from the statistics). Speed is in characters per second; higher is
better. Std dev is the population standard deviation across the 100
iterations.

`litsea (*, two-stage)` performs segmentation and POS tagging together from
a single model file, via `Segmenter::with_two_stage_learner`; the other litsea
rows only segment. `lindera` loads its dictionaries from the pre-built archives
lindera publishes per release (e.g. `lindera-ipadic-7.0.0.zip`) rather than the
`embed-*` cargo features, so its rows also cover the `cc-cedict` (Chinese),
`jieba` (Chinese), and `ko-dic` (Korean) dictionaries in addition to `ipadic`,
`unidic`, `unidic-cwj`, `unidic-csj` and `sudachidict`. Since lindera 6.1.0,
ko-dic applies mecab-ko's left-space penalty by default, and the `ko-dic` row
uses that default. lindera 7.0.0 segments closer to MeCab than 6.2.0 did: it
skips whitespace in the lattice, carries the context across `、` and `。`
within a line, creates unknown words as MeCab does, and breaks unknown words
at `・`. Its CC-CEDICT and Jieba dictionaries are also built from updated
sources. On these corpora, the token counts change from 6.2.0 by +441
(ipadic), +166 (unidic), -6 (cc-cedict), +13,958 (jieba) and -257 (ko-dic).

lindera's Japanese dictionaries come from different sources. `unidic` is
UniDic 2.1.2. `unidic-cwj` and `unidic-csj` are UniDic 202512 for written
(CWJ) and spoken (CSJ) Japanese, built from NINJAL's full packages;
`unidic-cwj` is the same release as the `mecab` row `unidic-cwj-202512`, and
the two segment the corpus identically except on 4 of its 2,346 lines. The
corpus is written Japanese, which `unidic-csj` is not made for. `sudachidict`
is SudachiDict 20260723 with its small, core and notcore lexicons (the full
edition), so its version and vocabulary differ from those of the `sudachi` and
`sudachi.rs` rows. lindera reads Sudachi's character definitions but does not
run Sudachi's plugins, such as input normalization, the joining of katakana
and numerals, or the A/B/C split modes.

`mecab` and `mecab-ko` also read mecab-ko-dic 2.1.1-20180720, the release
lindera's `ko-dic` is built from. mecab-ko 0.996-ko-0.9.2 is MeCab modified
for Korean. mecab-ko-dic's `dicrc` sets `left-space-penalty-factor`, which
raises the connection cost of parts of speech such as particles when a space
precedes them, and only mecab-ko reads it. mecab-ko therefore segments the
corpus exactly as lindera's `ko-dic` does, while the original MeCab segments
329 of its 3,967 lines differently. `download_resources.sh` fetches mecab-ko's
release archive and checks its SHA-256, and `compile_all.sh` builds it and
compiles the dictionary once with mecab-ko's `mecab-dict-index`; the original
MeCab's `mecab-dict-index` writes the same files.

`mecab` has two UniDic rows: `unidic-cwj-3.1.1`, the same dictionary as the
`vibrato` UniDic rows (every pre-built UniDic cwj dictionary vibrato
distributes is 3.1.1), and `unidic-cwj-202512`, the latest UniDic release. `sudachi`
and `sudachi.rs` read the same SudachiDict v20261015 core dictionary in the V1
binary format, the only format Sudachi 0.8.2 and sudachi.rs 0.7.0 read;
sudachi.rs 0.7 also changed parts of its analysis to match the Java version.
`vibrato` is built with a plain `cargo build --release`, like the other Rust
tokenizers. The KyTea model `jp-0.4.7-5.mod`, used by `kytea` and `vaporetto`,
is no longer served at its original URL, so `download_resources.sh` fetches
the Wayback Machine's copy and checks its SHA-256.

`alyze` is turbopuffer's text analysis library. Its kuromoji, nori and smartcn
analyzers are ports of the Lucene analyzers Elasticsearch uses, and the alyze
rows call their tokenizers (`tokenize`), not the Elasticsearch filter chain
(`analyze`). kuromoji runs in `Mode::Normal` and nori with
`DecompoundMode::None`, so that, like the `lindera`, `mecab` and `vibrato`
rows, they do not decompound (alyze's defaults are `Mode::Search` and
`DecompoundMode::Discard`). Both keep the default
`discard_punctuation: true`; smartcn always emits punctuation tokens. The
alyze rows reuse their token buffer across lines, as alyze intends, while
lindera's `Segmenter::segment` allocates per call; on the other hand, alyze's
kuromoji and nori fill in the part of speech, reading and so on of every token,
while lindera reads token details lazily. `alyze (UAX #29)` is alyze's
rule-based word segmenter (a DFA, with no dictionary); it reports every span
between word boundaries, and the bench counts the word-like ones. On English it
is a baseline, not a like-for-like comparison with litsea's learned
segmenter.

Dictionary / Model Size is the on-disk size of the dictionary/model file(s)
each tokenizer actually opens at runtime, not its runtime memory usage; the
opened files were logged with `strace`. The column excludes small
configuration files (MeCab's `mecabrc` and `dicrc`, lindera's `metadata.json`
and the like) and non-runtime data some distributions bundle alongside the
dictionary (e.g. the raw CSV lexicon
source, evaluation sets, license files, and the compile/training-only
`model.bin` and `*.def` sources shipped in the MeCab dictionary directories
besides the compiled `sys.dic`/`matrix.bin`/`char.bin`/`unk.dic` the tagger
itself opens; kuromoji's dictionary is measured from its extracted `.bin`
files rather than its compressed `.jar`; vibrato's `system.dic.zst` is
measured decompressed, matching what it actually holds in memory). For the
tokenizers that embed their dictionary in the executable, it is the size of
the embedded data: vaporetto's predictor, which its build script converts from
the KyTea model, and alyze's dictionary files, which its build script
downloads from alyze's GitHub release and checks against a SHA-256 (the
archive without licenses and notices). 1 MB is 1,048,576 bytes. Peak Memory is
the maximum resident set size (RSS) of the whole benchmark process, measured
with GNU time (`/usr/bin/time -v`) around each iteration; it therefore includes
dictionary loading, not just the segmentation loop that Speed measures. Every
engine is measured this way, including the two Java ones, which `run_all.sh`
launches directly with `java -cp` rather than through `mvn exec:java` so that
Maven's own footprint is not counted against them.

### Japanese (`wagahaiwa_nekodearu.txt`, 372,573 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| vaporetto | 0.7.0 | kytea jp-0.4.7-5.mod | 80.6 MB | 24,762,547 | 1,185,744 | 188.6 MB |
| litsea (japanese) | 0.16.0 | japanese.model | 1.1 MB | 16,638,107 | 654,034 | 12.0 MB |
| litsea (japanese, two-stage) | 0.16.0 | japanese_pos.model | 5.4 MB | 8,193,895 | 337,115 | 44.9 MB |
| vibrato | 0.5.3 | ipadic-mecab-2.7.0 | 45.6 MB | 7,859,537 | 226,563 | 68.8 MB |
| lindera | 7.0.0 | ipadic | 45.3 MB | 6,781,742 | 329,904 | 18.3 MB |
| mecab | thirdparty submodule | ipadic 2.7.0 | 50.5 MB | 6,482,138 | 279,234 | 33.8 MB |
| lindera | 7.0.0 | unidic | 189.9 MB | 4,727,136 | 250,452 | 91.0 MB |
| alyze (kuromoji) | 0.2.0 | ipadic (embedded) | 12.5 MB | 4,567,718 | 178,696 | 18.0 MB |
| vibrato | 0.5.3 | unidic-cwj-3.1.1 | 684.2 MB | 4,022,159 | 197,504 | 723.7 MB |
| lindera | 7.0.0 | sudachidict | 564.9 MB | 3,833,069 | 201,526 | 155.1 MB |
| rust-tinysegmenter | 0.1.1 | - | - | 2,759,251 | 52,395 | 3.8 MB |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 122.3 MB | 2,598,992 | 71,566 | 736.5 MB |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 691.0 MB | 2,524,186 | 128,903 | 371.5 MB |
| lindera | 7.0.0 | unidic-cwj | 1,244.3 MB | 2,313,688 | 119,081 | 1,009.6 MB |
| lindera | 7.0.0 | unidic-csj | 1,264.6 MB | 2,290,937 | 119,151 | 1,029.9 MB |
| kuromoji | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 31.9 MB | 2,253,468 | 80,966 | 341.1 MB |
| sudachi.rs | git tag `v0.7.0` | sudachi-dictionary-20261015-core | 192.9 MB | 1,834,100 | 68,889 | 176.0 MB |
| mecab | thirdparty submodule | unidic-cwj-202512 | 1,252.8 MB | 1,605,914 | 84,358 | 485.2 MB |
| vibrato | 0.5.3 | unidic-cwj-3.1.1+compact-dual | 286.4 MB | 1,587,345 | 55,504 | 326.0 MB |
| sudachi | 0.8.2 | sudachi-dictionary-20261015-core | 192.9 MB | 805,371 | 32,109 | 566.1 MB |

### Korean (`mujeong.txt`, 320,850 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | 0.16.0 | korean.model | 0.1 MB | 24,146,228 | 943,141 | 4.2 MB |
| litsea (korean, two-stage) | 0.16.0 | korean_pos.model | 3.9 MB | 7,677,924 | 265,297 | 32.3 MB |
| mecab | thirdparty submodule | mecab-ko-dic 2.1.1-20180720 | 96.7 MB | 3,647,144 | 159,079 | 70.5 MB |
| lindera | 7.0.0 | ko-dic | 81.6 MB | 3,613,149 | 94,180 | 83.8 MB |
| alyze (nori) | 0.2.0 | mecab-ko-dic (embedded) | 43.2 MB | 2,626,843 | 108,301 | 47.7 MB |
| mecab-ko | 0.996-ko-0.9.2 | mecab-ko-dic 2.1.1-20180720 | 96.7 MB | 1,691,201 | 103,063 | 70.3 MB |

### Chinese (`rulin_waishi.txt`, 328,153 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (chinese) | 0.16.0 | chinese.model | 1.9 MB | 16,158,038 | 800,224 | 19.3 MB |
| lindera | 7.0.0 | cc-cedict | 22.1 MB | 14,779,048 | 845,826 | 9.8 MB |
| lindera | 7.0.0 | jieba | 49.0 MB | 10,652,010 | 694,348 | 22.3 MB |
| litsea (chinese, two-stage) | 0.16.0 | chinese_pos.model | 8.0 MB | 6,199,567 | 168,798 | 56.0 MB |
| alyze (smartcn) | 0.2.0 | smartcn (embedded) | 4.5 MB | 5,391,555 | 276,166 | 22.0 MB |

### English (`pride_and_prejudice.txt`, 677,531 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| alyze (UAX #29) | 0.2.0 | - | - | 315,490,421 | 23,713,663 | 3.0 MB |
| litsea (english) | 0.16.0 | english.model | 0.1 MB | 32,872,916 | 1,164,280 | 4.6 MB |
| litsea (english, two-stage) | 0.16.0 | english_pos.model | 2.9 MB | 12,062,422 | 300,157 | 23.7 MB |

These numbers depend heavily on the measurement environment (CPU, memory
bandwidth, OS scheduler, JIT/JVM warm-up) and should only be used to compare
tokenizers measured together on the same run, not as absolute benchmarks.
Reproduce with `./run_all.sh | tee ./results` and `./stats.py < ./results`
as described above.

## License

Licensed under either of

* Apache License, Version 2.0
  ([LICENSE-APACHE](LICENSE-APACHE) or <http://www.apache.org/licenses/LICENSE-2.0>)
* MIT license
  ([LICENSE-MIT](LICENSE-MIT) or <http://opensource.org/licenses/MIT>)

at your option.

For softwares under `thirdparty`, follow the license terms of each software.

## Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall be
dual licensed as above, without any additional terms or conditions.
