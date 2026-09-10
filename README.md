# 📅 Calendario de partidos del Real Madrid

Genera un archivo `.ics` con los próximos partidos oficiales del Real Madrid
y lo mantiene actualizado automáticamente una vez al día con GitHub
Actions. Te suscribes a la URL una vez desde el iPhone y el propio
Calendario de iOS lo va refrescando solo, sin ninguna app ni credencial de
Apple de por medio.

> ⚠️ **Cobertura**: usa la API gratuita de football-data.org, que cubre
> **Liga y Champions League** pero no Copa del Rey ni Supercopa (esas
> competiciones solo están en planes de pago de esa API). Se probó antes
> con api-football.com, pero su plan gratuito solo da acceso a temporadas
> antiguas (2021-2023), no a la actual — por eso no se usa aquí.

## Cómo funciona

```
GitHub Actions (cron diario)
  → ejecuta generar_ics.py
  → consulta football-data.org (próximos partidos oficiales)
  → sobrescribe partidos-real-madrid.ics
  → hace commit y push del archivo actualizado
        ↓
Tu iPhone (suscrito a la URL raw del archivo)
  → refresca el calendario periódicamente (lo decide iOS, no hay forma de forzarlo)
```

## Puesta en marcha

### 1. Consigue un token gratuito

Regístrate en [football-data.org/client/register](https://www.football-data.org/client/register) (nombre + email, sin contraseña — el token te lo mandan por correo). Plan gratuito: 10 peticiones/minuto, de sobra para 1 al día.

### 2. Prueba el script en local (opcional pero recomendado)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edita `.env` y pon tu token. Luego:

```bash
python generar_ics.py
```

Debería crear `partidos-real-madrid.ics` en esta misma carpeta. Ábrelo con un editor de texto para comprobar que tiene los partidos.

### 3. Sube este proyecto a un repo de GitHub

Necesario para que GitHub Actions pueda ejecutarlo a diario. El repo puede ser público — el `.ics` solo contiene horarios de partidos, nada sensible (tu token nunca se sube, se queda en `.env`, que está en `.gitignore`).

### 4. Configura el token como secret del repo

En GitHub: **Settings → Secrets and variables → Actions → New repository secret** → nombre `FOOTBALL_DATA_API_KEY`, valor tu token.

O desde terminal, si tienes `gh` instalado:
```bash
gh secret set FOOTBALL_DATA_API_KEY --repo TU_USUARIO/TU_REPO
```
(te pedirá pegar el valor)

### 5. Lanza el workflow una vez a mano

Pestaña **Actions** del repo → **Actualizar calendario Real Madrid** → **Run workflow**. Comprueba que termina en verde y que aparece/actualiza `partidos-real-madrid.ics` en el repo.

### 6. Suscríbete desde el iPhone

1. Copia la URL "raw" del archivo, con esta pinta:
   ```
   https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/partidos-real-madrid.ics
   ```
2. En el iPhone: **Ajustes → Calendario → Cuentas → Añadir cuenta → Otra → Añadir calendario suscrito**.
3. Pega esa URL → **Siguiente** → **Guardar**.
4. Comprueba en la app Calendario que aparece el calendario "Partidos Real Madrid" con los próximos partidos.

## Notas

- Los amistosos se excluyen filtrando competiciones cuyo nombre contiene "Friendly" — si algún día quieres incluirlos, edita la función `es_amistoso` en `generar_ics.py`.
- El evento usa un `UID` estable por partido (`rm-fixture-{id}@madrid-calendar-sync`), así que si cambia la hora de un partido (típico por TV), el mismo evento se actualiza en vez de duplicarse.
- iOS decide cada cuánto refresca los calendarios suscritos (no hay forma de forzar tiempo real) — normalmente cada pocas horas.
- Duración de cada evento: estimada en 2 horas desde el saque inicial.
