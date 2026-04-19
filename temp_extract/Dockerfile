# Dockerfile para despliegue en Azure App Service (opcional)
FROM mcr.microsoft.com/azure-functions/python:4-python3.10

WORKDIR /home/site/wwwroot

COPY . .

RUN pip install --upgrade pip && pip install -r requirements.txt

CMD ["gunicorn", "--bind=0.0.0.0", "--timeout=600", "web_app:app"]
