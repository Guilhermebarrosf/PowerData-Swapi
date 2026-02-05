import json
import requests

SWAPI_BASE = "https://swapi.dev/api"
ALLOWED_RESOURCES = {"people", "films", "planets", "starships", "vehicles"}


# ---------- Helpers ----------

def json_response(payload: dict, status: int = 200):
    return (
        json.dumps(payload, ensure_ascii=False),
        status,
        {"Content-Type": "application/json; charset=utf-8"},
    )


def ok(data, meta=None):
    return json_response({"success": True, "data": data, "meta": meta or {}}, 200)


def fail(code: str, message: str, status: int, details: dict | None = None):
    return json_response(
        {
            "success": False,
            "error": {"code": code, "message": message, "details": details or {}},
        },
        status,
    )


def extract_resource_and_id_from_url(url: str):
    parts = [p for p in url.split("/") if p]
    if len(parts) < 2:
        return None, None
    return parts[-2], parts[-1]


def fetch_related_items(related_urls: list[str], fields: list[str] | None, limit: int | None):
    """
    Busca itens relacionados (ex: characters de um filme).
    Limitamos para não estourar tempo/custo.
    """
    max_items = limit or 10
    related_items = []

    for url in related_urls[:max_items]:
        rel_resource, rel_id = extract_resource_and_id_from_url(url)

        if rel_resource not in ALLOWED_RESOURCES or not rel_id:
            continue

        rel_url, rel_params = build_swapi_request(rel_resource, rel_id, None, None)
        rel_data, err_code, _, _ = fetch_swapi(rel_url, rel_params)

        if err_code:
            continue

        rel_data = filter_fields_item(rel_data, fields)
        related_items.append(rel_data)

    return related_items


def build_item_response_with_related(item: dict, related_name: str, related_items: list[dict], meta: dict):
    return ok(
        data={
            "item": item,
            "related": related_items
        },
        meta=meta | {"related": related_name}
    )

# ---------- Parsing ----------

def get_str(args, name: str) -> str | None:
    value = (args.get(name) or "").strip()
    return value if value else None


def parse_fields(fields_raw: str | None) -> list[str] | None:
    if not fields_raw:
        return None
    fields = [f.strip() for f in fields_raw.split(",") if f.strip()]
    return fields or None


def parse_limit(limit_raw: str | None) -> int | None:
    if not limit_raw:
        return None
    try:
        n = int(limit_raw)
    except ValueError:
        raise ValueError("limit must be a number")

    if n < 1 or n > 50:
        raise ValueError("limit must be between 1 and 50")

    return n


def validate_resource(resource: str | None):
    if not resource or resource not in ALLOWED_RESOURCES:
        raise ValueError("Invalid resource. Use: people, films, planets, starships, vehicles")


# ---------- fields/sort/limit ----------

def filter_fields_item(item: dict, fields: list[str] | None) -> dict:
    if not fields:
        return item
    return {k: v for k, v in item.items() if k in fields}


def filter_fields_list(items: list[dict], fields: list[str] | None) -> list[dict]:
    return [filter_fields_item(item, fields) for item in items]


def sort_results(items: list[dict], sort: str | None) -> list[dict]:
    if not sort:
        return items

    desc = sort.startswith("-")
    key = sort[1:] if desc else sort
    if not key:
        return items

    def getter(x):
        v = x.get(key)
        return (v is None, v)

    return sorted(items, key=getter, reverse=desc)


def apply_limit(items: list, limit: int | None) -> list:
    return items if limit is None else items[:limit]


# ---------- SWAPI ----------

def build_swapi_request(resource: str, item_id: str | None, search: str | None, page: str | None):
    if item_id:
        url = f"{SWAPI_BASE}/{resource}/{item_id}/"
        params = None
    else:
        url = f"{SWAPI_BASE}/{resource}/"
        params = {}
        if search:
            params["search"] = search
        if page:
            params["page"] = page
    return url, params


def fetch_swapi(url: str, params: dict | None):
    try:
        resp = requests.get(url, params=params, timeout=6)
    except requests.RequestException:
        return None, "UPSTREAM_UNAVAILABLE", 503, "SWAPI unavailable"

    if resp.status_code == 404:
        return None, "NOT_FOUND", 404, "Item not found"

    if resp.status_code >= 400:
        return None, "UPSTREAM_ERROR", 502, f"SWAPI error {resp.status_code}"

    return resp.json(), None, None, None


# ---------- Cloud Function ----------

def swapi(request):
    if request.method != "GET":
        return fail("METHOD_NOT_ALLOWED", "Only GET allowed", 405)

    args = request.args or {}

    resource = get_str(args, "resource")
    item_id = get_str(args, "id")
    search = get_str(args, "search")
    page = get_str(args, "page")

    fields_raw = get_str(args, "fields")
    sort = get_str(args, "sort")
    limit_raw = get_str(args, "limit")

    related = get_str(args, "related")


    try:
        validate_resource(resource)
        fields = parse_fields(fields_raw)
        limit = parse_limit(limit_raw)
    except ValueError as e:
        return fail("INVALID_PARAMS", str(e), 400)

    url, params = build_swapi_request(resource, item_id, search, page)

    data, err_code, err_status, err_message = fetch_swapi(url, params)
    if err_code:
        return fail(err_code, err_message, err_status)

    if item_id:
        item = filter_fields_item(data, fields)
        meta = {"resource": resource, "id": item_id}

        if related:
            rel_urls = data.get(related)
            if isinstance(rel_urls, list) and rel_urls:
                related_items = fetch_related_items(rel_urls, fields, limit)
            else:
                related_items = []

            return build_item_response_with_related(item, related, related_items, meta)

        return ok(item, meta=meta)


    results = data.get("results", [])
    results = filter_fields_list(results, fields)
    results = sort_results(results, sort)
    results = apply_limit(results, limit)

    meta = {
        "resource": resource,
        "count": data.get("count"),
        "next": data.get("next"),
        "previous": data.get("previous"),
        "page": page or 1,
        "limit": limit,
        "sort": sort,
        "fields": fields,
    }

    return ok(results, meta=meta)
