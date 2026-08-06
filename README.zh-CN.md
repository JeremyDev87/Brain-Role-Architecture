<!-- locales: README.md README.ko.md README.zh-CN.md README.es.md README.ja.md -->

# Brain-Role Architecture

[English](README.md) | [한국어](README.ko.md) | **简体中文** | [Español](README.es.md) | [日本語](README.ja.md)

[![验证](https://github.com/JeremyDev87/Brain-Role-Architecture/actions/workflows/verify.yml/badge.svg)](https://github.com/JeremyDev87/Brain-Role-Architecture/actions/workflows/verify.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](pyproject.toml)
[![许可证：Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-D22128.svg)](LICENSE)

**PRE_RELEASE · 源代码候选版本 0.3.0 · 尚未发布**

Brain-Role Architecture 是一种可验证、可感知角色的架构，用于治理 AI 智能体的不变量、
持久状态、风险、工作流、人格与目标，同时避免混淆责任关系与执行顺序。

> **无论如何重写，始终保留一条规则：**P0 是唯一的绝对不变量。P1-P6 只能通过明确的
> 所有权、审批、来源、回滚和生效时间契约进行变更。

![脑内的卡通办公室：P6 不断抛出新目标，P0 则冷静地守住不变量关卡](docs/assets/brain-role-meme.png)

*P6 又想出了一个绝妙的新方向。P0 早就见怪不怪了。*

## 为什么需要这个项目

智能体系统经常把安全规则、记忆、工作流、人格和目标混在一个可变提示词或配置中。
这会让一些基本的治理问题难以回答：什么可以变更？谁对变更负责？哪些内容依赖它？
能否回滚？Brain-Role Architecture 将这些边界变成明确、机器可检查且可移植的契约。

本 README 用于介绍项目；[SPEC.md](SPEC.md) 仍是规范性契约，并优先于所有解释性文档。

## 责任拓扑：P0-P6

| 层级 | 责任 | 变更契约 |
| --- | --- | --- |
| **P0** | 真实/不捏造、安全/安保、来源/无损、确定性转换 | **绝对不变量。**任何更高层或角色都不得覆盖它。 |
| **P1** | 可重复的自动化与调度 | 受控；可以保留。 |
| **P2** | 持久状态与记忆 | 在明确的所有权和来源记录下受控。 |
| **P3** | 风险与冲突登记 | 受控；可以保留。 |
| **P4** | 工作流与编排 | 受控、可审查且可回滚。 |
| **P5** | 人格与沟通行为 | 依据明确的变更控制元数据进行管理。 |
| **P6** | 目标与方向 | 依据明确的变更控制元数据进行管理。 |

P 编号表示的是**责任与权限**，并不代表运行时顺序或编译顺序。

## 三个相互独立的平面

1. **Brain 平面**——责任、权限与变更规则。
2. **Actor/Role 平面**——能力、输入/输出、权限、状态范围与升级机制。
3. **Compilation 平面**——显式的依赖 DAG 与显式的编译顺序，二者都独立于 P 编号。

将这三个平面分开，可以防止某个角色仅仅因为最先或最后运行就获得额外权限。
请参阅[三个平面的说明](docs/explanation/three-planes.md)。

## 架构一览

![Brain、Actor/Role、Compilation 以及正交 Neural Runtime 平面的架构图](docs/assets/brain-role-overview.svg)

*P0-P6 定义责任，Actor/Role 定义能力，Compilation 平面定义显式转换顺序。*

## 包含内容

- 规范性说明与 Draft 2020-12 JSON Schema
- 确定性、离线的 `brain-role` 验证器 CLI
- 由合成数据构成的有效和无效一致性测试夹具
- 公开/私有边界检查与威胁模型
- 单元测试、Schema 同步检查、文档检查和发行包冒烟验证

## 快速开始

要求：Python 3.11+ 和 [`uv`](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/JeremyDev87/Brain-Role-Architecture.git
cd Brain-Role-Architecture
uv sync --all-groups
uv run brain-role validate examples/minimal-public --format json
```

预期结果：

```json
{"errors":[],"specVersion":"0.1.0","valid":true}
```

编译确定性的中立产物，并运行仓库的所有验证门禁：

```bash
uv run brain-role compile examples/minimal-public --output .artifacts/compiled.json
make verify
```

## 验证与产物流

![确定性验证、编译和模拟流程，以及部署与发布边界](docs/assets/brain-role-flow.svg)

*验证会生成可检查的产物，但不会部署、发布或修改外部运行时状态。*

`compile` 生成具有显式层顺序和稳定角色/策略顺序的规范 JSON 文件，不添加源路径、凭据或运行时激活数据。

## 适用场景

- 设计可审计的 AI 智能体治理包
- 在 CI 中验证层级所有权、依赖关系与权限契约
- 使用确定性的合成测试夹具测试适配器
- 审查人格与目标的变更是否遵循其声明的变更控制契约

## 不属于本项目的范围

- 托管式智能体运行时或编排服务
- 自我修改的记忆系统
- 对外部运行时进行部署、发布、激活或修改的授权
- 用来存放真实个人资料、会话、凭据、私有 URL 或个人数据的容器

## 文档索引

- [规范性说明](SPEC.md)
- [快速入门教程](docs/tutorials/quickstart.md)
- [三个相互独立的平面](docs/explanation/three-planes.md)
- [CLI 参考](docs/reference/cli.md)
- [清单模型参考](docs/reference/manifest-model.md)
- [威胁模型](docs/security/threat-model.md)
- [贡献指南](CONTRIBUTING.md)与[治理说明](GOVERNANCE.md)

## 安全与公开/私有边界

公开包只能包含合成的 `PUBLIC` 材料。请勿添加凭据、私有 URL、真实个人资料或会话、
机密值、账户标识符或个人绝对路径。请按照 [SECURITY.md](SECURITY.md) 的说明报告漏洞，
不要提交公开 Issue。

验证器以离线、确定性且无副作用的方式运行。验证错误使用实例相对路径，并且不得回显
私有绝对路径或机密值。

## 项目状态

`0.3.0` 是实验性的源代码候选版本。本项目不将其表示为注册表中的软件包、Git 标签、
GitHub Release 或部署版本。在规范仍处于预发布阶段期间，兼容性可能发生变化。
请参阅 [CHANGELOG.md](CHANGELOG.md)。

## 贡献

请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。
改变行为的修改必须保留规范性契约、添加合成的回归证据，并通过：

```bash
make verify
```

## 发布边界

通过验证或 `make verify` **并不**授权执行 Git commit、push、release、package publication、
deployment、activation 或更改仓库可见性。这些操作分别由所有者独立控制和决定。

本项目采用 Apache-2.0 许可证。请参阅 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。
