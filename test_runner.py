import pandas as pd
import requests
import json
import os
import copy
from datetime import datetime

# --- CONFIGURACIÓN PRINCIPAL ---
AUTH_API_URL = "https://sandbox-api-pw.izipay.pe/authorization/api/Process/Authorize"
TOKEN_API_URL = "https://sandbox-api-pw.izipay.pe/security/v1/Token/Generate"
EXCEL_FILE = "Casos_de_Prueba.xlsx"
OUTPUT_DIR = "resultados_pruebas"
BASE_AUTH_BODY = {
    "Action": "pay", "MerchantCode": "4007611", "FacilitatorCode": "6666042",
    "Order": {"Currency": "PEN", "Amount": "KUlLYfuKShl/yU0EJk2DrgNchnbpdjdqo28WdsY1ycB4FkO3+QUzTqtYVHTLgVAv5vKB8dLWMxU9mRb6QrFtz2DDm9FIVIq+bUrU1UI3EnNgoflfrb/PemxFvCdSGOTABymFrTAyhyoCTlbSOdhI2vsOZheICf6tgHop5xNMabU7tyhkh8JQORuOI6zPcipQD29wU0KpY6sBPvzbL3X39ZBs4iC30PVBy2LbwPVceg605H0PCqJuFYvuBE6yob5viJa5B3YYge/LOLoHbN2ou++K9mYIeH8chaAusUFKZTBqwXZ29gZkK8SqNBEu5AzHMrirh/S8V+PJB8sqfqFJlw==", "Installments": "01", "PayMethod": "card", "Channel": "ecommerce", "ProcessType": "preautorize", "DatetimeTerminalTransaction": "2025-09-30 23:20:52.420"},
    "Card": { "Brand": "VS", "Pan": "LNFNBghwVsRTHDEWOrxLsuZJBRXQwha200trRj2A/kp0CyNQ8QScfE+h45fTI7JCj+aL6NKrnF1Kj9QKgtxP7rB6Op2Uyd/wMt1L4nEC1+9H19V2EbPf0M+Luutbgxm6HdazsKCfTBwMN/KADIKry193DyqV7Lpl4HQBIlKDTfYTHIfX5xH/9lE7YXPJ2UYxXJLm4FIZXF0+1vcy84EVWOpZyue0YaUlHBCqR5KHrwUQAwbY+yy9NPBiijUhnyHzukMYX606n+/UZMEDnd7Dq2u7rl9WnTnP7J2PHyLVvMgCoJv/BEZTsR7iXeqdFrbdRMCrgQ9qkCOOaQOSNf2zjg==", "ExpirationMonth": "WCTZRDW1AqNHzzEu9Fa3VepxLqGvPHKS8wqsTbcD1lzIioZaSY8RndiQ+cQELOpLA+3X1YT8rNRPsR4aySrsmKP/DsCOty4mrxEod9tOmSi+UOOFSeEhFSxQj0hysv+mWaNego2LdpguJm20tth9JHYuTZkKqleSZhlSbGuVfwPhot2rMCaakqDgA2kcx+zVyviBCojHooDwjJCANAmFzIBCsFFKo+87+e2kxdrDpj5+Q6IMipDgytWr4BmMwbPIbSOD49RNt3Y6BRmytqY4TuazK/OFN323qaq4fa5+y96WleHsi25pbLBXDgkFNVgCjEd4DLInky7Gyzu8T9BGwA==", "ExpirationYear": "dkzAFqK+RcCpocgu+E/F19y0OnofZGmQvT3pmiPyF6mTLUVzfQmqLpFP/5kik6d92VuvhkBrrlbjuO0XnY8kV5rRThFSl6Q0BGEFs1ZY0TfAdatCQzoNJFczKnA82pGQS03zuidamBODLj6KbYyNjF8v5Su1ef6cs+4dQUfJM0imTar8fE3Sf2WM56axEG6blWnuC3Rnyqi1oNEGR3KukzTHlwk5Pk5WWb+d3UUxzczVCjXwqeBiMs5fmGflQv6d8cxDKYwqE29BlM93NOs6lz6RaiITqIMcvTG9IK9pl7eNealRsF5CPWsONMW1k8g6YnuNRMi9M87NjRprRwMrcw==", "Cvc": "ExSkFPP562olJNbGD/aeUdzKLpWSRmc6K7wDECPmX2nY6eOy0Wjf9FPcpWlxT1UZB8DKzj0todbkskMs6QCmOtew2ywM5IeewFB8/rNKFHwh7Zdf1MG/R1zz9ENGaa86NLv6UGC/WMBx+rpyZB/STeZNtGJcDc2q7YVXoC8YwsosnS5eKutmDXw0504tLFEK8XxK/XrTFuc9Qmc//Qtv3UtR4U4MeCYjR04cmvcYnukyG4O0/0tLrVXnYxrNwmTemxKKNMN0PLUHtzsTaXvkCn0OVlQcTqAtMj4JX77BIbQDjFTqSTjNVrGxkdxMJzmHiKMPhOkfzvCnK5CJV3LhSQ==", "CvcPresent": "SI"},
    "Token": {}, "Billing": {"FirstName": "John", "LastName": "Doe", "Email": "izipay@example.com", "PhoneNumber": "11999999999", "Street": "Av Repblica de Panam 3414 ", "PostalCode": "15036", "City": "San Isidro", "State": "Lima", "Country": "PE", "DocumentType": "DNI", "Document": "35834219"},
    "Shipping": {}, "Antifraud": {"ClientIp": "127.0.0.1", "DeviceFingerPrintId": "some-fingerprint-id", "UserScoring": "izipay_low"},
    "Authentication": {}, "Language": "ESP", "CustomFields": []
}

# --- FUNCIONES AUXILIARES ---
# (Estas funciones no cambian, son las mismas de la versión anterior)
def generate_bearer_token(transaction_id):
    print(f"    Generando token para transactionId: {transaction_id}...")
    headers = {'transactionId': transaction_id}
    body = {"requestSource": "ECOMMERCE", "merchantCode": "4007611", "orderNumber": transaction_id, "publicKey": "VErethUtraQuxas57wuMuquprADrAHAb", "amount": "120.71"}
    try:
        response = requests.post(TOKEN_API_URL, headers=headers, json=body, timeout=15)
        response.raise_for_status()
        token = response.json().get("response", {}).get("token")
        if token:
            print("    Token generado exitosamente.")
            return token
        else:
            print("    ERROR: La respuesta de la API de token no contiene un token.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"    ERROR al generar token: {e}")
        return None

def modify_payload(base_payload, field_path, new_value):
    payload = copy.deepcopy(base_payload)
    keys = field_path.split('.')
    current_level = payload
    for key in keys[:-1]:
        found_key = next((k for k in current_level if k.lower() == key.lower()), None)
        if not found_key:
            current_level[key] = {}
            current_level = current_level[key]
        else:
            current_level = current_level[found_key]

    last_key = keys[-1]
    found_last_key = next((k for k in current_level if k.lower() == last_key.lower()), last_key)
    
    if new_value == 'Omitir':
        if found_last_key in current_level:
            del current_level[found_last_key]
    elif new_value == 'null':
        current_level[found_last_key] = None
    elif isinstance(new_value, str) and new_value.isdigit():
        try:
            current_level[found_last_key] = int(new_value)
        except ValueError:
            current_level[found_last_key] = new_value
    else:
        current_level[found_last_key] = new_value
    return payload

def generate_curl_command(headers, body):
    header_lines = " \\\n".join([f"--header '{key}: {value}'" for key, value in headers.items()])
    body_str = json.dumps(body, indent=4).replace("'", "'\\''")
    curl_command = (f"curl --location '{AUTH_API_URL}' \\\n{header_lines} \\\n--data-raw '{body_str}'")
    return curl_command

# --- LÓGICA PRINCIPAL ---

def run_tests():
    try:
        df = pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{EXCEL_FILE}'. Asegúrate de que exista.")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    date_prefix = f"AOQ{datetime.now().strftime('%Y%m%d')}"
    base_counter = 500

    for index, row in df.iterrows():
        caso = row['Caso']
        campo = row['Nombre del Campo']
        ejemplo_error = row['Ejemplo de Error (Dato Inválido)']
        
        print(f"\n--- Ejecutando Caso: {caso} | Campo: {campo} ---")

        transaction_id = f"{date_prefix}{base_counter + index + 1}"
        bearer_token = generate_bearer_token(transaction_id)
        
        if not bearer_token:
            print("    Fallo en la prueba: No se pudo generar el Bearer Token.")
            df.at[index, 'Codigo Resultado'] = "ERROR_TOKEN"
            df.at[index, 'Mensaje del Codigo'] = "No se pudo generar el token de seguridad"
            continue

        current_headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json',
            'transactionId': transaction_id
        }
        
        # --- INICIO DE LA CORRECCIÓN ---
        current_body = copy.deepcopy(BASE_AUTH_BODY)
        current_body['Order']['OrderNumber'] = transaction_id
        # --- FIN DE LA CORRECCIÓN ---

        if campo in current_headers:
             current_headers = modify_payload(current_headers, campo, str(ejemplo_error))
        else:
            current_body = modify_payload(current_body, campo, ejemplo_error)

        try:
            response = requests.post(AUTH_API_URL, headers=current_headers, json=current_body, timeout=30)
            response_json = response.json()
            code_result = response_json.get('code', 'N/A')
            message_result = response_json.get('message', 'N/A')
            print(f"    Respuesta recibida: code='{code_result}', message='{message_result}'")
        except requests.exceptions.RequestException as e:
            print(f"    Error en la petición: {e}")
            response_json, code_result, message_result = {"error": str(e)}, "ERROR_CONEXION", str(e)
        except json.JSONDecodeError:
            print(f"    Error: La respuesta no es un JSON válido. Status: {response.status_code}")
            response_json, code_result, message_result = {"error": "Respuesta no es JSON", "content": response.text}, f"ERROR_JSON_{response.status_code}", response.text

        df.at[index, 'Codigo Resultado'] = code_result
        df.at[index, 'Mensaje del Codigo'] = message_result
        file_prefix = f"{caso}_{str(campo).replace('.', '_')}"
        
        response_filename = os.path.join(OUTPUT_DIR, f"{file_prefix}_response.json")
        with open(response_filename, 'w', encoding='utf-8') as f:
            json.dump(response_json, f, indent=4, ensure_ascii=False)
            
        curl_command = generate_curl_command(current_headers, current_body)
        curl_filename = os.path.join(OUTPUT_DIR, f"{file_prefix}_curl.txt")
        with open(curl_filename, 'w', encoding='utf-8') as f:
            f.write(curl_command)
            
    df.to_excel(EXCEL_FILE, index=False)
    print(f"\n--- Pruebas finalizadas. El archivo '{EXCEL_FILE}' ha sido actualizado. ---")
    print(f"Los archivos de respuesta y cURL se han guardado en la carpeta '{OUTPUT_DIR}'.")

if __name__ == "__main__":
    run_tests()