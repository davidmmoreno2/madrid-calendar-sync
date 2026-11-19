"""
Genera partidos-sixers.ics con los próximos partidos de los Philadelphia
76ers (temporada regular, play-in y playoffs), usando la API pública de
ESPN, que no necesita token. Pensado para ejecutarse una vez al día (ver
.github/workflows/actualizar.yml) y sobrescribir siempre el mismo archivo.

Los partidos de playoffs aparecen solos en cuanto la NBA los programa.
"""

import os
from datetime import datetime, timedelta, timezone

import requests
from icalendar import Calendar, Event

SCHEDULE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/phi/schedule"
ICS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "partidos-sixers.ics")
# 2 = temporada regular, 3 = playoffs, 5 = play-in
TIPOS_TEMPORADA = {2: "Temporada regular", 3: "Playoffs", 5: "Play-in"}
ESTADOS_EXCLUIDOS = {"STATUS_POSTPONED", "STATUS_CANCELED"}
DURACION = timedelta(hours=2, minutes=30)  # duración estimada de un partido NBA


def obtener_partidos():
    ahora = datetime.now(timezone.utc)
    partidos = []
    for tipo, nombre_tipo in TIPOS_TEMPORADA.items():
        resp = requests.get(SCHEDULE_URL, params={"seasontype": tipo}, timeout=30)
        resp.raise_for_status()
        for evento in resp.json().get("events", []):
            comp = evento["competitions"][0]
            if comp["status"]["type"]["name"] in ESTADOS_EXCLUIDOS:
                continue
            inicio = datetime.fromisoformat(evento["date"].replace("Z", "+00:00"))
            if inicio + DURACION < ahora:
                continue  # ya jugado
            equipos = {c["homeAway"]: c["team"] for c in comp["competitors"]}
            partidos.append({
                "id": evento["id"],
                "inicio": inicio,
                "local": equipos["home"].get("shortDisplayName") or equipos["home"]["displayName"],
                "visitante": equipos["away"].get("shortDisplayName") or equipos["away"]["displayName"],
                "tipo": nombre_tipo,
                "notas": [n["headline"] for n in comp.get("notes", []) if n.get("headline")],
                "pabellon": comp.get("venue", {}).get("fullName"),
                "tv": [b["media"]["shortName"] for b in comp.get("broadcasts", []) if b.get("media", {}).get("shortName")],
                "hora_confirmada": comp.get("timeValid", True),
            })
    partidos.sort(key=lambda p: p["inicio"])
    return partidos


def construir_ics(partidos):
    cal = Calendar()
    cal.add("prodid", "-//madrid-calendar-sync//sixers//")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "Partidos Sixers")
    cal.add("x-wr-timezone", "UTC")

    for p in partidos:
        event = Event()
        event.add("uid", f"sixers-game-{p['id']}@madrid-calendar-sync")
        event.add("summary", f"🏀 {p['visitante']} @ {p['local']}")
        event.add("dtstart", p["inicio"])
        event.add("dtend", p["inicio"] + DURACION)
        lineas = [p["tipo"], *p["notas"]]
        if p["tv"]:
            lineas.append("TV: " + ", ".join(p["tv"]))
        if not p["hora_confirmada"]:
            lineas.append("Hora pendiente de confirmar")
        event.add("description", "\n".join(lineas))
        if p["pabellon"]:
            event.add("location", p["pabellon"])
        event.add("dtstamp", datetime.now(timezone.utc))
        cal.add_component(event)

    return cal


def main():
    partidos = obtener_partidos()
    print(f"Encontrados {len(partidos)} partidos próximos de los Sixers")

    cal = construir_ics(partidos)
    with open(ICS_PATH, "wb") as f:
        f.write(cal.to_ical())

    print(f"Escrito {ICS_PATH}")


if __name__ == "__main__":
    main()
