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
measure peak memory. The Lucene benches need Java 21 or later.

```sh
% sudo apt install build-essential patch autoconf automake \
    libtool libtool-bin default-jdk-headless maven \
    wget unzip xz-utils time
```

On macOS, install Rust, a JDK (21 or later) and the Xcode Command Line Tools,
plus the following tools from Homebrew. On Windows, run the scripts in WSL.

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

To measure how each tokenizer segments (see
[Segmentation accuracy](#segmentation-accuracy)), run the following command.
It runs every tokenizer once on the corpora above and on the gold-standard
data that `./download_resources.sh` fetches, and prints the tables.

```sh
% ./segment_all.sh | tee ./accuracy
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
the two segment the corpus identically except on 4 of its 2,346 lines; on 2
of them they split only a run of hyphens differently, which the agreement
table leaves out with the other punctuation, so that it counts 2 lines. The
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

`kuromoji (Atilika)` is Atilika's Kuromoji
(`com.atilika.kuromoji:kuromoji-ipadic` 0.9.0) with the IPADIC its jar
bundles; the bench calls `new Tokenizer()`, and its tokens include
punctuation. `kuromoji (Lucene)` and `nori (Lucene)` are the Japanese and
Korean tokenizers of Apache Lucene 10.6.0 (`lucene-analysis-kuromoji` and
`lucene-analysis-nori`), whose jars bundle mecab-ipadic-2.7.0-20070801 and
mecab-ko-dic-2.1.1-20180720. They run with `JapaneseTokenizer.Mode.NORMAL`
and `KoreanTokenizer.DecompoundMode.NONE` instead of Lucene's defaults
(`SEARCH` and `DISCARD`), and discard punctuation: the options of the alyze
rows, with which Lucene and alyze segment both corpora identically. Each
bench reuses one tokenizer for every line, as Lucene intends.

Dictionary / Model Size is the on-disk size of the dictionary/model file(s)
each tokenizer actually opens at runtime, not its runtime memory usage; the
opened files were logged with `strace`. The column excludes small
configuration files (MeCab's `mecabrc` and `dicrc`, lindera's `metadata.json`
and the like) and non-runtime data some distributions bundle alongside the
dictionary (e.g. the raw CSV lexicon
source, evaluation sets, license files, and the compile/training-only
`model.bin` and `*.def` sources shipped in the MeCab dictionary directories
besides the compiled `sys.dic`/`matrix.bin`/`char.bin`/`unk.dic` the tagger
itself opens; the dictionaries in jars are measured from their extracted
entries rather than the compressed `.jar`, the `.bin` files for
`kuromoji (Atilika)` and the `.dat` files for the Lucene rows; vibrato's
`system.dic.zst` is
measured decompressed, matching what it actually holds in memory). For the
tokenizers that embed their dictionary in the executable, it is the size of
the embedded data: vaporetto's predictor, which its build script converts from
the KyTea model, and alyze's dictionary files, which its build script
downloads from alyze's GitHub release and checks against a SHA-256 (the
archive without licenses and notices). 1 MB is 1,048,576 bytes. Peak Memory is
the maximum resident set size (RSS) of the whole benchmark process, measured
with GNU time (`/usr/bin/time -v`) around each iteration; it therefore includes
dictionary loading, not just the segmentation loop that Speed measures. Every
engine is measured this way, including the four Java ones, which `run_all.sh`
launches directly with `java -cp` rather than through `mvn exec:java` so that
Maven's own footprint is not counted against them.

Peak Memory is the physical memory the process occupied, not the memory it
allocated, so it does not mean the same thing for every row. RSS counts the
pages of mapped files that the process touched: the tokenizers that read their
dictionary with `mmap` (lindera, for example) or embed it in the executable
(alyze and vaporetto) include the dictionary pages they read, which are page
cache that other processes can share and that the kernel can reclaim under
memory pressure. The Java rows include the JVM's own memory and a
garbage-collected heap whose size depends on the collector's settings and
behavior. Compare this column across rows with these differences in mind.

### Japanese (`wagahaiwa_nekodearu.txt`, 372,573 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| vaporetto | 0.7.0 | kytea jp-0.4.7-5.mod | 80.6 MB | 25,271,524 | 1,143,837 | 188.7 MB |
| litsea (japanese) | 0.16.0 | japanese.model | 1.1 MB | 16,606,245 | 718,540 | 12.0 MB |
| litsea (japanese, two-stage) | 0.16.0 | japanese_pos.model | 5.4 MB | 8,125,056 | 319,308 | 44.9 MB |
| vibrato | 0.5.3 | ipadic-mecab-2.7.0 | 45.6 MB | 7,845,596 | 257,892 | 68.8 MB |
| lindera | 7.0.0 | ipadic | 45.3 MB | 6,624,743 | 333,468 | 18.2 MB |
| mecab | thirdparty submodule | ipadic 2.7.0 | 50.5 MB | 6,494,042 | 323,648 | 33.7 MB |
| lindera | 7.0.0 | unidic | 189.9 MB | 4,663,269 | 246,854 | 90.9 MB |
| alyze (kuromoji) | 0.2.0 | ipadic (embedded) | 12.5 MB | 4,506,713 | 185,606 | 18.0 MB |
| vibrato | 0.5.3 | unidic-cwj-3.1.1 | 684.2 MB | 3,944,257 | 188,425 | 723.7 MB |
| lindera | 7.0.0 | sudachidict | 564.9 MB | 3,816,300 | 192,864 | 155.1 MB |
| rust-tinysegmenter | 0.1.1 | - | - | 2,727,841 | 76,541 | 3.8 MB |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 122.3 MB | 2,596,773 | 53,237 | 736.6 MB |
| kuromoji (Lucene) | 10.6.0 | ipadic (bundled) | 8.7 MB | 2,592,213 | 64,598 | 111.3 MB |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 691.0 MB | 2,496,750 | 115,473 | 371.6 MB |
| lindera | 7.0.0 | unidic-csj | 1,264.6 MB | 2,353,893 | 115,446 | 1,029.8 MB |
| lindera | 7.0.0 | unidic-cwj | 1,244.3 MB | 2,350,549 | 130,874 | 1,009.5 MB |
| kuromoji (Atilika) | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 31.9 MB | 2,263,056 | 64,141 | 341.5 MB |
| sudachi.rs | git tag `v0.7.0` | sudachi-dictionary-20261015-core | 192.9 MB | 1,802,163 | 69,095 | 175.9 MB |
| mecab | thirdparty submodule | unidic-cwj-202512 | 1,252.8 MB | 1,588,292 | 76,189 | 485.1 MB |
| vibrato | 0.5.3 | unidic-cwj-3.1.1+compact-dual | 286.4 MB | 1,578,634 | 59,189 | 326.0 MB |
| sudachi | 0.8.2 | sudachi-dictionary-20261015-core | 192.9 MB | 797,026 | 27,874 | 565.7 MB |

### Korean (`mujeong.txt`, 320,850 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | 0.16.0 | korean.model | 0.1 MB | 24,042,430 | 1,065,937 | 4.2 MB |
| litsea (korean, two-stage) | 0.16.0 | korean_pos.model | 3.9 MB | 7,626,334 | 307,392 | 32.3 MB |
| mecab | thirdparty submodule | mecab-ko-dic 2.1.1-20180720 | 96.7 MB | 3,608,106 | 192,029 | 70.4 MB |
| lindera | 7.0.0 | ko-dic | 81.6 MB | 3,589,310 | 95,548 | 83.7 MB |
| alyze (nori) | 0.2.0 | mecab-ko-dic (embedded) | 43.2 MB | 2,625,118 | 108,350 | 48.0 MB |
| mecab-ko | 0.996-ko-0.9.2 | mecab-ko-dic 2.1.1-20180720 | 96.7 MB | 1,675,894 | 98,272 | 70.3 MB |
| nori (Lucene) | 10.6.0 | mecab-ko-dic (bundled) | 23.9 MB | 1,342,826 | 43,246 | 158.0 MB |

### Chinese (`rulin_waishi.txt`, 328,153 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (chinese) | 0.16.0 | chinese.model | 1.9 MB | 15,976,908 | 749,540 | 19.2 MB |
| lindera | 7.0.0 | cc-cedict | 22.1 MB | 14,782,429 | 758,476 | 9.8 MB |
| lindera | 7.0.0 | jieba | 49.0 MB | 10,597,993 | 748,201 | 22.3 MB |
| litsea (chinese, two-stage) | 0.16.0 | chinese_pos.model | 8.0 MB | 6,141,077 | 223,464 | 56.0 MB |
| alyze (smartcn) | 0.2.0 | smartcn (embedded) | 4.5 MB | 5,308,415 | 267,136 | 22.0 MB |

### English (`pride_and_prejudice.txt`, 677,531 characters)

| Tokenizer | Version | Dictionary / Model | Dictionary / Model Size | Speed [chars/sec] | Std dev | Peak Memory |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| alyze (UAX #29) | 0.2.0 | - | - | 322,484,408 | 25,960,954 | 2.9 MB |
| litsea (english) | 0.16.0 | english.model | 0.1 MB | 32,483,073 | 1,515,818 | 4.6 MB |
| litsea (english, two-stage) | 0.16.0 | english_pos.model | 2.9 MB | 12,010,536 | 456,011 | 23.7 MB |

These numbers depend heavily on the measurement environment (CPU, memory
bandwidth, OS scheduler, JIT/JVM warm-up) and should only be used to compare
tokenizers measured together on the same run, not as absolute benchmarks.
Reproduce with `./run_all.sh | tee ./results` and `./stats.py < ./results`
as described above.

## Segmentation accuracy

Measured 2026-11-23 on the machine above with `./segment_all.sh`. Every row
segments with the same executable and options as in the speed tables: run
with `BENCH_TOKENS=<file>`, each bench segments its input a second time after
the timed loop and writes the tokens, and `segmentation.py` scores them.

A token counts as correct when it covers exactly the same characters as a
token of the other side. Precision is over the tokens of the row, and recall
over the tokens of the reference or the gold data. Before scoring, tokens
whose first character is whitespace, punctuation, a symbol or a control
character are dropped from both sides, as Lucene's kuromoji and nori discard
punctuation, so that the rows that discard punctuation can be compared with
the rows that keep it. Percentages have two decimals, and only an exact match
is shown as 100.00: a share below 100 % that would round up to it is shown as
99.99.

### How to read the metrics

This section explains the metrics with one sentence, for readers who are
new to them; the sections below define them precisely.

**The units of the gold data.** Dictionaries split Japanese into words in
different ways, and none of them is the one right way. The Japanese gold data
splits each sentence into units of three sizes, each unit being made of whole
units of the smaller sizes. For 国際連合で猫を見た。 ("I saw a cat at the
United Nations"):

| Unit | Split | What it is |
| --- | --- | --- |
| Short units | 国際 / 連合 / で / 猫 / を / 見 / た / 。 | the smallest units |
| Long units | 国際連合 / で / 猫 / を / 見 / た / 。 | compounds joined into one unit |
| Bunsetsu | 国際連合で / 猫を / 見た。 | phrases: a content word with the particles after it |

Dictionaries that split into short units (UniDic) and dictionaries that split
into longer units (IPADIC, Sudachi) both split somewhere in this range. The
Korean tables read the same way, with morphemes as the small units and
eojeols (the space-separated words) as the large ones.

**F1 of a unit.** How closely a row follows the units of one size. Precision
is the share of the row's tokens that are exactly such units (how accurate
its output is), and recall the share of these units that the row outputs (how
little it misses); F1 combines the two and is high only when both are. A row
that splits 国際連合 / で / 猫 / を / 見 / た scores 76.9 % on short units, as
国際連合 is not a short unit (国際 and 連合 are), and 100 % on long units. The
F1 thus depends on which standard a dictionary follows, and a low F1 is not
always an error.

**Boundaries.** A boundary is a place between two words.

| Metric | The share of | Drops when the row |
| --- | --- | --- |
| Cuts at short-unit boundaries | the row's cuts that are also short-unit boundaries | cuts inside a word |
| Long-unit boundaries kept | the long-unit boundaries that no token of the row crosses | joins words across a long-unit boundary |
| Bunsetsu boundaries kept | the bunsetsu boundaries that no token of the row crosses | joins words across a bunsetsu boundary, an error in most standards |

Four ways to split the sentence above, scored by `segmentation.py` (%):

| Split | F1, short units | Cuts at short-unit boundaries | F1, long units | Long-unit boundaries kept | Bunsetsu boundaries kept |
| --- | ---: | ---: | ---: | ---: | ---: |
| A: 国際 / 連合 / で / 猫 / を / 見 / た / 。 | 100.0 | 100.0 | 76.9 | 100.0 | 100.0 |
| B: 国際連合 / で / 猫 / を / 見 / た / 。 | 76.9 | 100.0 | 100.0 | 100.0 | 100.0 |
| C: 国際 / 連 / 合 / で / 猫 / を / 見 / た / 。 | 80.0 | 87.5 | 71.4 | 100.0 | 100.0 |
| D: 国際連合で猫 / を / 見た / 。 | 20.0 | 100.0 | 22.2 | 50.0 | 50.0 |

* A follows short units and B long units: their F1 differ with the
  standard, but both keep every boundary, so both split correctly.
* C cuts inside 連合, so fewer of its cuts are at short-unit boundaries. In
  the tables below, `kytea` scores 91 % there, as it cuts い / る.
* D cuts only at the right places, so all its cuts are at short-unit
  boundaries, but it joins words across long-unit and bunsetsu boundaries.

When both "Cuts at short-unit boundaries" and "Long-unit boundaries kept" are
close to 100 %, the row splits correctly somewhere between short and long
units, whatever the standard of its dictionary: these two compare
dictionaries fairly. The two F1 show which standard a row is close to.

**Agreement F1.** The F1 against the output of the reference implementation
of the same dictionary (MeCab, for example) instead of the gold data: 100 %
means that the two split the same way. "Lines that differ" counts the lines
of the speed corpus where any split differs. Agreement shows how faithfully
an implementation reproduces the reference, not whether the split is right.

### Agreement with the reference implementation

The rows that read the same dictionary or model are compared with a
reference implementation of it, on the corpora of the speed tables. Agreement
shows how closely an implementation reproduces the reference, not whether its
segmentation is right. `kuromoji (Lucene)` and `alyze (kuromoji)` write the
same tokens, as do `nori (Lucene)` and `alyze (nori)`, and `lindera` with
`ko-dic` and `mecab-ko`. `lindera`'s `ipadic` is built from
`mecab-ipadic-2.7.0-20250920`, a later archive of the IPADIC version that
`mecab` reads (2.7.0-20070801); vibrato's release notes say that its
`ipadic-mecab-2.7.0` is built from IPADIC v2.7.0. `lindera`'s `sudachidict` is
not compared with `sudachi`: it is SudachiDict 20260723 with the small, core
and notcore lexicons and runs without Sudachi's split modes, while `sudachi`
reads the 20261015 core dictionary in mode C.

#### IPADIC (reference: mecab, ipadic 2.7.0)

| Tokenizer | Dictionary / Model | Agreement F1 [%] | Lines that differ |
| --- | --- | ---: | ---: |
| lindera | ipadic | 99.96 | 30 of 2,346 |
| vibrato | ipadic-mecab-2.7.0 | 99.99 | 1 of 2,346 |
| kuromoji (Atilika) | ipadic (bundled) | 99.34 | 426 of 2,346 |
| kuromoji (Lucene) | ipadic (bundled) | 99.41 | 398 of 2,346 |
| alyze (kuromoji) | ipadic (embedded) | 99.41 | 398 of 2,346 |

#### UniDic CWJ 3.1.1 (reference: mecab, unidic-cwj-3.1.1)

| Tokenizer | Dictionary / Model | Agreement F1 [%] | Lines that differ |
| --- | --- | ---: | ---: |
| vibrato | unidic-cwj-3.1.1 | 99.98 | 6 of 2,346 |
| vibrato | unidic-cwj-3.1.1+compact-dual | 99.97 | 15 of 2,346 |

#### UniDic CWJ 202512 (reference: mecab, unidic-cwj-202512)

| Tokenizer | Dictionary / Model | Agreement F1 [%] | Lines that differ |
| --- | --- | ---: | ---: |
| lindera | unidic-cwj | 99.99 | 2 of 2,346 |

#### mecab-ko-dic 2.1.1 (reference: mecab-ko, mecab-ko-dic 2.1.1-20180720)

| Tokenizer | Dictionary / Model | Agreement F1 [%] | Lines that differ |
| --- | --- | ---: | ---: |
| mecab | mecab-ko-dic 2.1.1-20180720 | 99.50 | 329 of 3,967 |
| lindera | ko-dic | 100.00 | 0 of 3,967 |
| nori (Lucene) | mecab-ko-dic (bundled) | 99.80 | 132 of 3,967 |
| alyze (nori) | mecab-ko-dic (embedded) | 99.80 | 132 of 3,967 |

#### SudachiDict 20261015 core (reference: sudachi, sudachi-dictionary-20261015-core)

| Tokenizer | Dictionary / Model | Agreement F1 [%] | Lines that differ |
| --- | --- | ---: | ---: |
| sudachi.rs | sudachi-dictionary-20261015-core | 99.73 | 192 of 2,346 |

#### KyTea model jp-0.4.7-5 (reference: kytea, jp-0.4.7-5.mod)

| Tokenizer | Dictionary / Model | Agreement F1 [%] | Lines that differ |
| --- | --- | ---: | ---: |
| vaporetto | kytea jp-0.4.7-5.mod | 99.96 | 47 of 2,346 |

### Accuracy against Universal Dependencies

The gold data are treebanks of [Universal Dependencies](https://universaldependencies.org/)
(UD), release r2.19: the test sets of the parallel treebanks
[UD_Japanese-PUD](https://github.com/UniversalDependencies/UD_Japanese-PUD),
[UD_Chinese-PUD](https://github.com/UniversalDependencies/UD_Chinese-PUD) and
[UD_English-PUD](https://github.com/UniversalDependencies/UD_English-PUD)
(1,000 sentences each, from news and Wikipedia, CC BY-SA 3.0), and the test
set of [UD_Korean-Kaist](https://github.com/UniversalDependencies/UD_Korean-Kaist)
(2,287 sentences of news, fiction and academic text, CC BY-SA 4.0).
`./download_resources.sh` fetches them; they are not part of this repository.
None of them is in the training data of litsea's models (UD Japanese-GSD,
Korean-GSD, Chinese-GSD and English-EWT) or of lindera's jieba dictionary (UD
Chinese-GSD and GSDSimp).

UD's units are syntactic words, and UD leaves the details of word
segmentation to the documentation of each language (see UD's
[tokenization guidelines](https://universaldependencies.org/u/overview/tokenization.html)).
Every row is scored against the layers that the UD data of its language
annotates, so that rows that segment by different standards are read against
the same data. The layers of Japanese (short units, long units, bunsetsu)
and Korean (morphemes, eojeols) run from fine to coarse, each unit of a
layer being made of whole units of the finer ones, and each layer is scored
in two ways:

* F1 of the units: how closely the row follows the standard of the layer. A
  row that follows another standard scores low on it; the notes say which
  rows follow which standard.
* For the finest layer, "Cuts at ... boundaries" is the share of the row's
  cuts (the edges of its tokens inside the sentence) that are boundaries of
  the layer: it is low when the row splits inside the units. For a coarser
  layer, "... boundaries kept" is the share of the layer's boundaries that no
  token of the row crosses: it is low when the row joins units across them.

A row whose cuts are all short-unit boundaries and that keeps every
long-unit boundary segments somewhere between short and long units, whatever
its standard. The cuts at the boundaries of the coarser layers are not
given, nor the F1 of bunsetsu: every row splits finer than these layers, so
these numbers would show how finely a row splits, not its errors. Chinese,
with one layer, and English, with words and tokens, are given precision,
recall and F1 of UD's words. The rows are sorted by the F1 of the first
layer.

* Japanese: UD Japanese is tokenized in three layers, as the Balanced Corpus
  of Contemporary Written Japanese (BCCWJ) is: short units, long units and
  bunsetsu (base phrases), as the
  [UD_Japanese-GSD README](https://github.com/UniversalDependencies/UD_Japanese-GSD/blob/r2.19/README.md)
  says.
  * UD's words are short units with cardinal numbers concatenated into one
    word, so adjacent tokens made only of digits are merged on both sides
    first. The UniDic rows and litsea follow short units. `kytea` and
    `vaporetto` (the same KyTea model) also split conjugated words into stem
    and ending. The IPADIC rows and `rust-tinysegmenter` use IPADIC's units,
    the Sudachi rows mode C (the mode for named entities) and `lindera`'s
    `sudachidict` the SudachiDict lexicon without Sudachi's split modes.
  * The long units are built from the MISC field `LUWBILabel` of each word;
    they equal the words of
    [UD_Japanese-PUDLUW](https://github.com/UniversalDependencies/UD_Japanese-PUDLUW),
    the long-unit version of the same sentences. No row follows long units.
  * Every bunsetsu boundary (MISC `BunsetuBILabel`) is also a boundary of
    long and short units. Ignored tokens cross no boundary, and the cuts are
    those of the tokens that are scored.
  * Every row but `kytea`, `vaporetto` and `rust-tinysegmenter` cuts at
    short-unit boundaries in at least 98.7 % of its cuts, and every row keeps
    at least 98.8 % of the long-unit and 98.7 % of the 8,972 bunsetsu
    boundaries. The IPADIC and Sudachi rows score lower on short units because
    their units are longer, not because they cut at wrong places. `kytea` and
    `vaporetto` split inside short units (い / る), and `rust-tinysegmenter`
    loses on both sides. The tokens that cross a bunsetsu boundary are mostly
    multiword entries of IPADIC (役に立つ, として) and named entities and
    idioms of `lindera`'s `sudachidict` (法の支配, トロイの木馬), which join
    words of two bunsetsu.
  * `lindera`'s `ipadic` scores higher than `mecab`'s, as lindera 7.0.0
    breaks unknown words at `・` and the gold data splits katakana names
    there (コリ・シューマン), while MeCab keeps such a name as one unknown
    word, as IPADIC's `char.def` puts `・` in its katakana category. 104 of
    the 106 places where `lindera` and `vibrato` segment differently are such
    names.
* Korean: the words of UD_Korean-Kaist are eojeols (the space-separated
  words) with the punctuation split off, which litsea outputs; the other rows
  output morphemes. The morphemes are the parts of each word's lemma split at
  `+` (조약에 = 조약+에). They are base forms, so a word whose parts do not
  concatenate back to it (의해 = 의하+어) is left out of the morpheme scores on
  both sides, which leaves 23,517 of the 28,366 words (82.9 %) scored; a cut
  inside such a word is not counted. The mecab-ko-dic rows cut at morpheme
  boundaries in 97.6 % of their cuts and litsea in all but 1 or 2 of its
  48,000 cuts, and every row keeps every eojeol boundary. The sentences are
  not those of the PUD treebanks. UD_Korean-PUD is not used: it splits the
  copula and some endings and compound nouns off eojeols
  (수준이지만 = 수준 + 이지만), so only 69.4 % of its words that are not
  punctuation are eojeols, and the others are not morphemes either.
* Chinese: UD_Chinese-PUD is in traditional script and was annotated by
  Google; UD's
  [Chinese tokenization page](https://universaldependencies.org/zh/tokenization.html)
  describes no segmentation standard for it. litsea and `lindera`'s `jieba`
  are trained on UD Chinese-GSD, which Google also annotated. CC-CEDICT gives
  words without a segmentation standard, and smartcn is for simplified
  Chinese only.
* English: UD's [English documentation](https://universaldependencies.org/en/index.html)
  splits clitics (do + n't, 's) and most hyphenated words (search, -, engine)
  into words, and keeps acronyms (U.S.) whole. The F1 column scores these
  words; "F1, tokens" scores the unsplit tokens (don't), which is how UAX #29
  segments.

#### Japanese, UD_Japanese-PUD r2.19 (short units, long units, bunsetsu)

| Tokenizer | Dictionary / Model | F1, short units [%] | Cuts at short-unit boundaries [%] | F1, long units [%] | Long-unit boundaries kept [%] | Bunsetsu boundaries kept [%] |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| vibrato | unidic-cwj-3.1.1 | 98.80 | 99.33 | 67.39 | 99.97 | 99.97 |
| vibrato | unidic-cwj-3.1.1+compact-dual | 98.77 | 99.32 | 67.40 | 99.97 | 99.97 |
| mecab | unidic-cwj-3.1.1 | 98.75 | 99.29 | 67.37 | 99.97 | 99.97 |
| mecab | unidic-cwj-202512 | 98.46 | 98.86 | 67.02 | 99.98 | 99.97 |
| lindera | unidic-cwj | 98.46 | 98.86 | 67.02 | 99.98 | 99.97 |
| lindera | unidic | 98.36 | 98.78 | 66.79 | 99.98 | 99.98 |
| lindera | unidic-csj | 98.23 | 98.77 | 66.91 | 99.96 | 99.97 |
| litsea (japanese) | japanese.model | 97.57 | 99.00 | 67.17 | 99.75 | 99.71 |
| litsea (japanese, two-stage) | japanese_pos.model | 97.51 | 98.95 | 67.12 | 99.76 | 99.71 |
| sudachi.rs | sudachi-dictionary-20261015-core | 94.68 | 99.81 | 71.50 | 99.91 | 99.94 |
| sudachi | sudachi-dictionary-20261015-core | 94.41 | 99.81 | 71.59 | 99.93 | 99.94 |
| lindera | ipadic | 93.41 | 99.15 | 70.18 | 99.42 | 99.45 |
| kuromoji (Lucene) | ipadic (bundled) | 93.38 | 99.12 | 70.15 | 99.42 | 99.45 |
| alyze (kuromoji) | ipadic (embedded) | 93.38 | 99.12 | 70.15 | 99.42 | 99.45 |
| mecab | ipadic 2.7.0 | 92.80 | 99.19 | 70.70 | 99.42 | 99.45 |
| vibrato | ipadic-mecab-2.7.0 | 92.80 | 99.19 | 70.70 | 99.42 | 99.45 |
| kuromoji (Atilika) | ipadic (bundled) | 92.66 | 99.15 | 70.70 | 99.42 | 99.44 |
| lindera | sudachidict | 92.09 | 99.49 | 72.84 | 99.80 | 99.78 |
| rust-tinysegmenter | - | 90.66 | 97.99 | 68.55 | 98.87 | 98.74 |
| vaporetto | kytea jp-0.4.7-5.mod | 84.87 | 91.23 | 57.27 | 99.93 | 99.89 |
| kytea | jp-0.4.7-5.mod | 84.85 | 91.21 | 57.27 | 99.95 | 99.92 |

#### Korean, UD_Korean-Kaist r2.19 test (morphemes, eojeols)

| Tokenizer | Dictionary / Model | F1, morphemes [%] | Cuts at morpheme boundaries [%] | F1, eojeols [%] | Eojeol boundaries kept [%] |
| --- | --- | ---: | ---: | ---: | ---: |
| nori (Lucene) | mecab-ko-dic (bundled) | 92.80 | 97.61 | 18.25 | 100.00 |
| alyze (nori) | mecab-ko-dic (embedded) | 92.80 | 97.61 | 18.25 | 100.00 |
| mecab-ko | mecab-ko-dic 2.1.1-20180720 | 92.79 | 97.61 | 18.24 | 100.00 |
| lindera | ko-dic | 92.79 | 97.61 | 18.24 | 100.00 |
| mecab | mecab-ko-dic 2.1.1-20180720 | 92.71 | 97.58 | 18.24 | 100.00 |
| litsea (korean) | korean.model | 18.15 | 99.99 | 99.99 | 100.00 |
| litsea (korean, two-stage) | korean_pos.model | 18.15 | 99.99 | 99.99 | 100.00 |

#### Chinese, UD_Chinese-PUD r2.19 (traditional)

| Tokenizer | Dictionary / Model | Precision [%] | Recall [%] | F1 [%] |
| --- | --- | ---: | ---: | ---: |
| litsea (chinese) | chinese.model | 85.22 | 88.00 | 86.59 |
| litsea (chinese, two-stage) | chinese_pos.model | 85.03 | 88.08 | 86.52 |
| lindera | jieba | 82.53 | 88.80 | 85.55 |
| lindera | cc-cedict | 79.37 | 81.69 | 80.51 |
| alyze (smartcn) | smartcn (embedded) | 43.29 | 61.47 | 50.80 |

#### English, UD_English-PUD r2.19

| Tokenizer | Dictionary / Model | Precision [%] | Recall [%] | F1 [%] | F1, tokens [%] |
| --- | --- | ---: | ---: | ---: | ---: |
| litsea (english, two-stage) | english_pos.model | 99.71 | 99.73 | 99.72 | 98.98 |
| litsea (english) | english.model | 99.62 | 99.64 | 99.63 | 98.89 |
| alyze (UAX #29) | - | 98.70 | 98.66 | 98.68 | 99.34 |

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
