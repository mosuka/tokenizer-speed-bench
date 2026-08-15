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

2026-08-15 に以下の環境で計測しました。

* CPU: Intel Core i7-1185G7（4 コア / 8 スレッド、最大 4.8GHz）
* メモリ: 32GiB
* OS: Ubuntu 24.04.4 LTS, Linux 6.8.0-137-generic
* ツールチェーン: rustc 1.97.1, OpenJDK 21.0.11, Apache Maven 3.8.7,
  g++ 13.3.0

各トークナイザはコーパスを 100 回分かち書きします（ウォームアップ 1 回を
実施し、統計からは除外）。速度（Speed）は 1 秒あたりの処理文字数で、
大きいほど高速です。標準偏差（Std dev）は 100 回の反復にわたる
母標準偏差です。

litsea 0.11.0 では、精度向上のために分かち書きモデル（`japanese.model`、
`korean.model`、`chinese.model`）が再学習されており、出力される単語数も
変わるため、以下の `litsea (*)` の行は litsea 0.10.0 での計測結果とは
直接比較できません。`litsea (*, two-stage)` は litsea 0.11.0 の新機能で、
`Segmenter::with_two_stage_learner` により 1 つのモデルファイルで
分かち書きと品詞付与を同時に行うモードです。`lindera` は `embed-*` cargo
feature ではなく、lindera がリリースごとに公開しているビルド済み辞書
アーカイブ（例: `lindera-ipadic-5.2.0.zip`）から辞書を読み込むように
なったため、`ipadic`・`unidic` に加えて `cc-cedict`（中国語）、
`jieba`（中国語）、`ko-dic`（韓国語）の辞書もカバーしています。

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
| vaporetto | 0.6.5 | kytea jp-0.4.7-5.mod | 67.9 MB | 12,600,106 | 2,088,127 | 177.5 MB |
| litsea (japanese) | 0.11.0 | japanese.model | 1.1 MB | 10,392,921 | 1,444,316 | 12.1 MB |
| vibrato | 0.5.2 | ipadic-mecab-2.7.0 | 45.6 MB | 5,279,422 | 765,667 | 68.9 MB |
| litsea (japanese, two-stage) | 0.11.0 | japanese_two_stage.model | 5.4 MB | 4,883,425 | 746,471 | 45.0 MB |
| lindera | 5.2.0 | ipadic | 55.2 MB | 3,925,298 | 612,325 | 36.8 MB |
| mecab | thirdparty submodule | ipadic 2.7.0 | 50.5 MB | 3,246,825 | 435,416 | 33.1 MB |
| lindera | 5.2.0 | unidic | 204.0 MB | 2,895,138 | 395,889 | 139.0 MB |
| vibrato | 0.5.2 | unidic-cwj-3.1.1 | 684.2 MB | 2,814,177 | 360,073 | 724.0 MB |
| litsea (japanese, POS) | 0.11.0 | japanese_pos.model | 10.5 MB | 1,721,239 | 246,725 | 45.7 MB |
| rust-tinysegmenter | 0.1.1 | - | - | 1,516,314 | 192,685 | 3.7 MB |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 122.3 MB | 1,440,471 | 201,393 | 736.7 MB |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 691.0 MB | 1,327,531 | 159,184 | 355.9 MB |
| sudachi.rs | git rev `90fd606` | sudachi-dictionary-20210802-core | 205.1 MB | 1,204,008 | 184,386 | 111.9 MB |
| kuromoji | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 31.9 MB | 1,033,107 | 166,657 | 353.9 MB |
| vibrato | 0.5.2 | unidic-cwj-3.1.1+compact-dual | 286.4 MB | 882,617 | 123,781 | 326.2 MB |
| sudachi | 0.7.5 | sudachi-dictionary-20210802-core | 205.1 MB | 377,368 | 72,352 | 531.9 MB |

### 韓国語（`mujeong.txt`、320,850 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | 0.11.0 | korean.model | 0.1 MB | 12,362,271 | 1,611,206 | 4.5 MB |
| litsea (korean, two-stage) | 0.11.0 | korean_two_stage.model | 5.0 MB | 4,994,341 | 713,082 | 39.1 MB |
| litsea (korean, POS) | 0.11.0 | korean_pos.model | 8.5 MB | 2,624,632 | 317,211 | 40.3 MB |
| lindera | 5.2.0 | ko-dic | 109.5 MB | 2,054,657 | 271,663 | 104.6 MB |

### 中国語（`rulin_waishi.txt`、328,153 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (chinese) | 0.11.0 | chinese.model | 1.9 MB | 9,891,193 | 1,126,787 | 19.2 MB |
| lindera | 5.2.0 | cc-cedict | 27.6 MB | 8,180,348 | 1,283,901 | 21.8 MB |
| lindera | 5.2.0 | jieba | 66.0 MB | 6,967,445 | 1,017,252 | 61.3 MB |
| litsea (chinese, two-stage) | 0.11.0 | chinese_two_stage.model | 8.0 MB | 3,688,857 | 530,095 | 56.1 MB |
| litsea (chinese, POS) | 0.11.0 | chinese_pos.model | 18.4 MB | 1,679,795 | 196,232 | 78.1 MB |

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
