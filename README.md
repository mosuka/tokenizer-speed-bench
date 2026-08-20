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

Measured 2026-08-20 on the following environment.

* CPU: Intel Core i7-1185G7 (4 cores / 8 threads, up to 4.8GHz)
* Memory: 32GiB
* OS: Ubuntu 24.04.4 LTS, Linux 6.8.0-137-generic
* Toolchains: rustc 1.97.1, OpenJDK 21.0.11, Apache Maven 3.8.7, g++ 13.3.0

Each tokenizer segmented its corpus 100 times (after 1 warm-up iteration,
excluded from the statistics). Speed is in characters per second; higher is
better. Std dev is the population standard deviation across the 100
iterations.

litsea 0.12.0 adds a pointwise fast path to `segment()` that skips the
sequential scoring pass when a model has no tag-dependent feature weights,
and retrains `korean.model` tag-free to take advantage of it (the model
shrinks from about 110 KB to 86 KB at equivalent accuracy). The
`litsea (korean)` row is therefore faster than in the 0.11.0 run and,
because the retrained model segments slightly differently, not directly
comparable to it; the Japanese and Chinese models are unchanged from
0.11.0. `litsea (*, two-stage)` performs segmentation and POS tagging
together from a single model file, via
`Segmenter::with_two_stage_learner`. `lindera` loads its dictionaries from
the pre-built archives lindera publishes per release (e.g.
`lindera-ipadic-5.3.0.zip`) rather than the `embed-*` cargo features, so
its rows also cover the `cc-cedict` (Chinese), `jieba` (Chinese), and
`ko-dic` (Korean) dictionaries in addition to `ipadic` and `unidic`.

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
| vaporetto | 0.6.5 | kytea jp-0.4.7-5.mod | 67.9 MB | 13,324,632 | 785,624 | 177.5 MB |
| litsea (japanese) | 0.12.0 | japanese.model | 1.1 MB | 10,098,342 | 679,278 | 12.0 MB |
| vibrato | 0.5.2 | ipadic-mecab-2.7.0 | 45.6 MB | 5,452,045 | 383,445 | 68.9 MB |
| litsea (japanese, two-stage) | 0.12.0 | japanese_two_stage.model | 5.4 MB | 4,890,225 | 404,876 | 45.0 MB |
| lindera | 5.3.0 | ipadic | 45.3 MB | 4,122,713 | 388,174 | 17.9 MB |
| mecab | thirdparty submodule | ipadic 2.7.0 | 50.5 MB | 3,361,361 | 230,780 | 33.1 MB |
| lindera | 5.3.0 | unidic | 190.1 MB | 2,963,561 | 240,026 | 63.4 MB |
| vibrato | 0.5.2 | unidic-cwj-3.1.1 | 684.2 MB | 2,903,020 | 163,255 | 724.0 MB |
| litsea (japanese, POS) | 0.12.0 | japanese_pos.model | 10.5 MB | 1,767,635 | 140,326 | 45.7 MB |
| rust-tinysegmenter | 0.1.1 | - | - | 1,603,811 | 131,259 | 3.7 MB |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 122.3 MB | 1,480,213 | 94,576 | 736.8 MB |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 691.0 MB | 1,364,869 | 70,031 | 355.9 MB |
| sudachi.rs | git rev `90fd606` | sudachi-dictionary-20210802-core | 205.1 MB | 1,248,045 | 110,179 | 111.9 MB |
| kuromoji | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 31.9 MB | 1,107,191 | 116,145 | 353.0 MB |
| vibrato | 0.5.2 | unidic-cwj-3.1.1+compact-dual | 286.4 MB | 925,345 | 59,588 | 326.2 MB |
| sudachi | 0.7.5 | sudachi-dictionary-20210802-core | 205.1 MB | 403,012 | 52,672 | 532.8 MB |

### Korean (`mujeong.txt`, 320,850 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | 0.12.0 | korean.model | 0.1 MB | 15,904,203 | 1,086,016 | 4.1 MB |
| litsea (korean, two-stage) | 0.12.0 | korean_two_stage.model | 5.0 MB | 5,013,428 | 445,414 | 39.2 MB |
| litsea (korean, POS) | 0.12.0 | korean_pos.model | 8.5 MB | 2,682,372 | 194,675 | 40.3 MB |
| lindera | 5.3.0 | ko-dic | 81.6 MB | 2,223,001 | 137,361 | 42.4 MB |

### Chinese (`rulin_waishi.txt`, 328,153 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (chinese) | 0.12.0 | chinese.model | 1.9 MB | 9,593,189 | 724,380 | 19.2 MB |
| lindera | 5.3.0 | cc-cedict | 22.1 MB | 8,627,257 | 835,520 | 10.0 MB |
| lindera | 5.3.0 | jieba | 48.9 MB | 7,091,309 | 512,462 | 22.4 MB |
| litsea (chinese, two-stage) | 0.12.0 | chinese_two_stage.model | 8.0 MB | 3,705,770 | 320,162 | 56.2 MB |
| litsea (chinese, POS) | 0.12.0 | chinese_pos.model | 18.4 MB | 1,730,064 | 112,923 | 78.0 MB |

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
