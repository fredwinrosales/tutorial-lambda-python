### **Cómo usarlo (solo necesitas Docker)**

```bash
# 1) Construir la imagen
docker compose build

# 2) Correr la lambda en contenedor (queda escuchando en localhost:9000)
docker compose up -d

# 3) Invocar localmente

# Curl mínimo (payload vacío)
curl  -X  POST  http://localhost:9000/2015-03-31/functions/function/invocations  -d  '{}'
# Con un payload personalizado (JSON)
curl  -X  POST  \
http://localhost:9000/2015-03-31/functions/function/invocations \
-H  'Content-Type: application/json'  \
--data-raw '{"foo":"bar"}'
# (Opcional) Simular evento de API Gateway HTTP API v2
curl  -X  POST  http://localhost:9000/2015-03-31/functions/function/invocations  \
-H 'Content-Type: application/json' \
--data-raw  '{
"version": "2.0",
"requestContext": { "http": { "method": "GET", "path": "/" } }
}'
# Consejito para formato “bonito”
curl  -s  -X  POST  http://localhost:9000/2015-03-31/functions/function/invocations  -d  '{}'  |  jq  .

# 4) Ver logs y parar
docker compose logs -f
docker compose down
```

La API de invocación local es la nativa de Lambda:

```bash
POST http://localhost:9000/2015-03-31/functions/function/invocations
```