FROM python:3.12-slim

WORKDIR /app

COPY services/agent-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY monitoring/ /app/monitoring/
COPY services/agent-service/stage1/ /app/stage1/
COPY services/agent-service/app/ /app/app/

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
