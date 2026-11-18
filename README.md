# Transparenta: Registro de Tratamientos de Datos Personales y Detección de Brechas según la Ley N° 21.719

> Proyecto APT · Capstone (PTY4614) · Ingeniería en Informática · Duoc UC
> Autora: **Josefa Vallejos Sánchez** (trabajo individual) · Docente: **Yerko Paredes Orellana**
> Aplicación web local construida con **Python, Flask y SQLite**. Empresa y datos ficticios (Nexa Soluciones TI).

| Estado al 18-11-2026 | Detalle |
|---|---|
| Fase actual | **Fase 2 – Desarrollo** cerrada · Evaluación 3 (informe final y presentación) |
| Prototipo | Funcional en ambiente local (`APLICACION` + `BASE DE DATOS`) |
| Pruebas de validación | **14 de 14 casos simulados aprobados** (`pruebas_validacion.py`) |
| Datos de ejemplo | 4 áreas, 3 terceros, 12 tratamientos, 5 registros de bitácora |
| Pendiente | Contraste de la regla de menores con el texto oficial, retroalimentación docente e implantación |

---

## Índice

1. [Nombre del proyecto](#1-nombre-del-proyecto)
2. [Descripción](#2-descripción)
3. [Innovación y valor agregado](#3-innovación-y-valor-agregado)
4. [Objetivos](#4-objetivos)
5. [Alcance funcional (MVP)](#5-alcance-funcional-mvp)
6. [Arquitectura y tecnologías](#6-arquitectura-y-tecnologías)
7. [Integrantes y roles](#7-integrantes-y-roles)
8. [Metodología de trabajo](#8-metodología-de-trabajo)
9. [Cómo ejecutarlo](#9-cómo-ejecutarlo)
10. [Pruebas de validación](#10-pruebas-de-validación)
11. [Estructura del repositorio](#11-estructura-del-repositorio)
12. [Estado de los objetivos](#12-estado-de-los-objetivos)
13. [Limitaciones y trabajo futuro](#13-limitaciones-y-trabajo-futuro)
14. [Marco normativo y referencias](#14-marco-normativo-y-referencias)

---

## 1. Nombre del proyecto

**Transparenta**: Registro de Tratamientos de Datos Personales y Detección de Brechas de Cumplimiento según la Ley N° 21.719.

## 2. Descripción

Las organizaciones deben saber qué datos personales tratan, para qué, con qué base de licitud, por cuánto tiempo y con quién los comparten. Hoy esa información suele estar dispersa en planillas y correos. Transparenta la ordena en un **Registro de Tratamientos vivo**, compara cada tratamiento con reglas de la Ley N° 21.719 y muestra las **brechas con un semáforo**. La persona responsable decide qué hacer con cada brecha y la decisión queda en una **bitácora**.

**¿A quién va dirigido?** A la Coordinación de Cumplimiento y a las personas responsables de cada área de una organización que trata datos personales (en el caso de estudio, la empresa ficticia Nexa Soluciones TI).

**¿Qué problema resuelve?** Evita que el registro de tratamientos quede disperso, desactualizado o incompleto, y permite ver a tiempo qué incumple la Ley N° 21.719, qué plazos de conservación vencen y quién tomó cada decisión.

## 3. Innovación y valor agregado

- **Registro vivo** en lugar de una planilla estática: cada cambio queda con fecha y responsable.
- **Semáforo de brechas** (verde, amarillo, rojo) que traduce la ley a señales simples.
- **Alertas de plazo de conservación** para saber cuándo corresponde eliminar o revisar un dato.
- **Confirmación humana** en cada decisión: el sistema sugiere, la persona decide.
- **Bitácora** de decisiones para respaldar el cumplimiento ante una auditoría.

## 4. Objetivos

**General:** diseñar y construir un prototipo funcional de software que permita a una organización registrar sus actividades de tratamiento de datos personales, detectar brechas de cumplimiento respecto de la Ley N° 21.719 y recibir avisos de plazos de conservación, con trazabilidad y confirmación humana de cada decisión.

**Específicos:**

| N° | Objetivo específico |
|---|---|
| OE1 | Requisitos de la Ley: sistematizar los elementos de la ley que usa el sistema (bases de licitud, categorías de datos, menores, plazos de conservación y terceros) |
| OE2 | Proceso y Modelo de Datos: diagramar el proceso de registro y revisión y diseñar el modelo de datos |
| OE3 | Interfaz: diseñar y construir las pantallas del sistema |
| OE4 | Prototipo Funcional: registro con semáforo, detección de brechas, avisos de vencimiento y bitácora |
| OE5 | Validación: probar el prototipo con casos simulados y con retroalimentación docente |

## 5. Alcance funcional (MVP)

**Incluye:** registro de tratamientos, áreas y terceros; semáforo de brechas; alertas de plazo de conservación; resolución de brechas una por una con confirmación; bitácora; simulación de dos roles (Persona Responsable del Área y Coordinación de Cumplimiento).

**No incluye (mejoras futuras):** autenticación de usuarios, edición directa de registros ya guardados, gestión de solicitudes de titulares y despliegue en un servidor.

## 6. Arquitectura y tecnologías

| Capa | Tecnología |
|---|---|
| Backend | Python 3 y Flask 3 |
| Base de datos | SQLite (archivo local `transparenta.db`) |
| Interfaz | Plantillas Jinja2, Bootstrap 5.3.3 (incluido en el proyecto) y fuente Source Sans 3 |
| Pruebas | Script en Python (`pruebas_validacion.py`) |
| Cloud | No se usa: el prototipo corre de forma local. El despliegue en la nube queda como mejora futura |
| Control de versiones | Git y GitHub (GitHub Desktop) |

**Diagrama de proceso**

![Diagrama de proceso](FASE%202%20-%20DESARROLLO%20DEL%20PROYECTO%20APT/EVIDENCIAS%20PROYECTO/EVIDENCIAS%20DE%20DOCUMENTACION/DIAGRAMA%20DE%20PROCESO.png)

**Modelo de datos**

![Modelo de datos](FASE%202%20-%20DESARROLLO%20DEL%20PROYECTO%20APT/EVIDENCIAS%20PROYECTO/EVIDENCIAS%20DE%20DOCUMENTACION/MODELO%20DE%20DATOS%20ER.png)

## 7. Integrantes y roles

| Integrante | Rol |
|---|---|
| Josefa Vallejos Sánchez | Trabajo individual: levantamiento de requisitos normativos, modelamiento, diseño de interfaz, desarrollo, pruebas, documentación y gestión del proyecto (rol de líder ágil) |

Docente guía: Yerko Paredes Orellana.

## 8. Metodología de trabajo

Metodología mixta, ajustada al alcance acotado y al trabajo individual:

- **Gestión:** Scrum adaptado a trabajo individual, con tareas pequeñas y fechas concretas. El avance se controla con una tabla de monitoreo y una carta Gantt, y el repositorio se versiona en GitHub.
- **Requisitos normativos:** análisis de la Ley N° 21.719 y de recursos de especialistas, contrastando los datos críticos con el texto oficial.
- **Modelamiento:** modelo entidad-relación y diagrama del proceso antes de programar.
- **Construcción incremental:** primero la base de datos con datos ficticios y luego la aplicación, probando una función a la vez.
- **Validación:** casos de prueba simulados y retroalimentación docente.
- **Principio de diseño:** el sistema no toma decisiones legales; toda decisión la confirma una persona. Se usó un asistente de inteligencia artificial generativa como apoyo, y las decisiones de diseño y la revisión de los resultados son de la autora.

## 9. Cómo ejecutarlo

En Windows:

1. Instalar Python 3 y ejecutar `pip install flask`.
2. Entrar a la carpeta `EVIDENCIAS DE SISTEMA` y hacer doble clic en `Iniciar Transparenta.bat`. Crea la base de datos si falta y abre el navegador.
3. Si no se abre solo, ir a http://127.0.0.1:5000

Manualmente:

```bash
cd APLICACION
pip install flask
python app.py
```

## 10. Pruebas de validación

Desde la carpeta `EVIDENCIAS DE SISTEMA`:

```bash
python pruebas_validacion.py
```

El script ejecuta **14 casos** sobre las reglas de brecha, las alertas de plazo y el registro en bitácora. Los resultados quedan descritos en el informe final (sección 6).

## 11. Estructura del repositorio

```
FASE 1/                                  Documentos de la Fase 1
FASE 2 - DESARROLLO DEL PROYECTO APT/
├── EVIDENCIAS INDIVIDUALES/             2.1 Diario, 2.2 Autoevaluación, 2.3 Formativa
├── EVIDENCIAS GRUPALES/                 2.4 a 2.7 y planilla de evaluación
└── EVIDENCIAS PROYECTO/
    ├── EVIDENCIAS DE DOCUMENTACION/     Diagramas, carta Gantt, plan y monitoreo
    ├── EVIDENCIAS DE SISTEMA/           APLICACION, BASE DE DATOS, pruebas y .bat
    └── PRESENTACION PROYECTO.pptx       Presentación de la Evaluación 3
```

## 12. Estado de los objetivos

| Objetivo | Estado |
|---|---|
| OE1 Requisitos de la Ley | En curso: falta contrastar la regla de menores con el texto oficial |
| OE2 Proceso y Modelo de Datos | Completado |
| OE3 Interfaz | Completado (rediseño del 18 de noviembre) |
| OE4 Prototipo Funcional | Completado el 18 de noviembre (10 días después de lo planificado) |
| OE5 Validación | En curso: 14 de 14 casos aprobados, falta la validación con retroalimentación docente |

## 13. Limitaciones y trabajo futuro

- Las reglas son un **apoyo** y no reemplazan el análisis jurídico.
- La aplicación se ejecuta **de forma local**, sin autenticación (los roles son una simulación).
- No permite editar directamente un registro guardado: la corrección se hace registrando de nuevo con los datos corregidos.
- Mejoras futuras: edición de registros, autenticación real, gestión de solicitudes de titulares, despliegue y revisión de reglas con un especialista.

## 14. Marco normativo y referencias

- Ley N° 21.719, que regula la protección y el tratamiento de los datos personales (publicada el 13 de diciembre de 2024). El 17 de noviembre de 2026 se aprobó postergar su entrada en vigencia al 15 de octubre de 2027, a la espera de su promulgación.
- Flask y SQLite: documentación oficial.
- ISO 31000: gestión del riesgo.

---

*Todos los datos de la aplicación son ficticios y no corresponden a personas ni empresas reales.*
