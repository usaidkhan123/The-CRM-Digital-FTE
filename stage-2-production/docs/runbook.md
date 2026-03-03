# Customer Success FTE — Operations Runbook

## Service Overview

| Service | Port | Purpose |
|---------|------|---------|
| API Gateway | 8000 | Webhook intake, routing, support form API |
| Agent Service | 8001 | Message processing, AI response generation |
| Memory Service | 8002 | PostgreSQL-backed state (customers, tickets, conversations) |
| Notification Service | 8003 | Channel-specific delivery (Gmail, Twilio, Web) |
| Web Form | 3001 | React/Next.js support form UI |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Monitoring dashboards |
| Kafka | 9092 | Event streaming |
| PostgreSQL | 5432 | Persistent storage |

## Startup Procedure

```bash
cd stage-2-production
docker compose up -d
# Wait ~60 seconds for all services to initialize
# Verify: curl http://localhost:8000/health
```

## Health Checks

```bash
# All services
for port in 8000 8001 8002 8003; do
  echo "Port $port: $(curl -s http://localhost:$port/health | python3 -m json.tool)"
done
```

## Common Incidents

### 1. Agent Service Not Processing Messages
**Symptoms**: Messages queued in Kafka but no responses generated
**Check**:
```bash
docker compose logs agent-service --tail 50
curl http://localhost:8001/metrics | grep kafka_messages_consumed
```
**Fix**: Restart agent service: `docker compose restart agent-service`

### 2. Memory Service Down
**Symptoms**: 500 errors from agent service, tickets not created
**Check**:
```bash
docker compose logs memory-service --tail 50
docker compose exec postgres pg_isready -U taskflow
```
**Fix**: Check PostgreSQL connection, restart if needed:
```bash
docker compose restart postgres memory-service
```

### 3. Kafka Consumer Lag
**Symptoms**: Increasing delay between message submission and response
**Check**:
```bash
docker compose exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group agent-group
```
**Fix**: Scale agent workers or restart consumer

### 4. Gmail API Token Expired
**Symptoms**: Email sending fails, logs show auth errors
**Fix**: Re-run OAuth flow to refresh token:
```bash
python3 -c "from services.notification_service.app.channels.email_sender import _get_gmail_service; _get_gmail_service()"
```

### 5. Twilio Rate Limiting
**Symptoms**: WhatsApp messages failing with 429 errors
**Fix**: Implement backoff or upgrade Twilio plan

## Scaling

### Horizontal Pod Autoscaler (K8s)
```bash
kubectl get hpa -n taskflow-prod
# Manual scale:
kubectl scale deployment agent-service --replicas=5 -n taskflow-prod
```

### Docker Compose (local)
```bash
docker compose up -d --scale agent-service=3
```

## Monitoring

- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Prometheus Queries**:
  - Request rate: `rate(http_requests_total[5m])`
  - Error rate: `rate(http_requests_total{status=~"5.."}[5m])`
  - Processing time: `histogram_quantile(0.95, rate(message_processing_seconds_bucket[5m]))`
  - Escalation rate: `sum(escalations_total) / sum(messages_processed_total)`

## Backup & Recovery

### Database Backup
```bash
docker compose exec postgres pg_dump -U taskflow taskflow_prod > backup_$(date +%Y%m%d).sql
```

### Database Restore
```bash
cat backup.sql | docker compose exec -T postgres psql -U taskflow taskflow_prod
```

## Channel Configuration

### Gmail Setup
1. Create Google Cloud project
2. Enable Gmail API
3. Create OAuth 2.0 credentials
4. Set env vars: `GMAIL_CREDENTIALS_PATH`, `GMAIL_TOKEN_PATH`, `GMAIL_SENDER_EMAIL`

### Twilio WhatsApp Setup
1. Create Twilio account
2. Join WhatsApp Sandbox
3. Set webhook URL to `https://your-domain/webhooks/twilio/whatsapp`
4. Set env vars: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`

## Emergency Procedures

### Full System Restart
```bash
docker compose down
docker compose up -d
```

### Data Preservation During Restart
PostgreSQL data persists in Docker volume `postgres_data`. Never use `docker compose down -v` in production.
