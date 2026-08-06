<!-- locales: README.md README.ko.md README.zh-CN.md README.es.md README.ja.md -->

# Brain-Role Architecture

[English](README.md) | **한국어** | [简体中文](README.zh-CN.md) | [Español](README.es.md) | [日本語](README.ja.md)

[![검증](https://github.com/JeremyDev87/Brain-Role-Architecture/actions/workflows/verify.yml/badge.svg)](https://github.com/JeremyDev87/Brain-Role-Architecture/actions/workflows/verify.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](pyproject.toml)
[![라이선스: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-D22128.svg)](LICENSE)

**PRE_RELEASE · 소스 후보 0.3.0 · 미출시**

Brain-Role Architecture는 AI 에이전트의 불변 규칙, 지속 상태, 위험, 워크플로, 페르소나,
목표를 책임과 실행 순서를 혼동하지 않고 통제하기 위한 검증 가능한 역할 기반 아키텍처입니다.

> **모든 재작성 뒤에도 남는 한 가지 규칙:** P0만 절대 불변입니다. P1-P6는 명시적인 소유권,
> 승인, 출처, 롤백, 효력 시점 계약을 통해서만 변경할 수 있습니다.

![Brain·Actor/Role·Compilation·직교 Neural Runtime의 네 구역과 P0-P6를 보여 주는 Brain-Role 포스터](docs/assets/brain-role-meme.png)

*책임·역량·결정론적 빌드·직교 조절을 네 시각 구역으로 구분합니다.*

## 왜 필요한가

에이전트 시스템은 안전 규칙, 메모리, 워크플로, 페르소나, 목표를 하나의 가변 프롬프트나 설정에
섞기 쉽습니다. 그러면 무엇을 바꿀 수 있는지, 누가 변경을 소유하는지, 무엇이 의존하는지,
롤백할 수 있는지를 답하기 어렵습니다. Brain-Role Architecture는 이 경계를 명시적이고,
기계적으로 검증 가능하며, 이식 가능한 계약으로 만듭니다.

이 README는 프로젝트를 설명하지만, 규범 계약은 [SPEC.md](SPEC.md)가 소유하며 모든 설명 문서보다
우선합니다.

## 책임 토폴로지: P0-P6

| 계층 | 책임 | 변경 계약 |
| --- | --- | --- |
| **P0** | 진실/비조작, 안전/보안, 출처/무손실, 결정론적 전이 | **절대 불변.** 상위 계층이나 역할이 덮어쓸 수 없습니다. |
| **P1** | 반복 가능한 자동화와 일정 | 통제된 변경 대상이며 예약 계층일 수 있습니다. |
| **P2** | 지속 상태와 메모리 | 명시적 소유권과 출처 아래 통제됩니다. |
| **P3** | 위험 및 충돌 레지스트리 | 통제된 변경 대상이며 예약 계층일 수 있습니다. |
| **P4** | 워크플로와 오케스트레이션 | 검토와 롤백이 가능한 통제 계층입니다. |
| **P5** | 페르소나와 커뮤니케이션 행동 | 명시적인 변경 통제 메타데이터 아래 관리됩니다. |
| **P6** | 목표와 방향 | 명시적인 변경 통제 메타데이터 아래 관리됩니다. |

P 번호는 **책임과 권한**을 나타내며 런타임 실행 순서나 컴파일 순서를 뜻하지 않습니다.

## 서로 독립적인 세 평면

1. **Brain 평면** — 책임, 권한, 변경 규칙
2. **Actor/Role 평면** — 역량, 입출력, 권한, 상태 범위, 에스컬레이션
3. **Compilation 평면** — P 번호와 독립된 명시적 의존성 DAG와 컴파일 순서

역할이 먼저 또는 나중에 실행된다는 이유만으로 권한을 얻지 않도록 세 평면을 분리합니다.
[세 평면 설명](docs/explanation/three-planes.md)을 참고하십시오.

## 한눈에 보는 구성

![P0-P6, Actor/Role, Compilation DAG, Neural 회로를 구분한 Brain-Role 구조도](docs/assets/brain-role-overview.svg)

*아이콘은 P0-P6를 파이프라인으로 만들지 않고 책임·역량·빌드 순서·조절을 보여 줍니다.*

## 포함 사항

- 규범 명세와 Draft 2020-12 JSON Schema
- 결정론적 오프라인 `brain-role` 검증 CLI
- 합성 기반의 유효/무효 적합성 fixture
- 공개/비공개 경계 검사와 위협 모델
- 단위, 스키마 동기화, 문서, 배포 패키지 smoke 검증

## 빠른 시작

요구 사항: Python 3.11+와 [`uv`](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/JeremyDev87/Brain-Role-Architecture.git
cd Brain-Role-Architecture
uv sync --all-groups
uv run brain-role validate examples/minimal-public --format json
```

예상 결과:

```json
{"errors":[],"specVersion":"0.1.0","valid":true}
```

결정론적 중립 산출물을 컴파일하고 저장소의 전체 검증을 실행합니다.

```bash
uv run brain-role compile examples/minimal-public --output .artifacts/compiled.json
make verify
```

## 검증 및 산출물 흐름

![public bundle에서 compiled.json·connectome.json·trace.json으로 이어지는 brain-role CLI 흐름](docs/assets/brain-role-flow.svg)

*검증은 확인 가능한 산출물을 만들지만 외부 runtime을 배포·게시하거나 상태를 변경하지 않습니다.*
`compile`은 명시적 레이어 순서와 안정적인 role/policy 순서를 가진 canonical JSON 파일을 생성하며,
source 경로·credential·runtime activation 정보를 추가하지 않습니다.

## 적합한 용도

- 감사 가능한 AI 에이전트 거버넌스 번들 설계
- CI에서 계층 소유권, 의존성, 권한 계약 검증
- 결정론적 합성 fixture를 이용한 adapter 테스트
- 페르소나와 목표 변경이 선언된 변경 통제 계약을 따르는지 검토

## 제공하지 않는 것

- 호스팅형 에이전트 런타임이나 오케스트레이션 서비스
- 자기 수정형 메모리 시스템
- 외부 runtime을 배포, 게시, 활성화하거나 변경할 권한
- 실제 프로필, 세션, 자격증명, 비공개 URL, 개인정보 보관소

## 문서 지도

- [규범 명세](SPEC.md)
- [빠른 시작 튜토리얼](docs/tutorials/quickstart.md)
- [서로 독립적인 세 평면](docs/explanation/three-planes.md)
- [CLI 참조](docs/reference/cli.md)
- [매니페스트 및 스키마 모델](docs/reference/manifest-model.md)
- [위협 모델](docs/security/threat-model.md)
- [기여 안내](CONTRIBUTING.md)와 [거버넌스](GOVERNANCE.md)

## 보안 및 공개/비공개 경계

공개 번들에는 합성 `PUBLIC` 자료만 포함해야 합니다. 자격증명, 비공개 URL, 실제 프로필이나 세션,
비밀값, 계정 식별자, 개인 절대 경로를 추가하지 마십시오. 취약점은 공개 이슈가 아니라
[SECURITY.md](SECURITY.md)에 따라 신고하십시오.

검증기는 오프라인·결정론적·무부작용 방식으로 동작합니다. 검증 오류는 인스턴스 상대 경로를
사용하고 비공개 절대 경로나 비밀값을 출력하지 않아야 합니다.

## 프로젝트 상태

`0.3.0`은 실험적 소스 후보입니다. 레지스트리 패키지, Git 태그, GitHub Release, 배포본으로
표시되지 않습니다. 명세가 사전 출시 상태인 동안 호환성이 변경될 수 있습니다.
[CHANGELOG.md](CHANGELOG.md)를 참고하십시오.

## 기여

[CONTRIBUTING.md](CONTRIBUTING.md)와 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)부터 확인하십시오.
동작 변경은 규범 계약을 보존하고 합성 회귀 근거를 추가하며 다음 명령을 통과해야 합니다.

```bash
make verify
```

## 게시 경계

검증이나 `make verify`의 성공은 Git commit, push, release, package publication, deployment,
activation, 저장소 공개 범위 변경을 허가하지 않습니다. 이는 각각 별도의 소유자 통제 결정입니다.

Apache-2.0으로 라이선스됩니다. [LICENSE](LICENSE)와 [NOTICE](NOTICE)를 참고하십시오.
