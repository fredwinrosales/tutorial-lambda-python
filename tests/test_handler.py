from src.handler import lambda_handler

def test_direct_invoke_returns_string():
    result = lambda_handler({}, None)
    assert result == "Hello World!"

def test_http_api_returns_proxy_response():
    event = {"requestContext": {"http": {"method": "GET"}}}
    result = lambda_handler(event, None)
    assert isinstance(result, dict)
    assert result.get("statusCode") == 200
    assert result.get("body") == "Hello World!"