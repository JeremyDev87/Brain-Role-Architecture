<!-- locales: README.md README.ko.md README.zh-CN.md README.es.md README.ja.md -->

# Brain-Role Architecture

[English](README.md) | [한국어](README.ko.md) | [简体中文](README.zh-CN.md) | **Español** | [日本語](README.ja.md)

[![Verificación](https://github.com/JeremyDev87/Brain-Role-Architecture/actions/workflows/verify.yml/badge.svg)](https://github.com/JeremyDev87/Brain-Role-Architecture/actions/workflows/verify.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](pyproject.toml)
[![Licencia: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-D22128.svg)](LICENSE)

**PRE_RELEASE · candidato de código fuente 0.1.0 · no publicado**

Brain-Role Architecture es una arquitectura verificable y consciente de los roles para gobernar los invariantes, el estado, los flujos de trabajo, la personalidad y los objetivos de agentes de IA desde P0 hasta P6.

> P0 es el único invariante absoluto. P1-P6 son capas de responsabilidad con mutabilidad controlada y contratos explícitos de propiedad, aprobación, procedencia, reversión y momento de entrada en vigor.

![Meme de Brain-Role Architecture: separar responsabilidades, roles y compilación](docs/assets/brain-role-meme.png)

*Una arquitectura clara separa qué puede cambiar, quién puede cambiarlo y cómo se convierte en una configuración ejecutable.*

## Por qué existe este proyecto

Las configuraciones de agentes suelen mezclar en un mismo lugar reglas no negociables, automatización, memoria, gestión de riesgos, procedimientos, estilo de comunicación y objetivos. Cuando esas preocupaciones se confunden, resulta difícil responder preguntas básicas: ¿qué regla prevalece?, ¿quién puede modificarla?, ¿qué aprobación requiere?, ¿cómo se rastrea su procedencia?, ¿cuándo entra en vigor? y ¿cómo se revierte de forma segura?

Brain-Role Architecture proporciona un vocabulario y contratos verificables para separar esas responsabilidades. Su propósito no es hacer que todas las capas sean inmutables, sino distinguir el único límite absoluto de las capas que pueden evolucionar bajo controles explícitos.

`SPEC.md` sigue siendo la fuente normativa. Este README explica el proyecto, pero no redefine el contrato. Los números P identifican ámbitos de responsabilidad; **no implican orden de ejecución, orden en tiempo de ejecución ni orden de compilación**.

## Capas de responsabilidad P0-P6

| Capa | Responsabilidad principal | Política de cambio |
|---|---|---|
| **P0** | Invariantes absolutos | Es la única capa absoluta; no se trata como preferencia, memoria, flujo de trabajo ni objetivo mutable. |
| **P1** | Automatización | Mutable de forma controlada, con propiedad, aprobación, procedencia, reversión y vigencia explícitas. |
| **P2** | Memoria duradera | Mutable de forma controlada; conserva estado duradero sin convertirlo en un invariante absoluto. |
| **P3** | Riesgo y conflictos | Mutable de forma controlada; establece cómo se identifican, escalan y resuelven riesgos o conflictos. |
| **P4** | Flujos de trabajo | Mutable de forma controlada; describe procedimientos y coordinación operativa. |
| **P5** | Personalidad y comunicación | Mutable de forma controlada; define voz, estilo y contratos de comunicación. |
| **P6** | Objetivos | Mutable de forma controlada; expresa resultados deseados sin elevarlos a la categoría de absolutos. |

P1-P6 no son «menos importantes» por ser mutables: sus cambios deben estar gobernados y ser auditables. Tampoco forman una canalización secuencial. Cualquier dependencia y orden de compilación pertenecen al plano de compilación y deben declararse explícitamente.

## Tres planos independientes

El proyecto separa tres conceptos que a menudo se confunden:

- **Plano Brain:** responsabilidades, autoridad y reglas de cambio.
- **Plano Actor/Role:** capacidades, entradas y salidas, permisos y escalamiento.
- **Plano de compilación:** un DAG de dependencias explícito y un orden de compilación explícito, independiente de los números P.

Separar los planos evita inferir permisos a partir de una capa, confundir un rol con una política o asumir que P0-P6 determina el orden de compilación o de ejecución.

## Qué incluye

- Especificación normativa y JSON Schemas Draft 2020-12.
- CLI de validación `brain-role`, determinista y sin conexión.
- Fixtures sintéticos de conformidad, tanto válidos como inválidos.
- Exportador de referencia de solo lectura para `prefill_messages_file` de Hermes.
- Límite público/privado, modelo de amenazas, pruebas y verificación de humo del paquete.

## Inicio rápido

Requisitos y dependencias del entorno se resuelven mediante `uv`. Desde la raíz del repositorio:

```bash
uv sync --all-groups
uv run brain-role validate examples/minimal-public --format json
uv run brain-role render hermes examples/minimal-public --output .artifacts/hermes
make verify
```

### Resultado esperado

```json
{"errors":[],"specVersion":"0.1.0","valid":true}
```

1. `uv sync --all-groups` sincroniza los grupos de dependencias necesarios para trabajar y verificar el código fuente.
2. `uv run brain-role validate examples/minimal-public --format json` valida el ejemplo público mínimo y emite el resultado en JSON.
3. `uv run brain-role render hermes examples/minimal-public --output .artifacts/hermes` genera el artefacto de referencia de Hermes dentro de `.artifacts/hermes`.
4. `make verify` ejecuta la puerta de verificación definida por el repositorio.

`render hermes` solo genera archivos dentro del directorio de salida seleccionado. No activa Hermes, no cambia su configuración y no modifica `SOUL.md`, `USER.md`, `MEMORY.md` ni `~/.hermes`.

## Casos de uso

Brain-Role Architecture resulta útil para:

- diseñar configuraciones de agentes con responsabilidades y autoridad explícitas;
- validar documentos y fixtures de arquitectura antes de integrarlos en otro sistema;
- mantener memoria, procedimientos, personalidad y objetivos bajo políticas de cambio auditables;
- modelar capacidades, permisos, entradas, salidas y rutas de escalamiento por rol;
- compilar una arquitectura mediante dependencias declaradas, sin deducir el orden a partir de P0-P6;
- generar artefactos de referencia de Hermes sin modificar un entorno de ejecución activo.

## Lo que no es

Este proyecto no pretende:

- definir P0-P6 como fases de tiempo de ejecución o compilación;
- convertir P1-P6 en invariantes absolutos;
- sustituir la especificación normativa por documentación explicativa;
- activar, reconfigurar o mutar automáticamente una instalación de Hermes;
- acceder a la red, ejecutar código dinámico o escribir en hogares de ejecución como `~/.hermes`;
- autorizar commits, pushes, lanzamientos, publicaciones, despliegues o cambios de visibilidad del repositorio;
- afirmar que existe una etiqueta, un lanzamiento o un paquete de registro publicado para `0.1.0`.

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

El validador y los adaptadores están diseñados para funcionar sin conexión y de forma determinista. No deben añadir acceso a la red, ejecución dinámica de código ni mutaciones de hogares de ejecución como `~/.hermes`.

Antes de compartir un ejemplo o una incidencia, sustituye cualquier dato privado por datos sintéticos y revisa [`SECURITY.md`](SECURITY.md). La validación estructural no convierte material privado en material seguro para publicación.

## Estado del proyecto

El proyecto se encuentra en estado **PRE_RELEASE** como candidato de código fuente `0.1.0` y **no está publicado**. Esta designación describe el estado del código fuente; no representa una etiqueta, un lanzamiento ni un paquete disponible en un registro.

La interfaz, los esquemas y la documentación pueden seguir evolucionando dentro de los límites establecidos por `SPEC.md`. No se deben inferir garantías de publicación a partir del número de versión.

## Contribuir

Consulta [`CONTRIBUTING.md`](CONTRIBUTING.md) y [`GOVERNANCE.md`](GOVERNANCE.md) antes de proponer cambios. Las contribuciones deben:

- preservar el contrato normativo de `SPEC.md`;
- mantener P0 como el único invariante absoluto y P1-P6 como responsabilidades con mutabilidad controlada;
- usar esquemas genéricos y datos sintéticos;
- conservar el comportamiento determinista y sin conexión del validador y los adaptadores;
- evitar datos personales, credenciales y demás material privado;
- ejecutar `make verify` antes de proponer la publicación de un cambio.

Una validación correcta o una ejecución satisfactoria de `make verify` aporta evidencia técnica, pero no concede por sí sola autorización para publicar.

## Límite de publicación y licencia

Superar la validación **no** autoriza un commit de Git, push, lanzamiento, publicación de paquetes, despliegue ni cambio de visibilidad del repositorio. Ninguna etiqueta, lanzamiento o paquete de registro está representado por la versión de código fuente `0.1.0`.

El proyecto está licenciado bajo Apache-2.0. Consulta [`LICENSE`](LICENSE) y [`NOTICE`](NOTICE).