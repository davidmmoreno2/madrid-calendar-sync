"""
Genera partidos-real-madrid.ics con los próximos partidos oficiales del
Real Madrid, usando la API gratuita de football-data.org. Pensado para
ejecutarse una vez al día (ver .github/workflows/actualizar.yml) y
sobrescribir siempre el mismo archivo.

Nota de cobertura: el plan gratuito de football-data.org cubre Liga y
Champions League, pero no Copa del Rey ni Supercopa (esas competiciones
solo están disponibles en planes de pago). Si necesitas cobertura
completa, habría que combinarlo con otra fuente o pasar a un plan de pago.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

import requests
from icalendar import Calendar, Event
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY")
BASE_URL = "https://api.football-data.org/v4"
REAL_MADRID_ID = 86  # id fijo de Real Madrid CF en football-data.org
ICS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "partidos-real-madrid.ics")
NUM_PARTIDOS = 20  # cuántos próximos partidos incluir
DIAS_ADELANTE = 120  # football-data.org limita el rango de fechas por petición


def api_get(path, params=None):
    resp = requests.get(
        f"{BASE_URL}{path}",
        headers={"X-Auth-Token": API_KEY},
        params=params or {},
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"La API devolvió {resp.status_code}: {resp.text}")
    return resp.json()


def obtener_proximos_partidos():
    hoy = datetime.now(timezone.utc).date()
    hasta = hoy + timedelta(days=DIAS_ADELANTE)

    data = api_get(
        f"/teams/{REAL_MADRID_ID}/matches",
        {
            "status": "SCHEDULED",
            "dateFrom": hoy.isoformat(),
            "dateTo": hasta.isoformat(),
        },
    )
    partidos = data.get("matches", [])
    partidos.sort(key=lambda p: p["utcDate"])
    return partidos[:NUM_PARTIDOS]


def construir_ics(partidos):
    cal = Calendar()
    cal.add("prodid", "-//madrid-calendar-sync//github.com//")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "Partidos Real Madrid")
    cal.add("x-wr-timezone", "UTC")

    for partido in partidos:
        local = partido["homeTeam"]["name"]
        visitante = partido["awayTeam"]["name"]
        competicion = partido["competition"]["name"]
        jornada = partido.get("matchday")
        inicio = datetime.fromisoformat(partido["utcDate"].replace("Z", "+00:00"))

        event = Event()
        event.add("uid", f"rm-fixture-{partido['id']}@madrid-calendar-sync")
        event.add("summary", f"⚽ {local} vs {visitante}")
        event.add("dtstart", inicio)
        event.add("dtend", inicio + timedelta(hours=2))  # duración estimada del partido
        descripcion = competicion
        if jornada:
            descripcion += f" — Jornada {jornada}"
        event.add("description", descripcion)
        event.add("dtstamp", datetime.now(timezone.utc))
        cal.add_component(event)

    return cal


def main():
    if not API_KEY:
        print("Falta FOOTBALL_DATA_API_KEY (rellena .env o configura el secret en GitHub Actions)", file=sys.stderr)
        sys.exit(1)

    partidos = obtener_proximos_partidos()
    print(f"Encontrados {len(partidos)} partidos oficiales próximos")

    cal = construir_ics(partidos)
    with open(ICS_PATH, "wb") as f:
        f.write(cal.to_ical())

    print(f"Escrito {ICS_PATH}")


if __name__ == "__main__":
    main()
