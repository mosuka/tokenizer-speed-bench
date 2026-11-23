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

各トークナイザの分かち書きを評価するには（[分割の精度](#分割の精度)）、
以下のコマンドを実行します。各トークナイザを、上のコーパスと、
`./download_resources.sh` が取得する正解のデータで 1 回ずつ実行し、表を
出力します。

```sh
% ./segment_all.sh | tee ./accuracy
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

### 韓国語（`mujeong.txt`、320,850 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | 0.16.0 | korean.model | 0.1 MB | 24,042,430 | 1,065,937 | 4.2 MB |
| litsea (korean, two-stage) | 0.16.0 | korean_pos.model | 3.9 MB | 7,626,334 | 307,392 | 32.3 MB |
| mecab | thirdparty submodule | mecab-ko-dic 2.1.1-20180720 | 96.7 MB | 3,608,106 | 192,029 | 70.4 MB |
| lindera | 7.0.0 | ko-dic | 81.6 MB | 3,589,310 | 95,548 | 83.7 MB |
| alyze (nori) | 0.2.0 | mecab-ko-dic (embedded) | 43.2 MB | 2,625,118 | 108,350 | 48.0 MB |
| mecab-ko | 0.996-ko-0.9.2 | mecab-ko-dic 2.1.1-20180720 | 96.7 MB | 1,675,894 | 98,272 | 70.3 MB |
| nori (Lucene) | 10.6.0 | mecab-ko-dic (bundled) | 23.9 MB | 1,342,826 | 43,246 | 158.0 MB |

### 中国語（`rulin_waishi.txt`、328,153 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (chinese) | 0.16.0 | chinese.model | 1.9 MB | 15,976,908 | 749,540 | 19.2 MB |
| lindera | 7.0.0 | cc-cedict | 22.1 MB | 14,782,429 | 758,476 | 9.8 MB |
| lindera | 7.0.0 | jieba | 49.0 MB | 10,597,993 | 748,201 | 22.3 MB |
| litsea (chinese, two-stage) | 0.16.0 | chinese_pos.model | 8.0 MB | 6,141,077 | 223,464 | 56.0 MB |
| alyze (smartcn) | 0.2.0 | smartcn (embedded) | 4.5 MB | 5,308,415 | 267,136 | 22.0 MB |

### 英語（`pride_and_prejudice.txt`、677,531 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| alyze (UAX #29) | 0.2.0 | - | - | 322,484,408 | 25,960,954 | 2.9 MB |
| litsea (english) | 0.16.0 | english.model | 0.1 MB | 32,483,073 | 1,515,818 | 4.6 MB |
| litsea (english, two-stage) | 0.16.0 | english_pos.model | 2.9 MB | 12,010,536 | 456,011 | 23.7 MB |

これらの数値は計測環境（CPU、メモリ帯域、OS スケジューラ、JIT/JVM の
ウォームアップ）に大きく依存するため、絶対的なベンチマークとしてでは
なく、同一の実行で一緒に計測されたトークナイザ間の比較にのみ使用して
ください。上記の手順どおり `./run_all.sh | tee ./results` と
`./stats.py < ./results` で再現できます。

## 分割の精度

2026-11-23 に上と同じ環境で、`./segment_all.sh` で計測しました。各行は、速度の
表と同じ実行ファイル・同じ設定で分かち書きします。`BENCH_TOKENS=<ファイル>` を
付けて実行すると、各ベンチは時間を測るループの後に入力をもう一度分かち書きして
トークンを書き出し、`segmentation.py` がそれを採点します。

トークンは、相手側のトークンとまったく同じ文字の範囲を覆うときに正解と数えます。
適合率はその行のトークンに対する割合、再現率は参照の実装または正解のデータの
トークンに対する割合です。採点の前に、最初の文字が空白・句読点・記号・制御文字
のトークンを両側から除きます。これは Lucene の kuromoji と nori が句読点を
捨てる規則で、句読点を捨てる行と残す行を比べられるようにするためです。

### 参照の実装との一致

同じ辞書またはモデルを読む行を、その参照の実装と、速度の表のコーパスで比べます。
一致は、実装が参照をどれだけ再現しているかを示すもので、分かち書きが正しいかは
示しません。`kuromoji (Lucene)` と `alyze (kuromoji)`、`nori (Lucene)` と
`alyze (nori)`、`ko-dic` の `lindera` と `mecab-ko` は、それぞれ同じトークンを
書き出します。`lindera` の `ipadic` は、`mecab` が読む IPADIC と同じ版の後の
アーカイブ（`mecab-ipadic-2.7.0-20250920`。`mecab` は 2.7.0-20070801）から
作られています。vibrato のリリースノートによると、`ipadic-mecab-2.7.0` は
IPADIC v2.7.0 から作られています。`lindera` の `sudachidict` は `sudachi` と
比べません。`lindera` の `sudachidict` は small・core・notcore の語彙を持つ
SudachiDict 20260723 で、Sudachi の分割モードを使わずに分割します。一方
`sudachi` は 20261015 の core の辞書を読み、C モードで分割します。

#### IPADIC（参照: mecab、ipadic 2.7.0）

| トークナイザ | 辞書・モデル | 一致の F 値 [%] | 違う行 |
| --- | --- | ---: | ---: |
| lindera | ipadic | 99.96 | 2,346 行中 30 行 |
| vibrato | ipadic-mecab-2.7.0 | 100.00 | 2,346 行中 1 行 |
| kuromoji (Atilika) | ipadic (bundled) | 99.34 | 2,346 行中 426 行 |
| kuromoji (Lucene) | ipadic (bundled) | 99.41 | 2,346 行中 398 行 |
| alyze (kuromoji) | ipadic (embedded) | 99.41 | 2,346 行中 398 行 |

#### UniDic CWJ 3.1.1（参照: mecab、unidic-cwj-3.1.1）

| トークナイザ | 辞書・モデル | 一致の F 値 [%] | 違う行 |
| --- | --- | ---: | ---: |
| vibrato | unidic-cwj-3.1.1 | 99.98 | 2,346 行中 6 行 |
| vibrato | unidic-cwj-3.1.1+compact-dual | 99.97 | 2,346 行中 15 行 |

#### UniDic CWJ 202512（参照: mecab、unidic-cwj-202512）

| トークナイザ | 辞書・モデル | 一致の F 値 [%] | 違う行 |
| --- | --- | ---: | ---: |
| lindera | unidic-cwj | 100.00 | 2,346 行中 2 行 |

#### mecab-ko-dic 2.1.1（参照: mecab-ko、mecab-ko-dic 2.1.1-20180720）

| トークナイザ | 辞書・モデル | 一致の F 値 [%] | 違う行 |
| --- | --- | ---: | ---: |
| mecab | mecab-ko-dic 2.1.1-20180720 | 99.50 | 3,967 行中 329 行 |
| lindera | ko-dic | 100.00 | 3,967 行中 0 行 |
| nori (Lucene) | mecab-ko-dic (bundled) | 99.80 | 3,967 行中 132 行 |
| alyze (nori) | mecab-ko-dic (embedded) | 99.80 | 3,967 行中 132 行 |

#### SudachiDict 20261015 core（参照: sudachi、sudachi-dictionary-20261015-core）

| トークナイザ | 辞書・モデル | 一致の F 値 [%] | 違う行 |
| --- | --- | ---: | ---: |
| sudachi.rs | sudachi-dictionary-20261015-core | 99.73 | 2,346 行中 192 行 |

#### KyTea model jp-0.4.7-5（参照: kytea、jp-0.4.7-5.mod）

| トークナイザ | 辞書・モデル | 一致の F 値 [%] | 違う行 |
| --- | --- | ---: | ---: |
| vaporetto | kytea jp-0.4.7-5.mod | 99.96 | 2,346 行中 47 行 |

### Universal Dependencies との比較

正解のデータは、[Universal Dependencies](https://universaldependencies.org/)
（UD）の r2.19 の treebank です。並行 treebank の
[UD_Japanese-PUD](https://github.com/UniversalDependencies/UD_Japanese-PUD)、
[UD_Chinese-PUD](https://github.com/UniversalDependencies/UD_Chinese-PUD)、
[UD_English-PUD](https://github.com/UniversalDependencies/UD_English-PUD) の
評価用データ（各 1,000 文、ニュースと Wikipedia の文、CC BY-SA 3.0）と、
[UD_Korean-Kaist](https://github.com/UniversalDependencies/UD_Korean-Kaist) の
評価用データ（ニュース・小説・学術の 2,287 文、CC BY-SA 4.0）を使います。
`./download_resources.sh` が取得し、このリポジトリには含めていません。どれも、
litsea のモデル（UD Japanese-GSD、Korean-GSD、Chinese-GSD、English-EWT で学習）と、
lindera の jieba の辞書（UD Chinese-GSD と GSDSimp で学習）の学習データには
含まれていません。

UD の単位は統語上の語で、語の分け方の細部は言語ごとの文書に任せています（UD の
[分割の指針](https://universaldependencies.org/u/overview/tokenization.html)）。
すべての行を、その言語の UD のデータが持つ層で採点し、分割の基準が違う行どうしも
同じデータで読めるようにします。UD の語の層は適合率・再現率・F 値で、ほかの層は
F 値で示します。ある層と違う基準で分割する行は、その層の点数が低くなります。
どの行がどの基準で分割するかは、下の注記に書きます。行は UD の語の F 値の高い順に
並べます。

* 日本語: UD の日本語は、現代日本語書き言葉均衡コーパス（BCCWJ）と同じく、
  短単位・長単位・文節の 3 つの層で分割されています
  （[UD_Japanese-GSD の README](https://github.com/UniversalDependencies/UD_Japanese-GSD/blob/r2.19/README.md)）。
  * UD の語は短単位で、数詞を 1 語にまとめています。そのため採点の前に、数字
    だけのトークンが続くところを両側で 1 語にまとめます。UniDic の行と litsea は
    短単位に従います。`kytea` と `vaporetto`（同じ KyTea のモデル）は、さらに
    活用語の語幹と語尾を分けます。IPADIC の行と `rust-tinysegmenter` は IPADIC の
    単位、Sudachi の行は C モード（固有表現の単位）、`lindera` の `sudachidict` は
    Sudachi の分割モードを持たない SudachiDict の語彙で分割します。
  * 長単位は、各語の MISC の `LUWBILabel` から組み立てます。組み立てた長単位は、
    同じ文の長単位版である
    [UD_Japanese-PUDLUW](https://github.com/UniversalDependencies/UD_Japanese-PUDLUW)
    の語と一致します。長単位に従う行はありません。
  * 文節の区切り（MISC の `BunsetuBILabel`）は、どれも長単位と短単位の区切りでも
    あります。「保った文節の区切り」は、8,972 個の区切りのうち、その行のどの
    トークンにもまたがれていないものの割合で、除くトークンは何もまたぎません。
    どの行も 98.7 % 以上を保つので、行どうしの違いは主に文節の中をどこまで細かく
    切るかにあります。文節をまたぐトークンの多くは、2 つの文節の語をつなげた
    IPADIC の連語の項目（役に立つ、として）と、`lindera` の `sudachidict` の
    固有表現や慣用句（法の支配、トロイの木馬）です。
  * `lindera` の `ipadic` が `mecab` より高いのは、lindera 7.0.0 が未知語を `・` で
    区切り、正解のデータもカタカナの名前をそこで分ける（コリ・シューマン）ためです。
    MeCab は、IPADIC の `char.def` が `・` をカタカナの分類に入れているので、
    そうした名前を 1 つの未知語にします。`lindera` と `vibrato` の分割が違う
    106 か所のうち 104 か所が、そうした名前です。
* 韓国語: UD_Korean-Kaist の語は、句読点を切り離した語節（空白で区切られた
  単位）で、litsea は語節を出力し、ほかの行は形態素を出力します。形態素は、各語の
  見出し語を `+` で分けたものです（조약에 = 조약+에）。形態素は基本形で書かれて
  いるので、つなげても元の語に戻らない語（의해 = 의하+어）は、形態素の採点から
  両側で除きます。採点するのは 28,366 語のうち 23,517 語（82.9 %）です。文は
  PUD の文とは別のものです。UD_Korean-PUD は使いません。指定詞や一部の語尾・
  複合名詞を語節から分けるので（수준이지만 = 수준 + 이지만）、句読点でない語の
  うち語節と一致するのは 69.4 % だけで、残りも形態素ではありません。
* 中国語: UD_Chinese-PUD は繁体字で、Google が注釈を付けました。UD の
  [中国語の分割の文書](https://universaldependencies.org/zh/tokenization.html)
  には、この treebank の分割の基準の説明がありません。litsea と `lindera` の
  `jieba` は、同じく Google が注釈を付けた UD Chinese-GSD で学習しています。
  CC-CEDICT は分割の基準を持たない語の一覧で、smartcn は簡体字専用です。
* 英語: UD の[英語の文書](https://universaldependencies.org/en/index.html)は、
  縮約（do + n't、's）と、ハイフンでつないだ語の多く（search、-、engine）を
  語に分け、略語（U.S.）は分けません。「F 値」の列はこの語で、「F 値（トークン）」
  の列は分ける前のトークン（don't）で採点します。後者は UAX #29 の分け方です。

#### 日本語、UD_Japanese-PUD r2.19（短単位、長単位、文節）

| トークナイザ | 辞書・モデル | 適合率 [%] | 再現率 [%] | F 値 [%] | F 値（長単位） [%] | 保った文節の区切り [%] |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| vibrato | unidic-cwj-3.1.1 | 98.57 | 99.03 | 98.80 | 67.39 | 99.97 |
| vibrato | unidic-cwj-3.1.1+compact-dual | 98.55 | 99.00 | 98.77 | 67.40 | 99.97 |
| mecab | unidic-cwj-3.1.1 | 98.50 | 99.01 | 98.75 | 67.37 | 99.97 |
| mecab | unidic-cwj-202512 | 97.95 | 98.98 | 98.46 | 67.02 | 99.97 |
| lindera | unidic-cwj | 97.95 | 98.98 | 98.46 | 67.02 | 99.97 |
| lindera | unidic | 97.78 | 98.94 | 98.36 | 66.79 | 99.98 |
| lindera | unidic-csj | 97.70 | 98.76 | 98.23 | 66.91 | 99.97 |
| litsea (japanese) | japanese.model | 97.51 | 97.64 | 97.57 | 67.17 | 99.71 |
| litsea (japanese, two-stage) | japanese_pos.model | 97.42 | 97.60 | 97.51 | 67.12 | 99.71 |
| sudachi.rs | sudachi-dictionary-20261015-core | 96.28 | 93.12 | 94.68 | 71.50 | 99.94 |
| sudachi | sudachi-dictionary-20261015-core | 96.11 | 92.77 | 94.41 | 71.59 | 99.94 |
| lindera | ipadic | 94.99 | 91.88 | 93.41 | 70.18 | 99.45 |
| kuromoji (Lucene) | ipadic (bundled) | 94.94 | 91.87 | 93.38 | 70.15 | 99.45 |
| alyze (kuromoji) | ipadic (embedded) | 94.94 | 91.87 | 93.38 | 70.15 | 99.45 |
| mecab | ipadic 2.7.0 | 94.61 | 91.05 | 92.80 | 70.70 | 99.45 |
| vibrato | ipadic-mecab-2.7.0 | 94.61 | 91.05 | 92.80 | 70.70 | 99.45 |
| kuromoji (Atilika) | ipadic (bundled) | 94.48 | 90.91 | 92.66 | 70.70 | 99.44 |
| lindera | sudachidict | 94.26 | 90.02 | 92.09 | 72.84 | 99.78 |
| rust-tinysegmenter | - | 92.11 | 89.24 | 90.66 | 68.55 | 98.74 |
| vaporetto | kytea jp-0.4.7-5.mod | 81.02 | 89.09 | 84.87 | 57.27 | 99.89 |
| kytea | jp-0.4.7-5.mod | 81.00 | 89.09 | 84.85 | 57.27 | 99.92 |

#### 韓国語、UD_Korean-Kaist r2.19 test（語節、形態素）

| トークナイザ | 辞書・モデル | 適合率 [%] | 再現率 [%] | F 値 [%] | F 値（形態素） [%] |
| --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | korean.model | 99.99 | 100.00 | 99.99 | 18.15 |
| litsea (korean, two-stage) | korean_pos.model | 99.99 | 100.00 | 99.99 | 18.15 |
| nori (Lucene) | mecab-ko-dic (bundled) | 13.69 | 27.38 | 18.25 | 92.80 |
| alyze (nori) | mecab-ko-dic (embedded) | 13.69 | 27.38 | 18.25 | 92.80 |
| mecab | mecab-ko-dic 2.1.1-20180720 | 13.68 | 27.37 | 18.24 | 92.71 |
| mecab-ko | mecab-ko-dic 2.1.1-20180720 | 13.68 | 27.37 | 18.24 | 92.79 |
| lindera | ko-dic | 13.68 | 27.37 | 18.24 | 92.79 |

#### 中国語、UD_Chinese-PUD r2.19（繁体字）

| トークナイザ | 辞書・モデル | 適合率 [%] | 再現率 [%] | F 値 [%] |
| --- | --- | ---: | ---: | ---: |
| litsea (chinese) | chinese.model | 85.22 | 88.00 | 86.59 |
| litsea (chinese, two-stage) | chinese_pos.model | 85.03 | 88.08 | 86.52 |
| lindera | jieba | 82.53 | 88.80 | 85.55 |
| lindera | cc-cedict | 79.37 | 81.69 | 80.51 |
| alyze (smartcn) | smartcn (embedded) | 43.29 | 61.47 | 50.80 |

#### 英語、UD_English-PUD r2.19

| トークナイザ | 辞書・モデル | 適合率 [%] | 再現率 [%] | F 値 [%] | F 値（トークン） [%] |
| --- | --- | ---: | ---: | ---: | ---: |
| litsea (english, two-stage) | english_pos.model | 99.71 | 99.73 | 99.72 | 98.98 |
| litsea (english) | english.model | 99.62 | 99.64 | 99.63 | 98.89 |
| alyze (UAX #29) | - | 98.70 | 98.66 | 98.68 | 99.34 |

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
