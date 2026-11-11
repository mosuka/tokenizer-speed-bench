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
macOS. On macOS, install Rust, a JDK and the Xcode Command Line Tools, plus the
following tools from Homebrew, before running the commands above. On Windows,
run the scripts in WSL.

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

Measured 2026-11-11 on the following environment.

* Machine: MacBook Air, Apple M4 (10 cores)
* Memory: 24GiB
* OS: macOS 27.2
* Toolchains: rustc 1.99.0, OpenJDK 25.0.1, Apache Maven 3.10.0,
  Apple clang 21.0.0

The results up to 2026-09-29 were measured on another machine (Intel Core
i7-1185G7, Ubuntu 24.04) with older versions, so they are not comparable with
these.

Each tokenizer segmented its corpus 100 times (after 1 warm-up iteration,
excluded from the statistics). Speed is in characters per second; higher is
better. Std dev is the population standard deviation across the 100
iterations.

`litsea (*, two-stage)` performs segmentation and POS tagging together from
a single model file, via `Segmenter::with_two_stage_learner`; the other litsea
rows only segment. `lindera` loads its dictionaries from the pre-built archives
lindera publishes per release (e.g. `lindera-ipadic-6.2.0.zip`) rather than the
`embed-*` cargo features, so its rows also cover the `cc-cedict` (Chinese),
`jieba` (Chinese), and `ko-dic` (Korean) dictionaries in addition to `ipadic`
and `unidic`. Since lindera 6.1.0, ko-dic applies mecab-ko's left-space
penalty by default, and the `ko-dic` row uses that default.

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
each tokenizer actually opens at runtime, not its runtime memory usage. macOS
has no `strace`, so the opened files were logged by an `open()` interposer
loaded with `DYLD_INSERT_LIBRARIES`; kytea reads its model through the C++
standard library, whose opens the interposer does not see, so its size is that
of the model file given with `-model`. The column excludes non-runtime data
some distributions bundle alongside the dictionary (e.g. the raw CSV lexicon
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
with `/usr/bin/time -l` around each iteration; it therefore includes
dictionary loading, not just the segmentation loop that Speed measures. Every
engine is measured this way, including the two Java ones, which `run_all.sh`
launches directly with `java -cp` rather than through `mvn exec:java` so that
Maven's own footprint is not counted against them.

### Japanese (`wagahaiwa_nekodearu.txt`, 372,573 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| vaporetto | 0.7.0 | kytea jp-0.4.7-5.mod | 80.6 MB | 37,111,410 | 1,524,907 | 188.4 MB |
| litsea (japanese) | 0.16.0 | japanese.model | 1.1 MB | 18,359,094 | 347,663 | 14.9 MB |
| vibrato | 0.5.3 | ipadic-mecab-2.7.0 | 45.6 MB | 9,631,719 | 334,599 | 80.5 MB |
| mecab | thirdparty submodule | ipadic 2.7.0 | 50.5 MB | 9,403,685 | 921,828 | 31.9 MB |
| litsea (japanese, two-stage) | 0.16.0 | japanese_pos.model | 5.4 MB | 9,178,386 | 509,463 | 58.0 MB |
| lindera | 6.2.0 | ipadic | 45.3 MB | 8,625,286 | 572,397 | 18.7 MB |
| lindera | 6.2.0 | unidic | 189.9 MB | 6,136,242 | 605,597 | 53.2 MB |
| alyze (kuromoji) | 0.2.0 | ipadic (embedded) | 12.5 MB | 5,747,868 | 144,808 | 19.5 MB |
| vibrato | 0.5.3 | unidic-cwj-3.1.1 | 684.2 MB | 5,212,278 | 518,688 | 742.7 MB |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 691.0 MB | 4,125,996 | 455,675 | 245.1 MB |
| rust-tinysegmenter | 0.1.1 | - | - | 3,597,208 | 69,880 | 5.1 MB |
| mecab | thirdparty submodule | unidic-cwj-202512 | 1,252.8 MB | 2,734,657 | 290,049 | 356.7 MB |
| kuromoji | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 31.9 MB | 2,729,299 | 184,974 | 253.4 MB |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 122.3 MB | 2,671,859 | 164,701 | 526.7 MB |
| sudachi.rs | git tag `v0.7.0` | sudachi-dictionary-20261015-core | 192.9 MB | 2,297,939 | 105,658 | 162.4 MB |
| vibrato | 0.5.3 | unidic-cwj-3.1.1+compact-dual | 286.4 MB | 2,004,000 | 103,802 | 351.1 MB |
| sudachi | 0.8.2 | sudachi-dictionary-20261015-core | 192.9 MB | 917,756 | 63,106 | 395.4 MB |

### Korean (`mujeong.txt`, 320,850 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | 0.16.0 | korean.model | 0.1 MB | 27,752,303 | 553,816 | 5.2 MB |
| litsea (korean, two-stage) | 0.16.0 | korean_pos.model | 3.9 MB | 8,121,009 | 247,887 | 42.5 MB |
| lindera | 6.2.0 | ko-dic | 81.6 MB | 4,935,683 | 143,525 | 80.9 MB |
| alyze (nori) | 0.2.0 | mecab-ko-dic (embedded) | 43.2 MB | 3,369,468 | 137,082 | 45.0 MB |

### Chinese (`rulin_waishi.txt`, 328,153 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| lindera | 6.2.0 | cc-cedict | 22.1 MB | 18,466,410 | 1,194,313 | 10.3 MB |
| litsea (chinese) | 0.16.0 | chinese.model | 1.9 MB | 17,476,213 | 695,845 | 23.6 MB |
| lindera | 6.2.0 | jieba | 49.0 MB | 14,480,349 | 1,222,270 | 22.9 MB |
| alyze (smartcn) | 0.2.0 | smartcn (embedded) | 4.5 MB | 6,978,738 | 209,246 | 21.7 MB |
| litsea (chinese, two-stage) | 0.16.0 | chinese_pos.model | 8.0 MB | 6,912,335 | 225,153 | 72.5 MB |

### English (`pride_and_prejudice.txt`, 677,531 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| alyze (UAX #29) | 0.2.0 | - | - | 385,941,358 | 20,237,273 | 3.0 MB |
| litsea (english) | 0.16.0 | english.model | 0.1 MB | 36,559,299 | 1,577,460 | 5.9 MB |
| litsea (english, two-stage) | 0.16.0 | english_pos.model | 2.9 MB | 12,540,157 | 355,949 | 30.7 MB |

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
