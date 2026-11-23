# 各種トークナイザのベンチマーク

[English](README.md) | 日本語

このリポジトリには、各種トークナイザのベンチマークツールが含まれています。

## 概要

ベンチマークを実行するには、以下の 2 つのステップを実行します。

### 準備

以下のコマンドで、リソース（モデルデータなど）の準備とソースコードの
コンパイルを行います。

```sh
% git submodule update --init
% ./download_resources.sh
% ./compile_all.sh
```

スクリプトは Linux と macOS で動きます（mecab-ko のビルドは Linux でだけ
確かめています）。下の結果は Linux で計測しています。
Rust と以下のパッケージを入れてから、上のコマンドを実行します。
Ubuntu では、`./compile_all.sh` が確かめる `libtool` コマンドは
`libtool-bin` に、`./run_all.sh` がピークメモリの計測に使う
`/usr/bin/time` は `time` に入っています。Lucene のベンチには Java 21 以上が
要ります。

```sh
% sudo apt install build-essential patch autoconf automake \
    libtool libtool-bin default-jdk-headless maven \
    wget unzip xz-utils time
```

macOS では、Rust、JDK（21 以上）、Xcode Command Line Tools と、
以下のツールを Homebrew で入れます。
Windows では WSL で実行してください。

```sh
% brew install wget autoconf automake libtool maven
```

### 計測

各トークナイザの速度を計測するには、以下のコマンドを実行します。
`./run_all.sh` を途中で停止した場合でも、`./stats.py` はその時点までの
結果から統計を算出します。

```sh
% ./run_all.sh | tee ./results
% ./stats.py < ./results
```

`./run_all.sh` は、各トークナイザを 1 回のウォームアップの後に 100 回計測します。
ざっくり比べるときは、`ITERATIONS` で計測の回数を減らせます。

```sh
% ITERATIONS=10 ./run_all.sh | tee ./results
```

## 計測結果

2026-11-23 に以下の環境で計測しました。

* マシン: GMKtec EVO-X2、AMD Ryzen AI MAX+ 395（16 コア、32 スレッド）
* メモリ: 126GiB
* OS: Ubuntu 26.04.1 LTS（Linux 7.0.0-43-generic）、CPU の周波数の
  governor は `performance`
* ツールチェーン: rustc 1.99.1, OpenJDK 25.0.5.1, Apache Maven 3.9.12,
  g++ 15.2.0

2026-11-11 までの計測結果は MacBook Air（Apple M4、macOS 27.2）で
lindera 6.2.0 を、2026-09-29 までの計測結果は別のマシン（Intel Core
i7-1185G7、Ubuntu 24.04）で古いバージョンを計測したものなので、
どちらも今回の結果とは比較できません。

各トークナイザはコーパスを 100 回分かち書きします（ウォームアップ 1 回を
実施し、統計からは除外）。速度（Speed）は 1 秒あたりの処理文字数で、
大きいほど高速です。標準偏差（Std dev）は 100 回の反復にわたる
母標準偏差です。

`litsea (*, two-stage)` は `Segmenter::with_two_stage_learner` により
1 つのモデルファイルで分かち書きと品詞付与を同時に行うモードで、ほかの
litsea の行は分かち書きだけを行います。`lindera` は `embed-*` cargo
feature ではなく、lindera がリリースごとに公開しているビルド済み辞書
アーカイブ（例: `lindera-ipadic-7.0.0.zip`）から辞書を読み込むため、
`ipadic`・`unidic`・`unidic-cwj`・`unidic-csj`・`sudachidict` に加えて
`cc-cedict`（中国語）、`jieba`（中国語）、`ko-dic`（韓国語）の辞書も
カバーしています。lindera 6.1.0 から、ko-dic は
mecab-ko の左側の空白に対するペナルティを既定で適用するようになり、
`ko-dic` の行はこの既定のまま計測しています。lindera 7.0.0 は、6.2.0 より
MeCab に近い分かち書きをします。空白を lattice（ラティス）から外し、行の中で
`、` と `。` をまたいで文脈をつなぎ、未知語を MeCab と同じように作り、`・` で
未知語を区切ります。CC-CEDICT と Jieba の辞書も、新しいソースから作り直されて
います。これらのコーパスでのトークン数は、6.2.0 と比べて ipadic で +441、
unidic で +166、cc-cedict で -6、jieba で +13,958、ko-dic で -257 変わります。

lindera の日本語の辞書は、元の辞書がそれぞれ違います。`unidic` は UniDic
2.1.2 です。`unidic-cwj` と `unidic-csj` は書き言葉（CWJ）と話し言葉（CSJ）の
UniDic 202512 で、NINJAL の full 版から作られています。`unidic-cwj` は `mecab`
の `unidic-cwj-202512` の行と同じ版で、このコーパスの 2,346 行のうち 4 行を
除いて同じ分かち書きをします。コーパスは書き言葉なので、`unidic-csj` が想定
する文章ではありません。`sudachidict` は small・core・notcore の 3 つの語彙を
含む SudachiDict 20260723（full 版）で、`sudachi` と `sudachi.rs` の行とは版
も語彙の範囲も違います。lindera は Sudachi の文字の定義を読みますが、入力の
正規化、カタカナや数字の連結、A/B/C の分割単位といった Sudachi のプラグイン
は動かしません。

`mecab` と `mecab-ko` は、lindera の `ko-dic` の元になった mecab-ko-dic
2.1.1-20180720 も読みます。mecab-ko 0.996-ko-0.9.2 は、MeCab を韓国語向けに
直したものです。mecab-ko-dic の `dicrc` は、助詞などの品詞の左に空白がある
ときに連接コストを上げる `left-space-penalty-factor` を設定しており、これを
読むのは mecab-ko だけです。そのため mecab-ko は lindera の `ko-dic` とまったく
同じ分かち書きをし、本家の MeCab はこのコーパスの 3,967 行のうち 329 行で
違う分かち書きをします。`download_resources.sh` は mecab-ko のリリースの
アーカイブを取得して SHA-256 で照合し、`compile_all.sh` はそれをビルドして、
mecab-ko の `mecab-dict-index` で辞書を 1 回だけコンパイルします。本家の
MeCab の `mecab-dict-index` も同じファイルを書き出します。

`mecab` には UniDic の行が 2 つあります。`unidic-cwj-3.1.1` は `vibrato`
の UniDic の行と同じ辞書で（vibrato が配布しているビルド済みの UniDic cwj
辞書はすべて 3.1.1 です）、`unidic-cwj-202512` は UniDic の最新版です。
`sudachi` と `sudachi.rs` は同じ SudachiDict v20261015 core 辞書を V1 形式で
読み込みます。Sudachi 0.8.2 と sudachi.rs 0.7.0 が読めるのは V1 形式だけです。
sudachi.rs 0.7 では、Java 版と結果をそろえるため解析の一部も変わっています。
`vibrato` は他の Rust 製トークナイザと同じく、素の `cargo build --release`
でビルドしています。`kytea` と `vaporetto` が使う KyTea のモデル
`jp-0.4.7-5.mod` は元の URL から配布されなくなったため、
`download_resources.sh` は Wayback Machine に保存された写しを取得し、
SHA-256 で照合します。

`alyze` は turbopuffer のテキスト解析ライブラリです。kuromoji・nori・smartcn
の解析器は Elasticsearch が使う Lucene の解析器を移植したもので、alyze の行は
Elasticsearch のフィルタの連鎖（`analyze`）ではなく、トークナイザ
（`tokenize`）を呼び出しています。kuromoji は `Mode::Normal`、nori は
`DecompoundMode::None` で計測しており、`lindera`・`mecab`・`vibrato` の行と
同じく複合語を分解しません（alyze の既定は `Mode::Search` と
`DecompoundMode::Discard` です）。どちらも既定の `discard_punctuation: true`
のままで、smartcn は句読点のトークンを常に出力します。alyze の行は、alyze
の想定どおりトークンのバッファを行をまたいで使い回します。一方、lindera の
`Segmenter::segment` は呼び出しごとにメモリを確保します。また、alyze の
kuromoji と nori はすべてのトークンの品詞や読みなどを作るのに対し、lindera
はトークンの詳細を必要になったときに読み込みます。`alyze (UAX #29)` は
alyze の規則ベースの単語分割（辞書を使わない DFA）で、単語境界の間の区間を
すべて報告し、ベンチマークはそのうち単語らしい区間を数えます。英語では
基準となる値であり、litsea の学習済みの分かち書きと同じ条件の比較では
ありません。

`kuromoji (Atilika)` は Atilika の Kuromoji
（`com.atilika.kuromoji:kuromoji-ipadic` 0.9.0）で、jar に同梱された IPADIC を
使います。ベンチは `new Tokenizer()` を呼び出し、トークンには句読点も含まれ
ます。`kuromoji (Lucene)` と `nori (Lucene)` は Apache Lucene 10.6.0 の日本語と
韓国語のトークナイザ（`lucene-analysis-kuromoji` と `lucene-analysis-nori`）で、
jar に mecab-ipadic-2.7.0-20070801 と mecab-ko-dic-2.1.1-20180720 が同梱されて
います。Lucene の既定（`SEARCH` と `DISCARD`）ではなく
`JapaneseTokenizer.Mode.NORMAL` と `KoreanTokenizer.DecompoundMode.NONE` で、
句読点を捨てて計測しています。これは alyze の行と同じ設定で、この設定では
Lucene と alyze は両方のコーパスで同じ分かち書きをします。どちらのベンチも、
Lucene の想定どおり 1 つのトークナイザをすべての行で使い回します。

辞書・モデルサイズ（Dictionary / Model Size）は、各トークナイザが実行時に
実際に開くファイルのディスク上のサイズであり、実行時のメモリ使用量では
ありません。開いたファイルは `strace` で確かめました。小さな設定ファイル
（MeCab の `mecabrc` と `dicrc`、lindera の `metadata.json` など）は含めて
いません。ディストリビューションによっては辞書と一緒に実行時には使われない
データが同梱されていますが、
それらは除外しています（例: MeCab の辞書ディレクトリに含まれる生の CSV 語彙
ソース、評価用データ、ライセンスファイル、コンパイル・学習専用の
`model.bin` や `*.def` ソース。Tagger 自身が開くのはコンパイル済みの
`sys.dic`/`matrix.bin`/`char.bin`/`unk.dic` のみです。jar の中の辞書は
圧縮された `.jar` ではなく展開後のファイル（`kuromoji (Atilika)` は `.bin`、
Lucene の行は `.dat`）で、vibrato の
`system.dic.zst` は実際にメモリ上に保持される展開後のサイズで計測して
います）。辞書を実行ファイルに埋め込むトークナイザは、埋め込んだデータの
サイズです。vaporetto はビルドスクリプトが KyTea のモデルから変換した
predictor、alyze はビルドスクリプトが alyze の GitHub リリースから取得して
SHA-256 で照合する辞書ファイル（アーカイブからライセンスと NOTICE を除いた
もの）です。1 MB は 1,048,576 バイトです。ピークメモリ（Peak Memory）は、
GNU time（`/usr/bin/time -v`）で各反復をラップして計測したベンチマークプロセス全体の
最大常駐セットサイズ（RSS）です。そのため、Speed が計測する分かち書き
ループだけでなく、辞書の読み込みも含まれます。全エンジンをこの方法で
計測しており、Java の 4 エンジンも Maven 自身のメモリが計上されないよう
`mvn exec:java` ではなく `java -cp` で直接起動しています。

ピークメモリは、プロセスが確保したメモリの量ではなく、物理メモリに載っていた
ページの量です。そのため、行によって意味が違います。RSS には、プロセスが
触れた、ファイルを写像したページも含まれます。辞書を `mmap` で読む
トークナイザ（lindera など）や、辞書を実行ファイルに埋め込むトークナイザ
（alyze と vaporetto）では、読んだ辞書のページも含まれます。このページは
ページキャッシュで、ほかのプロセスと共有でき、メモリが足りなくなればカーネル
が回収できます。Java の行は、JVM そのもののメモリと、GC が管理するヒープを
含み、ヒープの大きさは GC の設定と動きで決まります。行どうしを比べるときは、
これらの違いに注意してください。

### 日本語（`wagahaiwa_nekodearu.txt`、372,573 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| vaporetto | 0.7.0 | kytea jp-0.4.7-5.mod | 80.6 MB | 24,841,134 | 1,213,976 | 188.7 MB |
| litsea (japanese) | 0.16.0 | japanese.model | 1.1 MB | 16,722,972 | 623,392 | 12.0 MB |
| litsea (japanese, two-stage) | 0.16.0 | japanese_pos.model | 5.4 MB | 8,209,157 | 363,630 | 44.9 MB |
| vibrato | 0.5.3 | ipadic-mecab-2.7.0 | 45.6 MB | 7,881,993 | 183,118 | 68.8 MB |
| lindera | 7.0.0 | ipadic | 45.3 MB | 6,787,817 | 333,025 | 18.3 MB |
| mecab | thirdparty submodule | ipadic 2.7.0 | 50.5 MB | 6,563,562 | 282,572 | 33.8 MB |
| lindera | 7.0.0 | unidic | 189.9 MB | 4,723,004 | 253,681 | 91.0 MB |
| alyze (kuromoji) | 0.2.0 | ipadic (embedded) | 12.5 MB | 4,584,678 | 182,014 | 18.0 MB |
| vibrato | 0.5.3 | unidic-cwj-3.1.1 | 684.2 MB | 4,058,161 | 203,445 | 723.8 MB |
| lindera | 7.0.0 | sudachidict | 564.9 MB | 3,807,446 | 202,115 | 155.1 MB |
| rust-tinysegmenter | 0.1.1 | - | - | 2,604,513 | 52,431 | 3.8 MB |
| kuromoji (Lucene) | 10.6.0 | ipadic (bundled) | 8.7 MB | 2,604,376 | 65,793 | 111.2 MB |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 122.3 MB | 2,586,761 | 99,031 | 736.5 MB |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 691.0 MB | 2,518,872 | 119,100 | 371.5 MB |
| lindera | 7.0.0 | unidic-cwj | 1,244.3 MB | 2,304,829 | 128,556 | 1,009.6 MB |
| lindera | 7.0.0 | unidic-csj | 1,264.6 MB | 2,293,105 | 130,524 | 1,029.9 MB |
| kuromoji (Atilika) | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 31.9 MB | 2,260,815 | 80,788 | 341.4 MB |
| sudachi.rs | git tag `v0.7.0` | sudachi-dictionary-20261015-core | 192.9 MB | 1,837,778 | 76,484 | 176.0 MB |
| mecab | thirdparty submodule | unidic-cwj-202512 | 1,252.8 MB | 1,616,467 | 84,182 | 485.2 MB |
| vibrato | 0.5.3 | unidic-cwj-3.1.1+compact-dual | 286.4 MB | 1,589,938 | 55,646 | 326.0 MB |
| sudachi | 0.8.2 | sudachi-dictionary-20261015-core | 192.9 MB | 808,914 | 27,098 | 566.3 MB |

### 韓国語（`mujeong.txt`、320,850 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | 0.16.0 | korean.model | 0.1 MB | 24,081,430 | 883,999 | 4.2 MB |
| litsea (korean, two-stage) | 0.16.0 | korean_pos.model | 3.9 MB | 7,605,267 | 328,732 | 32.3 MB |
| mecab | thirdparty submodule | mecab-ko-dic 2.1.1-20180720 | 96.7 MB | 3,668,364 | 174,481 | 70.5 MB |
| lindera | 7.0.0 | ko-dic | 81.6 MB | 3,600,781 | 99,692 | 83.8 MB |
| alyze (nori) | 0.2.0 | mecab-ko-dic (embedded) | 43.2 MB | 2,621,246 | 99,389 | 47.9 MB |
| mecab-ko | 0.996-ko-0.9.2 | mecab-ko-dic 2.1.1-20180720 | 96.7 MB | 1,682,780 | 108,831 | 70.3 MB |
| nori (Lucene) | 10.6.0 | mecab-ko-dic (bundled) | 23.9 MB | 1,353,593 | 47,301 | 158.0 MB |

### 中国語（`rulin_waishi.txt`、328,153 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (chinese) | 0.16.0 | chinese.model | 1.9 MB | 16,104,948 | 626,072 | 19.2 MB |
| lindera | 7.0.0 | cc-cedict | 22.1 MB | 14,821,366 | 839,669 | 9.8 MB |
| lindera | 7.0.0 | jieba | 49.0 MB | 10,627,332 | 738,976 | 22.3 MB |
| litsea (chinese, two-stage) | 0.16.0 | chinese_pos.model | 8.0 MB | 6,240,491 | 227,699 | 56.0 MB |
| alyze (smartcn) | 0.2.0 | smartcn (embedded) | 4.5 MB | 5,403,179 | 254,533 | 22.0 MB |

### 英語（`pride_and_prejudice.txt`、677,531 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| alyze (UAX #29) | 0.2.0 | - | - | 321,883,225 | 19,996,784 | 3.0 MB |
| litsea (english) | 0.16.0 | english.model | 0.1 MB | 33,051,314 | 951,716 | 4.6 MB |
| litsea (english, two-stage) | 0.16.0 | english_pos.model | 2.9 MB | 12,125,331 | 300,371 | 23.7 MB |

これらの数値は計測環境（CPU、メモリ帯域、OS スケジューラ、JIT/JVM の
ウォームアップ）に大きく依存するため、絶対的なベンチマークとしてでは
なく、同一の実行で一緒に計測されたトークナイザ間の比較にのみ使用して
ください。上記の手順どおり `./run_all.sh | tee ./results` と
`./stats.py < ./results` で再現できます。

## ライセンス

以下のいずれかのライセンスの下で提供されます。

* Apache License, Version 2.0
  ([LICENSE-APACHE](LICENSE-APACHE) または
  <http://www.apache.org/licenses/LICENSE-2.0>)
* MIT license
  ([LICENSE-MIT](LICENSE-MIT) または <http://opensource.org/licenses/MIT>)

どちらを選択するかは自由です。

`thirdparty` 配下のソフトウェアについては、各ソフトウェアのライセンス
条項に従ってください。

## コントリビューション

特に明示しない限り、Apache-2.0 ライセンスに定義されるとおり、あなたが
本成果物への取り込みを意図して提出したコントリビューションは、追加の
条項や条件なしに、上記のデュアルライセンスの下で提供されるものとします。
