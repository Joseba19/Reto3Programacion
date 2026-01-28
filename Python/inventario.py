#Importamos todas las bibliotecas necesarias
import json
import sqlite3
from datetime import date
import pandas as pd

bbdd = "inventario.db"

#Funcion para crear las tablas cuando se ejecute el archivo
def crearTablas():
    #Conexion a la base de datos
    conn = sqlite3.connect(bbdd)
    cursor = conn.cursor()
    cursor.execute("""         
        CREATE TABLE IF NOT EXISTS componentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo VARCHAR(50) UNIQUE NOT NULL,
            descripcion VARCHAR(200) NOT NULL,
            stock INTEGER DEFAULT 0,
            ultimaEntrada DATE NOT NULL
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
            ultimaEntrada DATE NOT NULL,
            FOREIGN KEY (id_recepcion) REFERENCES recepciones(id)
        );
            """)
    
    conn.commit()
    conn.close()

#Funcion para leer el JSON del dia e introducir los datos en la tabla recepciones
def insertarEntradas():
    conn = sqlite3.connect(bbdd)
    cursor = conn.cursor()
    #Consulta SQL para leer los datos de recepciones, con el fin de ver cual ha sido la ultima fecha en la que ha entrado un producto
    cursor.execute("SELECT MAX(fecha) FROM recepciones")
    ultimaFecha = cursor.fetchall()
    
    #Abre el archivo que contiene la fecha de hoy
    with open(f"Archivos/entrada{date.today()}.json", "r") as f:
        inventario = json.load(f)

    #Si la fecha actual es mayor a la ultima fecha registrada recorre el archivo guardando en variables todos los datos, para despues introducirlos con una consulta SQL (Linea 77)
    if date.today() > date.fromisoformat(ultimaFecha[0][0]):
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

            cursor.execute(f"INSERT INTO recepciones(fecha, codigo_componente, descripcion, cantidad, cantidad_defectuosas, proveedor, lote, estado, observaciones) VALUES ('{fecha}', '{codigo}', '{descripcion}', {cantidad}, '{cantidad_defectuosas}', '{proveedor}', '{lote}', '{estado}', '{observaciones}')")
    else:
       print("\nNo hay datos nuevos que insertar")
    conn.commit()
    conn.close()

#Funcion para pasar los componentes que han entrado a la tabla recepciones a la tabla componentes
def entradaToComponentes():
    conn = sqlite3.connect(bbdd)
    cursor = conn.cursor()
    #Consulta para sacar todas las recepciones
    cursor.execute("SELECT * FROM recepciones")
    salida = cursor.fetchall()
    cursor.execute("SELECT MAX(ultimaEntrada) FROM componentes")
    ultimaFecha = cursor.fetchall()

    #Si la fecha de hoy es mayor a la del ultimo componente registrado, se ejecuta el bucle
    if date.today() > date.fromisoformat(ultimaFecha[0][0]):
        for s in salida:
            #Consulta para ver si ya existe ese componente en la tabla componentes
            cursor.execute(f"SELECT * FROM componentes WHERE codigo = '{s[2]}'")
            fila = cursor.fetchall()
            
            #Consulta para ver la fecha mas alta de la tabla recepciones
            cursor.execute("SELECT MAX(fecha) FROM recepciones")
            ultimaFecha = cursor.fetchall()

            #Si la fecha de esa entrada es igual a la de la ultima llegada, se ejecuta el bucle
            if s[1] == ultimaFecha[0][0]:
                #Si el componente no ha sido registrado anteriormente, introduce uno nuevo, si ya existe actualiza el stock y la fehca de entrada
                if len(fila) == 0:
                    cursor.execute(f"INSERT INTO componentes(codigo, descripcion, stock, ultimaEntrada) VALUES ('{s[2]}', '{s[3]}', {s[4]}, '{s[1]}')")
                elif len(fila) > 0:
                    cursor.execute(f"UPDATE componentes SET stock = stock + {s[4]} WHERE codigo = '{s[2]}'")
                    cursor.execute(f"UPDATE componentes SET ultimaEntrada = '{s[1]}' WHERE codigo = '{s[2]}'")

    conn.commit()
    conn.close()

#Funcion para pasar los componentes registrados como defectuosos a la tabla defectuosos
#Se ha cambiado la manera de indexar datos por problemas con el f"", falta revisar
def entradaToDefectuosos():
    conn = sqlite3.connect(bbdd)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(ultimaEntrada) FROM defectuosos")
    ultimaFecha = cursor.fetchall()
    
    #Si esto era para arrancar la tabla, ya no deberia ser necesario
    if ultimaFecha[0][0] is None:
        cursor.execute("SELECT * FROM recepciones WHERE cantidad_defectuosas != 0")
    else:
        cursor.execute(
            "SELECT * FROM recepciones WHERE fecha > ? AND cantidad_defectuosas != 0",
            (ultimaFecha[0][0],)
        )
    #Selecciona los registros de recepciones que tengan algun defectos y que tengan la fecha mas reciente
    salida = cursor.fetchall()
    
    for s in salida:
        cursor.execute(
            "SELECT id FROM defectuosos WHERE id_recepcion = ? AND tipo_defecto = ?",
            (s[0], s[9])
        )
        existe = cursor.fetchone()
        
        if not existe:
            cursor.execute(
                """INSERT INTO defectuosos(id_recepcion, cantidad_defectuosa, tipo_defecto, ultimaEntrada) 
                   VALUES (?, ?, ?, ?)""",
                (s[0], s[5], s[9], s[1])
            )
            print(f"Defecto registrado para recepción {s[0]}")
    
    conn.commit()
    conn.close()

#Funcion imprimir por pantalla los componentes de la tabla componentes
def visualizarComponentes():
    conn = sqlite3.connect(bbdd)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM componentes")
    salida = cursor.fetchall()
    
    for s in salida:
        print(f"{s[1]}: {s[2]} / {s[3]}")

    conn.commit()
    conn.close()

#Funcion para buscar componentes defectuosos
def buscarComponente(componente):
    conn = sqlite3.connect(bbdd)
    cursor = conn.cursor()
    #Consulta SQL generada con Inteligencia Artificial
    cursor.execute("""
        SELECT 
            c.codigo, 
            c.descripcion, 
            def.tipo_defecto, 
            def.total_defectuosos
        FROM componentes c
        JOIN (
            SELECT 
                r.codigo_componente,
                d.tipo_defecto,
                SUM(d.cantidad_defectuosa) AS total_defectuosos
            FROM defectuosos d
            JOIN recepciones r ON r.id = d.id_recepcion
            GROUP BY r.codigo_componente, d.tipo_defecto
        ) def ON def.codigo_componente = c.codigo
        WHERE c.codigo = ?
        ORDER BY def.total_defectuosos DESC
        """, (componente,))
    
    salida = cursor.fetchall()

    if salida:
        for s in salida:
            print(f"\n{s[0]}: {s[1]}")
            print(f"Unidades defectuosas: {s[3]}")  # ← Esto mostrará 6
            print(f"Motivo: {s[2]}")   
    else:
        print("\nNo hay componentes defectuosos")

    conn.close()
    
#Funcion para eliminar las tablas en caso de que sea necesario (actualmente)
def eliminarTablas():
    conn = sqlite3.connect(bbdd)
    cursor = conn.cursor()
    #cursor.execute("DROP TABLE recepciones")
    #cursor.execute("DROP TABLE componentes")
    #cursor.execute("DROP TABLE defectuosos")
    conn.commit()
    conn.close()

#Funcion sacada con la informacion de la documentacion oficial de pandas
#Funcion para exportar la tabla componentes en formato CSV
def exportarcsv(nombreCSV = "componentes"):
    conn = sqlite3.connect(bbdd)
    query = "SELECT * FROM componentes"

    df = pd.read_sql_query(query, conn)
    df.to_csv(f'{nombreCSV}.csv', index=False, encoding='utf-8')
    print("\n¡Archivo CSV creado con éxito!")

    conn.close()

#Funcion que sirve para elinimar el stock de un componente de manera manual
def eliminarstock(componente, cantidad):
    conn = sqlite3.connect(bbdd)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM componentes WHERE codigo = ?", (componente,))
    salida = cursor.fetchall()

    if salida:
        cursor.execute("UPDATE componentes SET stock = stock - ? WHERE codigo = ?", (cantidad, componente))
        print("\nRegistros actualizados correctamente")
    else:
        print("\nNo hay registros con ese codigo")
    
    conn.commit()
    conn.close()

#Funcion que sirve para elinimar el stock de un componente en masa, mediante un JSON
def eliminarstockJSON():
    conn = sqlite3.connect(bbdd)
    cursor = conn.cursor()
    with open(f"Archivos/salida{date.today()}.json", "r") as f:
        eliminados = json.load(f)
        
    for componente in eliminados['salidas']:
        codigo = componente["codigo"]
        cantidad = componente["cantidad"]
        
        cursor.execute("UPDATE componentes SET stock = stock - ? WHERE codigo = ?", (cantidad, codigo))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    exit = False
    crearTablas()
    
    #Menu para seleccionar las opciones
    while exit == False:
        print("\n=== INVENTARIO ===\n")
        print("1: Insertar nueva entrada")
        print("2: Visualizar componentes y stock")
        print("3: Buscar componentes defectuosos")
        print("4: Exportar componentes en formato CSV")
        print("5: Eliminar stock")
        print("6: Elminar la base de datos")
        print("7: Salir")
        eleccion = input("\n")
        
        #Bucles por si el usuario introduce mal los datos
        while not eleccion.isnumeric():
            eleccion = input("Debes introducir un numero: ")
        
        while int(eleccion) <= 0 or int(eleccion) > 7:
            eleccion = input("El numero debe ser uno entre el 1 y el 7: ")
        
        #If que gestiona el menu
        if int(eleccion) == 1:
            insertarEntradas()
            entradaToComponentes()
            entradaToDefectuosos()
        elif int(eleccion) == 2:
            print("")
            visualizarComponentes()
        elif int(eleccion) == 3:
            componente = input("\nIntroduce el codigo del componente que quieres buscar: ")
            buscarComponente(componente)
        elif int(eleccion) == 4:
            nombreCSV = input("Introduce el nombre del archivo (si lo dejas vacio el nombre sera 'componentes'): ")
            if nombreCSV == "":
                exportarcsv()
            else:
                exportarcsv(nombreCSV)
        elif int(eleccion) == 5:
            print("\n=== SELECCIONE METODO DE REDUCCION ===\n")
            print("1: Eliminar stock de un componente")
            print("2: Usar JSON para reducir automaticamente los componentes del dia")
            eleccion = input("\n")
        
            #Mismos bucles que antes 
            while not eleccion.isnumeric():
                eleccion = input("Debes introducir un numero: ")
        
            while int(eleccion) < 0 or int(eleccion) > 2:
                eleccion = input("El numero debe ser el 1 o el 2: ")
            
            if int(eleccion) == 1:
                componente = input("Introduce el codigo del componente que deseas eliminar: ")
                cantidad = int(input("Introduce la cantidad de componentes que deseas eliminar: "))
                eliminarstock(componente, cantidad)
            else:
                eliminarstockJSON()
        elif int(eleccion) == 6:
            eliminarTablas()
        elif int(eleccion) == 7:
            exit = True