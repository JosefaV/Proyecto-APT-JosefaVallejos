"""
app.py - Aplicación web de Transparenta (Flask + SQLite).

Qué hace en esta primera versión:
  /                       Inicio: resumen, qué atender primero y guía de uso
  /registro               Registro de tratamientos con semáforo de brechas
  /tratamiento/<id>       Detalle de un tratamiento, sus brechas y los botones de decisión
  /bitacora               Bitácora de acciones

Idea clave: el software ORDENA, REVISA y RECUERDA, pero la persona DECIDE.
Por eso confirmar una revisión o marcar una supresión son botones que SOLO se aplican
cuando alguien los pulsa, y cada uno deja una línea en la bitácora.

Para ejecutarlo (desde la carpeta Aplicacion):   python app.py
"""
import sqlite3
from datetime import date, datetime
from pathlib import Path
from flask import Flask, render_template, redirect, url_for, request, abort

CARPETA = Path(__file__).parent
# La base de datos vive en la carpeta hermana "Base de Datos"
RUTA_BD = CARPETA.parent / "Base de Datos" / "transparenta.db"

app = Flask(__name__)

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
        brechas.append(("Alta", "Falta la base de licitud (Arts. 12 y 13)."))
        if t["categoria_dato"] == "Sensible":
            brechas.append(("Alta", "Dato sensible sin base que lo respalde (Arts. 2 g y 16)."))

    # 2) Menores de edad: se espera consentimiento
    if t["titulares"] != "Adultos" and t["base_licitud"] != "Consentimiento":
        brechas.append(("Alta", "Titulares menores de edad sin consentimiento (Art. 16 quáter)."))

    # 3) Terceros: contrato vigente y cláusula de supresión
    if t["tercero_id"]:
        if not t["contrato_vigente"]:
            brechas.append(("Media", f"El tercero «{t['tercero_nombre']}» no tiene contrato vigente."))
        if not t["clausula_supresion"]:
            brechas.append(("Media", f"El contrato con «{t['tercero_nombre']}» no tiene cláusula de supresión."))

    # 4) Plazo de conservación
    supresion, dias = None, None
    if t["plazo_meses"]:
        supresion = sumar_meses(date.fromisoformat(t["fecha_inicio"]), t["plazo_meses"])
        dias = (supresion - hoy).days
        if not t["suprimido"]:
            if dias < 0:
                brechas.append(("Alta", f"El plazo de conservación venció hace {-dias} días: corresponde suprimir."))
            elif dias <= 30:
                brechas.append(("Media", f"El plazo de conservación vence en {dias} días."))
    else:
        brechas.append(("Media", "No se definió un plazo de conservación."))

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
def cargar_filas():
    """Lee los tratamientos vigentes y calcula brechas y semáforo de cada uno."""
    con = conectar()
    filas = []
    for t in con.execute(CONSULTA + " WHERE t.suprimido = 0 ORDER BY t.id"):
        brechas, semaforo, supresion, dias = analizar(t)
        filas.append({"t": t, "brechas": brechas, "semaforo": semaforo, "supresion": supresion, "dias": dias})
    con.close()
    return filas

@app.route("/")
def inicio():
    """Pantalla de inicio: resumen general y lo que hay que atender primero."""
    filas = cargar_filas()
    orden = {"rojo": 0, "amarillo": 1, "verde": 2}
    cuenta = {k: sum(1 for f in filas if f["semaforo"] == k) for k in orden}
    urgentes = sorted([f for f in filas if f["semaforo"] == "rojo"], key=lambda f: -len(f["brechas"]))[:5]
    por_vencer = sorted([f for f in filas if f["dias"] is not None and 0 <= f["dias"] <= 60], key=lambda f: f["dias"])
    sin_revisar = [f for f in filas if not f["t"]["revisado_por"]]
    con = conectar()
    ultimas = con.execute("""SELECT b.*, t.actividad FROM bitacora b
                             LEFT JOIN tratamiento t ON t.id = b.tratamiento_id ORDER BY b.id DESC LIMIT 4""").fetchall()
    con.close()
    return render_template("inicio.html", cuenta=cuenta, total=len(filas), urgentes=urgentes,
                           por_vencer=por_vencer, sin_revisar=len(sin_revisar), ultimas=ultimas)

@app.route("/registro")
def registro():
    filas = cargar_filas()
    orden = {"rojo": 0, "amarillo": 1, "verde": 2}
    filas.sort(key=lambda x: (orden[x["semaforo"]], x["t"]["id"]))   # primero los rojos
    cuenta = {k: sum(1 for f in filas if f["semaforo"] == k) for k in orden}
    return render_template("registro.html", filas=filas, cuenta=cuenta)

@app.route("/tratamiento/<int:tid>")
def detalle(tid):
    con = conectar()
    t = con.execute(CONSULTA + " WHERE t.id = ?", (tid,)).fetchone()
    if t is None: abort(404)
    brechas, semaforo, supresion, dias = analizar(t)
    hist = con.execute("SELECT * FROM bitacora WHERE tratamiento_id = ? ORDER BY id DESC", (tid,)).fetchall()
    con.close()
    return render_template("detalle.html", t=t, brechas=brechas, semaforo=semaforo, supresion=supresion, dias=dias, hist=hist)

@app.route("/tratamiento/<int:tid>/revisar", methods=["POST"])
def revisar(tid):
    """La PERSONA confirma que revisó el tratamiento."""
    usuario = request.form.get("usuario", "").strip() or "Usuario"
    con = conectar()
    con.execute("UPDATE tratamiento SET revisado_por = ?, fecha_revision = ? WHERE id = ?",
                (usuario, date.today().isoformat(), tid))
    registrar(con, usuario, "Revisión", tid, "Revisión confirmada por una persona.")
    con.commit(); con.close()
    return redirect(url_for("detalle", tid=tid))

@app.route("/tratamiento/<int:tid>/suprimir", methods=["POST"])
def suprimir(tid):
    """La PERSONA confirma que los datos fueron suprimidos."""
    usuario = request.form.get("usuario", "").strip() or "Usuario"
    con = conectar()
    con.execute("UPDATE tratamiento SET suprimido = 1 WHERE id = ?", (tid,))
    registrar(con, usuario, "Supresión", tid, "Supresión confirmada por una persona.")
    con.commit(); con.close()
    return redirect(url_for("registro"))

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
