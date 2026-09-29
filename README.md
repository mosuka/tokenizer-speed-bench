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

### Measurement

To measure the speed of each tokenizer, run the following commands.
If you stop `./run_all.sh` in the middle, `./stats.py` will calculate
statistics from available results.

```sh
% ./run_all.sh | tee ./results
% ./stats.py < ./results
```

## Results

Measured 2026-09-29 on the following environment.

* CPU: Intel Core i7-1185G7 (4 cores / 8 threads, up to 4.8GHz)
* Memory: 32GiB
* OS: Ubuntu 24.04.5 LTS, Linux 6.8.0-142-generic
* Toolchains: rustc 1.98.0, OpenJDK 21.0.12.1, Apache Maven 3.8.7, g++ 13.3.0

Each tokenizer segmented its corpus 100 times (after 1 warm-up iteration,
excluded from the statistics). Speed is in characters per second; higher is
better. Std dev is the population standard deviation across the 100
iterations.

litsea 0.13.0 removed the joint POS architecture that the earlier
`litsea (*, POS)` rows measured, so those rows are gone. Two-stage is now
litsea's only segmentation + POS pipeline, and its bundled models were
renamed from `*_two_stage.model` to `*_pos.model`; the Japanese and Chinese
files are byte-identical to the 0.12.0 ones. `litsea (*, two-stage)`
performs segmentation and POS tagging together from a single model file,
via `Segmenter::with_two_stage_learner`. `korean_pos.model` was retrained
in 0.13.0 on a corpus that keeps the original spacing, so the
`litsea (korean, two-stage)` row is not directly comparable to the 0.12.0
run (2026-08-20). The segmentation models (`japanese.model`, `korean.model`,
`chinese.model`) are unchanged from 0.12.0. The English table, added in the
2026-09-28 run, measures only litsea's two English models, added in 0.13.0, on
`pride_and_prejudice.txt`, the corpus litsea's own benchmark uses for
English; no other tokenizer is measured on English here. `lindera` loads
its dictionaries from
the pre-built archives lindera publishes per release (e.g.
`lindera-ipadic-5.3.0.zip`) rather than the `embed-*` cargo features, so
its rows also cover the `cc-cedict` (Chinese), `jieba` (Chinese), and
`ko-dic` (Korean) dictionaries in addition to `ipadic` and `unidic`.

`vibrato` is built with a plain `cargo build --release`, like the other Rust
tokenizers. The previous results (2026-09-28) used a build with
`-C target-feature=+avx2`, which makes the `unidic-cwj-3.1.1+compact-dual`
connector use AVX2 gather instructions (`vpgatherdd`). On this machine that
build measured 439,712 chars/sec for that row, about half of this run's
figure, and profiling attributed most of its segmentation time to the
gather instructions. This CPU has the Gather Data Sampling microcode mitigation
enabled, which Intel says slows gather-heavy code, but how much of the gap
it causes was not measured. The August 2026 results also used a plain build.

Model Size is the on-disk size of the dictionary/model file(s) each
tokenizer actually opens at runtime (verified with `strace`), not its
runtime memory usage: it excludes non-runtime data some distributions
bundle alongside the dictionary (e.g. the raw CSV lexicon source,
evaluation sets, license files, and the compile/training-only `model.bin`
and `*.def` sources shipped in the MeCab dictionary directories besides the
compiled `sys.dic`/`matrix.bin`/`char.bin`/`unk.dic` the tagger itself
opens; kuromoji's dictionary is measured from its extracted `.bin` files
rather than its compressed `.jar`; vibrato's `system.dic.zst` is measured
decompressed, matching what it actually holds in memory). Peak Memory is
the maximum resident set size (RSS) of the whole benchmark process,
measured with `/usr/bin/time -v`
around each iteration; it therefore includes dictionary loading, not just
the segmentation loop that Speed measures. Every engine is measured this
way, including the two Java ones, which `run_all.sh` launches directly with
`java -cp` rather than through `mvn exec:java` so that Maven's own
footprint is not counted against them.

### Japanese (`wagahaiwa_nekodearu.txt`, 372,573 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| vaporetto | 0.6.5 | kytea jp-0.4.7-5.mod | 67.9 MB | 13,833,194 | 748,702 | 177.5 MB |
| litsea (japanese) | 0.14.3 | japanese.model | 1.1 MB | 10,076,216 | 509,951 | 12.0 MB |
| vibrato | 0.5.2 | ipadic-mecab-2.7.0 | 45.6 MB | 5,573,064 | 413,150 | 68.9 MB |
| litsea (japanese, two-stage) | 0.14.3 | japanese_pos.model | 5.4 MB | 4,978,287 | 337,272 | 45.0 MB |
| lindera | 5.3.0 | ipadic | 45.3 MB | 4,028,073 | 390,383 | 17.8 MB |
| mecab | thirdparty submodule | ipadic 2.7.0 | 50.5 MB | 3,433,390 | 167,856 | 33.1 MB |
| vibrato | 0.5.2 | unidic-cwj-3.1.1 | 684.2 MB | 3,012,259 | 177,514 | 724.0 MB |
| lindera | 5.3.0 | unidic | 190.1 MB | 2,924,434 | 251,189 | 63.1 MB |
| rust-tinysegmenter | 0.1.1 | - | - | 1,595,601 | 75,519 | 3.7 MB |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 122.3 MB | 1,542,198 | 85,786 | 736.8 MB |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 691.0 MB | 1,390,977 | 92,277 | 350.7 MB |
| sudachi.rs | git rev `90fd606` | sudachi-dictionary-20210802-core | 205.1 MB | 1,265,510 | 95,766 | 111.8 MB |
| kuromoji | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 31.9 MB | 1,063,970 | 107,672 | 353.2 MB |
| vibrato | 0.5.2 | unidic-cwj-3.1.1+compact-dual | 286.4 MB | 963,707 | 51,169 | 326.2 MB |
| sudachi | 0.7.5 | sudachi-dictionary-20210802-core | 205.1 MB | 382,263 | 43,875 | 531.2 MB |

### Korean (`mujeong.txt`, 320,850 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | 0.14.3 | korean.model | 0.1 MB | 15,425,382 | 705,818 | 4.1 MB |
| litsea (korean, two-stage) | 0.14.3 | korean_pos.model | 3.9 MB | 4,808,836 | 295,756 | 32.3 MB |
| lindera | 5.3.0 | ko-dic | 81.6 MB | 2,226,304 | 136,206 | 42.3 MB |

### Chinese (`rulin_waishi.txt`, 328,153 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (chinese) | 0.14.3 | chinese.model | 1.9 MB | 9,475,465 | 704,071 | 19.2 MB |
| lindera | 5.3.0 | cc-cedict | 22.1 MB | 8,603,073 | 687,734 | 9.9 MB |
| lindera | 5.3.0 | jieba | 48.9 MB | 7,039,302 | 537,167 | 22.4 MB |
| litsea (chinese, two-stage) | 0.14.3 | chinese_pos.model | 8.0 MB | 3,829,770 | 310,391 | 56.1 MB |

### English (`pride_and_prejudice.txt`, 677,531 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (english) | 0.14.3 | english.model | 0.1 MB | 19,428,307 | 1,099,160 | 4.4 MB |
| litsea (english, two-stage) | 0.14.3 | english_pos.model | 2.9 MB | 7,187,453 | 469,541 | 23.7 MB |

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
