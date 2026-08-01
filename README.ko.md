# Brain-Role Architecture

**PRE_RELEASE · 소스 후보 0.1.0 · 미출시**

Brain-Role Architecture는 AI 에이전트의 불변 원칙, 상태, 워크플로우, 페르소나, 목표를
P0부터 P6까지 검증 가능하게 관리하는 역할 인식 아키텍처입니다.

> **P0만 절대 불변**입니다. P1-P6는 owner, approval, provenance, rollback, effective time을
> 명시하는 통제된 가변성의 책임 계층입니다.

이 프로젝트는 다음 세 축을 분리합니다.

- **Brain plane:** 책임, 권한, 변경 규칙
- **Actor/Role plane:** capability, 입출력, permission, escalation
- **Compilation plane:** P번호와 별개로 선언하는 dependency DAG와 compile order

## 빠른 시작

```bash
uv sync --all-groups
uv run brain-role validate examples/minimal-public --format json
uv run brain-role render hermes examples/minimal-public --output .artifacts/hermes
make verify
```

Hermes exporter는 지정한 출력 디렉터리에 참조 파일만 생성합니다. Hermes를 활성화하거나 설정,
`SOUL.md`, `USER.md`, `MEMORY.md`, `~/.hermes`를 변경하지 않습니다.

규범은 [SPEC.md](SPEC.md)가 소유합니다. [빠른 시작](docs/tutorials/quickstart.md)도 참고하십시오.

검증 통과는 commit, push, release, package publication, deploy, 저장소 공개 전환을 허가하지
않습니다. `0.1.0`은 아직 tag/release/registry publication이 없는 소스 후보입니다.
