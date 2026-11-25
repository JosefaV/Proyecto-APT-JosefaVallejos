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
HOY = date.today()                 # fecha de referencia fija para la demo

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
    (1, "Contratación de personal", "Formalizar Contratos de Trabajo", "Común",
     "Nombre, Correo Electrónico, Dirección", "Trabajadores", "Mayores de Edad", "Contrato",
     "Formulario de Ingreso", "Camila Rojas", 60, 400, None, "Acceso Restringido a Recursos Humanos", "Camila Rojas", 30),
    (1, "Proceso de reclutamiento", "Evaluar Postulantes a Cargos", "Común",
     "Nombre, Correo Electrónico, Currículum", "Postulantes", "Mayores de Edad", None,           # SIN base de licitud -> brecha Alta
     "Portal de Empleo", "Camila Rojas", 6, 250, 1, "Carpeta Compartida", None, None),
    (1, "Exámenes preocupacionales", "Verificar Aptitud para el Cargo", "Sensible",
     "Resultados de Salud Ocupacional", "Trabajadores", "Mayores de Edad", "Obligación Legal",
     "Mutual de Seguridad", "Camila Rojas", 120, 300, None, "Cifrado de Disco", "Camila Rojas", 90),
    (1, "Taller de verano para hijos e hijas de colaboradores", "Organizar Actividades Recreativas", "Común",
     "Nombre, Edad, Contacto del Apoderado", "Familiares de Trabajadores", "Niños y Niñas (Menores de 14 años)", "Interés Legítimo",  # niños <14 sin consentimiento -> brecha Alta
     "Inscripción en Recursos Humanos", "Camila Rojas", 12, 200, None, "Acceso Restringido", None, None),
    (2, "Pago de remuneraciones", "Pagar Remuneraciones y Cotizaciones", "Económico",
     "Cuenta Bancaria, Remuneración", "Trabajadores", "Mayores de Edad", "Obligación Legal",
     "Contrato de Trabajo", "Diego Fuentes", 72, 600, 2, "Transferencia Cifrada", "Diego Fuentes", 20),
    (2, "Facturación a proveedores", "Registrar Pagos a Proveedores", "Económico",
     "Nombre, RUT Ficticio, Cuenta Bancaria", "Proveedores", "Mayores de Edad", "Contrato",
     "Factura Recibida", "Diego Fuentes", 72, 500, None, "Sistema Contable con Clave de Acceso", "Diego Fuentes", 45),
    (2, "Cobranza de clientes morosos", "Recuperar Deudas Pendientes", "Económico",
     "Nombre, Deuda, Historial de Pago", "Clientes", "Mayores de Edad", "Interés Legítimo",
     "Sistema de Ventas", "Diego Fuentes", 12, 500, None, "Acceso Restringido", "Diego Fuentes", 15),   # plazo VENCIDO
    (3, "Registro de clientes", "Gestionar la Relación Comercial", "Común",
     "Nombre, Correo Electrónico, Teléfono", "Clientes", "Mayores de Edad", "Contrato",
     "Formulario Web", "Valentina Soto", 36, 700, None, "CRM con autenticación", "Valentina Soto", 60),
    (3, "Campañas de marketing", "Enviar Promociones por Correo Electrónico", "Común",
     "Correo Electrónico, Preferencias", "Clientes", "Mayores de Edad", "Consentimiento",
     "Suscripción Voluntaria", "Valentina Soto", 12, 340, None, "Lista con Baja Automática", "Valentina Soto", 10),   # vence en ~1 mes
    (4, "Control de acceso a oficinas", "Resguardar la Seguridad Física del Edificio", "Sensible",
     "Huella Digital (Biométrico)", "Trabajadores", "Mayores de Edad", None,   # sensible SIN base -> brecha Alta
     "Lector Biométrico", "Matías Araya", 12, 100, None, "Cifrado Local", None, None),
    (4, "Geolocalización de vehículos", "Monitorear la Flota de Vehículos", "Geolocalización",
     "Ubicación de Conductores", "Trabajadores Externos", "Mayores de Edad", "Interés Legítimo",
     "GPS de Vehículos", "Matías Araya", 6, 190, 3, "Plataforma del Proveedor", "Matías Araya", 100),   # tercero con contrato vencido
    (4, "Respaldo de correos", "Asegurar la Continuidad Operacional", "Común",
     "Correos Corporativos", "Trabajadores", "Mayores de Edad", "Interés Legítimo",
     "Servidor de Correo", "Matías Araya", 24, 150, 3, "Respaldo Cifrado", "Matías Araya", 25),
]

BITACORA = [  # (dias_atras, usuario, accion, tratamiento_id, detalle)
    (30, "Camila Rojas", "Revisión", 1, "Revisión confirmada por el Responsable."),
    (20, "Diego Fuentes", "Revisión", 5, "Revisión confirmada por el Responsable."),
    (15, "Diego Fuentes", "Revisión", 7, "Revisión confirmada; se detecta un Plazo de Conservación próximo a vencer."),
    (10, "Valentina Soto", "Revisión", 9, "Revisión confirmada por el Responsable."),
    (5, "Matías Araya", "Alta", 11, "Alta del Tratamiento «Geolocalización de Vehículos»."),
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
