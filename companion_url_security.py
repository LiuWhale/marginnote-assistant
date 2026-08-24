from __future__ import annotations

from urllib import request
from urllib.parse import urlsplit


ACTION_TOKEN_HEADER = "X-Codex-Action-Token"
COMPANION_PORT = 48761
COMPANION_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def is_local_companion_url(url: str) -> bool:
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except (TypeError, ValueError):
        return False
    return (
        parsed.scheme.lower() == "http"
        and parsed.hostname in COMPANION_HOSTS
        and port == COMPANION_PORT
        and parsed.username is None
        and parsed.password is None
    )


class TokenStrippingRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            for header_map in (redirected.headers, redirected.unredirected_hdrs):
                for name in list(header_map):
                    if name.lower() == ACTION_TOKEN_HEADER.lower():
                        del header_map[name]
        return redirected


def open_json_request(req: request.Request, timeout: int | float):
    opener = request.build_opener(TokenStrippingRedirectHandler())
    return opener.open(req, timeout=timeout)
