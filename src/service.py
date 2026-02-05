class SwapiService:
    def apply_filters(self, data, fields=None, sort=None, limit=None):
        if not isinstance(data, list):
            return data

        if fields:
            data = [{k: v for k, v in item.items() if k in fields} for item in data]

        if sort:
            reverse = sort.startswith("-")
            key = sort[1:] if reverse else sort
            data = sorted(data, key=lambda x: x.get(key), reverse=reverse)

        if limit:
            data = data[:limit]

        return data
