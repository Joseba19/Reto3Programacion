import json
import sqlite3
from datetime import date

def crearTablas():
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    cursor.execute("""         
        CREATE TABLE IF NOT EXISTS componentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo VARCHAR(50) UNIQUE NOT NULL,
            descripcion VARCHAR(200) NOT NULL,
            stock INTEGER DEFAULT 0
        );
            """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recepciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            codigo_componente VARCHAR(50) NOT NULL,
            descripcion VARCHAR(200) NOT NULL,
            cantidad INTEGER NOT NULL,
            cantidad_defectuosas INTEGER,
            lote VARCHAR(50) NOT NULL,
            proveedor VARCHAR(100),
            estado VARCHAR(20) NOT NULL,
            observaciones TEXT
        );
            """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS defectuosos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_recepcion INTEGER NOT NULL,
            cantidad_defectuosa INTEGER NOT NULL,
            tipo_defecto VARCHAR(100),
            FOREIGN KEY (id_recepcion) REFERENCES recepciones(id)
        );   
            """)
    
    conn.commit()
    conn.close()

def insertarEntradas(fecha, codigo, descripcion, cantidad, cantidad_defectuosas, proveedor, lote, estado, observaciones):
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(fecha) FROM recepciones")
    ultimaFecha = cursor.fetchall()
    
    if ultimaFecha[0][0] is None or ultimaFecha[0][0] >= fecha:
        cursor.execute(f"INSERT INTO recepciones(fecha, codigo_componente, descripcion, cantidad, cantidad_defectuosas, proveedor, lote, estado, observaciones) VALUES ('{fecha}', '{codigo}', '{descripcion}', {cantidad}, '{cantidad_defectuosas}', '{proveedor}', '{lote}', '{estado}', '{observaciones}')")
    conn.commit()
    conn.close()

def entradaToComponentes(fecha):
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recepciones")
    salida = cursor.fetchall()
    cursor.execute("SELECT MAX(fecha) FROM recepciones")
    ultimaFecha = cursor.fetchall()

    if ultimaFecha[0][0] <= fecha:
        for s in salida:
            cursor.execute(f"SELECT * FROM componentes WHERE codigo = '{s[2]}'")
            fila = cursor.fetchall()
            
            if len(fila) == 0:
                cursor.execute(f"INSERT INTO componentes(codigo, descripcion, stock) VALUES ('{s[2]}', '{s[3]}', {s[4]})")
            elif len(fila) > 0:
                cursor.execute(f"UPDATE componentes SET stock = stock + {s[4]} WHERE codigo = '{s[2]}'")

    conn.commit()
    conn.close()

def visualizarComponentes():
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM componentes")
    salida = cursor.fetchall()
    
    for s in salida:
        print(f"{s[1]}: {s[2]} / {s[3]}")

    conn.commit()
    conn.close()

def eliminarTablas():
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE recepciones")
    cursor.execute("DROP TABLE componentes")
    cursor.execute("DROP TABLE defectuosos")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    exit = True
    crearTablas()
    while exit == True:
        print("\n=== INVENTARIO ===\n")
        print("1: Insertar nueva entrada")
        print("2: Visualizar componentes y stock")
        print("3: Elminar la base de datos")
        print("4: Salir")
        eleccion = int(input())
        
        if eleccion == 1:
            with open(f"Archivos/entrada{date.today()}.json", "r") as f:
                inventario = json.load(f)

            for recepcion in inventario['recepciones']:
                fecha = recepcion["fecha"]
                codigo = recepcion["codigo"]
                descripcion = recepcion["descripcion"]
                cantidad = recepcion["cantidad"]
                proveedor = recepcion["proveedor"]
                lote = recepcion["lote"]
                estado = recepcion["estado"]
                cantidad_defectuosas = recepcion["cantidad_defectuosas"]
                observaciones = recepcion["observaciones"]
                insertarEntradas(fecha, codigo, descripcion, cantidad, cantidad_defectuosas, proveedor, lote, estado, observaciones)

            entradaToComponentes(fecha)
        elif eleccion == 2:
            print("")
            visualizarComponentes()
        elif eleccion == 3:
            eliminarTablas()
        elif eleccion == 4:
            exit = False