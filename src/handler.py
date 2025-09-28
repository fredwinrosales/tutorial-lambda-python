def lambda_handler(event, context):
    """
    Lambda handler que retorna "Hello World!".
    - Si se invoca vía API Gateway HTTP API, devuelve un objeto con statusCode/body.
    - Si se invoca directamente, devuelve una cadena simple.
    """
    message = "Hello World!"

    # Detección simple de invocación por API Gateway HTTP API v2
    if isinstance(event, dict) and event.get("requestContext", {}).get("http"):
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/plain; charset=utf-8"
            },
            "body": message,
        }

    # Respuesta directa para invocaciones no HTTP
    return message