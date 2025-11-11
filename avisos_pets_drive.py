import pandas as pd
import requests
import time
import json
import os
from datetime import datetime, timedelta

# --- Configuración Telegram ---
TOKEN = "8597696917:AAFD6aj5HCxVE1xjzniHqPMDfvgEQPil3bY"    # (Recomendado: regenerar después de probar)
CHAT_ID = "-4873702567"  # Grupo "Aviso Internet"

# --- Enlace de Google Sheets (formato export .xlsx) ---
# Tomado de tu link:
# https://docs.google.com/spreadsheets/d/1-HIluKGkheJNvYmFG0RR8F9Qj9aHDMrdb3_bkBymmEM/edit?usp=sharing
EXCEL_URL = "https://docs.google.com/spreadsheets/d/1-HIluKGkheJNvYmFG0RR8F9Qj9aHDMrdb3_bkBymmEM/export?format=xlsx"

# --- Archivo local para evitar avisos repetidos ---
STATE_FILE = "notified.json"

def enviar_mensaje(texto: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": texto}
    try:
        r = requests.get(url, params=params, timeout=10)
        print("Telegram:", r.text)
    except Exception as e:
        print("⚠ Error al enviar mensaje:", e)

def cargar_estado():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_estado(estado):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("⚠ No pude guardar estado:", e)

def ahora_local():
    # Asume hora local del servidor; si quieres fijar America/Lima exacto,
    # puedes usar zoneinfo pero no es estrictamente necesario para comparar.
    return datetime.now()

def main():
    estado = cargar_estado()

    # Nombres de columnas esperadas en la hoja
    COL_PET = "Pet"
    COL_INICIO = "Hora inicio"
    COL_HORAS = "Duración (horas)"
    COL_MIN = "Duración (min)"

    # Frecuencia de revisión (en segundos)
    INTERVALO = 300  # 5 minutos

    while True:
        try:
            # Leer Google Sheets como Excel
            df = pd.read_excel(EXCEL_URL)

            # Validación mínima de columnas
            for col in [COL_PET, COL_INICIO, COL_HORAS, COL_MIN]:
                if col not in df.columns:
                    raise ValueError(f"Falta la columna '{col}' en la hoja.")

            # Recorrer filas
            for _, row in df.iterrows():
                try:
                    pet = str(row[COL_PET]).strip()

                    # Parseo de fecha/hora de inicio
                    hora_inicio = pd.to_datetime(row[COL_INICIO], errors="coerce")
                    if pd.isna(hora_inicio):
                        continue

                    horas = int(row[COL_HORAS]) if not pd.isna(row[COL_HORAS]) else 0
                    minutos = int(row[COL_MIN]) if not pd.isna(row[COL_MIN]) else 0

                    hora_fin = hora_inicio + timedelta(hours=horas, minutes=minutos)
                    clave = f"{pet}|{hora_fin.isoformat()}"

                    # Si ya finalizó y no avisamos antes, enviamos
                    if ahora_local() >= hora_fin and clave not in estado:
                        msg = (
                            f"🐣 Tu pet '{pet}' terminó su incubación 🎉\n"
                            f"⏰ Finalizó a las {hora_fin.strftime('%Y-%m-%d %H:%M')}"
                        )
                        enviar_mensaje(msg)
                        estado[clave] = {"pet": pet, "hora_fin": hora_fin.isoformat()}
                        guardar_estado(estado)

                except Exception as inner_e:
                    print("Fila con error:", inner_e)
        except Exception as e:
            print("⚠ Error general:", e)

        time.sleep(INTERVALO)

if __name__ == "__main__":
    main()
