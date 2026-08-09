<!-- locales: README.md README.ko.md README.zh-CN.md README.es.md README.ja.md -->

# Brain-Role Architecture

[English](README.md) | [한국어](README.ko.md) | [简体中文](README.zh-CN.md) | **Español** | [日本語](README.ja.md)

[![Verificación](https://github.com/JeremyDev87/Brain-Role-Architecture/actions/workflows/verify.yml/badge.svg)](https://github.com/JeremyDev87/Brain-Role-Architecture/actions/workflows/verify.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](pyproject.toml)
[![Licencia: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-D22128.svg)](LICENSE)

**PRE_RELEASE · candidato de código fuente 0.4.0 · [GitHub Pre-release v0.4.0](https://github.com/JeremyDev87/Brain-Role-Architecture/releases/tag/v0.4.0)**

<!-- release-state: source=PRE_RELEASE github=v0.4.0:prerelease registry=unpublished deployment=none -->

Brain-Role Architecture es una herramienta de policy-as-code y conformidad que permite comprobar de forma mecánica las responsabilidades, la autoridad y los contratos de cambio de agentes de IA sin confundir responsabilidad con orden de ejecución.

**Primero la evidencia:** la [demostración de cambio controlado](docs/tutorials/controlled-mutation-demo.md) bloquea un cambio de Brainstem de forma fail-closed y permite un cambio gobernado de Cerebral Cortex con evidencia determinista.

> Brainstem es el único invariante absoluto. Cerebellum through Prefrontal Cortex son capas de responsabilidad con mutabilidad controlada y contratos explícitos de propiedad, aprobación, procedencia, reversión y momento de entrada en vigor.

![Póster de Brain-Role con la banda Neural ortogonal, el plano Brain Brainstem through Prefrontal Cortex y los planos Actor/Role y Compilation](docs/assets/brain-role-meme.png)

*Cuatro zonas visuales separan responsabilidad, capacidad, compilación determinista y modulación ortogonal.*

## Por qué existe este proyecto

Las configuraciones de agentes suelen mezclar en un mismo lugar reglas no negociables, automatización, memoria, gestión de riesgos, procedimientos, estilo de comunicación y objetivos. Cuando esas preocupaciones se confunden, resulta difícil responder preguntas básicas: ¿qué regla prevalece?, ¿quién puede modificarla?, ¿qué aprobación requiere?, ¿cómo se rastrea su procedencia?, ¿cuándo entra en vigor? y ¿cómo se revierte de forma segura?

Brain-Role Architecture proporciona un vocabulario y contratos verificables para separar esas responsabilidades. Su propósito no es hacer que todas las capas sean inmutables, sino distinguir el único límite absoluto de las capas que pueden evolucionar bajo controles explícitos.

`SPEC.md` sigue siendo la fuente normativa. Este README explica el proyecto, pero no redefine el contrato. Los nombres anatómicos identifican ámbitos de responsabilidad; **no implican orden de ejecución, orden en tiempo de ejecución ni orden de compilación**.

## Capas de responsabilidad Brainstem through Prefrontal Cortex

| Capa | Responsabilidad principal | Política de cambio |
|---|---|---|
| **Brainstem** | Invariantes absolutos | Es la única capa absoluta; no se trata como preferencia, memoria, flujo de trabajo ni objetivo mutable. |
| **Cerebellum** | Automatización | Mutable de forma controlada, con propiedad, aprobación, procedencia, reversión y vigencia explícitas. |
| **Hippocampus** | Memoria duradera | Mutable de forma controlada; conserva estado duradero sin convertirlo en un invariante absoluto. |
| **Amygdala** | Riesgo y conflictos | Mutable de forma controlada; establece cómo se identifican, escalan y resuelven riesgos o conflictos. |
| **Cerebral Cortex** | Flujos de trabajo | Mutable de forma controlada; describe procedimientos y coordinación operativa. |
| **Default Mode Network** | Personalidad y comunicación | Mutable de forma controlada; define voz, estilo y contratos de comunicación. |
| **Prefrontal Cortex** | Objetivos | Mutable de forma controlada; expresa resultados deseados sin elevarlos a la categoría de absolutos. |

Cerebellum through Prefrontal Cortex no son «menos importantes» por ser mutables: sus cambios deben estar gobernados y ser auditables. Tampoco forman una canalización secuencial. Cualquier dependencia y orden de compilación pertenecen al plano de compilación y deben declararse explícitamente.

## Tres planos independientes

El proyecto separa tres conceptos que a menudo se confunden:

- **Plano Brain:** responsabilidades, autoridad y reglas de cambio.
- **Plano Actor/Role:** capacidades, entradas y salidas, permisos y escalamiento.
- **Plano de compilación:** un DAG de dependencias explícito y un orden de compilación explícito, independiente de los nombres anatómicos de responsabilidad.

Separar los planos evita inferir permisos a partir de una capa, confundir un rol con una política o asumir que Brainstem through Prefrontal Cortex determina el orden de compilación o de ejecución.

## Vista general de la arquitectura

![Mapa estructural de Brain-Role con Brainstem through Prefrontal Cortex, Actor/Role, el DAG de Compilation y el circuito Neural](docs/assets/brain-role-overview.svg)

*Los iconos muestran responsabilidad, capacidad, orden de compilación y modulación sin convertir Brainstem through Prefrontal Cortex en una canalización.*

## Qué incluye

- Especificación normativa y JSON Schemas Draft 2020-12.
- CLI de validación `brain-role`, determinista y sin conexión.
- Fixtures sintéticos de conformidad, tanto válidos como inválidos.
- Límite público/privado, modelo de amenazas, pruebas y verificación de humo del paquete.

## Inicio rápido

Requisitos y dependencias del entorno se resuelven mediante `uv`. Desde la raíz del repositorio:

```bash
uv sync --all-groups
uv run brain-role validate examples/minimal-public --format json
uv run brain-role compile examples/minimal-public --output .artifacts/compiled.json
make verify
```

### Resultado esperado

```json
{"errors":[],"specVersion":"0.1.0","valid":true}
```

## Flujo de validación y artefactos

![Flujo de la CLI brain-role desde el public bundle hasta compiled.json, connectome.json y trace.json](docs/assets/brain-role-flow.svg)

*La validación produce artefactos inspeccionables; no despliega, publica ni modifica el estado de un runtime externo.*
1. `uv sync --all-groups` sincroniza los grupos de dependencias necesarios para trabajar y verificar el código fuente.
2. `uv run brain-role validate examples/minimal-public --format json` valida el ejemplo público mínimo y emite el resultado en JSON.
3. `uv run brain-role compile examples/minimal-public --output .artifacts/compiled.json` genera un JSON canónico con orden explícito, sin rutas de origen, credenciales ni activación del runtime.
4. `make verify` ejecuta la puerta de verificación definida por el repositorio.

## Casos de uso

Brain-Role Architecture resulta útil para:

- diseñar configuraciones de agentes con responsabilidades y autoridad explícitas;
- validar documentos y fixtures de arquitectura antes de integrarlos en otro sistema;
- mantener memoria, procedimientos, personalidad y objetivos bajo políticas de cambio auditables;
- modelar capacidades, permisos, entradas, salidas y rutas de escalamiento por rol;
- compilar una arquitectura mediante dependencias declaradas, sin deducir el orden a partir de Brainstem through Prefrontal Cortex;
- generar artefactos de referencia deterministas sin modificar un entorno de ejecución externo.

## Lo que no es

Este proyecto no pretende:

- definir Brainstem through Prefrontal Cortex como fases de tiempo de ejecución o compilación;
- convertir Cerebellum through Prefrontal Cortex en invariantes absolutos;
- sustituir la especificación normativa por documentación explicativa;
- activar, reconfigurar o mutar automáticamente un entorno de ejecución externo;
- acceder a la red, ejecutar código dinámico o escribir en hogares de ejecución;
- autorizar commits, pushes, lanzamientos, publicaciones, despliegues o cambios de visibilidad del repositorio;
- afirmar que existe un paquete de registro, despliegue, estado stable/GA o garantía de producción para `0.4.0`.

## Mapa de documentación

- [`SPEC.md`](SPEC.md): contrato normativo de Brain-Role Architecture.
- [`README.md`](README.md): README predeterminado en inglés.
- [`README.ko.md`](README.ko.md): traducción coreana.
- [`README.zh-CN.md`](README.zh-CN.md): traducción al chino simplificado.
- [`README.es.md`](README.es.md): esta traducción al español.
- [`README.ja.md`](README.ja.md): traducción japonesa.
- [`docs/tutorials/quickstart.md`](docs/tutorials/quickstart.md): tutorial de inicio rápido.
- [`CONTRIBUTING.md`](CONTRIBUTING.md): guía de contribución.
- [`SECURITY.md`](SECURITY.md): política y proceso de seguridad.
- [`GOVERNANCE.md`](GOVERNANCE.md): gobernanza del proyecto.
- [`CHANGELOG.md`](CHANGELOG.md): historial documentado de cambios.

Si una explicación de cualquiera de estos documentos entra en conflicto con `SPEC.md`, prevalece `SPEC.md`.

## Seguridad y límite público/privado

El repositorio público debe contener únicamente esquemas genéricos y fixtures sintéticos. No deben incorporarse canon personal, perfiles reales, sesiones, credenciales, URL privadas, identificadores de cuenta ni rutas de directorios personales.

El validador, el compilador y el simulador funcionan sin conexión y de forma determinista. No deben añadir acceso a la red, ejecución dinámica de código ni mutaciones de entornos de ejecución externos.

Antes de compartir un ejemplo o una incidencia, sustituye cualquier dato privado por datos sintéticos y revisa [`SECURITY.md`](SECURITY.md). La validación estructural no convierte material privado en material seguro para publicación.

## Estado del proyecto

El proyecto sigue en estado **PRE_RELEASE** como candidato de código fuente `0.4.0`. Existen la etiqueta anotada `v0.4.0` y el [GitHub Pre-release](https://github.com/JeremyDev87/Brain-Role-Architecture/releases/tag/v0.4.0) con artefactos wheel y source distribution. No existe paquete de registro ni despliegue; los artefactos descargables no implican instalación desde un registro, estado stable/GA, preparación para producción ni certificación de seguridad.

La interfaz, los esquemas y la documentación pueden seguir evolucionando dentro de los límites establecidos por `SPEC.md`. No se deben inferir garantías de publicación a partir del número de versión.

## Contribuir

Consulta [`CONTRIBUTING.md`](CONTRIBUTING.md) y [`GOVERNANCE.md`](GOVERNANCE.md) antes de proponer cambios. Las contribuciones deben:

- preservar el contrato normativo de `SPEC.md`;
- mantener Brainstem como el único invariante absoluto y Cerebellum through Prefrontal Cortex como responsabilidades con mutabilidad controlada;
- usar esquemas genéricos y datos sintéticos;
- conservar el comportamiento determinista y sin conexión del validador y los adaptadores;
- evitar datos personales, credenciales y demás material privado;
- ejecutar `make verify` antes de proponer la publicación de un cambio.

Una validación correcta o una ejecución satisfactoria de `make verify` aporta evidencia técnica, pero no concede por sí sola autorización para publicar.

## Límite de publicación y licencia

Superar la validación **no** autoriza un commit de Git, push, lanzamiento, publicación de paquetes, despliegue ni cambio de visibilidad del repositorio. La etiqueta y el GitHub Pre-release existentes no representan una publicación en un registro ni una autorización de despliegue.

El proyecto está licenciado bajo Apache-2.0. Consulta [`LICENSE`](LICENSE) y [`NOTICE`](NOTICE).

## Elementos del Neural Runtime

El Neural Runtime es un plano ortogonal de ejecución y evidencia; nunca crea autoridad Brain o Role.

| Elemento | Función |
| --- | --- |
| **Functional Neuron** | Procesador ligado a una capacidad, con puertos tipados y umbrales explícitos. |
| **Synapse** | Conexión tipada con efecto excitador/inhibidor, fuerza y retardo lógico. |
| **Regulator** | Modulación acotada con decaimiento y TTL; no actúa sin Receptor. |
| **Receptor** | Vincula un Regulator al umbral o ganancia de un Neuron dentro de límites. |
| **Homeostat** | Retroalimentación negativa basada en métricas y rangos objetivo. |
| **Support** | Observa salud y solo propone throttle, retry o quarantine. |
| **Logical Clock** | Fases deterministas de ticks sin autoridad de reloj real. |
| **Plasticity Proposal** | Propuesta con evidencia y rollback que la simulación nunca aplica. |
| **ActivationScenario** | Señales, métricas y límites explícitos de ticks/eventos. |
| **CompiledConnectome** | Proyección canónica del circuito; no es fuente de autoridad. |
| **NeuralTrace** | Evidencia inmutable de activación, modulación, propuestas y parada. |
