from fastapi import Request
from fastapi import Response


def _connection_tokens(headers: dict[str, str]) -> set[str]:
    raw = headers.get("connection", "")
    return {token.strip().lower() for token in raw.split(",") if token.strip()}


def copy_from_request(request: Request) -> dict[str, str]:
    # Do not forward hop-by-hop or payload-length/integrity headers.
    skip = {
        "host",
        "content-length",
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
        "expect",
        "content-md5",
        "digest",
    }
    skip.update(_connection_tokens(dict(request.headers.items())))

    headers = {}
    for key, value in request.headers.items():
        if key.lower() in skip:
            continue
        headers[key] = value
    return headers


def copy_from_response(response: Response) -> dict[str, str]:
    skip = {
        "content-length",
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
    }
    skip.update(_connection_tokens(dict(response.headers.items())))

    headers = {}
    for key, value in response.headers.items():
        if key.lower() in skip:
            continue
        headers[key] = value
    return headers