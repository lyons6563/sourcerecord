from urllib.parse import urlsplit, urlunsplit

def canonicalize_url(url: str) -> str:
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()

    # drop fragments always
    path = parts.path or "/"
    query = parts.query

    # normalize trailing slash (keep root as /, strip others)
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return urlunsplit((scheme, netloc, path, query, ""))
