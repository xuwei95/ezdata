# Live match snapshots

Read tennis match snapshots through the `live_matches` table.
The source uses the free `GET /matches?status=live` endpoint from Live Tennis API.

Install its optional dependencies from the repository root.

```bash
pip install -r api/ezdata/handlers/livetennis_handler/requirements.txt
```

Set `LIVETENNIS_API_KEY` to an existing free API key, then run Python with `PYTHONPATH=api`.

```python
import os

from ezdata import services

config = {}
secrets = {'api_key': os.environ['LIVETENNIS_API_KEY']}

print(services.list_tables('livetennis', config, secrets))
rows = services.query(
    'livetennis',
    config,
    secrets,
    statement={'func': 'live_matches', 'params': {'tour': 'atp'}},
    limit=10,
)
print(rows)
```

The API key is a secret connection parameter.
The platform can store it through its existing encrypted credential fields.
The connector uses `X-API-Key`. It never stores credentials in cache files or follows redirects.

## Queries and scores

The table accepts one query shape.

Use `live_matches` or `{'func': 'live_matches'}` as the statement.
A `tour` parameter filters the cached rows locally.
Limits also apply locally, so different queries share the same API request.
A zero limit returns no rows and makes no request.

Rows preserve the API's match fields, including `players` and `score`.
Missing scores and nullable points stay unknown.
The `score.games` arrays remain player-major.
For example, `[[6, 3], [4, 4]]` means set scores of 6-4 and 3-4.

Each row adds `snapshot_at`, the successful fetch time in UTC, and `snapshot_has_more`.
Snapshots contain at most 200 matches from the first page.
A true `snapshot_has_more` means other live matches were omitted.
The connector does not fetch additional pages.

Only live matches are supported.
Historical matches and rankings require other API plans and are outside this source.
The connector declares read and schema capabilities.
Writes, streaming, extraction and generated APIs are unsupported.

## Request budget and shared storage

`refresh_interval` defaults to 900 seconds.
Smaller values are clamped to 900.
That permits at most 96 attempts per 24 hours, within the free allowance of 100 requests per day.
Failed attempts count too.

A file lock and durable attempt timestamp share this budget across handler instances.
The lock also covers threads and separate processes.
The timestamp is saved before the request.
Restarting a process does not reset it.
Query changes and calendar dates do not reset it either.
During the interval, reads return the last successful snapshot with its original `snapshot_at`.
If no snapshot exists, reads report that another attempt must wait.

`cache_dir` defaults to a directory under the user's cache location.
Every process using the same API key must use the same directory.
For backend and worker containers, mount one persistent directory in both and set `cache_dir` to that path.
Keep these files between restarts.
A corrupt or unwritable cache blocks requests instead of resetting the budget.

`timeout` defaults to 30 seconds.
Metadata methods such as `list_tables` and `get_columns` make no requests.
`test_connection` uses the same snapshot and request floor as queries.

API fields and plan limits are documented in the [OpenAPI specification](https://docs.livetennisapi.com/openapi.yaml).
