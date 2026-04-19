# Instrucciones rápidas para desplegar en Azure App Service

1. Sube tu código a un repositorio (GitHub, Azure DevOps, etc.)
2. Crea un recurso "Web App" en Azure (Linux, Python 3.10+)
3. En "Startup Command" pon:
   gunicorn --bind=0.0.0.0 --timeout 600 web_app:app
4. Sube tu código o conecta el repositorio
5. Configura variables de entorno en "Configuration" (usa .env.example como referencia)
6. Asegúrate de que requirements.txt esté actualizado
7. (Opcional) Usa Dockerfile si prefieres despliegue en contenedor

¡Listo para producción en Azure!
