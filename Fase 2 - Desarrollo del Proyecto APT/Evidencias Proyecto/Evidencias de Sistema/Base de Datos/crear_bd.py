"""
crear_bd.py - Crea la base de datos de Transparenta y la llena con datos FICTICIOS.

Cómo funciona (en 3 ideas):
1. SQLite guarda todo en un solo archivo: transparenta.db (no hay que instalar nada).
2. schema.sql tiene las 4 tablas (area, tercero, tratamiento, bitacora).
3. Este script borra la base anterior, crea las tablas y agrega datos de ejemplo
   de una empresa inventada: "Nexa Soluciones TI". Ningún dato es real.

Para ejecutarlo:   python crear_bd.py
"""
import sqlite3
from datetime import date, timedelta
from pathlib import Path

CARPETA = Path(__file__).parent          # carpeta donde está este archivo
ARCHIVO_BD = CARPETA / "transparenta.db"  # archivo de la base de datos
HOY = date(2026, 10, 28)                 # fecha de referencia fija para la demo

def f(dias_atras):
    """Devuelve una fecha como texto 'AAAA-MM-DD', X días antes de HOY."""
    return (HOY - timedelta(days=dias_atras)).isoformat()

# ---------------------------------------------------------------- datos ficticios
AREAS = [  # (nombre, responsable)
    ("Recursos Humanos", "Camila Rojas"),
    ("Finanzas", "Diego Fuentes"),
    ("Comercial", "Valentina Soto"),
    ("Soporte TI", "Matías Araya"),
]

TERCEROS = [  # (nombre, rol, contrato_vigente, clausula_supresion)
    ("Head Hunter Andes SpA", "Encargado", 1, 0),   # contrato vigente, SIN cláusula de supresión -> brecha
    ("Nómina Express Ltda.", "Proveedor", 1, 1),
    ("Nube Segura Hosting", "Proveedor", 0, 0),     # contrato vencido -> brecha
]

# (area, actividad, finalidad, categoria, detalle, grupo_titular, titulares, base_licitud,
#  origen, responsable, plazo_meses, dias_desde_inicio, tercero, medidas, revisado_por, dias_desde_revision)
TRATAMIENTOS = [
    (1, "Contratación de personal", "Formalizar contratos de trabajo", "Común",
     "Nombre, correo, dirección", "Empleados", "Adultos", "Contrato",
     "Formulario de ingreso", "Camila Rojas", 60, 400, None, "Acceso restringido a RRHH", "Camila Rojas", 30),
    (1, "Proceso de reclutamiento", "Evaluar postulantes a cargos", "Común",
     "Nombre, correo, currículum", "Postulantes", "Adultos", None,           # SIN base de licitud -> brecha Alta
     "Portal de empleo", "Camila Rojas", 6, 250, 1, "Carpeta compartida", None, None),
    (1, "Exámenes preocupacionales", "Verificar aptitud para el cargo", "Sensible",
     "Resultados de salud ocupacional", "Empleados", "Adultos", "Obligación legal",
     "Mutual de seguridad", "Camila Rojas", 120, 300, None, "Cifrado en disco", "Camila Rojas", 90),
    (1, "Práctica profesional de adolescentes", "Gestionar prácticas de estudiantes", "Común",
     "Nombre, edad, colegio", "Empleados", "Adolescentes (14-17)", "Interés legítimo",  # menor sin consentimiento -> brecha
     "Convenio con liceo", "Camila Rojas", 12, 200, None, "Acceso restringido", None, None),
    (2, "Pago de remuneraciones", "Pagar sueldos y cotizaciones", "Económico",
     "Cuenta bancaria, sueldo", "Empleados", "Adultos", "Obligación legal",
     "Contrato de trabajo", "Diego Fuentes", 72, 600, 2, "Transferencia cifrada", "Diego Fuentes", 20),
    (2, "Facturación a proveedores", "Registrar pagos a proveedores", "Económico",
     "Nombre, RUT ficticio, cuenta", "Proveedores", "Adultos", "Contrato",
     "Factura recibida", "Diego Fuentes", 72, 500, None, "Sistema contable con clave", "Diego Fuentes", 45),
    (2, "Cobranza de clientes morosos", "Recuperar deudas pendientes", "Económico",
     "Nombre, deuda, historial de pago", "Clientes", "Adultos", "Interés legítimo",
     "Sistema de ventas", "Diego Fuentes", 12, 500, None, "Acceso restringido", "Diego Fuentes", 15),   # plazo VENCIDO
    (3, "Registro de clientes", "Gestionar la relación comercial", "Común",
     "Nombre, correo, teléfono", "Clientes", "Adultos", "Contrato",
     "Formulario web", "Valentina Soto", 36, 700, None, "CRM con autenticación", "Valentina Soto", 60),
    (3, "Campañas de marketing", "Enviar promociones por correo", "Común",
     "Correo, preferencias", "Clientes", "Adultos", "Consentimiento",
     "Suscripción voluntaria", "Valentina Soto", 12, 340, None, "Lista con baja automática", "Valentina Soto", 10),   # vence en ~1 mes
    (4, "Control de acceso a oficinas", "Seguridad física del edificio", "Sensible",
     "Huella digital (biométrico)", "Empleados", "Adultos", None,   # sensible SIN base -> brecha Alta
     "Lector biométrico", "Matías Araya", 12, 100, None, "Cifrado local", None, None),
    (4, "Geolocalización de vehículos", "Rastrear la flota de la empresa", "Geolocalización",
     "Ubicación de conductores", "Empleados Externos", "Adultos", "Interés legítimo",
     "GPS de vehículos", "Matías Araya", 6, 190, 3, "Plataforma del proveedor", "Matías Araya", 100),   # tercero con contrato vencido
    (4, "Respaldo de correos", "Continuidad del negocio", "Común",
     "Correos corporativos", "Empleados", "Adultos", "Interés legítimo",
     "Servidor de correo", "Matías Araya", 24, 150, 3, "Respaldo cifrado", "Matías Araya", 25),
]

BITACORA = [  # (dias_atras, usuario, accion, tratamiento_id, detalle)
    (30, "Camila Rojas", "Revisión", 1, "Registro revisado y confirmado."),
    (20, "Diego Fuentes", "Revisión", 5, "Registro revisado y confirmado."),
    (15, "Diego Fuentes", "Revisión", 7, "Registro revisado; se detecta plazo próximo a vencer."),
    (10, "Valentina Soto", "Revisión", 9, "Registro revisado y confirmado."),
    (5, "Matías Araya", "Alta", 11, "Se registra el tratamiento de geolocalización de vehículos."),
]

# ---------------------------------------------------------------- creación
def main():
    if ARCHIVO_BD.exists():
        ARCHIVO_BD.unlink()                       # borra la base anterior para empezar limpio
    con = sqlite3.connect(ARCHIVO_BD)             # crea el archivo transparenta.db
    con.execute("PRAGMA foreign_keys = ON")       # obliga a respetar las relaciones entre tablas
    con.executescript((CARPETA / "schema.sql").read_text(encoding="utf-8"))  # crea las 4 tablas

    con.executemany("INSERT INTO area (nombre, responsable) VALUES (?, ?)", AREAS)
    con.executemany("INSERT INTO tercero (nombre, rol, contrato_vigente, clausula_supresion) VALUES (?, ?, ?, ?)", TERCEROS)

    for t in TRATAMIENTOS:
        (area, act, fin, cat, det, grupo, tit, base, ori, resp, plazo, d_ini, terc, med, rev_por, d_rev) = t
        con.execute(
            """INSERT INTO tratamiento
               (area_id, actividad, finalidad, categoria_dato, detalle_datos, grupo_titular, titulares,
                base_licitud, origen, responsable, plazo_meses, fecha_inicio, tercero_id,
                medidas_seguridad, revisado_por, fecha_revision)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (area, act, fin, cat, det, grupo, tit, base, ori, resp, plazo, f(d_ini), terc, med,
             rev_por, f(d_rev) if d_rev is not None else None))

    for d, usuario, accion, trat, detalle in BITACORA:
        con.execute("INSERT INTO bitacora (fecha_hora, usuario, accion, tratamiento_id, detalle) VALUES (?,?,?,?,?)",
                    (f(d) + " 10:00", usuario, accion, trat, detalle))
    con.commit()

    # ---- comprobación: cuántas filas hay en cada tabla
    print("Base de datos creada:", ARCHIVO_BD.name)
    for tabla in ("area", "tercero", "tratamiento", "bitacora"):
        n = con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
        print(f"  {tabla:12s} {n} filas")
    con.close()

if __name__ == "__main__":
    main()
