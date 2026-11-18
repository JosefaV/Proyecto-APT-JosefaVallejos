"""
app.py - Aplicación web de Transparenta (Flask + SQLite).

Qué hace en esta primera versión:
  /                       Inicio: resumen, qué atender primero y guía de uso
  /registro               Registro de tratamientos con semáforo de brechas
  /tratamiento/<id>       Detalle de un tratamiento, sus brechas y los botones de decisión
  /nuevo                  Formulario guiado para registrar un tratamiento nuevo
  /bitacora               Bitácora de acciones

Idea clave: el software ORDENA, REVISA y RECUERDA, pero la persona DECIDE.
Por eso confirmar una revisión o marcar una supresión son botones que SOLO se aplican
cuando alguien los pulsa, y cada uno deja una línea en la bitácora.

Para ejecutarlo (desde la carpeta Aplicacion):   python app.py
"""
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path
from flask import Flask, render_template, redirect, url_for, request, abort, session

CARPETA = Path(__file__).parent
# La base de datos vive en la carpeta hermana "Base de Datos"
RUTA_BD = CARPETA.parent / "Base de Datos" / "transparenta.db"

app = Flask(__name__)
app.secret_key = "transparenta-demo"   # solo para recordar el rol elegido (demo)

def conectar():
    """Abre la base de datos y deja que las filas se lean por nombre de columna."""
    con = sqlite3.connect(RUTA_BD)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def sumar_meses(fecha, meses):
    """Suma 'meses' a una fecha (calcula la fecha de supresión)."""
    m = fecha.month - 1 + meses
    anio, mes = fecha.year + m // 12, m % 12 + 1
    dia = min(fecha.day, [31, 29 if anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0) else 28,
                          31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1])
    return date(anio, mes, dia)

# ------------------------------------------------------------------ REGLAS DE BRECHAS
def analizar(t, hoy=None):
    """
    Recibe un tratamiento (una fila de la BD) y devuelve:
      - lista de brechas [(gravedad, texto), ...]
      - semáforo: 'rojo', 'amarillo' o 'verde'
      - fecha de supresión calculada y días que faltan
    Las reglas son un APOYO: no reemplazan el análisis jurídico.
    """
    hoy = hoy or date.today()
    brechas = []

    # 1) Base de licitud: todo tratamiento debe tener una
    if not t["base_licitud"]:
        brechas.append(("Alta", "Falta la Base de Licitud (Arts. 12 y 13)."))
        if t["categoria_dato"] == "Sensible":
            brechas.append(("Alta", "Dato Sensible sin base que lo respalde (Arts. 2 g y 16)."))

    # 2) Niños, niñas y adolescentes (Art. 16 quáter)
    #    - Menores de 14 años: se espera el consentimiento de sus padres o representantes.
    #    - Adolescentes (14-17): los datos comunes se tratan como en un adulto; los datos sensibles
    #      de menores de 16 años requieren consentimiento de sus padres, por eso se pide verificar.
    if t["titulares"] == "Niños y niñas (<14)" and t["base_licitud"] != "Consentimiento":
        brechas.append(("Alta", "Datos de Niños y Niñas menores de 14 años sin Consentimiento de sus padres o representantes (Art. 16 quáter)."))
    if t["titulares"] == "Adolescentes (14-17)" and t["categoria_dato"] == "Sensible" and t["base_licitud"] != "Consentimiento":
        brechas.append(("Media", "Datos Sensibles de Adolescentes: verifica si hay menores de 16 años, que requieren Consentimiento de sus padres (Art. 16 quáter)."))

    # 3) Terceros: contrato vigente y cláusula de supresión
    if t["tercero_id"]:
        if not t["contrato_vigente"]:
            brechas.append(("Media", f"El Tercero «{t['tercero_nombre']}» no tiene Contrato vigente."))
        if not t["clausula_supresion"]:
            brechas.append(("Media", f"El Contrato con «{t['tercero_nombre']}» no tiene Cláusula de Supresión."))

    # 4) Plazo de conservación
    supresion, dias = None, None
    if t["plazo_meses"]:
        supresion = sumar_meses(date.fromisoformat(t["fecha_inicio"]), t["plazo_meses"])
        dias = (supresion - hoy).days
        if not t["suprimido"]:
            if dias < 0:
                brechas.append(("Alta", f"El Plazo de Conservación venció hace {-dias} días: corresponde suprimir."))
            elif dias <= 30:
                brechas.append(("Media", f"El Plazo de Conservación vence en {dias} días."))
    else:
        brechas.append(("Media", "No se definió un Plazo de Conservación."))

    # 5) Revisión humana pendiente
    if not t["revisado_por"]:
        brechas.append(("Media", "Todavía no ha sido revisado por una persona."))

    if any(g == "Alta" for g, _ in brechas): semaforo = "rojo"
    elif brechas: semaforo = "amarillo"
    else: semaforo = "verde"
    return brechas, semaforo, supresion, dias

CONSULTA = """
SELECT t.*, a.nombre AS area_nombre, te.nombre AS tercero_nombre,
       te.contrato_vigente, te.clausula_supresion
FROM tratamiento t
JOIN area a ON a.id = t.area_id
LEFT JOIN tercero te ON te.id = t.tercero_id
"""

def registrar(con, usuario, accion, trat_id, detalle):
    """Deja una línea en la bitácora (trazabilidad)."""
    con.execute("INSERT INTO bitacora (fecha_hora, usuario, accion, tratamiento_id, detalle) VALUES (?,?,?,?,?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M"), usuario, accion, trat_id, detalle))

# ------------------------------------------------------------------ PANTALLAS
ORDEN = {"rojo": 0, "amarillo": 1, "verde": 2}

CATEGORIAS = [("Común", "Nombre, correo, teléfono, dirección"),
              ("Económico", "Deudas, pagos, cuentas bancarias, sueldos"),
              ("Sensible", "Salud, biométricos (huella), origen étnico, etc."),
              ("Geolocalización", "Ubicación, rutas, dispositivos")]
GRUPOS = ["Empleados", "Empleados Externos", "Postulantes", "Clientes", "Proveedores", "Familiares de Empleados"]
EDADES = ["Adultos", "Adolescentes (14-17)", "Niños y niñas (<14)"]
BASES = ["Consentimiento", "Contrato", "Obligación legal", "Interés legítimo", "Obligación económica", "Defensa de derechos"]

def lista_areas():
    con = conectar()
    areas = con.execute("SELECT * FROM area ORDER BY id").fetchall()
    con.close()
    return areas

def cargar_filas():
    """Lee los tratamientos vigentes y calcula brechas y semáforo de cada uno."""
    con = conectar()
    filas = []
    for t in con.execute(CONSULTA + " WHERE t.suprimido = 0 ORDER BY t.id"):
        brechas, semaforo, supresion, dias = analizar(t)
        filas.append({"t": t, "brechas": brechas, "semaforo": semaforo, "supresion": supresion, "dias": dias})
    con.close()
    if session.get("rol") == "area":          # el Responsable de Área solo ve su área
        filas = [f for f in filas if f["t"]["area_id"] == session.get("area_id", 1)]
    return filas



# ------------------------------------------------------------------ MAYÚSCULAS EN TÍTULOS
MENORES = {"de", "del", "la", "las", "el", "los", "y", "e", "o", "u", "a", "al", "en", "con", "por", "para", "un", "una", "sin", "su", "sus", "que"}

def titulo(texto):
    """Escribe un texto en formato título: 'Proceso de reclutamiento' -> 'Proceso de Reclutamiento'."""
    if not texto: return texto
    palabras, salida = str(texto).split(" "), []
    for i, p in enumerate(palabras):
        pura = p.strip("«»()¿?¡!,.")
        if i > 0 and pura.lower() in MENORES: salida.append(p)
        elif p[:1] in "«(" and len(p) > 1: salida.append(p[0] + p[1:2].upper() + p[2:])
        else: salida.append(p[:1].upper() + p[1:])
    return " ".join(salida)
app.jinja_env.filters["titulo"] = titulo

def fecha(texto):
    """'2026-07-30 12:35' -> '30-07-2026 12:35'."""
    if not texto: return texto
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})(.*)", str(texto))
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}{m.group(4)}" if m else texto
app.jinja_env.filters["fecha"] = fecha

# ------------------------------------------------------------------ ROL, AYUDAS Y TEXTOS
QUE_HACER = [("venció", "Suprime los datos y confirma la Supresión."),
             ("vence en", "Prepara la Supresión antes de que termine el Plazo."),
             ("No se definió", "Define por cuántos meses se guardarán los datos."),
             ("base de licitud", "Define con qué Derecho se tratan estos datos (por ejemplo, Contrato o Consentimiento)."),
             ("sin base", "Define con qué Derecho se tratan estos datos (por ejemplo, Contrato o Consentimiento)."),
             ("niños y niñas", "Obtén el Consentimiento de sus padres o representantes y regístralo."),
             ("adolescentes", "Verifica la edad y, si hay menores de 16 años, pide el Consentimiento de sus padres."),
             ("no tiene contrato", "Pide o renueva el Contrato con el Proveedor."),
             ("cláusula de supresión", "Agrega al Contrato la obligación de eliminar los datos al terminar."),
             ("revisado por una persona", "Revisa el Tratamiento y presiona Confirmar Revisión.")]

def que_hacer(texto):
    for clave, ayuda in QUE_HACER:
        if clave.lower() in texto.lower(): return ayuda
    return "Revisa este punto con tu equipo."
app.jinja_env.globals["que_hacer"] = que_hacer

@app.context_processor
def contexto():
    rol = session.get("rol", "coord")
    areas = lista_areas()
    area_id = session.get("area_id", 1)
    area = next((a for a in areas if a["id"] == area_id), areas[0])
    return {"rol": rol, "areas_menu": areas, "area_actual": area, "ep": request.endpoint}

@app.route("/rol/<r>")
def cambiar_rol(r):
    session["rol"] = "coord" if r == "coord" else "area"
    a = request.args.get("area", type=int)
    if a: session["area_id"] = a
    return redirect(request.referrer or url_for("inicio"))

@app.route("/plazos")
def plazos():
    filas = [f for f in cargar_filas() if f["dias"] is not None]
    filas.sort(key=lambda f: f["dias"])
    return render_template("plazos.html", filas=filas)

@app.route("/como-funciona")
def como():
    return render_template("como.html")

@app.route("/semaforo")
def semaforo_ayuda():
    return render_template("semaforo.html")

@app.route("/ley")
def ley():
    return render_template("ley.html")

@app.route("/")
def inicio():
    """Pantalla de inicio: resumen general y lo que hay que atender primero."""
    filas = cargar_filas()
    orden = ORDEN
    cuenta = {k: sum(1 for f in filas if f["semaforo"] == k) for k in orden}
    por_area = []
    for ar in lista_areas():
        fa = [f for f in filas if f["t"]["area_id"] == ar["id"]]
        por_area.append({"area": ar, "total": len(fa),
                         **{k: sum(1 for f in fa if f["semaforo"] == k) for k in orden}})
    urgentes = sorted([f for f in filas if f["semaforo"] == "rojo"], key=lambda f: -len(f["brechas"]))[:5]
    por_vencer = sorted([f for f in filas if f["dias"] is not None and 0 <= f["dias"] <= 60], key=lambda f: f["dias"])
    sin_revisar = [f for f in filas if not f["t"]["revisado_por"]]
    con = conectar()
    ultimas = con.execute("""SELECT b.*, t.actividad FROM bitacora b
                             LEFT JOIN tratamiento t ON t.id = b.tratamiento_id ORDER BY b.id DESC LIMIT 4""").fetchall()
    con.close()
    dias_es = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
    meses_es = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
    h = date.today()
    hoy_texto = f"{dias_es[h.weekday()].capitalize()}, {h.day} de {meses_es[h.month-1].capitalize()} de {h.year}"
    return render_template("inicio.html", hoy_texto=hoy_texto, cuenta=cuenta, total=len(filas), urgentes=urgentes,
                           por_vencer=por_vencer, sin_revisar=len(sin_revisar), ultimas=ultimas, por_area=por_area)

@app.route("/registro")
def registro():
    filas = cargar_filas()
    areas = lista_areas()
    area_id = request.args.get("area", type=int)
    estado = request.args.get("estado", "")
    if area_id:
        filas = [f for f in filas if f["t"]["area_id"] == area_id]
    cuenta = {k: sum(1 for f in filas if f["semaforo"] == k) for k in ORDEN}
    if estado in ORDEN:
        filas = [f for f in filas if f["semaforo"] == estado]
    filas.sort(key=lambda x: (ORDEN[x["semaforo"]], x["t"]["id"]))   # primero los rojos
    return render_template("registro.html", filas=filas, cuenta=cuenta, areas=areas, area_id=area_id, estado=estado)

@app.route("/tratamiento/<int:tid>")
def detalle(tid):
    con = conectar()
    t = con.execute(CONSULTA + " WHERE t.id = ?", (tid,)).fetchone()
    if t is None: abort(404)
    brechas, semaforo, supresion, dias = analizar(t)
    hist = con.execute("SELECT * FROM bitacora WHERE tratamiento_id = ? ORDER BY id DESC", (tid,)).fetchall()
    con.close()
    return render_template("detalle.html", es_nuevo=request.args.get("nuevo"), t=t, brechas=brechas, semaforo=semaforo, supresion=supresion, dias=dias, hist=hist)

@app.route("/tratamiento/<int:tid>/revisar", methods=["POST"])
def revisar(tid):
    """La PERSONA confirma que revisó el tratamiento."""
    usuario = titulo(request.form.get("usuario", "").strip()) or "Usuario"
    con = conectar()
    con.execute("UPDATE tratamiento SET revisado_por = ?, fecha_revision = ? WHERE id = ?",
                (usuario, date.today().isoformat(), tid))
    registrar(con, usuario, "Revisión", tid, "Revisión confirmada por una persona.")
    con.commit(); con.close()
    return redirect(url_for("detalle", tid=tid))

@app.route("/tratamiento/<int:tid>/suprimir", methods=["POST"])
def suprimir(tid):
    """La PERSONA confirma que los datos fueron suprimidos."""
    usuario = titulo(request.form.get("usuario", "").strip()) or "Usuario"
    con = conectar()
    con.execute("UPDATE tratamiento SET suprimido = 1 WHERE id = ?", (tid,))
    registrar(con, usuario, "Supresión", tid, "Supresión confirmada por una persona.")
    con.commit(); con.close()
    return redirect(url_for("registro"))


@app.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    """Formulario guiado para registrar un tratamiento. Al guardar, el sistema lo revisa al instante."""
    con = conectar()
    areas = con.execute("SELECT * FROM area ORDER BY id").fetchall()
    terceros = con.execute("SELECT * FROM tercero ORDER BY nombre").fetchall()
    errores, datos = [], {}
    if request.method == "POST":
        datos = {k: request.form.get(k, "").strip() for k in
                 ("area_id", "actividad", "finalidad", "categoria_dato", "detalle_datos", "grupo_titular", "titulares",
                  "base_licitud", "origen", "plazo_meses", "fecha_inicio", "tercero_id", "medidas_seguridad", "usuario")}
        datos["usuario"] = titulo(datos["usuario"])
        if not datos["actividad"]: errores.append("Cuéntanos qué actividad es (por ejemplo: Contratación de personal).")
        if not datos["finalidad"]: errores.append("Indica para qué se usan los datos.")
        if not datos["usuario"]: errores.append("Escribe tu nombre: la persona que registra queda en la Bitácora.")
        if not datos["area_id"].isdigit() or not any(str(a["id"]) == datos["area_id"] for a in areas):
            errores.append("Elige el área responsable.")
        if datos["categoria_dato"] not in [c for c, _ in CATEGORIAS]: errores.append("Elige la categoría de los datos.")
        if datos["grupo_titular"] not in GRUPOS: errores.append("Elige de quién son los datos.")
        if datos["titulares"] not in EDADES: errores.append("Indica la edad de las personas.")
        if datos["base_licitud"] and datos["base_licitud"] not in BASES: errores.append("La Base de Licitud no es válida.")
        try:
            plazo = int(datos["plazo_meses"]) if datos["plazo_meses"] else None
            if plazo is not None and plazo < 1: raise ValueError
        except ValueError:
            plazo = None; errores.append("El Plazo debe ser un número de meses mayor que 0.")
        try:
            date.fromisoformat(datos["fecha_inicio"])
        except ValueError:
            errores.append("Indica la fecha desde la que se tratan los datos.")
        if not errores:
            area = next(a for a in areas if str(a["id"]) == datos["area_id"])
            cur = con.execute("""INSERT INTO tratamiento (area_id, actividad, finalidad, categoria_dato, detalle_datos,
                        grupo_titular, titulares, base_licitud, origen, responsable, plazo_meses, fecha_inicio,
                        tercero_id, medidas_seguridad) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (int(datos["area_id"]), titulo(datos["actividad"]), datos["finalidad"], datos["categoria_dato"],
                         datos["detalle_datos"] or None, datos["grupo_titular"], datos["titulares"],
                         datos["base_licitud"] or None, datos["origen"] or None, area["responsable"], plazo,
                         datos["fecha_inicio"], int(datos["tercero_id"]) if datos["tercero_id"].isdigit() else None,
                         datos["medidas_seguridad"] or None))
            tid = cur.lastrowid
            registrar(con, datos["usuario"], "Alta", tid, f"Se registra el Tratamiento «{titulo(datos['actividad'])}».")
            con.commit(); con.close()
            return redirect(url_for("detalle", tid=tid, nuevo=1))
    con.close()
    return render_template("nuevo.html", areas=areas, terceros=terceros, categorias=CATEGORIAS, grupos=GRUPOS,
                           edades=EDADES, bases=BASES, errores=errores, d=datos, hoy=date.today().isoformat())

@app.route("/bitacora")
def bitacora():
    con = conectar()
    filas = con.execute("""SELECT b.*, t.actividad FROM bitacora b
                           LEFT JOIN tratamiento t ON t.id = b.tratamiento_id ORDER BY b.id DESC""").fetchall()
    con.close()
    return render_template("bitacora.html", filas=filas)

if __name__ == "__main__":
    if not RUTA_BD.exists():
        print("No encuentro la base de datos en:", RUTA_BD)
        print("Primero ejecuta crear_bd.py dentro de la carpeta 'Base de Datos'.")
    else:
        app.run(debug=True)
