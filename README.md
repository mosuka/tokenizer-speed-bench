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

### Japanese (`wagahaiwa_nekodearu.txt`, 372,573 characters)

| Tokenizer | Version | Dictionary / Model | Speed [chars/sec] | Std dev |
| --- | --- | --- | ---: | ---: |
| vaporetto | 0.6.5 | kytea jp-0.4.7-5.mod | 12,227,567 | 1,452,004 |
| litsea (japanese) | 0.11.0 | japanese.model | 10,001,822 | 1,383,247 |
| vibrato | 0.5.2 | ipadic-mecab-2.7.0 | 5,016,972 | 684,970 |
| litsea (japanese, two-stage) | 0.11.0 | japanese_two_stage.model | 4,645,669 | 594,039 |
| lindera | 5.2.0 | ipadic | 3,860,516 | 556,228 |
| mecab | thirdparty submodule | ipadic 2.7.0 | 3,147,088 | 351,059 |
| lindera | 5.2.0 | unidic | 2,795,718 | 393,652 |
| vibrato | 0.5.2 | unidic-cwj-3.1.1 | 2,680,070 | 297,335 |
| litsea (japanese, POS) | 0.11.0 | japanese_pos.model | 1,593,400 | 198,189 |
| rust-tinysegmenter | 0.1.1 | - | 1,511,267 | 180,117 |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 1,351,072 | 166,630 |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 1,247,304 | 124,965 |
| sudachi.rs | git rev `90fd606` | sudachi-dictionary-20210802-core | 1,139,695 | 162,292 |
| kuromoji | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 1,048,616 | 180,883 |
| vibrato | 0.5.2 | unidic-cwj-3.1.1+compact-dual | 846,818 | 97,223 |
| sudachi | 0.7.5 | sudachi-dictionary-20210802-core | 380,163 | 65,002 |

### Korean (`mujeong.txt`, 320,850 characters)

| Tokenizer | Version | Dictionary / Model | Speed [chars/sec] | Std dev |
| --- | --- | --- | ---: | ---: |
| litsea (korean) | 0.11.0 | korean.model | 11,936,090 | 1,665,610 |
| litsea (korean, two-stage) | 0.11.0 | korean_two_stage.model | 4,749,496 | 653,981 |
| litsea (korean, POS) | 0.11.0 | korean_pos.model | 2,409,842 | 358,190 |
| lindera | 5.2.0 | ko-dic | 1,960,057 | 270,483 |

### Chinese (`rulin_waishi.txt`, 328,153 characters)

| Tokenizer | Version | Dictionary / Model | Speed [chars/sec] | Std dev |
| --- | --- | --- | ---: | ---: |
| litsea (chinese) | 0.11.0 | chinese.model | 9,439,464 | 1,333,277 |
| lindera | 5.2.0 | cc-cedict | 8,110,959 | 1,223,136 |
| lindera | 5.2.0 | jieba | 6,742,608 | 947,039 |
| litsea (chinese, two-stage) | 0.11.0 | chinese_two_stage.model | 3,500,228 | 514,461 |
| litsea (chinese, POS) | 0.11.0 | chinese_pos.model | 1,563,991 | 201,424 |

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
