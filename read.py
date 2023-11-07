import pandas as pd
import json
from tqdm import tqdm



datos = []

with open('date_base1pcmary.json', 'r', encoding='utf-8') as archivo_json:
    for linea in tqdm(archivo_json):
        try:
            objeto_json = json.loads(linea)
            datos.append(objeto_json)
        except json.JSONDecodeError as e:
            # print(f"Error al analizar línea: {linea}")
            print(e)

# 'datos' ahora es una lista de diccionarios
# print(datos)