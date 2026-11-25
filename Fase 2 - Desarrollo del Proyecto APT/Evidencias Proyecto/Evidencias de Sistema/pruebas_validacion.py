"""
pruebas_validacion.py - Casos de prueba de Transparenta (OE5, validación con casos simulados).

Dónde ponerlo: en la carpeta "Evidencias de Sistema", al lado de "Aplicacion" y "Base de Datos".
Cómo ejecutarlo:   python pruebas_validacion.py
No modifica tu base de datos: trabaja sobre una copia temporal.
"""
import sys, shutil, tempfile
from datetime import date, timedelta
from pathlib import Path

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI / "Aplicacion"))
import app as A

# Copia temporal de la base de datos para no tocar la original
tmp = Path(tempfile.mkdtemp()) / "prueba.db"
shutil.copy(AQUI / "Base de Datos" / "transparenta.db", tmp)
A.RUTA_BD = tmp

HOY = date.today()
def base(**cambios):
    """Un tratamiento sin brechas; cada caso cambia solo lo que quiere probar."""
    t = dict(base_licitud="Contrato", categoria_dato="Común", titulares="Mayores de Edad", tercero_id=None, tercero_nombre=None,
             contrato_vigente=1, clausula_supresion=1, plazo_meses=36, fecha_inicio=(HOY - timedelta(days=30)).isoformat(),
             suprimido=0, revisado_por="Camila Rojas")
    t.update(cambios); return t

# (descripción, tratamiento, semáforo esperado, texto que debe aparecer en las brechas o None)
CASOS = [
    ("Tratamiento completo, sin brechas", base(), "verde", None),
    ("Sin base de licitud", base(base_licitud=None), "rojo", "base de licitud"),
    ("Dato sensible sin base de licitud", base(base_licitud=None, categoria_dato="Sensible"), "rojo", "sensible"),
    ("Niños menores de 14 años sin consentimiento", base(titulares="Niños y Niñas (Menores de 14 años)", base_licitud="Interés Legítimo"), "rojo", "menores de 14"),
    ("Niños menores de 14 años con consentimiento", base(titulares="Niños y Niñas (Menores de 14 años)", base_licitud="Consentimiento"), "verde", None),
    ("Adolescentes (14 a 17) con dato común", base(titulares="Adolescentes (14 a 17 años)"), "verde", None),
    ("Adolescentes con dato sensible sin consentimiento", base(titulares="Adolescentes (14 a 17 años)", categoria_dato="Sensible", base_licitud="Obligación Legal"), "amarillo", "menores de 16"),
    ("Tercero con contrato vencido", base(tercero_id=3, tercero_nombre="Nube Segura Hosting", contrato_vigente=0), "amarillo", "no tiene contrato"),
    ("Tercero sin cláusula de supresión", base(tercero_id=1, tercero_nombre="Head Hunter Andes SpA", clausula_supresion=0), "amarillo", "cláusula"),
    ("Plazo de conservación vencido", base(plazo_meses=1, fecha_inicio=(HOY - timedelta(days=200)).isoformat()), "rojo", "venció"),
    ("Plazo que vence en menos de 30 días", base(plazo_meses=12, fecha_inicio=(HOY - timedelta(days=345)).isoformat()), "amarillo", "vence en"),
    ("Sin revisión de una persona", base(revisado_por=None), "amarillo", "revisión de una persona"),
]

def main():
    resultados, ok = [], 0
    print(f"{'N°':>2}  {'Caso':52s} {'Esperado':9s} {'Obtenido':9s} Resultado")
    for n, (desc, t, esperado, texto) in enumerate(CASOS, 1):
        brechas, semaforo, _, _ = A.analizar(t)
        junto = " ".join(b[1] for b in brechas).lower()
        bien = semaforo == esperado and (texto is None or texto.lower() in junto)
        ok += bien
        print(f"{n:>2}  {desc:52s} {esperado:9s} {semaforo:9s} {'OK' if bien else 'FALLA'}")

    # Pruebas del formulario "Nuevo Registro" (validación y guardado)
    cli = A.app.test_client()
    r = cli.post("/nuevo", data={"actividad": "x"})
    bien = r.status_code == 200 and "Se deben corregir los siguientes puntos".encode() in r.data
    ok += bien; n = len(CASOS) + 1
    print(f"{n:>2}  {'Formulario incompleto: se rechaza y explica':52s} {'rechaza':9s} {'rechaza' if bien else 'guarda':9s} {'OK' if bien else 'FALLA'}")
    datos = dict(area_id="1", actividad="prueba de registro", finalidad="Probar el formulario", categoria_dato="Común",
                 grupo_titular="Trabajadores", titulares="Mayores de Edad", base_licitud="Contrato", plazo_meses="6",
                 fecha_inicio=HOY.isoformat(), usuario="josefa vallejos")
    r = cli.post("/nuevo", data=datos, follow_redirects=True)
    texto = r.data.decode()
    bien = r.status_code == 200 and "Prueba de Registro" in texto and "Tratamiento Registrado!" in texto
    ok += bien; n += 1
    print(f"{n:>2}  {'Formulario completo: guarda y deja la Bitácora':52s} {'guarda':9s} {'guarda' if bien else 'falla':9s} {'OK' if bien else 'FALLA'}")
    total = len(CASOS) + 2
    print(f"\nResultado: {ok} de {total} casos aprobados.")
    return ok == total

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
