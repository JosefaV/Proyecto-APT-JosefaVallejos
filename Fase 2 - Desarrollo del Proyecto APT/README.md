# TRANSPARENTA - PROYECTO APT (CAPSTONE PTY4614)

Autora: Josefa Vallejos Sanchez (trabajo individual). Docente: Yerko Paredes Orellana.

Transparenta es una aplicacion web local (Python, Flask y SQLite) que ordena el Registro de Tratamientos de Datos Personales de una organizacion, detecta brechas respecto de la Ley N° 21.719 con un semaforo, avisa los plazos de conservacion y deja una bitacora de decisiones. Todo dato es ficticio (empresa ficticia Nexa Soluciones TI).

## Estructura de la Fase 2

- EVIDENCIAS INDIVIDUALES: 2.1 Diario de Reflexion, 2.2 Autoevaluacion y 2.3 Formativa.
- EVIDENCIAS GRUPALES: 2.4 Guia del Estudiante (espanol e ingles), 2.5 Sumativa de Avance, 2.6 Guia del Informe Final, 2.7 Sumativa Final y la planilla de evaluacion del docente.
- EVIDENCIAS PROYECTO / EVIDENCIAS DE DOCUMENTACION: diagramas (modelo de datos y proceso), carta Gantt, plan de trabajo y tabla de monitoreo.
- EVIDENCIAS PROYECTO / EVIDENCIAS DE SISTEMA: APLICACION, BASE DE DATOS, pruebas_validacion.py e Iniciar Transparenta.bat.
- EVIDENCIAS PROYECTO / PRESENTACION PROYECTO: presentacion de la Evaluacion 3.

## Como ejecutarla (Windows)

1. Instalar Python 3 y ejecutar `pip install flask`.
2. Hacer doble clic en `Iniciar Transparenta.bat` (crea la base de datos si falta y abre el navegador en http://127.0.0.1:5000).
3. Para correr las 14 pruebas de validacion: `python pruebas_validacion.py`.

## Limitaciones

Las reglas son un apoyo y no reemplazan el analisis juridico. La aplicacion se ejecuta de forma local, sin autenticacion, sin edicion directa de registros guardados y sin gestion de solicitudes de titulares (mejoras futuras).
