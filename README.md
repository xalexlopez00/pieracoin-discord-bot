# PieraCoin Discord Economy Bot

Este directorio contiene un bot de Discord independiente para crear una economía comunitaria con PieraCoin. El bot incluye:

- Sistema de wallet y banco local
- Comandos de saldo, depósito, retiro y pago entre usuarios
- Ruleta de apuestas
- Blackjack contra el dealer
- Recompensa diaria
- Ranking de riqueza

## Instalación local

1. Copia `.env.example` a `.env` y completa `DISCORD_TOKEN`.
2. Instala dependencias:

```bash
python -m pip install -r requirements.txt
```

3. Ejecuta el bot:

```bash
python bot.py
```

## Variables de entorno

- `DISCORD_TOKEN`: Token del bot de Discord.
- `BOT_PREFIX`: Prefijo de comandos. Por defecto es `!`, pero puedes usar `-` o cualquier otro carácter.
- `DATABASE_URL`: URL de conexión a PostgreSQL (para producción en Render). Si no se especifica, usa archivo JSON local.
- `DATABASE_FILE`: Archivo JSON donde se guarda la economía (opcional si usas DATABASE_URL).
- `START_BALANCE`: Saldo inicial para nuevos usuarios.
- `DAILY_REWARD`: Recompensa diaria en PieraCoin.

## Comandos principales

- `!help` - Muestra la lista de comandos.
- `!help <comando>` - Muestra ayuda detallada de un comando.
- `!balance` - Muestra tu wallet y banco.
- `!deposit <cantidad>` - Deposita dinero en el banco.
- `!withdraw <cantidad>` - Retira dinero al wallet.
- `!pay @user <cantidad>` - Envía PieraCoin a otro miembro.
- `!daily` - Reclama la recompensa diaria.
- `!roulette <cantidad> <rojo|negro|verde>` - Juega ruleta.
- `!blackjack <cantidad>` - Juega blackjack contra el dealer.
- `!leaderboard` - Muestra el top de riqueza.

## Despliegue en Render

Para que funcione en Render, crea un servicio de tipo **Background Worker** (no Web Service) y configura estas variables:

- `DISCORD_TOKEN`
- `BOT_PREFIX` (opcional)
- `DATABASE_URL` (opcional, pero recomendado para persistencia)

### Configuración de base de datos en Render

Para mantener los datos persistentes entre reinicios:

1. En tu dashboard de Render, crea una nueva **PostgreSQL** database.
2. Copia la **Internal Database URL** (empieza con `postgresql://`).
3. Pégala en la variable de entorno `DATABASE_URL` de tu Background Worker.

Si no configuras `DATABASE_URL`, el bot usará un archivo JSON local, pero perderás los datos al reiniciar el servicio.

Render ejecutará el bot con el `Dockerfile` incluido.

### Pasos rápidos en Render

1. Conecta tu repositorio.
2. Crea una nueva **PostgreSQL** database.
3. Crea un nuevo servicio de tipo `Background Worker`.
4. Selecciona Docker como runtime.
5. Establece las variables de entorno necesarias (incluyendo `DATABASE_URL`).
6. Despliega.

> El bot no expone un puerto HTTP. Render lo ejecuta como worker de fondo.

## Pruebas locales

1. Copia `discord_bot/.env.example` a `discord_bot/.env`.
2. Ajusta `DISCORD_TOKEN` con el token de tu bot.
3. Si quieres mantener datos separados, usa `DATABASE_FILE=economy-test.json`.
4. Inicia el bot con:

```bash
python bot.py
```

5. En Discord, prueba estos comandos:
   - `!help`
   - `!balance`
   - `!deposit 100`
   - `!withdraw 50`
   - `!pay @usuario 25`
   - `!daily`
   - `!roulette 50 rojo`
   - `!blackjack 100`

6. Revisa `economy.json` o `economy-test.json` para ver los cambios de saldo.

### Probar en un servidor de Discord

- Invita al bot usando `https://discord.com/oauth2/authorize?client_id=TU_CLIENT_ID&scope=bot&permissions=19456`
- Verifica que el bot esté en línea y responde a `!help`.
- Prueba cada comando en un canal de texto con permisos de lectura y escritura.

### Crear e invitar el bot de Discord

1. Entra en el Discord Developer Portal: https://discord.com/developers/applications.
2. Crea una nueva aplicación.
3. Ve a la pestaña Bot y haz clic en "Add Bot".
4. Copia el token en `discord_bot/.env` localmente o configúralo en Render como `DISCORD_TOKEN`.
5. Ve a "OAuth2" → "URL Generator".
6. Marca `bot` en Scopes y selecciona permisos como `Send Messages`, `Embed Links`, `Read Message History`.
7. Copia el enlace generado y úsalo para invitar el bot a tu servidor.

> El token nunca debe compartirse o subirse a GitHub.

## Notas

- Esta carpeta es independiente del código principal de PieraCoin.
- El bot guarda los datos localmente en `economy.json`.
- Si quieres integrar directamente la economía con el backend de PieraCoin, se puede agregar en una segunda fase usando la API REST existente.
