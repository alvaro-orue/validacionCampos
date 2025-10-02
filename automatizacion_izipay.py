import pandas as pd
import requests
import json
import os
from datetime import datetime
import copy
import time

# --- CONFIGURACIÓN ---
TOKEN_URL = "https://sandbox-api-pw.izipay.pe/security/v1/Token/Generate"
AUTH_URL = "https://sandbox-api-pw.izipay.pe/authorization/api/Process/Authorize"

# Archivos de entrada
TOKEN_BODY_FILE = 'body_token.json'
AUTH_BODY_FILE = 'body_autorizacion.json'
CASES_FILE = 'casosCampoError.xlsx' 

# Archivo de salida para los resultados
RESULTS_CSV_FILE = 'resultados_pruebas.csv'

# Directorio para guardar los archivos de salida (request y curl)
OUTPUT_DIR = 'output_files'

# --- FIN DE LA CONFIGURACIÓN ---

def set_nested_value(d, key_path, value):
    keys = key_path.split('.')
    current_level = d
    for i, key in enumerate(keys):
        if i == len(keys) - 1:
            if isinstance(value, str) and value.lower() == "omitir":
                if key in current_level:
                    del current_level[key]
            elif isinstance(value, str) and value.lower() == "null":
                current_level[key] = None
            else:
                current_level[key] = value
        elif key in current_level and isinstance(current_level[key], dict):
            current_level = current_level[key]
        else:
            print(f"  [Advertencia] La ruta '{key_path}' no se encontró completamente en el JSON. Se detuvo en '{key}'.")
            return

def generate_curl_command(url, headers, data):
    data_str = json.dumps(data, indent=4)
    command = f"curl --location --request POST '{url}' \\\n"
    for key, value in headers.items():
        command += f"--header '{key}: {value}' \\\n"
    command += f"--data-raw '{data_str}'"
    return command

def main():
    print("Iniciando el proceso de validación automatizada...")

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Directorio '{OUTPUT_DIR}' creado.")

    try:
        with open(TOKEN_BODY_FILE, 'r', encoding='utf-8') as f:
            base_token_body = json.load(f)
        with open(AUTH_BODY_FILE, 'r', encoding='utf-8') as f:
            base_auth_body = json.load(f)
        
        df = pd.read_excel(CASES_FILE)
        print("Archivos JSON y Excel cargados correctamente.")

    except Exception as e:
        print(f"Error al leer los archivos de configuración o el Excel: {e}")
        return
        
    for index, row in df.iterrows():
        time.sleep(1)

        # --- LECTURA DE CAMPOS DEL EXCEL (incluyendo los nuevos) ---
        caso = str(row.get('Caso', f'Fila_{index+2}'))
        field_to_modify = row.get('Nombre del Campo')
        invalid_value_raw = row.get('Ejemplo de Error (Dato Inválido)')
        secondary_field = row.get('Campo_Secundario') # Nuevo
        secondary_value_raw = row.get('Valor_Secundario') # Nuevo

        # Limpieza de datos (convierte NaN a strings vacíos)
        field_to_modify = "" if pd.isna(field_to_modify) else str(field_to_modify)
        invalid_value = "" if pd.isna(invalid_value_raw) else str(invalid_value_raw)
        secondary_field = "" if pd.isna(secondary_field) else str(secondary_field)
        secondary_value = "" if pd.isna(secondary_value_raw) else str(secondary_value_raw)

        if not field_to_modify:
            print(f"  [Advertencia] Saltando fila {index + 2} porque 'Nombre del Campo' está vacía.")
            continue

        print(f"\n--- Procesando Caso: {caso} | Campo Principal: {field_to_modify} ---")

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        transaction_id = f"AUTO{timestamp}{index}"
        print(f"  ID de Transacción generado: {transaction_id}")
        
        try:
            print("  1. Solicitando token...")
            token_body = copy.deepcopy(base_token_body)
            token_body['orderNumber'] = transaction_id
            token_headers = {
                'x-api-key': 'izipay-api',
                'transactionId': transaction_id,
                'accept': 'application/json',
                'Content-Type': 'application/json'
            }
            response_token = requests.post(TOKEN_URL, json=token_body, headers=token_headers)
            response_token.raise_for_status()
            token_data = response_token.json()
            bearer_token = token_data.get('response', {}).get('token')
            if not bearer_token:
                print("  [Error] No se pudo obtener el token de la respuesta.")
                df.loc[index, 'Codigo Resultado'] = token_data.get('code', 'N/A')
                df.loc[index, 'Mensaje del Codigo'] = token_data.get('message', 'Fallo al obtener token')
                continue
            print("  Token obtenido exitosamente.")
        
        except requests.exceptions.RequestException as e:
            print(f"  [Error] Fallo en la solicitud del token: {e}")
            df.loc[index, 'Codigo Resultado'] = 'Error de Red'
            df.loc[index, 'Mensaje del Codigo'] = str(e)
            continue
            
        try:
            print("  2. Preparando y enviando solicitud de autorización...")
            auth_body = copy.deepcopy(base_auth_body)
            set_nested_value(auth_body, 'Order.OrderNumber', transaction_id)
            
            # --- INICIO DE LA NUEVA LÓGICA ---
            # Primero, aplica la acción secundaria si existe
            if secondary_field:
                print(f"     Acción secundaria: Modificando '{secondary_field}' a '{secondary_value}'")
                set_nested_value(auth_body, secondary_field, secondary_value)

            # Después, aplica la acción principal
            print(f"     Acción principal: Modificando '{field_to_modify}' con '{invalid_value}'")
            set_nested_value(auth_body, field_to_modify, invalid_value)
            # --- FIN DE LA NUEVA LÓGICA ---

            auth_headers = {
                'x-api-key': 'izipay-api',
                'transactionId': transaction_id,
                'Authorization': f'Bearer {bearer_token}',
                'accept': 'application/json',
                'Content-Type': 'application/json'
            }
            response_auth = requests.post(AUTH_URL, json=auth_body, headers=auth_headers)
            auth_data = response_auth.json()
            
            code = auth_data.get('code', 'N/A')
            message = auth_data.get('message', 'Sin mensaje')
            df.loc[index, 'Codigo Resultado'] = code
            df.loc[index, 'Mensaje del Codigo'] = message
            print(f"  Respuesta recibida: Código='{code}', Mensaje='{message}'")

            print("  3. Generando archivos de salida...")
            safe_field_name = field_to_modify.replace('.', '_').replace('/', '_')
            base_filename = f"{OUTPUT_DIR}/{caso}_{safe_field_name}"
            
            json_filename = f"{base_filename}_response.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(auth_data, f, indent=4, ensure_ascii=False)
            
            curl_command = generate_curl_command(AUTH_URL, auth_headers, auth_body)
            curl_filename = f"{base_filename}_request.curl"
            with open(curl_filename, 'w', encoding='utf-8') as f:
                f.write(curl_command)
            
            print(f"     Archivos generados: '{json_filename}' y '{curl_filename}'")

        except Exception as e:
            print(f"  [Error] Ocurrió un error inesperado durante la autorización: {e}")
            df.loc[index, 'Codigo Resultado'] = 'Error Script'
            df.loc[index, 'Mensaje del Codigo'] = str(e)
            continue
            
    df.to_csv(RESULTS_CSV_FILE, index=False, encoding='utf-8-sig')
    print(f"\n--- Proceso finalizado ---")
    print(f"Todos los casos han sido procesados. Los resultados se han guardado en '{RESULTS_CSV_FILE}'.")

if __name__ == "__main__":
    main()