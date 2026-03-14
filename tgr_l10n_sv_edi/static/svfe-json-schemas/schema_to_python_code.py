import subprocess
import os

# Definimos la ruta donde se encuentra el archivo o carpeta JSON Schema que queremos procesar
ruta = r"./fe-nc-v3.json"

# Verificamos si la ruta especificada existe en el sistema de archivos
if os.path.exists(ruta):
    print("La ruta existe.")  # Mensaje de éxito si la ruta es válida
else:
    print("La ruta no existe.")  # Mensaje de error si la ruta no se encuentra

# Construimos la lista de argumentos para ejecutar el generador de modelos
comando = [
    "python",  # Invocamos el intérprete de Python
    "-m",  # Indicamos que usaremos un módulo
    "datamodel_code_generator",  # Módulo encargado de generar los modelos Pydantic
    "--input",
    ruta,  # Ruta de entrada al JSON Schema
    "--input-file-type",
    "jsonschema",  # Tipo de archivo de entrada
    "--output",
    "fe_ccf_v3.py",  # Archivo de salida donde se guardará el modelo generado
    "--output-model-type",
    "pydantic_v2.BaseModel",  # Clase base usada para los modelos resultantes
    "--use-annotated",  # Opción para usar anotaciones de tipo en los campos
]

# Ejecutamos el comando en un subproceso y capturamos la salida
try:
    resultado = subprocess.run(
        comando,
        check=True,  # Lanza una excepción si el proceso termina con código de error
        text=True,  # Devuelve la salida como cadenas de texto en lugar de bytes
        capture_output=True,  # Captura stdout y stderr para poder imprimirlos
    )
    print("Modelo generado con éxito.")
    print(
        resultado.stdout
    )  # Mostramos la salida estándar del comando (información adicional)

# En caso de error, capturamos y mostramos el mensaje de error
except subprocess.CalledProcessError as e:
    print(
        "Error al generar el modelo:", e.stderr
    )  # Imprime el error capturado en stderr
