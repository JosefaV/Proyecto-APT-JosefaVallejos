# Transparenta

**Sistema de Registro Dinámico de Tratamientos de Datos Personales y Evaluación de Brechas de Cumplimiento de la Ley N° 21.719**

Proyecto APT, asignatura Capstone (PTY4614), Ingeniería en Informática, Duoc UC.

| | |
|---|---|
| **Estudiante** | Josefa Vallejos Sánchez |
| **Docente** | Yerko Paredes Orellana |
| **Modalidad** | Desarrollo individual (modalidad autorizada, ya que Capstone es de modalidad grupal) |
| **Organización de demostración** | Nexa Soluciones TI (empresa ficticia) |
| **Fecha** | Noviembre de 2026 |

---

## Descripción

Transparenta es una herramienta de software local que permite a una organización mantener actualizado su Registro de Tratamientos de Datos Personales y verificar su estado de cumplimiento respecto de la Ley N° 21.719. El sistema:

- Registra cada actividad de tratamiento mediante un formulario guiado en cuatro pasos.
- Detecta brechas de cumplimiento con reglas basadas en artículos de la Ley y las resume en un Semáforo (Rojo, Amarillo y Verde).
- Organiza cada tratamiento según un modelo de ciclo de vida de los datos en cinco etapas: Recolectar, Usar y Compartir, Conservar, Suprimir y Revisar.
- Calcula las fechas de supresión y emite alertas de plazos de conservación.
- Requiere la confirmación de una persona para cada revisión y cada supresión, y deja el registro en una Bitácora de Decisiones.
- Genera un Informe de Seguimiento por etapas del ciclo de vida.

El sistema es un apoyo a la gestión: **no reemplaza el análisis jurídico** y no toma decisiones legales. Todos los datos incluidos son **completamente ficticios**.

## Marco Normativo

La Ley N° 21.719, que regula la protección y el tratamiento de los Datos Personales y crea la Agencia de Protección de Datos Personales, fue publicada en el Diario Oficial el 13 de Diciembre de 2024. Se encuentra en vacancia legal, con entrada en vigencia diferida. El 17 de Noviembre de 2026 el Congreso aprobó postergar su entrada en vigencia al 15 de Octubre de 2027, a la espera de su promulgación.

Artículos contrastados con el texto oficial e implementados como reglas:

| Artículo | Regla en el sistema |
|---|---|
| Art. 2, letra g | Identificación de Datos Sensibles |
| Art. 3, letra c | Plazo de conservación, alerta de vencimiento y supresión |
| Arts. 12 y 13 | Base de Licitud obligatoria para cada tratamiento |
| Art. 15 bis | Contrato vigente y Cláusula de Supresión con terceros |
| Art. 16 | Tratamiento de Datos Sensibles |
| Art. 16 quáter | Consentimiento de padres o representantes para niños y niñas menores de 14 años, y verificación para Datos Sensibles de adolescentes |

## Tecnologías

- Python 3 y Flask 3 (aplicación web local)
- SQLite (Base de Datos relacional de cuatro tablas: área, tercero, tratamiento y bitácora)
- Jinja2 y Bootstrap 5.3 (interfaz)

## Estructura del Repositorio

```
Proyecto-APT-JosefaVallejos/
├── Fase 1 - Definicion Proyecto APT/
│   ├── Evidencias Individuales/
│   └── Evidencias Grupales/
└── Fase 2 - Desarrollo del Proyecto APT/
    ├── Evidencias Individuales/
    ├── Evidencias Grupales/
    └── Evidencias Proyecto/
        ├── Evidencias de Documentacion/
        └── Evidencias de Sistema/
            ├── Aplicacion/
            ├── Base de Datos/
            ├── Iniciar Transparenta.bat
            ├── pruebas_validacion.py
            └── Reiniciar Datos de Demostracion.bat
```

- **Evidencias de Documentacion:** Plan de Trabajo, Carta Gantt, Tabla de Monitoreo, Diagrama de Proceso y Modelo de Datos ER.
- **Evidencias de Sistema:** código de la aplicación, Base de Datos con su esquema, script de pruebas y lanzadores.

## Ejecución (Windows)

**Requisito:** Python 3 instalado y agregado al PATH.

1. Descargar o clonar el repositorio y abrir la carpeta `Fase 2 - Desarrollo del Proyecto APT/Evidencias Proyecto/Evidencias de Sistema`.
2. Hacer doble clic en `Iniciar Transparenta.bat`. El lanzador instala Flask si no está presente, crea la Base de Datos en la primera ejecución y abre el navegador en `http://127.0.0.1:5000`.
3. Para cerrar el sistema, cerrar la ventana del lanzador o presionar `Ctrl + C`.

Para volver a los datos de demostración originales, ejecutar `Reiniciar Datos de Demostracion.bat`.

### Ejecución manual

```bash
pip install flask
cd "Base de Datos"
python crear_bd.py        # solo la primera vez
cd ../Aplicacion
python app.py             # http://127.0.0.1:5000
```

## Pruebas de Validación

Se diseñaron 14 Casos de Prueba simulados, con brechas puestas a propósito en datos ficticios. El script trabaja sobre una copia temporal y no modifica la Base de Datos original.

```bash
python pruebas_validacion.py
```

Resultado esperado: 14 de 14 casos aprobados.

## Roles de la Demostración

El selector de rol de la barra superior es una simulación para la demostración (el sistema no incluye autenticación):

- **Responsable de Área:** registra y resuelve los tratamientos de su área.
- **Coordinación de Cumplimiento:** supervisa todas las áreas y consulta el Informe de Seguimiento.

## Alcance y Proyecciones

El sistema se ejecuta de forma local. Se identifican como proyecciones su implantación en un servidor institucional con autenticación real de usuarios, la incorporación de Inteligencia Artificial local y la ampliación de las reglas a los derechos de los titulares.

## Autoría y Uso de Inteligencia Artificial

Proyecto de desarrollo individual (modalidad autorizada, ya que Capstone es de modalidad grupal). En el diseño y la programación se utilizó un asistente de Inteligencia Artificial generativa como apoyo, y las decisiones de diseño y la revisión de los resultados fueron realizadas por la estudiante.

Proyecto académico sin fines comerciales. No contiene Datos Personales reales.
