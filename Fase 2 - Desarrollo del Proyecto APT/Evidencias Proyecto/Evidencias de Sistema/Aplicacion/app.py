"""
app.py - Aplicación web de Transparenta (Flask + SQLite).

Qué hace en esta primera versión:
  /                       Inicio: resumen, qué atender primero y guía de uso
  /registro               Registro de tratamientos con semáforo de brechas
  /tratamiento/<id>       Detalle de un tratamiento, sus brechas y los botones de decisión
  /nuevo                  Formulario guiado para registrar un tratamiento nuevo
  /bitacora               Bitácora de acciones
  /informe                Informe de seguimiento (imprimible / PDF)

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
        brechas.append(("Alta", "El Tratamiento carece de Base de Licitud (Arts. 12 y 13)."))
        if t["categoria_dato"] == "Sensible":
            brechas.append(("Alta", "Dato Sensible sin Base de Licitud que lo respalde (Arts. 2 g y 16)."))

    # 2) Niños, niñas y adolescentes (Art. 16 quáter)
    #    - Menores de 14 años: se espera el consentimiento de sus padres o representantes.
    #    - Adolescentes (14-17): los datos comunes se tratan como en un adulto; los datos sensibles
    #      de menores de 16 años requieren consentimiento de sus padres, por eso se pide verificar.
    if t["titulares"] == MENOR14 and t["base_licitud"] != "Consentimiento":
        brechas.append(("Alta", "Datos de Niños y Niñas menores de 14 años sin Consentimiento de sus padres o representantes (Art. 16 quáter)."))
    if t["titulares"] == ADOLESC and t["categoria_dato"] == "Sensible" and t["base_licitud"] != "Consentimiento":
        brechas.append(("Media", "Datos Sensibles de Adolescentes: se debe verificar si existen menores de 16 años, quienes requieren el Consentimiento de sus padres o representantes (Art. 16 quáter)."))

    # 3) Terceros: contrato vigente y cláusula de supresión
    if t["tercero_id"]:
        if not t["contrato_vigente"]:
            brechas.append(("Media", f"El Tercero Receptor «{t['tercero_nombre']}» no tiene Contrato vigente."))
        if not t["clausula_supresion"]:
            brechas.append(("Media", f"El Contrato con «{t['tercero_nombre']}» no tiene Cláusula de Supresión."))

    # 4) Plazo de conservación
    supresion, dias = None, None
    if t["plazo_meses"]:
        supresion = sumar_meses(date.fromisoformat(t["fecha_inicio"]), t["plazo_meses"])
        dias = (supresion - hoy).days
        if not t["suprimido"]:
            if dias < 0:
                brechas.append(("Alta", f"El Plazo de Conservación venció hace {-dias} días: corresponde la Supresión."))
            elif dias <= 30:
                brechas.append(("Media", f"El Plazo de Conservación vence en {dias} días."))
    else:
        brechas.append(("Media", "No se definió un Plazo de Conservación."))

    # 5) Revisión humana pendiente
    if not t["revisado_por"]:
        brechas.append(("Media", "El Tratamiento aún no cuenta con Revisión de una persona."))

    if any(g == "Alta" for g, _ in brechas): semaforo = "rojo"
    elif brechas: semaforo = "amarillo"
    else: semaforo = "verde"
    return brechas, semaforo, supresion, dias

# ------------------------------------------------------------------ CICLO DE VIDA DE LOS DATOS
# Cada tratamiento recorre 5 etapas. Para cada una el sistema indica: ok / aviso / alerta / info.
ETAPAS = [
 {"k": "recolectar", "n": 1, "nombre": "Recolectar", "icono": "bi-pencil-square",
  "pregunta": "Identificar qué datos se solicitan, con qué finalidad y bajo qué Base de Licitud.",
  "ley": "Todo tratamiento requiere una finalidad determinada y una Base de Licitud (por ejemplo, Contrato o Consentimiento). Los datos de niños, niñas y adolescentes están sujetos a reglas especiales (Art. 16 quáter).",
  "revisa": "Que cada tratamiento cuente con finalidad, Base de Licitud y, cuando corresponda, el Consentimiento de los padres o representantes.",
  "tu": "Registrar cada actividad que utilice Datos Personales y completar su Base de Licitud."},
 {"k": "compartir", "n": 2, "nombre": "Usar y Compartir", "icono": "bi-people",
  "pregunta": "Determinar quién utiliza los datos y con qué terceros se comparten.",
  "ley": "Cuando un tercero (proveedor o encargado) trata los datos, debe existir un Contrato vigente que le exija resguardarlos y suprimirlos al término de la relación.",
  "revisa": "Que cada Tercero Receptor tenga Contrato vigente y Cláusula de Supresión.",
  "tu": "Solicitar o renovar el Contrato e incorporar la Cláusula de Supresión."},
 {"k": "conservar", "n": 3, "nombre": "Conservar", "icono": "bi-clock-history",
  "pregunta": "Establecer por cuánto tiempo se conservan los datos.",
  "ley": "Los datos solo pueden conservarse durante el tiempo necesario para cumplir su finalidad.",
  "revisa": "Que cada tratamiento tenga un Plazo de Conservación definido y se calcule el tiempo restante.",
  "tu": "Definir el Plazo de Conservación en meses y monitorear los plazos próximos a vencer."},
 {"k": "suprimir", "n": 4, "nombre": "Suprimir", "icono": "bi-trash3",
  "pregunta": "Verificar la supresión de los datos una vez vencido el plazo.",
  "ley": "Vencido el plazo, los datos deben suprimirse o anonimizarse.",
  "revisa": "Qué tratamientos cumplieron su plazo y aún no han sido suprimidos.",
  "tu": "Eliminar los datos y registrar la acción con Marcar como Suprimido, lo que queda en la Bitácora de Decisiones."},
 {"k": "revisar", "n": 5, "nombre": "Revisar", "icono": "bi-person-check",
  "pregunta": "Confirmar que una persona valida cada decisión.",
  "ley": "La organización debe poder demostrar su cumplimiento (Responsabilidad Proactiva). Por ello, cada decisión es confirmada por una persona y queda registrada.",
  "revisa": "Que cada tratamiento tenga una Revisión confirmada por una persona.",
  "tu": "Abrir el tratamiento y presionar Confirmar Revisión."},
]
ETAPA_POR_K = {e["k"]: e for e in ETAPAS}
ESTADO_ORDEN = {"alerta": 0, "aviso": 1, "ok": 2, "info": 3}

def etapas_de(t, brechas, supresion, dias):
    """Estado de las 5 etapas del ciclo de vida de un tratamiento: {clave: (estado, texto corto)}."""
    r = {}
    menores = any("16 quáter" in tx and g == "Alta" for g, tx in brechas)
    if not t["base_licitud"]: r["recolectar"] = ("alerta", "Sin Base de Licitud")
    elif menores: r["recolectar"] = ("alerta", "Sin Consentimiento de Padres o Representantes")
    elif not t["finalidad"]: r["recolectar"] = ("aviso", "Sin Finalidad Definida")
    else: r["recolectar"] = ("ok", "Base: " + titulo(t["base_licitud"]))
    if t["tercero_id"]:
        if not t["contrato_vigente"]: r["compartir"] = ("aviso", "Contrato no vigente: " + t["tercero_nombre"])
        elif not t["clausula_supresion"]: r["compartir"] = ("aviso", "Contrato sin Cláusula de Supresión")
        else: r["compartir"] = ("ok", "Contrato vigente: " + t["tercero_nombre"])
    else: r["compartir"] = ("info", "Sin Terceros Receptores")
    if t["suprimido"]: r["conservar"] = ("info", "Suprimido")
    elif not t["plazo_meses"]: r["conservar"] = ("aviso", "Sin Plazo de Conservación")
    elif dias < 0: r["conservar"] = ("alerta", f"Plazo vencido hace {-dias} días")
    elif dias <= 30: r["conservar"] = ("aviso", f"Vence en {dias} días")
    else: r["conservar"] = ("ok", "Vigente hasta el " + supresion.strftime("%d-%m-%Y"))
    if t["suprimido"]: r["suprimir"] = ("ok", "Suprimido")
    elif t["plazo_meses"] and dias < 0: r["suprimir"] = ("alerta", "Supresión Pendiente")
    elif t["plazo_meses"] and dias <= 30: r["suprimir"] = ("aviso", "Supresión Próxima")
    else: r["suprimir"] = ("info", "Plazo en Curso")
    if t["revisado_por"]: r["revisar"] = ("ok", "Revisado por " + titulo(t["revisado_por"]))
    else: r["revisar"] = ("aviso", "Pendiente de Revisión")
    return r

def resumen_ciclo(filas, suprimidos=0):
    """Una tarjeta por etapa, con cuántos tratamientos están bien y cuántos necesitan atención."""
    n = len(filas); out = []
    for e in ETAPAS:
        c = {x: sum(1 for f in filas if f["etapas"][e["k"]][0] == x) for x in ESTADO_ORDEN}
        k = e["k"]
        if k == "recolectar": txt = f"{c['ok']} de {n} con Base de Licitud y Finalidad"
        elif k == "compartir":
            con_t = c["ok"] + c["aviso"] + c["alerta"]
            txt = f"{con_t} con Terceros Receptores · {c['aviso']} con Contrato por regularizar"
        elif k == "conservar": txt = f"{c['alerta']} Plazos vencidos · {c['aviso']} por vencer"
        elif k == "suprimir": txt = f"{c['alerta'] + c['aviso']} con Supresión pendiente · {suprimidos} suprimidos"
        else: txt = f"{c['ok']} de {n} con Revisión confirmada"
        out.append({**e, "c": c, "txt": txt, "atencion": c["alerta"] + c["aviso"]})
    return out

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

CATEGORIAS = [("Común", "Nombre, Correo Electrónico, Teléfono, Dirección"),
              ("Económico", "Deudas, Pagos, Cuentas Bancarias, Remuneraciones"),
              ("Sensible", "Salud, Datos Biométricos, Origen Étnico, entre otros"),
              ("Geolocalización", "Ubicación, Rutas, Dispositivos")]
GRUPOS = ["Trabajadores", "Trabajadores Externos", "Postulantes", "Clientes", "Proveedores", "Familiares de Trabajadores"]
MAYOR, ADOLESC, MENOR14 = "Mayores de Edad", "Adolescentes (14 a 17 años)", "Niños y Niñas (Menores de 14 años)"
EDADES = [MAYOR, ADOLESC, MENOR14]
BASES = ["Consentimiento", "Contrato", "Obligación Legal", "Interés Legítimo", "Defensa de Derechos"]

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
        filas.append({"t": t, "brechas": brechas, "semaforo": semaforo, "supresion": supresion, "dias": dias,
                      "etapas": etapas_de(t, brechas, supresion, dias)})
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
QUE_HACER = [("venció", "Suprimir los datos y confirmar la Supresión."),
             ("vence en", "Preparar la Supresión antes del término del Plazo de Conservación."),
             ("No se definió", "Definir el Plazo de Conservación en meses."),
             ("base de licitud", "Determinar el fundamento de licitud del Tratamiento (por ejemplo, Contrato o Consentimiento)."),
             ("sin base", "Determinar el fundamento de licitud del Tratamiento (por ejemplo, Contrato o Consentimiento)."),
             ("niños y niñas", "Obtener el Consentimiento de los padres o representantes y registrarlo."),
             ("adolescentes", "Verificar la edad de los titulares y, si existen menores de 16 años, solicitar el Consentimiento de sus padres o representantes."),
             ("no tiene contrato", "Solicitar o renovar el Contrato con el Tercero Receptor."),
             ("cláusula de supresión", "Incorporar al Contrato la obligación de suprimir los datos al término de la relación."),
             ("revisión de una persona", "Revisar el Tratamiento y presionar Confirmar Revisión.")]

def que_hacer(texto):
    for clave, ayuda in QUE_HACER:
        if clave.lower() in texto.lower(): return ayuda
    return "Revisar este punto con el equipo responsable."
app.jinja_env.globals["que_hacer"] = que_hacer

@app.context_processor
def contexto():
    rol = session.get("rol", "coord")
    areas = lista_areas()
    area_id = session.get("area_id", 1)
    area = next((a for a in areas if a["id"] == area_id), areas[0])
    return {"rol": rol, "areas_menu": areas, "area_actual": area, "ep": request.endpoint,
            "etapas_menu": ETAPAS, "etapa_k": (request.view_args or {}).get("clave")}

@app.route("/rol/<r>")
def cambiar_rol(r):
    session["rol"] = "coord" if r == "coord" else "area"
    a = request.args.get("area", type=int)
    if a: session["area_id"] = a
    return redirect(request.referrer or url_for("inicio"))

@app.route("/etapa/<clave>")
def etapa(clave):
    """Una etapa del ciclo de vida: qué dice la Ley, qué revisa el sistema y en qué estado está cada tratamiento."""
    e = ETAPA_POR_K.get(clave)
    if e is None: abort(404)
    filas = cargar_filas()
    filas.sort(key=lambda f: (ESTADO_ORDEN[f["etapas"][clave][0]], f["t"]["id"]))
    cuenta = {x: sum(1 for f in filas if f["etapas"][clave][0] == x) for x in ESTADO_ORDEN}
    con = conectar()
    sup = con.execute(CONSULTA + " WHERE t.suprimido = 1 ORDER BY t.id").fetchall() if clave == "suprimir" else []
    con.close()
    return render_template("etapa.html", e=e, filas=filas, cuenta=cuenta, suprimidos=sup)

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
    hoy_texto = f"{dias_es[h.weekday()].capitalize()}, {h.day} de {meses_es[h.month-1]} de {h.year}"
    con2 = conectar(); suprimidos = con2.execute("SELECT COUNT(*) FROM tratamiento WHERE suprimido = 1").fetchone()[0]; con2.close()
    return render_template("inicio.html", ciclo=resumen_ciclo(filas, suprimidos), hoy_texto=hoy_texto, cuenta=cuenta, total=len(filas), urgentes=urgentes,
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
    et = etapas_de(t, brechas, supresion, dias)
    return render_template("detalle.html", es_nuevo=request.args.get("nuevo"), t=t, brechas=brechas, semaforo=semaforo, supresion=supresion, dias=dias, hist=hist, et=et)

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
        for k in ("finalidad", "detalle_datos", "origen", "medidas_seguridad"): datos[k] = titulo(datos[k])
        if not datos["actividad"]: errores.append("Se debe indicar la Actividad de Tratamiento (por ejemplo: Contratación de Personal).")
        if not datos["finalidad"]: errores.append("Se debe indicar la Finalidad del Tratamiento.")
        if not datos["usuario"]: errores.append("Se debe indicar el nombre del responsable del registro, que queda en la Bitácora de Decisiones.")
        if not datos["area_id"].isdigit() or not any(str(a["id"]) == datos["area_id"] for a in areas):
            errores.append("Se debe seleccionar el Área Responsable.")
        if datos["categoria_dato"] not in [c for c, _ in CATEGORIAS]: errores.append("Se debe seleccionar la Categoría de Datos Personales.")
        if datos["grupo_titular"] not in GRUPOS: errores.append("Se debe seleccionar la Categoría de Titulares.")
        if datos["titulares"] not in EDADES: errores.append("Se debe seleccionar el Tramo Etario de los Titulares.")
        if datos["base_licitud"] and datos["base_licitud"] not in BASES: errores.append("La Base de Licitud no es válida.")
        try:
            plazo = int(datos["plazo_meses"]) if datos["plazo_meses"] else None
            if plazo is not None and plazo < 1: raise ValueError
        except ValueError:
            plazo = None; errores.append("El Plazo de Conservación debe ser un número de meses mayor que 0.")
        try:
            date.fromisoformat(datos["fecha_inicio"])
        except ValueError:
            errores.append("Se debe indicar la Fecha de Inicio del Tratamiento.")
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
            registrar(con, datos["usuario"], "Alta", tid, f"Alta del Tratamiento «{titulo(datos['actividad'])}».")
            con.commit(); con.close()
            return redirect(url_for("detalle", tid=tid, nuevo=1))
    con.close()
    return render_template("nuevo.html", areas=areas, terceros=terceros, categorias=CATEGORIAS, grupos=GRUPOS,
                           edades=EDADES, bases=BASES, errores=errores, d=datos, hoy=date.today().isoformat())

@app.route("/informe")
def informe():
    """Informe de Seguimiento: foto del estado de cumplimiento, lista para imprimir o guardar como PDF."""
    filas = cargar_filas()
    filas.sort(key=lambda x: (ORDEN[x["semaforo"]], x["t"]["id"]))
    total = len(filas)
    cuenta = {k: sum(1 for f in filas if f["semaforo"] == k) for k in ORDEN}
    resumen = {
        "revisados": sum(1 for f in filas if f["t"]["revisado_por"]),
        "vencidos": sum(1 for f in filas if f["dias"] is not None and f["dias"] < 0),
        "por_vencer": sum(1 for f in filas if f["dias"] is not None and 0 <= f["dias"] <= 30),
        "pct_orden": round(cuenta["verde"] / total * 100) if total else 0,
    }
    pendientes = [f for f in filas if f["brechas"]]
    con = conectar()
    suprimidos = con.execute("SELECT COUNT(*) FROM tratamiento WHERE suprimido = 1").fetchone()[0]
    if session.get("rol") == "area":
        movs = con.execute("""SELECT b.*, t.actividad FROM bitacora b JOIN tratamiento t ON t.id = b.tratamiento_id
                              WHERE t.area_id = ? ORDER BY b.id DESC LIMIT 8""", (session.get("area_id", 1),)).fetchall()
    else:
        movs = con.execute("""SELECT b.*, t.actividad FROM bitacora b
                              LEFT JOIN tratamiento t ON t.id = b.tratamiento_id ORDER BY b.id DESC LIMIT 8""").fetchall()
    con.close()
    return render_template("informe.html", ciclo=resumen_ciclo(filas, suprimidos), filas=filas, total=total, cuenta=cuenta, resumen=resumen,
                           pendientes=pendientes, suprimidos=suprimidos, movs=movs, hoy=date.today())

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
        app.run(host="127.0.0.1", port=5000, debug=False)
