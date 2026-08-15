# Benchmarking of various tokenizers

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

Measured 2026-08-15 on the following environment.

* CPU: Intel Core i7-1185G7 (4 cores / 8 threads, up to 4.8GHz)
* Memory: 32GiB
* OS: Ubuntu 24.04.4 LTS, Linux 6.8.0-137-generic
* Toolchains: rustc 1.97.1, OpenJDK 21.0.11, Apache Maven 3.8.7, g++ 13.3.0

Each tokenizer segmented its corpus 100 times (after 1 warm-up iteration,
excluded from the statistics). Speed is in characters per second; higher is
better. Std dev is the sample standard deviation across the 100 iterations.

litsea 0.11.0 retrained its plain segmentation models (`japanese.model`,
`korean.model`, `chinese.model`) for better accuracy, which also changes how
many words they produce, so the `litsea (*)` rows below are not directly
comparable to a run made against litsea 0.10.0. `litsea (*, two-stage)` is a
new litsea 0.11.0 mode that performs segmentation and POS tagging together
from a single model file, via `Segmenter::with_two_stage_learner`. `lindera`
loads its dictionaries from the pre-built archives lindera publishes per
release (e.g. `lindera-ipadic-5.2.0.zip`) rather than the `embed-*` cargo
features, so its rows now also cover the `cc-cedict` (Chinese), `jieba`
(Chinese), and `ko-dic` (Korean) dictionaries in addition to `ipadic` and
`unidic`.

Model Size is the on-disk size of the dictionary/model file(s) each
tokenizer actually reads at runtime, not its runtime memory usage: it
excludes non-runtime data some distributions bundle alongside the
dictionary (e.g. the raw CSV lexicon source, evaluation sets, and license
files shipped in the UniDic archive besides the compiled `sys.dic`/
`matrix.bin`/etc. MeCab itself opens; kuromoji's dictionary is measured from
its extracted `.bin` files rather than its compressed `.jar`; vibrato's
`system.dic.zst` is measured decompressed, matching what its `Predictor`
actually holds in memory). Peak Memory is the maximum resident set size
(RSS) of the whole benchmark process, measured with `/usr/bin/time -v`
around each iteration; it therefore includes dictionary loading, not just
the segmentation loop that Speed measures. `kuromoji` and `sudachi` run via
`mvn exec:java`, in the same JVM process as Maven itself, so their Peak
Memory is dominated by Maven's own overhead rather than the library's
actual footprint and should not be compared directly against the other
rows.

### Japanese (`wagahaiwa_nekodearu.txt`, 372,573 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| vaporetto | 0.6.5 | kytea jp-0.4.7-5.mod | 67.9 MB | 12,478,243 | 1,139,576 | 177.5 MB |
| litsea (japanese) | 0.11.0 | japanese.model | 1.1 MB | 10,348,176 | 934,201 | 12.1 MB |
| vibrato | 0.5.2 | ipadic-mecab-2.7.0 | 45.6 MB | 5,138,285 | 509,648 | 68.9 MB |
| litsea (japanese, two-stage) | 0.11.0 | japanese_two_stage.model | 5.4 MB | 4,771,555 | 527,686 | 45.0 MB |
| lindera | 5.2.0 | ipadic | 55.2 MB | 3,913,948 | 531,651 | 36.8 MB |
| mecab | thirdparty submodule | ipadic 2.7.0 | 50.6 MB | 3,234,859 | 312,807 | 33.2 MB |
| lindera | 5.2.0 | unidic | 204.0 MB | 2,824,551 | 376,607 | 139.0 MB |
| vibrato | 0.5.2 | unidic-cwj-3.1.1 | 684.2 MB | 2,711,599 | 182,629 | 724.0 MB |
| litsea (japanese, POS) | 0.11.0 | japanese_pos.model | 10.5 MB | 1,668,639 | 148,377 | 45.7 MB |
| rust-tinysegmenter | 0.1.1 | - | - | 1,543,617 | 135,524 | 3.6 MB |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 122.3 MB | 1,396,260 | 122,506 | 736.8 MB |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 770.9 MB | 1,284,150 | 110,883 | 356.0 MB |
| sudachi.rs | git rev `90fd606` | sudachi-dictionary-20210802-core | 205.1 MB | 1,165,980 | 131,884 | 111.9 MB |
| kuromoji | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 31.9 MB | 1,059,015 | 157,818 | 446.1 MB[^jvm] |
| vibrato | 0.5.2 | unidic-cwj-3.1.1+compact-dual | 286.4 MB | 876,934 | 67,456 | 326.2 MB |
| sudachi | 0.7.5 | sudachi-dictionary-20210802-core | 205.1 MB | 381,014 | 63,323 | 572.4 MB[^jvm] |

### Korean (`mujeong.txt`, 320,850 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | 0.11.0 | korean.model | 0.1 MB | 12,458,926 | 1,127,294 | 4.5 MB |
| litsea (korean, two-stage) | 0.11.0 | korean_two_stage.model | 5.0 MB | 4,884,101 | 508,217 | 39.1 MB |
| litsea (korean, POS) | 0.11.0 | korean_pos.model | 8.5 MB | 2,534,067 | 255,360 | 40.3 MB |
| lindera | 5.2.0 | ko-dic | 109.5 MB | 2,004,777 | 240,719 | 104.5 MB |

### Chinese (`rulin_waishi.txt`, 328,153 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (chinese) | 0.11.0 | chinese.model | 1.9 MB | 9,714,994 | 912,925 | 19.2 MB |
| lindera | 5.2.0 | cc-cedict | 27.6 MB | 8,204,356 | 1,136,403 | 21.7 MB |
| lindera | 5.2.0 | jieba | 66.0 MB | 6,798,410 | 852,604 | 61.3 MB |
| litsea (chinese, two-stage) | 0.11.0 | chinese_two_stage.model | 8.0 MB | 3,597,369 | 376,460 | 56.1 MB |
| litsea (chinese, POS) | 0.11.0 | chinese_pos.model | 18.4 MB | 1,624,453 | 132,622 | 78.0 MB |

[^jvm]: Measured for the whole `mvn exec:java` process, which runs in the
same JVM as Maven itself; this figure is dominated by Maven's own overhead,
not kuromoji's/sudachi's actual memory footprint.

These numbers depend heavily on the measurement environment (CPU, memory
bandwidth, OS scheduler, JIT/JVM warm-up) and should only be used to compare
tokenizers measured together on the same run, not as absolute benchmarks.
Reproduce with `./run_all.sh | tee ./results` and `./stats.py < ./results`
as described above.

## Disclaimer

This software is developed by LegalForce, Inc.,
but not an officially supported LegalForce product.

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
