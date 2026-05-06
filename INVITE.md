# Cómo invitar el bot de Discord

Este bot está listo para ejecutarse. Solo necesitas crear una aplicación de bot y luego invitarla a tu servidor.

## Pasos

1. Ve a https://discord.com/developers/applications.
2. Crea una nueva aplicación.
3. En la pestaña **Bot**, haz clic en **Add Bot**.
4. Copia el token y añádelo a tu archivo `.env` localmente o configúralo en Render como `DISCORD_TOKEN`.
5. En la pestaña **OAuth2** → **URL Generator**:
   - Marca el scope `bot`.
   - Selecciona permisos como `Send Messages`, `Embed Links`, `Read Message History`.
6. Copia el enlace generado y abrelo en tu navegador.
7. Elige tu servidor y autoriza el bot.

## Enlace de invitación manual

Si quieres hacerlo sin el generador, puedes usar esta plantilla:

```
https://discord.com/oauth2/authorize?client_id=TU_CLIENT_ID&scope=bot&permissions=19456
```

Cambia `TU_CLIENT_ID` por el Client ID de tu aplicación.

## Notas

- No compartas el token del bot.
- Si despliegas en Render, usa `DISCORD_TOKEN` como variable de entorno en el panel de Render.
