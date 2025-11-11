import os
import json
import pandas as pd
import requests
from datetime import datetime, timedelta

# === Config desde Secrets de GitHub ===
TOKEN     = os.getenv("TOKEN")        # Token del bot de Telegram
CHAT_ID   = os.getenv("CHAT_ID")      # ID del chat/grupo
EXCEL_URL = os.getenv("EXCEL_URL")    # URL export ?format=xlsx

# === Constantes ===
STATE_FILE = "notified.json"          # Registro de avisos ya enviados
COL_PET, COL_INICIO = "Pet", "Hora inicio"
COL_HORAS, COL_MIN  = "Duración (horas)", "Duración (min)"

# Margen para capturar finales que ocurren entre ejecuciones
MARGEN_MINUTOS = 5     # <- ajusta aquí si quieres más/menos margen

# === Utilidades ===
def enviar(texto: str):
    """Envía un mensaje de texto a Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.get(url, params={"chat_id": CHAT_ID, "text": texto}, timeout=15)
        print("Telegram:", r.text)
    except Exception as e:
        print("⚠ Error enviando telegram:", e)

def cargar_estado():
    """Carga el diccionario de notificaciones previas (para no duplicar avisos)."""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def guardar_estado(estado):
    """Guarda el registro de notificaciones."""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("⚠ No pude guardar estado:", e)

def to_int_safe(x, default=0):
    """Convierte a int de forma segura."""
    try:
        if pd.isna(x):
            return default
        return int(float(x))
    except:
        return default

# === Lógica principal ===
def main():
    # Carga estado previo
    estado = cargar_estado()

    # Lee la hoja
    df = pd.read_excel(EXCEL_URL)

    # Valida columnas mínimas
    for col in [COL_PET, COL_INICIO, COL_HORAS, COL_MIN]:
        if col not in df.columns:
            raise ValueError(f"Falta la columna '{col}' en la hoja.")

    # GitHub Actions corre en UTC -> miramos 5 minutos hacia adelante
    ahora = datetime.utcnow() + timedelta(minutes=MARGEN_MINUTOS)

    for _, row in df.iterrows():
        try:
            pet = str(row[COL_PET]).strip()
            inicio = pd.to_datetime(row[COL_INICIO], errors="coerce")
            if pd.isna(inicio):
                continue

            horas   = to_int_safe(row[COL_HORAS], 0)
            minutos = to_int_safe(row[COL_MIN], 0)

            fin = inicio + timedelta(hours=horas, minutes=minutos)
            clave = f"{pet}|{fin.isoformat()}"

            # Si ya terminó (considerando el margen) y nunca avisamos, enviamos
            if ahora >= fin and clave not in estado:
                msg = (
                    f"🐣 Tu pet '{pet}' terminó su incubación 🎉\n"
                    f"⏰ Finalizó a las {fin.strftime('%Y-%m-%d %H:%M')} (UTC)"
                )
                enviar(msg)
                estado[clave] = {"pet": pet, "hora_fin": fin.isoformat()}

        except Exception as e:
            print("Fila con error:", e)

    # Guarda estado para evitar duplicados en próximas ejecuciones
    guardar_estado(estado)

if __name__ == "__main__":
    main()
