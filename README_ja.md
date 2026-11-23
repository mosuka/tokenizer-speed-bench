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

## トークナイザ

表では、次のトークナイザを比べます。分割の方式は、次の 3 種類のどれかです。

* **辞書**: 文の中から辞書の語を引き、候補をラティスに並べ、合計のコストが最も
  小さい経路を Viterbi 法で選びます。単位は辞書の語なので、同じトークナイザでも
  辞書が違えば分割が変わります。
* **分類器**: 文字と文字の間ごとに、そこが語の境界かどうかを、周りの文字から
  判定します。判定のモデルは、分割済みのコーパスから学習したものです。辞書は
  要らず、単位は学習に使ったコーパスの単位になります。
* **規則**: 規則が定める語の境界で分割します。

| トークナイザ | 実装の言語 | 種類 | 方式 | 表にある言語 |
| --- | --- | --- | --- | --- |
| [mecab](https://github.com/taku910/mecab) | C++ | 辞書 | コストを条件付き確率場（CRF）で学習 | 日本語、韓国語 |
| [mecab-ko](https://bitbucket.org/eunjeon/mecab-ko) | C++ | 辞書 | 韓国語向けの MeCab の fork で、空白の後の一部の品詞のコストを上げる | 韓国語 |
| [lindera](https://github.com/lindera/lindera) | Rust | 辞書 | kuromoji-rs から fork したもので、出どころの違う多くの辞書を読む | 日本語、韓国語、中国語 |
| [vibrato](https://github.com/daac-tools/vibrato) | Rust | 辞書 | Viterbi 法の高速な実装 | 日本語 |
| [sudachi](https://github.com/WorksApplications/Sudachi) | Java | 辞書 | 3 つの分割モード（A、B、C）を持ち、表には 3 つとも載せる | 日本語 |
| [sudachi.rs](https://github.com/WorksApplications/sudachi.rs) | Rust | 辞書 | Sudachi の Rust の実装で、表には 3 つのモードとも載せる | 日本語 |
| [kuromoji (Atilika)](https://github.com/atilika/kuromoji) | Java | 辞書 | jar に IPADIC を同梱 | 日本語 |
| [kuromoji (Lucene)](https://lucene.apache.org/) | Java | 辞書 | Lucene の日本語の解析モジュールで、IPADIC を同梱 | 日本語 |
| [nori (Lucene)](https://lucene.apache.org/) | Java | 辞書 | Lucene の韓国語の解析モジュールで、mecab-ko-dic を同梱 | 韓国語 |
| [alyze](https://github.com/turbopuffer/alyze) | Rust | 辞書、規則 | Lucene の kuromoji・nori の移植と、smartcn（簡体字向けの、ICTCLAS の辞書の上の隠れマルコフモデル）の移植、UAX #29 のトークナイザ（規則） | 日本語、韓国語、中国語、英語 |
| [kytea](https://github.com/neubig/kytea) | C++ | 分類器 | SVM かロジスティック回帰による点予測 | 日本語 |
| [vaporetto](https://github.com/daac-tools/vaporetto) | Rust | 分類器 | 点予測で、KyTea のモデルを読む | 日本語 |
| [rust-tinysegmenter](https://github.com/woxtu/rust-tinysegmenter) | Rust | 分類器 | TinySegmenter の Rust の実装。モデルはブースティングで学習したもので、MeCab と IPADIC と同じ単位で分割する | 日本語 |
| [litsea](https://github.com/mosuka/litsea) | Rust | 分類器 | TinySegmenter に着想を得た AdaBoost。two-stage のモデルは、境界と品詞を平均化パーセプトロンで学習する | 日本語、韓国語、中国語、英語 |

一部の行を計測した条件（版、設定、辞書）は、[計測結果](#計測結果)の注記に
書いています。

## 計測結果

2026-11-24 に以下の環境で計測しました。

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
除いて同じ分かち書きをします。4 行のうち 2 行は、ハイフン（-）の並びの切り方
だけが違います。一致の表はほかの句読点と同じくこれを除くので、違う行を 2 行と数えます。
コーパスは書き言葉なので、`unidic-csj` が想定
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
どちらも、Sudachi の 3 つの分割モードのそれぞれで計測しています。A が最も短く、
C が最も長い単位（固有表現）で、B はその間です。たとえば「選挙 / 管理 / 委員 / 会」、
「選挙 / 管理 / 委員会」、「選挙管理委員会」と切ります。モードはベンチの引数で渡す
ので、どのモードも同じ実行ファイルと同じ辞書で動きます。sudachi.rs は、A と B の
モードでは、辞書の分割の情報も読み、選んだ経路の語をさらに分けます。この計測では、
C モードより約 5 % 遅く、Java 版のモードの差は 1 % 未満でした。
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
| vaporetto | 0.7.0 | kytea jp-0.4.7-5.mod | 80.6 MB | 25,291,199 | 1,252,521 | 188.7 MB |
| litsea (japanese) | 0.16.0 | japanese.model | 1.1 MB | 16,771,086 | 654,894 | 12.0 MB |
| litsea (japanese, two-stage) | 0.16.0 | japanese_pos.model | 5.4 MB | 8,284,612 | 283,158 | 44.9 MB |
| vibrato | 0.5.3 | ipadic-mecab-2.7.0 | 45.6 MB | 7,955,519 | 202,753 | 68.8 MB |
| lindera | 7.0.0 | ipadic | 45.3 MB | 6,735,160 | 332,238 | 18.2 MB |
| mecab | thirdparty submodule | ipadic 2.7.0 | 50.5 MB | 6,489,178 | 238,194 | 33.2 MB |
| lindera | 7.0.0 | unidic | 189.9 MB | 4,654,131 | 225,912 | 90.9 MB |
| alyze (kuromoji) | 0.2.0 | ipadic (embedded) | 12.5 MB | 4,598,344 | 191,778 | 18.0 MB |
| vibrato | 0.5.3 | unidic-cwj-3.1.1 | 684.2 MB | 4,127,407 | 157,933 | 723.7 MB |
| lindera | 7.0.0 | sudachidict | 564.9 MB | 3,708,021 | 180,040 | 155.0 MB |
| rust-tinysegmenter | 0.1.1 | - | - | 2,755,798 | 71,232 | 3.8 MB |
| kuromoji (Lucene) | 10.6.0 | ipadic (bundled) | 8.7 MB | 2,642,382 | 61,431 | 110.6 MB |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 122.3 MB | 2,625,467 | 48,428 | 736.5 MB |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 691.0 MB | 2,439,133 | 81,882 | 371.1 MB |
| kuromoji (Atilika) | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 31.9 MB | 2,286,190 | 87,307 | 340.7 MB |
| lindera | 7.0.0 | unidic-cwj | 1,244.3 MB | 2,178,620 | 69,974 | 1,009.5 MB |
| lindera | 7.0.0 | unidic-csj | 1,264.6 MB | 2,172,487 | 70,574 | 1,029.9 MB |
| sudachi.rs (mode C) | git tag `v0.7.0` | sudachi-dictionary-20261015-core | 192.9 MB | 1,823,303 | 60,043 | 176.0 MB |
| sudachi.rs (mode B) | git tag `v0.7.0` | sudachi-dictionary-20261015-core | 192.9 MB | 1,729,287 | 52,311 | 178.6 MB |
| sudachi.rs (mode A) | git tag `v0.7.0` | sudachi-dictionary-20261015-core | 192.9 MB | 1,723,738 | 46,736 | 178.5 MB |
| vibrato | 0.5.3 | unidic-cwj-3.1.1+compact-dual | 286.4 MB | 1,616,795 | 43,324 | 326.1 MB |
| mecab | thirdparty submodule | unidic-cwj-202512 | 1,252.8 MB | 1,583,978 | 60,187 | 484.8 MB |
| sudachi (mode C) | 0.8.2 | sudachi-dictionary-20261015-core | 192.9 MB | 812,058 | 20,388 | 567.2 MB |
| sudachi (mode A) | 0.8.2 | sudachi-dictionary-20261015-core | 192.9 MB | 809,642 | 22,758 | 569.6 MB |
| sudachi (mode B) | 0.8.2 | sudachi-dictionary-20261015-core | 192.9 MB | 807,738 | 21,108 | 567.5 MB |

### 韓国語（`mujeong.txt`、320,850 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | 0.16.0 | korean.model | 0.1 MB | 24,165,244 | 935,163 | 4.2 MB |
| litsea (korean, two-stage) | 0.16.0 | korean_pos.model | 3.9 MB | 7,659,927 | 363,724 | 32.4 MB |
| mecab | thirdparty submodule | mecab-ko-dic 2.1.1-20180720 | 96.7 MB | 3,680,142 | 142,842 | 69.8 MB |
| lindera | 7.0.0 | ko-dic | 81.6 MB | 3,553,845 | 114,768 | 83.8 MB |
| alyze (nori) | 0.2.0 | mecab-ko-dic (embedded) | 43.2 MB | 2,647,757 | 108,910 | 48.1 MB |
| mecab-ko | 0.996-ko-0.9.2 | mecab-ko-dic 2.1.1-20180720 | 96.7 MB | 1,693,673 | 89,784 | 69.7 MB |
| nori (Lucene) | 10.6.0 | mecab-ko-dic (bundled) | 23.9 MB | 1,374,605 | 41,917 | 157.7 MB |

### 中国語（`rulin_waishi.txt`、328,153 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (chinese) | 0.16.0 | chinese.model | 1.9 MB | 16,169,060 | 694,823 | 19.2 MB |
| lindera | 7.0.0 | cc-cedict | 22.1 MB | 14,705,012 | 817,127 | 9.8 MB |
| lindera | 7.0.0 | jieba | 49.0 MB | 10,632,285 | 671,145 | 22.2 MB |
| litsea (chinese, two-stage) | 0.16.0 | chinese_pos.model | 8.0 MB | 6,247,305 | 189,767 | 56.1 MB |
| alyze (smartcn) | 0.2.0 | smartcn (embedded) | 4.5 MB | 5,402,345 | 213,488 | 22.1 MB |

### 英語（`pride_and_prejudice.txt`、677,531 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| alyze (UAX #29) | 0.2.0 | - | - | 326,090,911 | 22,143,797 | 3.0 MB |
| litsea (english) | 0.16.0 | english.model | 0.1 MB | 33,282,114 | 1,104,369 | 4.6 MB |
| litsea (english, two-stage) | 0.16.0 | english_pos.model | 2.9 MB | 12,183,420 | 338,517 | 23.7 MB |

これらの数値は計測環境（CPU、メモリ帯域、OS スケジューラ、JIT/JVM の
ウォームアップ）に大きく依存するため、絶対的なベンチマークとしてでは
なく、同一の実行で一緒に計測されたトークナイザ間の比較にのみ使用して
ください。上記の手順どおり `./run_all.sh | tee ./results` と
`./stats.py < ./results` で再現できます。

## 分割の精度

2026-11-24 に上と同じ環境で、`./segment_all.sh` で計測しました。各行は、速度の
表と同じ実行ファイル・同じ設定で分かち書きします。`BENCH_TOKENS=<ファイル>` を
付けて実行すると、各ベンチは時間を測るループの後に入力をもう一度分かち書きして
トークンを書き出し、`segmentation.py` がそれを採点します。

トークンは、相手側のトークンとまったく同じ文字の範囲を覆うときに正解と数えます。
適合率はその行のトークンに対する割合、再現率はリファレンス実装または正解の
データのトークンに対する割合です。採点の前に、最初の文字が空白・句読点・記号・
制御文字のトークンを両側から除きます。これは Lucene の kuromoji と nori が句読点を
捨てる規則で、句読点を捨てる行と残す行を比べられるようにするためです。割合は
小数第 2 位まで示し、100.00 と示すのは完全に一致したときだけです。100 % 未満で
四捨五入すると 100.00 になる値は、99.99 と示します。

### 指標の読み方

この節の指標に詳しくない人に向けて、1 つの例文で読み方を説明します。正確な定義は、
下の各節にあります。

**正解のデータの単位**: 日本語の「単語」の切り方は辞書ごとに違い、どれか 1 つが
正しいわけではありません。日本語の正解のデータは、同じ文を 3 つの大きさの単位で
切ったものを持ち、大きい単位は小さい単位を丸ごと組み合わせたものです。例文
「国際連合で猫を見た。」の場合は次のとおりです。

| 単位 | 切り方 | どんな単位か |
| --- | --- | --- |
| 短単位 | 国際 / 連合 / で / 猫 / を / 見 / た / 。 | いちばん細かい単位 |
| 長単位 | 国際連合 / で / 猫 / を / 見 / た / 。 | 複合語などを 1 つにまとめた単位 |
| 文節 | 国際連合で / 猫を / 見た。 | 「ね」を挟める区切り（国際連合でね、猫をね、見たね） |

短単位で切る辞書（UniDic）も、もっと長く切る辞書（IPADIC、C モードの
Sudachi）も、この範囲のどこかで切っています。韓国語の表も同じように読めます。
形態素が小さい単位、語節（空白で区切られた単位）が大きい単位です。

**単位の F 値**: ある大きさの単位にどれだけ従って切れているかの点数です。
適合率は、その行が出したトークンのうち、その単位と完全に一致したものの割合
（出したものの正確さ）で、再現率は、その単位のうち、その行が当てたものの割合
（取りこぼしの少なさ）です。F 値は 2 つをまとめた数で、両方が高いときだけ高く
なります。「国際連合 / で / 猫 / を / 見 / た」と切る行は、短単位では「国際連合」が
正解（国際・連合）に無いので 76.9 % で、長単位では 100 % です。このように、F 値は
どちらの基準に合わせた辞書かで変わり、低くても誤りとは限りません。

**区切り**: 語と語の境目のことです。

| 指標 | 何の割合か | 下がるのはどんなときか |
| --- | --- | --- |
| 短単位の区切りで切った割合 | その行が入れた区切りのうち、短単位の区切りでもあるもの | 語の途中で切ったとき |
| 保った長単位の区切り | 長単位の区切りのうち、その行のどのトークンにもまたがれていないもの | 長単位をまたいでくっつけたとき |
| 保った文節の区切り | 文節の区切りのうち、その行のどのトークンにもまたがれていないもの | 文節をまたいでくっつけたとき（ほとんどの基準で誤り） |

上の例文を 4 通りに切り、`segmentation.py` で採点した値です（%）。

| 切り方 | F 値（短単位） | 短単位の区切りで切った割合 | F 値（長単位） | 保った長単位の区切り | 保った文節の区切り |
| --- | ---: | ---: | ---: | ---: | ---: |
| A: 国際 / 連合 / で / 猫 / を / 見 / た / 。 | 100.0 | 100.0 | 76.9 | 100.0 | 100.0 |
| B: 国際連合 / で / 猫 / を / 見 / た / 。 | 76.9 | 100.0 | 100.0 | 100.0 | 100.0 |
| C: 国際 / 連 / 合 / で / 猫 / を / 見 / た / 。 | 80.0 | 87.5 | 71.4 | 100.0 | 100.0 |
| D: 国際連合で猫 / を / 見た / 。 | 20.0 | 100.0 | 22.2 | 50.0 | 50.0 |

* A は短単位に、B は長単位に従います。F 値は基準によって分かれますが、どちらも
  区切りをすべて保つので、どちらも正しく切れています。
* C は「連合」の途中で切るので、短単位の区切りで切った割合が下がります。下の表
  では、`kytea` が「い / る」と切るため、ここが 91 % です。
* D は正しい位置でしか切らないので、短単位の区切りで切った割合は 100 % ですが、
  長単位と文節の区切りをまたいでくっつけています。

「短単位の区切りで切った割合」と「保った長単位の区切り」がどちらも 100 % に近い
行は、辞書の基準が何であれ、短単位と長単位の間のどこかの細かさで正しく切れて
います。この 2 つで、基準の違う辞書を公平に比べられます。2 つの F 値は、その行が
どちらの基準に近いかを表します。

**一致の F 値**: 正解のデータの代わりに、同じ辞書のリファレンス実装（MeCab など）の
出力を正解とみなして計算した F 値です。100 % なら、両者は同じように切っています。
「違う行」は、速度の表のコーパスの行のうち、1 か所でも切り方が違う行の数です。
一致は、実装がリファレンス実装をどれだけ忠実に再現しているかを表すもので、切り方が
正しいかは表しません。

### リファレンス実装との一致

同じ辞書またはモデルを読む行を、そのリファレンス実装と、速度の表のコーパスで
比べます。一致は、実装がリファレンス実装をどれだけ再現しているかを示すもので、
分かち書きが正しいかは示しません。`kuromoji (Lucene)` と `alyze (kuromoji)`、
`nori (Lucene)` と `alyze (nori)`、`ko-dic` の `lindera` と `mecab-ko` は、
それぞれ同じトークンを書き出します。`lindera` の `ipadic` は、`mecab` が読む IPADIC と同じ版の後の
アーカイブ（`mecab-ipadic-2.7.0-20250920`。`mecab` は 2.7.0-20070801）から
作られています。vibrato のリリースノートによると、`ipadic-mecab-2.7.0` は
IPADIC v2.7.0 から作られています。`lindera` の `sudachidict` は `sudachi` と
比べません。`lindera` の `sudachidict` は small・core・notcore の語彙を持つ
SudachiDict 20260723 で、Sudachi の分割モードを使わずに分割します。一方
`sudachi` は 20261015 の core の辞書を読み、それぞれの分割モードで分割します。
`sudachi.rs` は、同じモードの `sudachi` と比べます。

#### IPADIC（リファレンス実装: mecab、ipadic 2.7.0）

| トークナイザ | 辞書・モデル | 一致の F 値 [%] | 違う行 |
| --- | --- | ---: | ---: |
| lindera | ipadic | 99.96 | 2,346 行中 30 行 |
| vibrato | ipadic-mecab-2.7.0 | 99.99 | 2,346 行中 1 行 |
| kuromoji (Atilika) | ipadic (bundled) | 99.34 | 2,346 行中 426 行 |
| kuromoji (Lucene) | ipadic (bundled) | 99.41 | 2,346 行中 398 行 |
| alyze (kuromoji) | ipadic (embedded) | 99.41 | 2,346 行中 398 行 |

#### UniDic CWJ 3.1.1（リファレンス実装: mecab、unidic-cwj-3.1.1）

| トークナイザ | 辞書・モデル | 一致の F 値 [%] | 違う行 |
| --- | --- | ---: | ---: |
| vibrato | unidic-cwj-3.1.1 | 99.98 | 2,346 行中 6 行 |
| vibrato | unidic-cwj-3.1.1+compact-dual | 99.97 | 2,346 行中 15 行 |

#### UniDic CWJ 202512（リファレンス実装: mecab、unidic-cwj-202512）

| トークナイザ | 辞書・モデル | 一致の F 値 [%] | 違う行 |
| --- | --- | ---: | ---: |
| lindera | unidic-cwj | 99.99 | 2,346 行中 2 行 |

#### mecab-ko-dic 2.1.1（リファレンス実装: mecab-ko、mecab-ko-dic 2.1.1-20180720）

| トークナイザ | 辞書・モデル | 一致の F 値 [%] | 違う行 |
| --- | --- | ---: | ---: |
| mecab | mecab-ko-dic 2.1.1-20180720 | 99.50 | 3,967 行中 329 行 |
| lindera | ko-dic | 100.00 | 3,967 行中 0 行 |
| nori (Lucene) | mecab-ko-dic (bundled) | 99.80 | 3,967 行中 132 行 |
| alyze (nori) | mecab-ko-dic (embedded) | 99.80 | 3,967 行中 132 行 |

#### SudachiDict 20261015 core、A モード（リファレンス実装: sudachi (mode A)、sudachi-dictionary-20261015-core）

| トークナイザ | 辞書・モデル | 一致の F 値 [%] | 違う行 |
| --- | --- | ---: | ---: |
| sudachi.rs (mode A) | sudachi-dictionary-20261015-core | 99.73 | 2,346 行中 192 行 |

#### SudachiDict 20261015 core、B モード（リファレンス実装: sudachi (mode B)、sudachi-dictionary-20261015-core）

| トークナイザ | 辞書・モデル | 一致の F 値 [%] | 違う行 |
| --- | --- | ---: | ---: |
| sudachi.rs (mode B) | sudachi-dictionary-20261015-core | 99.73 | 2,346 行中 192 行 |

#### SudachiDict 20261015 core、C モード（リファレンス実装: sudachi (mode C)、sudachi-dictionary-20261015-core）

| トークナイザ | 辞書・モデル | 一致の F 値 [%] | 違う行 |
| --- | --- | ---: | ---: |
| sudachi.rs (mode C) | sudachi-dictionary-20261015-core | 99.73 | 2,346 行中 192 行 |

#### KyTea model jp-0.4.7-5（リファレンス実装: kytea、jp-0.4.7-5.mod）

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
同じデータで読めるようにします。日本語（短単位・長単位・文節）と韓国語（形態素・
語節）の層は細かい順に並び、ある層の単位は、より細かい層の単位を丸ごと組み
合わせたものです。各層を次の 2 通りで採点します。

* 単位の F 値: その行がその層の基準にどれだけ従っているか。違う基準で分割する
  行は、その層の点数が低くなります。どの行がどの基準で分割するかは、下の注記に
  書きます。
* 最も細かい層の「区切りで切った割合」は、その行の区切り（文の中にあるトークンの
  端）のうち、その層の区切りでもあるものの割合です。その層の単位の中を切ると
  下がります。それより粗い層の「保った区切り」は、その層の区切りのうち、その行の
  どのトークンにもまたがれていないものの割合です。その層の単位をまたいでまとめると
  下がります。

区切りがすべて短単位の区切りで、長単位の区切りをすべて保つ行は、基準が何であれ、
短単位と長単位の間の細かさで分割しています。粗い層の「区切りで切った割合」と、
文節の F 値は載せません。どの行もこれらの層より細かく切るので、これらの値は
誤りではなく、どこまで細かく切るかを表すだけだからです。層が 1 つの中国語と、
語とトークンを持つ英語は、UD の語の適合率・再現率・F 値で示します。行は最初の層の
F 値の高い順に並べます。

* 日本語: UD の日本語は、現代日本語書き言葉均衡コーパス（BCCWJ）と同じく、
  短単位・長単位・文節の 3 つの層で分割されています
  （[UD_Japanese-GSD の README](https://github.com/UniversalDependencies/UD_Japanese-GSD/blob/r2.19/README.md)）。
  * UD の語は短単位で、数詞を 1 語にまとめています。そのため採点の前に、数字
    だけのトークンが続くところを両側で 1 語にまとめます。UniDic の行、litsea、
    Sudachi の A モードは短単位に従います（A モードは 98.5〜98.7 %）。`kytea` と
    `vaporetto`（同じ KyTea のモデル）は、さらに活用語の語幹と語尾を分けます。
    IPADIC の行と `rust-tinysegmenter` は IPADIC の単位、Sudachi の B・C モードは
    より長い単位（C は固有表現の単位）、`lindera` の `sudachidict` は Sudachi の
    分割モードを持たない SudachiDict の語彙で分割します。
  * 長単位は、各語の MISC の `LUWBILabel` から組み立てます。組み立てた長単位は、
    同じ文の長単位版である
    [UD_Japanese-PUDLUW](https://github.com/UniversalDependencies/UD_Japanese-PUDLUW)
    の語と一致します。長単位に従う行はありません。
  * 文節の区切り（MISC の `BunsetuBILabel`）は、どれも長単位と短単位の区切りでも
    あります。除くトークンはどの区切りもまたがず、区切りは採点するトークンの
    ものだけを数えます。
  * `kytea`、`vaporetto`、`rust-tinysegmenter` 以外の行は、区切りの 98.7 % 以上が
    短単位の区切りです。また、どの行も長単位の区切りの 98.8 % 以上と、8,972 個の
    文節の区切りの 98.7 % 以上を保ちます。IPADIC の行と Sudachi の B・C モードの
    短単位の点数が低いのは、単位が長いためで、間違った所で切るためではありません。
    `kytea` と `vaporetto` は短単位の中を切り（い / る）、`rust-tinysegmenter` は
    両方で下がります。文節をまたぐトークンの多くは、2 つの文節の語をつなげた IPADIC の
    連語の項目（役に立つ、として）と、`lindera` の `sudachidict` の固有表現や
    慣用句（法の支配、トロイの木馬）です。
  * `lindera` の `ipadic` が `mecab` より高いのは、lindera 7.0.0 が未知語を `・` で
    区切り、正解のデータもカタカナの名前をそこで分ける（コリ・シューマン）ためです。
    MeCab は、IPADIC の `char.def` が `・` をカタカナの分類に入れているので、
    そうした名前を 1 つの未知語にします。`lindera` と `vibrato` の分割が違う
    106 か所のうち 104 か所が、そうした名前です。
* 韓国語: UD_Korean-Kaist の語は、句読点を切り離した語節（空白で区切られた
  単位）で、litsea は語節を出力し、ほかの行は形態素を出力します。形態素は、各語の
  見出し語を `+` で分けたものです（조약에 = 조약+에）。形態素は基本形で書かれて
  いるので、つなげても元の語に戻らない語（의해 = 의하+어）は、形態素の採点から
  両側で除きます。採点するのは 28,366 語のうち 23,517 語（82.9 %）で、除く語の
  中の区切りは数えません。mecab-ko-dic の行は区切りの 97.6 %、litsea は約
  48,000 か所の区切りのうち 1〜2 か所を除くすべてが形態素の区切りで、どの行も
  語節の区切りをすべて保ちます。文は PUD の文とは別のものです。UD_Korean-PUD は
  使いません。指定詞や一部の語尾・複合名詞を語節から分けるので
  （수준이지만 = 수준 + 이지만）、句読点でない語の
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

| トークナイザ | 辞書・モデル | F 値（短単位） [%] | 短単位の区切りで切った割合 [%] | F 値（長単位） [%] | 保った長単位の区切り [%] | 保った文節の区切り [%] |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| vibrato | unidic-cwj-3.1.1 | 98.80 | 99.33 | 67.39 | 99.97 | 99.97 |
| vibrato | unidic-cwj-3.1.1+compact-dual | 98.77 | 99.32 | 67.40 | 99.97 | 99.97 |
| mecab | unidic-cwj-3.1.1 | 98.75 | 99.29 | 67.37 | 99.97 | 99.97 |
| sudachi.rs (mode A) | sudachi-dictionary-20261015-core | 98.73 | 99.44 | 67.26 | 99.93 | 99.97 |
| sudachi (mode A) | sudachi-dictionary-20261015-core | 98.47 | 99.44 | 67.34 | 99.95 | 99.97 |
| mecab | unidic-cwj-202512 | 98.46 | 98.86 | 67.02 | 99.98 | 99.97 |
| lindera | unidic-cwj | 98.46 | 98.86 | 67.02 | 99.98 | 99.97 |
| lindera | unidic | 98.36 | 98.78 | 66.79 | 99.98 | 99.98 |
| lindera | unidic-csj | 98.23 | 98.77 | 66.91 | 99.96 | 99.97 |
| litsea (japanese) | japanese.model | 97.57 | 99.00 | 67.17 | 99.75 | 99.71 |
| litsea (japanese, two-stage) | japanese_pos.model | 97.51 | 98.95 | 67.12 | 99.76 | 99.71 |
| sudachi.rs (mode B) | sudachi-dictionary-20261015-core | 95.31 | 99.79 | 70.88 | 99.92 | 99.94 |
| sudachi (mode B) | sudachi-dictionary-20261015-core | 95.04 | 99.79 | 70.97 | 99.93 | 99.94 |
| sudachi.rs (mode C) | sudachi-dictionary-20261015-core | 94.68 | 99.81 | 71.50 | 99.91 | 99.94 |
| sudachi (mode C) | sudachi-dictionary-20261015-core | 94.41 | 99.81 | 71.59 | 99.93 | 99.94 |
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

#### 韓国語、UD_Korean-Kaist r2.19 test（形態素、語節）

| トークナイザ | 辞書・モデル | F 値（形態素） [%] | 形態素の区切りで切った割合 [%] | F 値（語節） [%] | 保った語節の区切り [%] |
| --- | --- | ---: | ---: | ---: | ---: |
| nori (Lucene) | mecab-ko-dic (bundled) | 92.80 | 97.61 | 18.25 | 100.00 |
| alyze (nori) | mecab-ko-dic (embedded) | 92.80 | 97.61 | 18.25 | 100.00 |
| mecab-ko | mecab-ko-dic 2.1.1-20180720 | 92.79 | 97.61 | 18.24 | 100.00 |
| lindera | ko-dic | 92.79 | 97.61 | 18.24 | 100.00 |
| mecab | mecab-ko-dic 2.1.1-20180720 | 92.71 | 97.58 | 18.24 | 100.00 |
| litsea (korean) | korean.model | 18.15 | 99.99 | 99.99 | 100.00 |
| litsea (korean, two-stage) | korean_pos.model | 18.15 | 99.99 | 99.99 | 100.00 |

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
