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

### 計測

各トークナイザの速度を計測するには、以下のコマンドを実行します。
`./run_all.sh` を途中で停止した場合でも、`./stats.py` はその時点までの
結果から統計を算出します。

```sh
% ./run_all.sh | tee ./results
% ./stats.py < ./results
```

## 計測結果

2026-09-28 に以下の環境で計測しました。

* CPU: Intel Core i7-1185G7（4 コア / 8 スレッド、最大 4.8GHz）
* メモリ: 32GiB
* OS: Ubuntu 24.04.5 LTS, Linux 6.8.0-142-generic
* ツールチェーン: rustc 1.98.0, OpenJDK 21.0.12.1, Apache Maven 3.8.7,
  g++ 13.3.0

各トークナイザはコーパスを 100 回分かち書きします（ウォームアップ 1 回を
実施し、統計からは除外）。速度（Speed）は 1 秒あたりの処理文字数で、
大きいほど高速です。標準偏差（Std dev）は 100 回の反復にわたる
母標準偏差です。

litsea 0.13.0 では、以前の `litsea (*, POS)` の行が計測していた
joint POS アーキテクチャが削除されたため、その行はなくなりました。
二段構成（two-stage）が litsea で唯一の分かち書き＋品詞付与の
パイプラインとなり、同梱モデルの名前は `*_two_stage.model` から
`*_pos.model` に変わりました。日本語と中国語のファイルは 0.12.0 のものと
バイト単位で同一です。`litsea (*, two-stage)` は
`Segmenter::with_two_stage_learner` により 1 つのモデルファイルで
分かち書きと品詞付与を同時に行うモードです。`korean_pos.model` は
0.13.0 で元の空白を保持したコーパスにより再学習されたため、
`litsea (korean, two-stage)` の行は 0.12.0 の計測結果とは直接比較
できません。分かち書きモデル（`japanese.model`、`korean.model`、
`chinese.model`）は 0.12.0 から変更ありません。英語の表は今回新設した
もので、0.13.0 で追加された litsea の英語モデル 2 つだけを、litsea 自身の
ベンチマークが英語に使う `pride_and_prejudice.txt` で計測しています。
英語では他のトークナイザは計測していません。`lindera` は `embed-*` cargo
feature ではなく、lindera がリリースごとに公開しているビルド済み辞書
アーカイブ（例: `lindera-ipadic-5.3.0.zip`）から辞書を読み込むため、
`ipadic`・`unidic` に加えて `cc-cedict`（中国語）、`jieba`（中国語）、
`ko-dic`（韓国語）の辞書もカバーしています。

辞書・モデルサイズ（Dictionary / Model Size）は、各トークナイザが実行時に
実際に開くファイル（`strace` で検証済み）のディスク上のサイズであり、
実行時のメモリ使用量ではありません。ディストリビューションによっては
辞書と一緒に実行時には使われないデータが同梱されていますが、それらは
除外しています（例: MeCab の辞書ディレクトリに含まれる生の CSV 語彙
ソース、評価用データ、ライセンスファイル、コンパイル・学習専用の
`model.bin` や `*.def` ソース。Tagger 自身が開くのはコンパイル済みの
`sys.dic`/`matrix.bin`/`char.bin`/`unk.dic` のみです。kuromoji の辞書は
圧縮された `.jar` ではなく展開後の `.bin` ファイルで、vibrato の
`system.dic.zst` は実際にメモリ上に保持される展開後のサイズで計測して
います）。ピークメモリ（Peak Memory）は、`/usr/bin/time -v` で各反復を
ラップして計測したベンチマークプロセス全体の最大常駐セットサイズ
（RSS）です。そのため、Speed が計測する分かち書きループだけでなく、
辞書の読み込みも含まれます。全エンジンをこの方法で計測しており、
Java の 2 エンジンも Maven 自身のメモリが計上されないよう
`mvn exec:java` ではなく `java -cp` で直接起動しています。

### 日本語（`wagahaiwa_nekodearu.txt`、372,573 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| vaporetto | 0.6.5 | kytea jp-0.4.7-5.mod | 67.9 MB | 13,708,513 | 1,886,236 | 177.5 MB |
| litsea (japanese) | 0.14.3 | japanese.model | 1.1 MB | 9,846,654 | 1,173,394 | 11.9 MB |
| vibrato | 0.5.2 | ipadic-mecab-2.7.0 | 45.6 MB | 5,534,292 | 649,461 | 68.9 MB |
| litsea (japanese, two-stage) | 0.14.3 | japanese_pos.model | 5.4 MB | 4,942,196 | 611,597 | 45.0 MB |
| lindera | 5.3.0 | ipadic | 45.3 MB | 4,196,532 | 707,337 | 17.9 MB |
| mecab | thirdparty submodule | ipadic 2.7.0 | 50.5 MB | 3,410,079 | 456,515 | 33.1 MB |
| lindera | 5.3.0 | unidic | 190.1 MB | 3,020,502 | 516,751 | 63.4 MB |
| vibrato | 0.5.2 | unidic-cwj-3.1.1 | 684.2 MB | 2,923,535 | 411,532 | 724.0 MB |
| rust-tinysegmenter | 0.1.1 | - | - | 1,601,006 | 213,442 | 3.7 MB |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 122.3 MB | 1,523,347 | 189,316 | 736.8 MB |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 691.0 MB | 1,366,194 | 159,935 | 355.9 MB |
| sudachi.rs | git rev `90fd606` | sudachi-dictionary-20210802-core | 205.1 MB | 1,287,739 | 212,049 | 112.0 MB |
| kuromoji | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 31.9 MB | 1,123,410 | 183,813 | 353.2 MB |
| vibrato | 0.5.2 | unidic-cwj-3.1.1+compact-dual | 286.4 MB | 439,712 | 53,372 | 326.2 MB |
| sudachi | 0.7.5 | sudachi-dictionary-20210802-core | 205.1 MB | 407,921 | 78,402 | 532.3 MB |

### 韓国語（`mujeong.txt`、320,850 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | 0.14.3 | korean.model | 0.1 MB | 15,403,882 | 1,677,007 | 4.1 MB |
| litsea (korean, two-stage) | 0.14.3 | korean_pos.model | 3.9 MB | 4,748,428 | 531,080 | 32.3 MB |
| lindera | 5.3.0 | ko-dic | 81.6 MB | 2,208,435 | 362,370 | 42.4 MB |

### 中国語（`rulin_waishi.txt`、328,153 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (chinese) | 0.14.3 | chinese.model | 1.9 MB | 9,274,934 | 1,143,029 | 19.1 MB |
| lindera | 5.3.0 | cc-cedict | 22.1 MB | 8,632,360 | 1,557,491 | 10.0 MB |
| lindera | 5.3.0 | jieba | 48.9 MB | 7,085,668 | 1,297,080 | 22.4 MB |
| litsea (chinese, two-stage) | 0.14.3 | chinese_pos.model | 8.0 MB | 3,758,586 | 478,455 | 56.1 MB |

### 英語（`pride_and_prejudice.txt`、677,531 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (english) | 0.14.3 | english.model | 0.1 MB | 19,256,684 | 2,309,002 | 4.4 MB |
| litsea (english, two-stage) | 0.14.3 | english_pos.model | 2.9 MB | 7,000,538 | 885,232 | 23.6 MB |

`unidic-cwj-3.1.1+compact-dual` を使う `vibrato` の行は、コード・辞書・
ビルドフラグをまったく変えていないにもかかわらず、このベンチマークの実行
ごとに大きく変動しています（約 84,000〜985,000 chars/sec）。古い Rust
ツールチェーンで再ビルドしても今回の値が再現したため、この行を異なる
実行間で比較する際は注意してください。

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
