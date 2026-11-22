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

スクリプトは Linux と macOS で動きます。下の結果は Linux で計測しています。
Rust と以下のパッケージを入れてから、上のコマンドを実行します。
Ubuntu では、`./compile_all.sh` が確かめる `libtool` コマンドは
`libtool-bin` に、`./run_all.sh` がピークメモリの計測に使う
`/usr/bin/time` は `time` に入っています。

```sh
% sudo apt install build-essential patch autoconf automake \
    libtool libtool-bin default-jdk-headless maven \
    wget unzip xz-utils time
```

macOS では、Rust、JDK、Xcode Command Line Tools と、
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

2026-11-22 に以下の環境で計測しました。

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
`ipadic`・`unidic` に加えて `cc-cedict`（中国語）、`jieba`（中国語）、
`ko-dic`（韓国語）の辞書もカバーしています。lindera 6.1.0 から、ko-dic は
mecab-ko の左側の空白に対するペナルティを既定で適用するようになり、
`ko-dic` の行はこの既定のまま計測しています。lindera 7.0.0 は、6.2.0 より
MeCab に近い分かち書きをします。空白を lattice（ラティス）から外し、行の中で
`、` と `。` をまたいで文脈をつなぎ、未知語を MeCab と同じように作り、`・` で
未知語を区切ります。CC-CEDICT と Jieba の辞書も、新しいソースから作り直されて
います。これらのコーパスでのトークン数は、6.2.0 と比べて ipadic で +441、
unidic で +166、cc-cedict で -6、jieba で +13,958、ko-dic で -257 変わります。

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

辞書・モデルサイズ（Dictionary / Model Size）は、各トークナイザが実行時に
実際に開くファイルのディスク上のサイズであり、実行時のメモリ使用量では
ありません。開いたファイルは `strace` で確かめました。小さな設定ファイル
（MeCab の `mecabrc` と `dicrc`、lindera の `metadata.json` など）は含めて
いません。ディストリビューションによっては辞書と一緒に実行時には使われない
データが同梱されていますが、
それらは除外しています（例: MeCab の辞書ディレクトリに含まれる生の CSV 語彙
ソース、評価用データ、ライセンスファイル、コンパイル・学習専用の
`model.bin` や `*.def` ソース。Tagger 自身が開くのはコンパイル済みの
`sys.dic`/`matrix.bin`/`char.bin`/`unk.dic` のみです。kuromoji の辞書は
圧縮された `.jar` ではなく展開後の `.bin` ファイルで、vibrato の
`system.dic.zst` は実際にメモリ上に保持される展開後のサイズで計測して
います）。辞書を実行ファイルに埋め込むトークナイザは、埋め込んだデータの
サイズです。vaporetto はビルドスクリプトが KyTea のモデルから変換した
predictor、alyze はビルドスクリプトが alyze の GitHub リリースから取得して
SHA-256 で照合する辞書ファイル（アーカイブからライセンスと NOTICE を除いた
もの）です。1 MB は 1,048,576 バイトです。ピークメモリ（Peak Memory）は、
GNU time（`/usr/bin/time -v`）で各反復をラップして計測したベンチマークプロセス全体の
最大常駐セットサイズ（RSS）です。そのため、Speed が計測する分かち書き
ループだけでなく、辞書の読み込みも含まれます。全エンジンをこの方法で
計測しており、Java の 2 エンジンも Maven 自身のメモリが計上されないよう
`mvn exec:java` ではなく `java -cp` で直接起動しています。

### 日本語（`wagahaiwa_nekodearu.txt`、372,573 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| vaporetto | 0.7.0 | kytea jp-0.4.7-5.mod | 80.6 MB | 24,529,346 | 1,325,511 | 188.5 MB |
| litsea (japanese) | 0.16.0 | japanese.model | 1.1 MB | 16,231,000 | 978,470 | 11.9 MB |
| litsea (japanese, two-stage) | 0.16.0 | japanese_pos.model | 5.4 MB | 7,879,683 | 422,145 | 44.7 MB |
| vibrato | 0.5.3 | ipadic-mecab-2.7.0 | 45.6 MB | 7,396,521 | 376,945 | 68.7 MB |
| lindera | 7.0.0 | ipadic | 45.3 MB | 6,491,705 | 384,348 | 18.3 MB |
| mecab | thirdparty submodule | ipadic 2.7.0 | 50.5 MB | 6,260,699 | 403,827 | 33.7 MB |
| lindera | 7.0.0 | unidic | 189.9 MB | 4,527,248 | 272,086 | 90.9 MB |
| alyze (kuromoji) | 0.2.0 | ipadic (embedded) | 12.5 MB | 4,418,573 | 237,108 | 17.9 MB |
| vibrato | 0.5.3 | unidic-cwj-3.1.1 | 684.2 MB | 3,536,769 | 279,099 | 723.3 MB |
| rust-tinysegmenter | 0.1.1 | - | - | 2,700,535 | 97,215 | 3.7 MB |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 122.3 MB | 2,433,187 | 140,828 | 736.3 MB |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 691.0 MB | 2,246,609 | 169,726 | 371.4 MB |
| kuromoji | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 31.9 MB | 2,128,035 | 93,479 | 340.8 MB |
| sudachi.rs | git tag `v0.7.0` | sudachi-dictionary-20261015-core | 192.9 MB | 1,681,922 | 110,772 | 175.8 MB |
| vibrato | 0.5.3 | unidic-cwj-3.1.1+compact-dual | 286.4 MB | 1,474,615 | 75,764 | 325.7 MB |
| mecab | thirdparty submodule | unidic-cwj-202512 | 1,252.8 MB | 1,434,051 | 95,986 | 484.9 MB |
| sudachi | 0.8.2 | sudachi-dictionary-20261015-core | 192.9 MB | 756,611 | 32,729 | 567.4 MB |

### 韓国語（`mujeong.txt`、320,850 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | 0.16.0 | korean.model | 0.1 MB | 23,229,540 | 1,495,830 | 4.1 MB |
| litsea (korean, two-stage) | 0.16.0 | korean_pos.model | 3.9 MB | 7,326,074 | 435,103 | 32.2 MB |
| lindera | 7.0.0 | ko-dic | 81.6 MB | 3,483,359 | 135,335 | 83.6 MB |
| alyze (nori) | 0.2.0 | mecab-ko-dic (embedded) | 43.2 MB | 2,496,290 | 135,221 | 47.7 MB |

### 中国語（`rulin_waishi.txt`、328,153 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (chinese) | 0.16.0 | chinese.model | 1.9 MB | 15,735,132 | 860,786 | 19.1 MB |
| lindera | 7.0.0 | cc-cedict | 22.1 MB | 13,922,220 | 1,100,910 | 9.7 MB |
| lindera | 7.0.0 | jieba | 49.0 MB | 10,144,422 | 776,767 | 22.3 MB |
| litsea (chinese, two-stage) | 0.16.0 | chinese_pos.model | 8.0 MB | 5,861,685 | 322,936 | 55.9 MB |
| alyze (smartcn) | 0.2.0 | smartcn (embedded) | 4.5 MB | 5,110,060 | 339,849 | 22.0 MB |

### 英語（`pride_and_prejudice.txt`、677,531 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| alyze (UAX #29) | 0.2.0 | - | - | 298,534,085 | 30,991,909 | 3.0 MB |
| litsea (english) | 0.16.0 | english.model | 0.1 MB | 31,675,670 | 2,039,685 | 4.5 MB |
| litsea (english, two-stage) | 0.16.0 | english_pos.model | 2.9 MB | 11,684,650 | 505,312 | 23.6 MB |

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
