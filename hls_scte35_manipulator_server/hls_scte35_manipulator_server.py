from urllib.parse import urljoin

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response

from .logger import init_logger, logger
from .parser import parser
from .profiles import load_profile
from .profiles import Profile
from .middleware import rewrite_manifest_if_needed
from .headers import copy_from_request, copy_from_response

def create_app(
    origin_base_url: str,
    profile_path: str,
    timeout_seconds: float,
    trust_env: bool = True,
) -> FastAPI:
    app = FastAPI(title="scte35-manipolator")
    profile:Profile = load_profile(profile_path)

    @app.get("/health")
    async def health() -> Response:
        content = "ok"
        status_code = 200
        logger.debug(f"GET /health | {content} | {status_code}")
        return Response(content=content, status_code=status_code) 


    @app.put("/{full_path:path}")
    async def proxy_put(full_path: str, request: Request) -> Response:
        query = request.url.query
        upstream_path = full_path
        if query:
            upstream_path = f"{full_path}?{query}"

        target_url = urljoin(origin_base_url.rstrip("/") + "/", upstream_path)
        logger.debug(f"PUT /{target_url}")
        logger.debug(f"Forwarding: {target_url}")

        body = await request.body()
        content_type = request.headers.get("content-type", "")
        logger.debug(f"Request content-type: {content_type}")

        is_manifest = full_path.lower().endswith(".m3u8") or "mpegurl" in content_type.lower()
        if is_manifest:
            body = rewrite_manifest_if_needed(target_url, body, profile)

        # use requester headers to forward the request  
        headers = copy_from_request(request)
        logger.debug("Forward request headers: %s", headers)
        logger.debug("Forward request body length: %d", len(body))
        async with httpx.AsyncClient(timeout=timeout_seconds, trust_env=trust_env) as client:
            response = await client.put(target_url, content=body, headers=headers)

        # use headers from the answerer to answer to the requester
        headers = copy_from_response(response)
        logger.debug(f"Received from {target_url} - {response.status_code}")
        logger.debug("Upstream response preview: %s", response.text[:500])

        logger.info(f"PUT /{target_url} | {response.status_code} | {len(body)} bytes")
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=headers,
            media_type=response.headers.get("content-type"),
        )

    return app


def main() -> int:
    args = parser.parse_args()
    init_logger(args.log_level)
    logger.info("Starting SCTE-35 manipulator middleware")
    logger.info("Origin base URL: %s", args.origin_base_url)
    logger.info("Profile: %s", args.profile)
    logger.info("Listening: %s:%d", args.host, args.port)

    app = create_app(args.origin_base_url, args.profile, args.request_timeout)
    uvicorn.run(app, host=args.host, port=args.port, access_log=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())