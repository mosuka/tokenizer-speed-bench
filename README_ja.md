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

2026-08-20 に以下の環境で計測しました。

* CPU: Intel Core i7-1185G7（4 コア / 8 スレッド、最大 4.8GHz）
* メモリ: 32GiB
* OS: Ubuntu 24.04.4 LTS, Linux 6.8.0-137-generic
* ツールチェーン: rustc 1.97.1, OpenJDK 21.0.11, Apache Maven 3.8.7,
  g++ 13.3.0

各トークナイザはコーパスを 100 回分かち書きします（ウォームアップ 1 回を
実施し、統計からは除外）。速度（Speed）は 1 秒あたりの処理文字数で、
大きいほど高速です。標準偏差（Std dev）は 100 回の反復にわたる
母標準偏差です。

litsea 0.12.0 では、タグ依存特徴の重みを持たないモデルに対して
`segment()` が逐次スコアリングパスを丸ごとスキップする pointwise
fast path が追加され、これを活かすために `korean.model` が tag-free で
再学習されました（精度は同等のまま、モデルは約 110 KB から 86 KB に
縮小）。そのため `litsea (korean)` の行は 0.11.0 での計測より高速に
なっていますが、再学習されたモデルは分かち書き結果もわずかに変わる
ため、0.11.0 の計測結果とは直接比較できません。日本語・中国語の
モデルは 0.11.0 から変更ありません。`litsea (*, two-stage)` は
`Segmenter::with_two_stage_learner` により 1 つのモデルファイルで
分かち書きと品詞付与を同時に行うモードです。`lindera` は `embed-*` cargo
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
| vaporetto | 0.6.5 | kytea jp-0.4.7-5.mod | 67.9 MB | 13,324,632 | 785,624 | 177.5 MB |
| litsea (japanese) | 0.12.0 | japanese.model | 1.1 MB | 10,098,342 | 679,278 | 12.0 MB |
| vibrato | 0.5.2 | ipadic-mecab-2.7.0 | 45.6 MB | 5,452,045 | 383,445 | 68.9 MB |
| litsea (japanese, two-stage) | 0.12.0 | japanese_two_stage.model | 5.4 MB | 4,890,225 | 404,876 | 45.0 MB |
| lindera | 5.3.0 | ipadic | 45.3 MB | 4,122,713 | 388,174 | 17.9 MB |
| mecab | thirdparty submodule | ipadic 2.7.0 | 50.5 MB | 3,361,361 | 230,780 | 33.1 MB |
| lindera | 5.3.0 | unidic | 190.1 MB | 2,963,561 | 240,026 | 63.4 MB |
| vibrato | 0.5.2 | unidic-cwj-3.1.1 | 684.2 MB | 2,903,020 | 163,255 | 724.0 MB |
| litsea (japanese, POS) | 0.12.0 | japanese_pos.model | 10.5 MB | 1,767,635 | 140,326 | 45.7 MB |
| rust-tinysegmenter | 0.1.1 | - | - | 1,603,811 | 131,259 | 3.7 MB |
| kytea | thirdparty submodule | jp-0.4.7-5.mod | 122.3 MB | 1,480,213 | 94,576 | 736.8 MB |
| mecab | thirdparty submodule | unidic-cwj-3.1.1 | 691.0 MB | 1,364,869 | 70,031 | 355.9 MB |
| sudachi.rs | git rev `90fd606` | sudachi-dictionary-20210802-core | 205.1 MB | 1,248,045 | 110,179 | 111.9 MB |
| kuromoji | kuromoji-ipadic 0.9.0 | ipadic (bundled) | 31.9 MB | 1,107,191 | 116,145 | 353.0 MB |
| vibrato | 0.5.2 | unidic-cwj-3.1.1+compact-dual | 286.4 MB | 925,345 | 59,588 | 326.2 MB |
| sudachi | 0.7.5 | sudachi-dictionary-20210802-core | 205.1 MB | 403,012 | 52,672 | 532.8 MB |

### 韓国語（`mujeong.txt`、320,850 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (korean) | 0.12.0 | korean.model | 0.1 MB | 15,904,203 | 1,086,016 | 4.1 MB |
| litsea (korean, two-stage) | 0.12.0 | korean_two_stage.model | 5.0 MB | 5,013,428 | 445,414 | 39.2 MB |
| litsea (korean, POS) | 0.12.0 | korean_pos.model | 8.5 MB | 2,682,372 | 194,675 | 40.3 MB |
| lindera | 5.3.0 | ko-dic | 81.6 MB | 2,223,001 | 137,361 | 42.4 MB |

### 中国語（`rulin_waishi.txt`、328,153 文字）

| トークナイザ | バージョン | 辞書・モデル | 辞書・モデルサイズ | 速度 [chars/sec] | 標準偏差 | ピークメモリ |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| litsea (chinese) | 0.12.0 | chinese.model | 1.9 MB | 9,593,189 | 724,380 | 19.2 MB |
| lindera | 5.3.0 | cc-cedict | 22.1 MB | 8,627,257 | 835,520 | 10.0 MB |
| lindera | 5.3.0 | jieba | 48.9 MB | 7,091,309 | 512,462 | 22.4 MB |
| litsea (chinese, two-stage) | 0.12.0 | chinese_two_stage.model | 8.0 MB | 3,705,770 | 320,162 | 56.2 MB |
| litsea (chinese, POS) | 0.12.0 | chinese_pos.model | 18.4 MB | 1,730,064 | 112,923 | 78.0 MB |

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
