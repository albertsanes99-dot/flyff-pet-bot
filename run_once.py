import os, json, pandas as pd, requests
from datetime import datetime, timedelta

TOKEN     = os.getenv("TOKEN")        # secreto en GitHub
CHAT_ID   = os.getenv("CHAT_ID")      # secreto en GitHub (grupo o chat)
EXCEL_URL = os.getenv("EXCEL_URL")    # secreto en GitHub (link export xlsx)

STATE_FILE = "notified.json"          # se guarda en el repo de Actions (ephemeral)
COL_PET, COL_INICIO = "Pet", "Hora inicio"
COL_HORAS, COL_MIN  = "Duración (horas)", "Duración (min)"

def enviar(texto: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.get(url, params={"chat_id": CHAT_ID, "text": texto}, timeout=15)
        print("Telegram:", r.text)
    except Exception as e:
        print("⚠ Error enviando telegram:", e)

def cargar_estado():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def guardar_estado(estado):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("⚠ No pude guardar estado:", e)

def main():
    estado = cargar_estado()
    df = pd.read_excel(EXCEL_URL)

    # Validar columnas mínimas
    for col in [COL_PET, COL_INICIO, COL_HORAS, COL_MIN]:
        if col not in df.columns:
            raise ValueError(f"Falta la columna '{col}' en la hoja.")

    ahora = datetime.utcnow()  # GitHub Actions corre en UTC
    for _, row in df.iterrows():
        try:
            pet = str(row[COL_PET]).strip()
            inicio = pd.to_datetime(row[COL_INICIO], errors="coerce")
            if pd.isna(inicio):
                continue
            horas   = int(row[COL_HORAS]) if not pd.isna(row[COL_HORAS]) else 0
            minutos = int(row[COL_MIN])   if not pd.isna(row[COL_MIN])   else 0
            fin = inicio + timedelta(hours=horas, minutes=minutos)

            clave = f"{pet}|{fin.isoformat()}"
            if ahora >= fin and clave not in estado:
                msg = f"🐣 Tu pet '{pet}' terminó su incubación 🎉\n⏰ Finalizó a las {fin.strftime('%Y-%m-%d %H:%M')} (UTC)"
                enviar(msg)
                estado[clave] = {"pet": pet, "hora_fin": fin.isoformat()}
        except Exception as e:
            print("Fila con error:", e)

    guardar_estado(estado)

if __name__ == "__main__":
    main()
