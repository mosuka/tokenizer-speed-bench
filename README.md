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

The scripts run on Linux and on macOS; the results below are measured on
Linux. Install Rust and the following packages before running the commands
above. On Ubuntu, `libtool-bin` provides the `libtool` command that
`./compile_all.sh` checks for, and `time` provides the `/usr/bin/time` that
`./run_all.sh` uses to measure peak memory.

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

Measured 2026-11-22 on the following environment.

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
`jieba` (Chinese), and `ko-dic` (Korean) dictionaries in addition to `ipadic`
and `unidic`. Since lindera 6.1.0, ko-dic applies mecab-ko's left-space
penalty by default, and the `ko-dic` row uses that default. lindera 7.0.0
segments closer to MeCab than 6.2.0 did: it skips whitespace in the lattice,
carries the context across `、` and `。` within a line, creates unknown words
as MeCab does, and breaks unknown words at `・`. Its CC-CEDICT and Jieba
dictionaries are also built from updated sources. On these corpora, the
token counts change from 6.2.0 by +441 (ipadic), +166 (unidic), -6
(cc-cedict), +13,958 (jieba) and -257 (ko-dic).

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
| vaporetto | 0.7.0 | kytea jp-0.4.7-5.mod | 80.6 MB | 24,529,346 | 1,325,511 | 188.5 MB |
| litsea (japanese) | 0.16.0 | japanese.model | 1.1 MB | 16,231,000 | 978,470 | 11.9 MB |
| litsea (japanese, two-stage) | 0.16.0 | japanese_pos.model | 5.4 MB | 7,879,683 | 422,145 | 44.7 MB |
| vibrato | 0.5.3 | ipadic-mecab-2.7.0 | 45.6 MB | 7,396,521 | 376,945 | 68.7 MB |
| lindera | 7.0.0 | ipadic | 45.3 MB | 6,491,705 | 384,348 | 18.3 MB |
| mecab | thirdparty submodule | ipadic 2.7.0 | 50.5 MB | 6,260,699 | 403,827 | 33.7 MB |
| lindera | 7.0.0 | unidic | 189.9 MB | 4,527,248 | 272,086 | 90.9 MB |
| alyze (kuromoji) | 0.2.0 | ipadic (embedded) | 12.5 MB | 4,418,573 | 237,108 | 17.9 MB |
| vibrato | 0.5.3 | unidic-cwj-3.1.1 | 684.2 MB | 3,536,769 | 279,099 | 723.3 MB |
| rust-tinysegmenter | 0.1.1 | - | - | 2,700,535 | 97,215 | 3.7 MB |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 122.3 MB | 2,433,187 | 140,828 | 736.3 MB |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 691.0 MB | 2,246,609 | 169,726 | 371.4 MB |
| kuromoji | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 31.9 MB | 2,128,035 | 93,479 | 340.8 MB |
| sudachi.rs | git tag `v0.7.0` | sudachi-dictionary-20261015-core | 192.9 MB | 1,681,922 | 110,772 | 175.8 MB |
| vibrato | 0.5.3 | unidic-cwj-3.1.1+compact-dual | 286.4 MB | 1,474,615 | 75,764 | 325.7 MB |
| mecab | thirdparty submodule | unidic-cwj-202512 | 1,252.8 MB | 1,434,051 | 95,986 | 484.9 MB |
| sudachi | 0.8.2 | sudachi-dictionary-20261015-core | 192.9 MB | 756,611 | 32,729 | 567.4 MB |

### Korean (`mujeong.txt`, 320,850 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | 0.16.0 | korean.model | 0.1 MB | 23,229,540 | 1,495,830 | 4.1 MB |
| litsea (korean, two-stage) | 0.16.0 | korean_pos.model | 3.9 MB | 7,326,074 | 435,103 | 32.2 MB |
| lindera | 7.0.0 | ko-dic | 81.6 MB | 3,483,359 | 135,335 | 83.6 MB |
| alyze (nori) | 0.2.0 | mecab-ko-dic (embedded) | 43.2 MB | 2,496,290 | 135,221 | 47.7 MB |

### Chinese (`rulin_waishi.txt`, 328,153 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (chinese) | 0.16.0 | chinese.model | 1.9 MB | 15,735,132 | 860,786 | 19.1 MB |
| lindera | 7.0.0 | cc-cedict | 22.1 MB | 13,922,220 | 1,100,910 | 9.7 MB |
| lindera | 7.0.0 | jieba | 49.0 MB | 10,144,422 | 776,767 | 22.3 MB |
| litsea (chinese, two-stage) | 0.16.0 | chinese_pos.model | 8.0 MB | 5,861,685 | 322,936 | 55.9 MB |
| alyze (smartcn) | 0.2.0 | smartcn (embedded) | 4.5 MB | 5,110,060 | 339,849 | 22.0 MB |

### English (`pride_and_prejudice.txt`, 677,531 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| alyze (UAX #29) | 0.2.0 | - | - | 298,534,085 | 30,991,909 | 3.0 MB |
| litsea (english) | 0.16.0 | english.model | 0.1 MB | 31,675,670 | 2,039,685 | 4.5 MB |
| litsea (english, two-stage) | 0.16.0 | english_pos.model | 2.9 MB | 11,684,650 | 505,312 | 23.6 MB |

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
