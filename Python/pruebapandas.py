import sqlite3
import pandas as pd

# 1. Crear la conexión a la base de datos SQLite
conexion = sqlite3.connect('inventario.db')

# 2. Definir la consulta SQL para traer los datos
query = "SELECT * FROM componentes"

# 3. Cargar los datos en un DataFrame de Pandas
# Pandas ejecuta la consulta y organiza el resultado en una tabla automáticamente
df = pd.read_sql_query(query, conexion)

# 4. Guardar el DataFrame como un archivo CSV
# index=False evita que se cree una columna extra con los números de fila
df.to_csv('resultado.csv', index=False, encoding='utf-8')

# 5. Cerrar la conexión
conexion.close()

print("¡Archivo CSV creado con éxito!")