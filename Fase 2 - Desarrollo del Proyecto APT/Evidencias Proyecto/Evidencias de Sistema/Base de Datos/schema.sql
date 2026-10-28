-- Transparenta - Modelo de datos (SQLite). Datos 100% ficticios.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS area (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL UNIQUE,
    responsable  TEXT
);

CREATE TABLE IF NOT EXISTS tercero (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre             TEXT NOT NULL,
    rol                TEXT NOT NULL CHECK (rol IN ('Encargado','Proveedor','Otro')),
    contrato_vigente   INTEGER NOT NULL DEFAULT 0 CHECK (contrato_vigente IN (0,1)),
    clausula_supresion INTEGER NOT NULL DEFAULT 0 CHECK (clausula_supresion IN (0,1))
);

CREATE TABLE IF NOT EXISTS tratamiento (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    area_id             INTEGER NOT NULL REFERENCES area(id),
    actividad           TEXT NOT NULL,
    finalidad           TEXT,
    categoria_dato      TEXT NOT NULL CHECK (categoria_dato IN ('Común','Económico','Sensible','Geolocalización')),
    detalle_datos       TEXT,
    grupo_titular       TEXT NOT NULL CHECK (grupo_titular IN ('Empleados','Empleados Externos','Proveedores','Clientes','Postulantes')),
    titulares           TEXT NOT NULL CHECK (titulares IN ('Adultos','Adolescentes (14-17)','Niños y niñas (<14)')),
    base_licitud        TEXT CHECK (base_licitud IN ('Consentimiento','Contrato','Obligación legal','Interés legítimo','Obligación económica','Defensa de derechos') OR base_licitud IS NULL),
    origen              TEXT,
    responsable         TEXT,
    plazo_meses         INTEGER,
    fecha_inicio        TEXT NOT NULL,
    tercero_id          INTEGER REFERENCES tercero(id),
    medidas_seguridad   TEXT,
    revisado_por        TEXT,
    fecha_revision      TEXT,
    suprimido           INTEGER NOT NULL DEFAULT 0 CHECK (suprimido IN (0,1))
);

CREATE TABLE IF NOT EXISTS bitacora (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_hora     TEXT NOT NULL,
    usuario        TEXT NOT NULL,
    accion         TEXT NOT NULL,
    tratamiento_id INTEGER REFERENCES tratamiento(id),
    detalle        TEXT
);
