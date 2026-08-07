<!-- locales: README.md README.ko.md README.zh-CN.md README.es.md README.ja.md -->

# Brain-Role Architecture

[English](README.md) | [한국어](README.ko.md) | [簡体中文](README.zh-CN.md) | [Español](README.es.md) | **日本語**

[![検証](https://github.com/JeremyDev87/Brain-Role-Architecture/actions/workflows/verify.yml/badge.svg)](https://github.com/JeremyDev87/Brain-Role-Architecture/actions/workflows/verify.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](pyproject.toml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-D22128.svg)](LICENSE)

**PRE_RELEASE · ソース候補 0.4.0 · 未公開**

Brain-Role Architecture は、AI エージェントの不変条件、永続状態、リスク、ワークフロー、
ペルソナ、目標を、責任と実行順序を混同せずに統制するための検証可能なロール指向アーキテクチャです。

> **どれだけ書き換えても残る一つの規則:** 絶対不変なのは Brainstem だけです。Cerebellum through Prefrontal Cortex は、明示的な所有者、
> 承認、来歴、ロールバック、発効時刻の契約を通じてのみ変更できます。

![直交する Neural 領域、Brainstem through Prefrontal Cortex の Brain プレーン、Actor/Role と Compilation の各プレーンを示す Brain-Role ポスター](docs/assets/brain-role-meme.png)

*責任・能力・決定論的ビルド・直交モジュレーションを四つの視覚領域に分けます。*

## なぜ必要なのか

エージェントシステムでは、安全規則、メモリ、ワークフロー、ペルソナ、目標を一つの可変プロンプトや
設定に混在させがちです。その結果、何を変更できるのか、誰が変更を所有するのか、何が依存するのか、
ロールバックできるのかという基本的な統制上の問いに答えにくくなります。Brain-Role Architecture は、
これらの境界を明示し、機械的に検証可能で移植可能な契約にします。

この README はプロジェクトを説明する文書です。規範的な契約は [SPEC.md](SPEC.md) が保持し、
すべての説明文書より優先されます。

## 責任トポロジー: Brainstem through Prefrontal Cortex

| レイヤー | 責任 | 変更契約 |
| --- | --- | --- |
| **Brainstem** | 真実性/非捏造、安全/セキュリティ、来歴/無損失、決定論的遷移 | **絶対不変。** 上位レイヤーやロールは上書きできません。 |
| **Cerebellum** | 反復可能な自動化とスケジュール | 統制された変更対象。予約レイヤーにできます。 |
| **Hippocampus** | 永続状態とメモリ | 明示的な所有者と来歴の下で統制されます。 |
| **Amygdala** | リスクと競合のレジストリ | 統制された変更対象。予約レイヤーにできます。 |
| **Cerebral Cortex** | ワークフローとオーケストレーション | レビューとロールバックが可能な統制レイヤーです。 |
| **Default Mode Network** | ペルソナとコミュニケーション動作 | 明示的な変更統制メタデータの下で管理されます。 |
| **Prefrontal Cortex** | 目標と方向性 | 明示的な変更統制メタデータの下で管理されます。 |

解剖学的な名称が表すのは **責任と権限** であり、ランタイムの実行順序やコンパイル順序ではありません。

## 独立した三つのプレーン

1. **Brain プレーン** — 責任、権限、変更規則
2. **Actor/Role プレーン** — 能力、入出力、権限、状態スコープ、エスカレーション
3. **Compilation プレーン** — 解剖学的な責任名から独立した、明示的な依存 DAG とコンパイル順序

ロールが先または後に実行されるという理由だけで権限を得ないよう、この三つを分離します。
[三つのプレーンの解説](docs/explanation/three-planes.md)も参照してください。

## アーキテクチャの全体像

![Brainstem through Prefrontal Cortex、Actor/Role、Compilation DAG、Neural 回路を分離した Brain-Role 構造図](docs/assets/brain-role-overview.svg)

*アイコンは Brainstem through Prefrontal Cortex をパイプライン化せず、責任・能力・ビルド順序・モジュレーションを示します。*

## 含まれるもの

- 規範仕様と Draft 2020-12 JSON Schema
- 決定論的でオフラインの `brain-role` 検証 CLI
- 合成された有効/無効の適合性 fixture
- 公開/非公開境界チェックと脅威モデル
- 単体、スキーマ同期、文書、配布パッケージの smoke 検証

## クイックスタート

要件: Python 3.11+ と [`uv`](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/JeremyDev87/Brain-Role-Architecture.git
cd Brain-Role-Architecture
uv sync --all-groups
uv run brain-role validate examples/minimal-public --format json
```

期待される結果:

```json
{"errors":[],"specVersion":"0.1.0","valid":true}
```

決定論的な中立成果物をコンパイルし、リポジトリの全ゲートを実行します。

```bash
uv run brain-role compile examples/minimal-public --output .artifacts/compiled.json
make verify
```

## 検証と成果物のフロー

![public bundle から compiled.json、connectome.json、trace.json へ至る brain-role CLI フロー](docs/assets/brain-role-flow.svg)

*検証は確認可能な成果物を生成しますが、外部ランタイムのデプロイ、公開、状態変更は行いません。*
`compile` は明示的なレイヤー順と安定した role/policy 順を持つ canonical JSON を生成し、
source path、credential、runtime activation 情報を追加しません。

## 適した用途

- 監査可能な AI エージェント統制バンドルの設計
- CI によるレイヤー所有権、依存関係、権限契約の検証
- 決定論的な合成 fixture に対する adapter のテスト
- ペルソナや目標の変更が宣言された変更統制契約に従うかのレビュー

## これは何ではないか

- ホスト型エージェントランタイムやオーケストレーションサービス
- 自己変更型メモリシステム
- 稼働中の外部ランタイムをデプロイ、公開、有効化、変更する権限
- 実在のプロフィール、セッション、認証情報、非公開 URL、個人データの保管場所

## ドキュメントマップ

- [規範仕様](SPEC.md)
- [クイックスタート](docs/tutorials/quickstart.md)
- [独立した三つのプレーン](docs/explanation/three-planes.md)
- [CLI リファレンス](docs/reference/cli.md)
- [マニフェストと Schema モデル](docs/reference/manifest-model.md)
- [脅威モデル](docs/security/threat-model.md)
- [コントリビューション](CONTRIBUTING.md)と[ガバナンス](GOVERNANCE.md)

## セキュリティと公開/非公開境界

公開バンドルには、合成された `PUBLIC` 素材だけを含めてください。認証情報、非公開 URL、実在する
プロフィールやセッション、秘密値、アカウント識別子、個人の絶対パスを追加しないでください。
脆弱性は公開 issue ではなく [SECURITY.md](SECURITY.md) に従って報告してください。

検証器はオフライン、決定論的、副作用なしで動作します。検証エラーにはインスタンス相対パスを使い、
非公開の絶対パスや秘密値を出力してはなりません。

## プロジェクトの状態

`0.4.0` は実験的なソース候補です。レジストリパッケージ、Git tag、GitHub Release、デプロイとして
表明されていません。仕様がプレリリースの間は互換性が変わる可能性があります。
[CHANGELOG.md](CHANGELOG.md)を参照してください。

## コントリビューション

[CONTRIBUTING.md](CONTRIBUTING.md) と [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) から始めてください。
動作を変える変更は規範契約を保ち、合成回帰証拠を追加し、次を通過する必要があります。

```bash
make verify
```

## 公開境界

検証または `make verify` の成功は、Git commit、push、release、package publication、deployment、
activation、リポジトリ可視性の変更を許可しません。これらはそれぞれ所有者が別途決定します。

Apache-2.0 でライセンスされています。[LICENSE](LICENSE) と [NOTICE](NOTICE)を参照してください。

## Neural Runtime の要素

Neural Runtime は直交する実行・証拠プレーンであり、Brain や Role の権限を生成しません。

| 要素 | 役割 |
| --- | --- |
| **Functional Neuron** | 型付きポートと明示的なしきい値を持つ能力結合プロセッサです。 |
| **Synapse** | 興奮/抑制、強度、論理遅延を持つ型付き接続です。 |
| **Regulator** | 減衰と TTL を持つ制限値で、Receptor なしでは作用しません。 |
| **Receptor** | Regulator を Neuron のしきい値または gain に制限付きで結合します。 |
| **Homeostat** | メトリクスを目標範囲へ戻す負帰還です。 |
| **Support** | 状態を観察し throttle・retry・quarantine を提案するだけです。 |
| **Logical Clock** | wall-clock 権限を持たない決定論的 tick phase です。 |
| **Plasticity Proposal** | 証拠と rollback を持ち、simulation が適用しない変更案です。 |
| **ActivationScenario** | 合成信号、メトリクス、tick/event 上限を宣言します。 |
| **CompiledConnectome** | 決定論的な回路投影であり、権限源ではありません。 |
| **NeuralTrace** | 活性化、調節、提案、停止理由を持つ不変実行証拠です。 |
