"""Read shared live match snapshots within the free plan's daily request budget."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import stat
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from filelock import FileLock, Timeout

from ezdata.handlers.base import Capability, Column, Connector, ConnectResult
from ezdata.handlers.livetennis_handler.connection_args import connection_args, connection_args_example

MATCHES_URL = 'https://api.livetennisapi.com/api/public/v1/matches'
MIN_REFRESH_INTERVAL = 900
TOURS = frozenset({'atp', 'wta', 'challenger', 'itf', 'juniors'})
TABLE = 'live_matches'


def _positive_number(value: Any, field: str, *, allow_zero: bool = False) -> float:
    if isinstance(value, bool):
        raise ValueError(f'{field} must be a finite positive number.')
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f'{field} must be a finite positive number.') from None
    if not math.isfinite(number) or number < 0 or (not allow_zero and number == 0):
        raise ValueError(f'{field} must be a finite positive number.')
    return number


def _default_cache_dir() -> Path:
    base = os.environ.get('XDG_CACHE_HOME')
    return (Path(base).expanduser() if base else Path.home() / '.cache') / 'ezdata' / 'livetennis'


def _validate_table(table: Any) -> None:
    if table != TABLE:
        raise ValueError('Only the live_matches table is supported.')


def _reject_json_constant(value: str) -> None:
    raise ValueError('Nonfinite numbers are not valid cache data.')


class LiveTennisHandler(Connector):
    name = 'livetennis'
    title = 'Live Tennis API'
    family = 'api'
    capabilities = Capability.READ | Capability.SCHEMA
    connection_args = connection_args
    connection_args_example = connection_args_example

    def list_tables(self) -> list[str]:
        return [TABLE]

    def get_columns(self, table: str) -> list[Column]:
        _validate_table(table)
        return [
            Column('id', 'integer', nullable=False),
            Column('tournament', 'string', nullable=False),
            Column('tour', 'string'),
            Column('status', 'string', nullable=False),
            Column('scheduled_time', 'string'),
            Column('players', 'object', nullable=False),
            Column('score', 'object'),
            Column(
                'snapshot_at', 'string', nullable=False, comment='UTC time of the last successful snapshot request.'
            ),
            Column(
                'snapshot_has_more',
                'boolean',
                nullable=False,
                comment='The API reported more matches beyond this page.',
            ),
        ]

    def sample_query(self, table: str, limit: int = 100) -> dict:
        _validate_table(table)
        return {'func': TABLE}

    def describe(self, table: str) -> str:
        _validate_table(table)
        return 'Live matches from one shared snapshot. Only the first 200 matches are fetched. Optional tour filtering is local.'

    def test_connection(self) -> ConnectResult:
        try:
            snapshot = self._snapshot()
        except (ValueError, RuntimeError) as exc:
            return ConnectResult(False, str(exc))
        return ConnectResult(True, f'Live match snapshot fetched at {snapshot["fetched_at"]}.')

    def query(self, statement: Any, params: dict | None = None, limit: int | None = None) -> list[dict]:
        embedded = None
        if isinstance(statement, dict):
            if set(statement) - {'func', 'params'}:
                raise ValueError('The query supports only func and params.')
            _validate_table(statement.get('func'))
            embedded = statement.get('params')
        else:
            _validate_table(statement)
        filters: dict = {}
        for supplied in (embedded, params):
            if supplied is None:
                continue
            if not isinstance(supplied, dict) or set(supplied) - {'tour'}:
                raise ValueError('Only the local tour filter is supported.')
            if 'tour' in supplied:
                tour = supplied['tour']
                if not isinstance(tour, str) or tour not in TOURS:
                    raise ValueError('tour must be atp, wta, challenger, itf or juniors.')
                if 'tour' in filters and filters['tour'] != tour:
                    raise ValueError('The query contains conflicting tour filters.')
                filters['tour'] = tour
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 0):
            raise ValueError('limit must be a nonnegative integer.')
        if limit == 0:
            return []
        snapshot = self._snapshot()
        rows = [
            dict(copy.deepcopy(row), snapshot_at=snapshot['fetched_at'], snapshot_has_more=snapshot['has_more'])
            for row in snapshot['data']
            if not filters or row.get('tour') == filters['tour']
        ]
        return rows if limit is None else rows[:limit]

    def _settings(self) -> tuple[str, Path, float, float]:
        key = self.arg('api_key')
        if not isinstance(key, str) or not key.strip() or '\r' in key or '\n' in key:
            raise ValueError('A nonempty API key is required.')
        refresh = self.arg('refresh_interval', default=MIN_REFRESH_INTERVAL)
        try:
            if isinstance(refresh, bool):
                raise ValueError
            interval = float(refresh)
            if not math.isfinite(interval):
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            raise ValueError('refresh_interval must be a finite number.') from None
        interval = max(MIN_REFRESH_INTERVAL, interval)
        timeout = _positive_number(self.arg('timeout', default=30), 'timeout')
        try:
            cache_dir = Path(self.arg('cache_dir', default=_default_cache_dir())).expanduser()
        except (TypeError, ValueError):
            raise ValueError('cache_dir must be a filesystem path.') from None
        return key, cache_dir, interval, timeout

    def _snapshot(self) -> dict:
        key, cache_dir, interval, timeout = self._settings()
        digest = hashlib.sha256(key.encode('utf-8')).hexdigest()
        state_path = cache_dir / f'{digest}.json'
        lock_path = cache_dir / f'{digest}.json.lock'
        try:
            self._prepare_directory(cache_dir)
            if lock_path.is_symlink():
                raise RuntimeError('The snapshot lock must be a regular file.')
            with FileLock(str(lock_path), timeout=timeout + 5, mode=0o600):
                state = self._load_state(state_path)
                now = _positive_number(time.time(), 'Current time', allow_zero=True)
                if state is not None and now - state['last_attempt'] < interval:
                    if state['snapshot'] is not None:
                        return state['snapshot']
                    raise RuntimeError('No successful snapshot is cached. Retry after the refresh interval.')
                state = state or {'version': 1, 'last_attempt': now, 'snapshot': None}
                state['last_attempt'] = now
                # 86400 / 900 = 96 attempts a day, below the free plan's 100 request limit.
                # Persist before HTTP so failures, restarts and other readers share the same floor.
                self._write_state(state_path, state)
                snapshot = self._fetch_snapshot(key, timeout)
                state['snapshot'] = snapshot
                self._write_state(state_path, state)
                return snapshot
        except Timeout:
            raise RuntimeError('The snapshot cache is busy. Retry later.') from None
        except OSError:
            raise RuntimeError('The private snapshot cache cannot be accessed.') from None

    @staticmethod
    def _prepare_directory(cache_dir: Path) -> None:
        if cache_dir.is_symlink():
            raise RuntimeError('The snapshot cache directory must not be a symbolic link.')
        cache_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = cache_dir.stat()
        if not stat.S_ISDIR(info.st_mode):
            raise RuntimeError('The snapshot cache path must be a directory.')
        if os.name == 'posix' and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
            raise RuntimeError('The snapshot cache directory must be private and owned by the current user.')

    @staticmethod
    def _load_state(path: Path) -> dict | None:
        if path.is_symlink():
            raise RuntimeError('The snapshot cache must be a regular file.')
        try:
            info = path.stat()
        except FileNotFoundError:
            return None
        if not stat.S_ISREG(info.st_mode):
            raise RuntimeError('The snapshot cache must be a regular file.')
        if os.name == 'posix' and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
            raise RuntimeError('The snapshot cache file must be private and owned by the current user.')
        try:
            state = json.loads(path.read_text(encoding='utf-8'), parse_constant=_reject_json_constant)
            if not isinstance(state, dict) or type(state.get('version')) is not int or state['version'] != 1:
                raise ValueError
            if isinstance(state.get('last_attempt'), bool) or not isinstance(state.get('last_attempt'), (int, float)):
                raise ValueError
            _positive_number(state['last_attempt'], 'Cached attempt time', allow_zero=True)
            if state.get('snapshot') is not None:
                snapshot = state['snapshot']
                LiveTennisHandler._validate_payload(
                    {'data': snapshot['data'], 'meta': {'has_more': snapshot['has_more']}}
                )
                stamp = datetime.fromisoformat(snapshot['fetched_at'].replace('Z', '+00:00'))
                if stamp.tzinfo is None or stamp.utcoffset().total_seconds() != 0:
                    raise ValueError
            elif 'snapshot' not in state:
                raise ValueError
            return state
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            raise RuntimeError(
                'The snapshot cache is corrupt. Restore it before requesting another snapshot.'
            ) from None

    @staticmethod
    def _write_state(path: Path, state: dict) -> None:
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8', dir=path.parent, prefix=path.stem + '-', delete=False
            ) as handle:
                temporary = Path(handle.name)
                json.dump(state, handle, ensure_ascii=False, allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            if os.name == 'posix':
                directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    @staticmethod
    def _validate_payload(payload: Any) -> None:
        if not isinstance(payload, dict) or not isinstance(payload.get('data'), list):
            raise ValueError('Invalid snapshot response.')
        if any(not isinstance(row, dict) for row in payload['data']):
            raise ValueError('Invalid snapshot response.')
        meta = payload.get('meta')
        if not isinstance(meta, dict) or not isinstance(meta.get('has_more'), bool):
            raise ValueError('Invalid snapshot response.')

    @staticmethod
    def _fetch_snapshot(key: str, timeout: float) -> dict:
        response = None
        try:
            response = requests.get(
                MATCHES_URL,
                params={'status': 'live', 'limit': 200},
                headers={'X-API-Key': key},
                timeout=timeout,
                allow_redirects=False,
            )
            if response.status_code != 200:
                raise ValueError
            payload = response.json()
            LiveTennisHandler._validate_payload(payload)
            if key in json.dumps(payload, ensure_ascii=False, allow_nan=False):
                raise ValueError
            fetched_at = datetime.fromtimestamp(time.time(), tz=timezone.utc).isoformat().replace('+00:00', 'Z')
            return {'data': payload['data'], 'has_more': payload['meta']['has_more'], 'fetched_at': fetched_at}
        except Exception:
            raise RuntimeError('The live match snapshot request failed. Retry after the refresh interval.') from None
        finally:
            if response is not None:
                close = getattr(response, 'close', None)
                if callable(close):
                    try:
                        close()
                    except Exception:
                        pass
