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

Measured 2026-08-14 on the following environment.

* CPU: Intel Core i7-1185G7 (4 cores / 8 threads, up to 4.8GHz)
* Memory: 32GiB
* OS: Ubuntu 24.04.4 LTS, Linux 6.8.0-137-generic
* Toolchains: rustc 1.97.1, OpenJDK 21.0.11, Apache Maven 3.8.7, g++ 13.3.0

Each tokenizer segmented its corpus 100 times (after 1 warm-up iteration,
excluded from the statistics). Speed is in characters per second; higher is
better. Std dev is the sample standard deviation across the 100 iterations.

### Japanese (`wagahaiwa_nekodearu.txt`, 372,573 characters)

| Tokenizer | Version | Dictionary / Model | Speed [chars/sec] | Std dev |
| --- | --- | --- | ---: | ---: |
| vaporetto | 0.6.5 | kytea jp-0.4.7-5.mod | 12,744,850 | 1,053,181 |
| litsea (japanese) | 0.10.0 | japanese.model | 10,814,868 | 844,266 |
| vibrato | 0.5.2 | ipadic-mecab-2.7.0 | 5,279,304 | 433,507 |
| lindera | 5.2.0 | embed-ipadic | 4,044,870 | 480,966 |
| mecab | thirdparty submodule | ipadic 2.7.0 | 3,275,520 | 303,792 |
| lindera | 5.2.0 | embed-unidic | 2,918,180 | 286,369 |
| vibrato | 0.5.2 | unidic-cwj-3.1.1 | 2,751,371 | 274,206 |
| litsea (japanese, POS) | 0.10.0 | japanese_pos.model | 1,709,476 | 121,261 |
| rust-tinysegmenter | 0.1.1 | - | 1,569,876 | 123,595 |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 1,423,593 | 132,231 |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 1,325,753 | 107,817 |
| sudachi.rs | git rev `90fd606` | sudachi-dictionary-20210802-core | 1,211,248 | 111,892 |
| kuromoji | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 1,088,987 | 150,468 |
| vibrato | 0.5.2 | unidic-cwj-3.1.1+compact-dual | 894,248 | 84,162 |
| sudachi | 0.7.5 | sudachi-dictionary-20210802-core | 390,541 | 55,030 |

### Korean (`mujeong.txt`, 320,850 characters)

| Tokenizer | Version | Dictionary / Model | Speed [chars/sec] | Std dev |
| --- | --- | --- | ---: | ---: |
| litsea (korean) | 0.10.0 | korean.model | 12,683,492 | 1,078,995 |
| litsea (korean, POS) | 0.10.0 | korean_pos.model | 2,620,156 | 203,035 |

### Chinese (`rulin_waishi.txt`, 328,153 characters)

| Tokenizer | Version | Dictionary / Model | Speed [chars/sec] | Std dev |
| --- | --- | --- | ---: | ---: |
| litsea (chinese) | 0.10.0 | chinese.model | 10,927,062 | 953,870 |
| litsea (chinese, POS) | 0.10.0 | chinese_pos.model | 1,667,362 | 119,967 |

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
