"""Live snapshot behavior through the connector and its public facade."""

import copy
import hashlib
import importlib
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ezdata.handlers import Capability, connection_schema, create_handler, get_write_modes
from ezdata.services import facade, secrets

MODULE = 'ezdata.handlers.livetennis_handler.livetennis_handler'
KEY = 'test-credential-never-persist'
START = 1_800_000_000.0
MATCH = {
    'id': 42,
    'tour': 'atp',
    'status': 'live',
    'tournament': 'Example Open',
    'players': {'p1': {'name': 'First Player'}, 'p2': {'name': 'Second Player'}},
    'score': {
        'sets': [1, 1],
        'games': [[6, 4, 1], [4, 6, 0]],
        'points': ['40', '30'],
        'server': 1,
        'is_tiebreak': False,
    },
    'extra_field': {'value': 'preserved'},
}


class Response:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status
        self.closed = False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f'HTTP {self.status_code}')

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return copy.deepcopy(self.payload)

    def close(self):
        self.closed = True


def payload(rows=None, has_more=False):
    return {'data': [copy.deepcopy(MATCH)] if rows is None else rows, 'meta': {'has_more': has_more}}


def state_path(cache_dir, key=KEY):
    return Path(cache_dir) / (hashlib.sha256(key.encode()).hexdigest() + '.json')


@pytest.fixture
def api(monkeypatch, tmp_path):
    module = importlib.import_module(MODULE)
    now = [START]
    calls = []
    replies = []

    def get(url, **kwargs):
        calls.append((url, copy.deepcopy(kwargs)))
        reply = replies.pop(0) if replies else Response(payload())
        if isinstance(reply, Exception):
            raise reply
        return reply

    def make(**changes):
        return module.LiveTennisHandler({'api_key': KEY, 'cache_dir': str(tmp_path), **changes})

    monkeypatch.setattr(module.requests, 'get', get)
    monkeypatch.setattr(module.time, 'time', lambda: now[0])
    return SimpleNamespace(module=module, now=now, calls=calls, replies=replies, make=make, cache_dir=tmp_path)


def test_fixed_free_request_preserves_raw_scores_and_marks_snapshot(api):
    original = copy.deepcopy(MATCH)
    api.replies.append(Response(payload(has_more=True)))
    rows = api.make().query('live_matches')
    assert len(api.calls) == 1
    url, kwargs = api.calls[0]
    assert url == 'https://api.livetennisapi.com/api/public/v1/matches'
    assert kwargs['params'] == {'status': 'live', 'limit': 200}
    assert {key.lower(): value for key, value in kwargs['headers'].items()} == {'x-api-key': KEY}
    assert kwargs['allow_redirects'] is False
    assert kwargs['timeout'] > 0
    assert {name: rows[0][name] for name in original} == original
    assert rows[0]['snapshot_has_more'] is True
    fetched_at = datetime.fromisoformat(rows[0]['snapshot_at'].replace('Z', '+00:00'))
    assert fetched_at.utcoffset().total_seconds() == 0
    assert fetched_at.timestamp() == START
    persisted = state_path(api.cache_dir).read_text()
    assert KEY not in persisted
    assert all(KEY not in entry.name for entry in api.cache_dir.iterdir())


def test_nullable_scores_remain_nullable(api):
    unavailable = {**MATCH, 'score': None}
    withheld = {**MATCH, 'id': 43, 'score': {'sets': [0, 0], 'games': None, 'points': None, 'server': None}}
    api.replies.append(Response(payload([unavailable, withheld])))
    rows = api.make().query('live_matches')
    assert rows[0]['score'] is None
    assert rows[1]['score'] == withheld['score']
    assert rows[0]['players'] == MATCH['players']
    assert rows[0]['tournament'] == MATCH['tournament']


def test_tour_and_limit_filter_locally_without_changing_request(api):
    api.replies.append(Response(payload([MATCH, {**MATCH, 'id': 43, 'tour': 'wta'}, {**MATCH, 'id': 44}])))
    handler = api.make()
    assert [row['id'] for row in handler.query('live_matches', {'tour': 'atp'}, 1)] == [42]
    assert [row['id'] for row in handler.query({'func': 'live_matches', 'params': {'tour': 'wta'}})] == [43]
    assert len(api.calls) == 1
    assert api.calls[0][1]['params'] == {'status': 'live', 'limit': 200}


def test_zero_limit_does_not_read_cache_or_call_api(api):
    assert api.module.LiveTennisHandler({}).query('live_matches', limit=0) == []
    assert api.calls == []
    assert list(api.cache_dir.iterdir()) == []


@pytest.mark.parametrize('limit', [-1, True, 1.5])
def test_invalid_local_limits_do_not_call_api(api, limit):
    with pytest.raises(ValueError):
        api.make().query('live_matches', limit=limit)
    assert api.calls == []


@pytest.mark.parametrize(
    ('statement', 'params'),
    [
        ('matches', None),
        ('fixtures', None),
        ({'func': 'rankings'}, None),
        ({'func': 'live_matches', 'params': {'status': 'finished'}}, None),
        ('live_matches', {'date': '2026-10-05'}),
        ('live_matches', {'limit': 1000}),
        ('live_matches', {'tour': 'padel'}),
        ({'func': 'live_matches', 'params': {'tour': 'atp'}}, {'tour': 'wta'}),
    ],
)
def test_only_live_matches_and_supported_local_filters_are_admitted(api, statement, params):
    with pytest.raises(ValueError):
        api.make().query(statement, params)
    assert api.calls == []


def test_registration_and_schema_discovery_do_not_load_connector():
    script = f"""
import json, sys
from ezdata.handlers import connection_schema, list_source_types
name = {MODULE!r}
assert name not in sys.modules
source = next(row for row in list_source_types() if row['source_type'] == 'livetennis')
schema = connection_schema('livetennis')
assert name not in sys.modules
assert source['family'] == 'api'
assert set(source['capabilities']) == {{'READ', 'SCHEMA'}}
assert schema['properties']['api_key']['writeOnly'] is True
assert 'default' not in schema['properties']['api_key']
print(json.dumps(source))
"""
    env = {**os.environ, 'PYTHONPATH': os.pathsep.join(sys.path)}
    result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True, check=True, env=env)
    assert json.loads(result.stdout)['source_type'] == 'livetennis'


def test_offline_metadata_and_facade_with_secret_injection(api, monkeypatch):
    handler = api.module.LiveTennisHandler({})
    assert handler.list_tables() == ['live_matches']
    columns = {column.name: column for column in handler.get_columns('live_matches')}
    assert {'players', 'tournament', 'score', 'snapshot_at', 'snapshot_has_more'} <= set(columns)
    assert columns['score'].nullable
    assert handler.has(Capability.READ) and handler.has(Capability.SCHEMA)
    assert not handler.has(Capability.WRITE) and not handler.has(Capability.EXTRACT)
    assert not handler.has(Capability.GEN_API)
    assert get_write_modes('livetennis') == []
    assert handler.secret_fields() == ['api_key']
    assert connection_schema('livetennis')['properties']['api_key']['format'] == 'password'
    assert api.calls == []

    monkeypatch.setattr(
        secrets, '_decryptor', lambda value: json.dumps({'api_key': KEY}) if value == 'cipher' else '{}'
    )
    restored = create_handler('livetennis', {'cache_dir': str(api.cache_dir)}, 'cipher', cache=False)
    assert isinstance(restored, api.module.LiveTennisHandler)
    api.replies.append(Response(payload([{**MATCH, 'tour': 'wta'}])))
    rows = facade.query(
        'livetennis',
        {'cache_dir': str(api.cache_dir)},
        {'api_key': KEY},
        statement={'func': 'live_matches', 'params': {'tour': 'wta'}},
        limit=1,
    )
    assert [row['id'] for row in rows] == [42]
    assert restored.query('live_matches') == rows
    assert len(api.calls) == 1


def test_restarts_and_changed_settings_share_attempt_floor(api):
    first = api.make(refresh_interval=1, timeout=2).query('live_matches')
    api.now[0] += 899
    restarted = api.make(refresh_interval=-1, timeout=30)
    assert restarted.query('live_matches') == first
    assert len(api.calls) == 1
    api.now[0] += 1
    restarted.query('live_matches')
    assert len(api.calls) == 2


def test_requested_longer_refresh_is_respected(api):
    handler = api.make(refresh_interval=1800)
    first = handler.query('live_matches')
    api.now[0] += 900
    assert handler.query('live_matches') == first
    assert len(api.calls) == 1
    api.now[0] += 900
    handler.query('live_matches')
    assert len(api.calls) == 2


def test_at_most_96_attempts_in_half_open_day(api):
    handler = api.make(refresh_interval=0)
    for offset in range(0, 86_400, 900):
        api.now[0] = START + offset
        handler.query('live_matches')
        api.now[0] += 899
        api.make(timeout=1).query('live_matches')
    assert len(api.calls) == 96
    assert api.now[0] < START + 86_400


@pytest.mark.parametrize('status', [302, 401, 429, 500])
def test_failed_http_attempts_are_not_followed_or_retried(api, status):
    api.replies.append(Response(payload(), status=status))
    with pytest.raises(RuntimeError):
        api.make().query('live_matches')
    api.now[0] += 899
    with pytest.raises(RuntimeError):
        api.make(timeout=1).query('live_matches')
    assert len(api.calls) == 1
    api.now[0] += 1
    assert api.make().query('live_matches')
    assert len(api.calls) == 2


@pytest.mark.parametrize(
    'invalid_payload',
    [
        ValueError('invalid JSON'),
        {'data': [], 'error': 'denied'},
        {'data': None, 'meta': {'has_more': False}},
        {'data': [None], 'meta': {'has_more': False}},
        {'data': [], 'meta': {}},
        {'data': [], 'meta': {'has_more': 'false'}},
    ],
)
def test_malformed_responses_reserve_attempt_budget(api, invalid_payload):
    api.replies.append(Response(invalid_payload))
    with pytest.raises(RuntimeError):
        api.make().query('live_matches')
    with pytest.raises(RuntimeError):
        api.make().query('live_matches')
    assert len(api.calls) == 1


def test_failure_preserves_successful_snapshot_and_does_not_leak_secret(api):
    handler = api.make()
    first = handler.query('live_matches')
    api.now[0] += 900
    api.replies.append(requests.Timeout(f'request failed with {KEY}'))
    with pytest.raises(RuntimeError) as error:
        handler.query('live_matches')
    assert KEY not in str(error.value)
    assert error.value.__suppress_context__
    assert api.make().query('live_matches') == first
    assert len(api.calls) == 2
    assert KEY not in state_path(api.cache_dir).read_text()


def test_successful_empty_snapshot_survives_restart(api):
    api.replies.append(Response(payload([])))
    assert api.make().query('live_matches') == []
    assert api.make().query('live_matches') == []
    assert len(api.calls) == 1


def test_each_api_key_has_an_independent_budget(api):
    first = api.make().query('live_matches')
    other_key = 'another-test-credential'
    other = api.make(api_key=other_key).query('live_matches')
    assert other == first
    assert len(api.calls) == 2
    assert api.make().query('live_matches') == first
    assert len(api.calls) == 2
    assert state_path(api.cache_dir).is_file()
    assert state_path(api.cache_dir, other_key).is_file()


def test_corrupt_state_never_resets_attempt_floor(api):
    api.make().query('live_matches')
    state_path(api.cache_dir).write_text('{broken')
    api.now[0] += 1
    with pytest.raises(RuntimeError):
        api.make().query('live_matches')
    assert len(api.calls) == 1


@pytest.mark.parametrize('last_attempt', [str(START), True, float('nan'), float('inf'), float('-inf')])
def test_invalid_saved_attempt_time_fails_closed(api, last_attempt):
    api.make().query('live_matches')
    path = state_path(api.cache_dir)
    state = json.loads(path.read_text())
    state['last_attempt'] = last_attempt
    path.write_text(json.dumps(state))
    api.now[0] += 900
    with pytest.raises(RuntimeError) as error:
        api.make().query('live_matches')
    assert KEY not in str(error.value)
    assert len(api.calls) == 1


def test_saved_json_number_overflow_fails_closed(api):
    api.make().query('live_matches')
    path = state_path(api.cache_dir)
    state = json.loads(path.read_text())
    state['last_attempt'] = 'overflow-marker'
    path.write_text(json.dumps(state).replace('"overflow-marker"', '1e1000'))
    api.now[0] += 900
    with pytest.raises(RuntimeError):
        api.make().query('live_matches')
    assert len(api.calls) == 1


def test_clock_rollback_cannot_create_another_attempt(api):
    first = api.make().query('live_matches')
    api.now[0] -= 3600
    assert api.make().query('live_matches') == first
    api.now[0] = START + 899
    assert api.make().query('live_matches') == first
    assert len(api.calls) == 1
    api.now[0] = START + 900
    api.make().query('live_matches')
    assert len(api.calls) == 2


@pytest.mark.parametrize(
    'config',
    [
        {'api_key': ''},
        {'api_key': None},
        {'timeout': 0},
        {'timeout': float('nan')},
        {'timeout': float('inf')},
        {'refresh_interval': float('nan')},
        {'refresh_interval': float('inf')},
    ],
)
def test_invalid_configuration_fails_without_calling_api(api, config):
    with pytest.raises((ValueError, RuntimeError)):
        api.make(**config).query('live_matches')
    assert api.calls == []


def test_cache_reservation_failure_prevents_network_request(api, monkeypatch):
    def fail_replace(*args, **kwargs):
        raise OSError('disk unavailable')

    monkeypatch.setattr(api.module.os, 'replace', fail_replace)
    with pytest.raises(RuntimeError):
        api.make().query('live_matches')
    assert api.calls == []


def test_failure_saving_response_keeps_persisted_attempt_budget(api, monkeypatch):
    replace = api.module.os.replace
    writes = []

    def fail_snapshot_write(source, destination):
        writes.append(destination)
        if len(writes) == 2:
            raise OSError('snapshot disk write failed')
        replace(source, destination)

    monkeypatch.setattr(api.module.os, 'replace', fail_snapshot_write)
    with pytest.raises(RuntimeError):
        api.make().query('live_matches')
    assert len(api.calls) == 1
    with pytest.raises(RuntimeError):
        api.make().query('live_matches')
    assert len(api.calls) == 1


def test_response_echoing_key_is_rejected_before_persistence(api):
    api.replies.append(Response(payload([{**MATCH, 'unexpected': KEY}])))
    with pytest.raises(RuntimeError) as error:
        api.make().query('live_matches')
    assert KEY not in str(error.value)
    assert KEY not in state_path(api.cache_dir).read_text()
    assert len(api.calls) == 1


@pytest.mark.parametrize('status', [200, 500])
def test_response_close_failure_cannot_leak_key_or_reset_budget(api, status):
    closed = []

    class BrokenCloseResponse(Response):
        def close(self):
            closed.append(True)
            raise RuntimeError(f'close failed with {KEY}')

    api.replies.append(BrokenCloseResponse(payload(), status=status))
    if status == 200:
        rows = api.make().query('live_matches')
        assert KEY not in json.dumps(rows)
    else:
        with pytest.raises(RuntimeError) as error:
            api.make().query('live_matches')
        assert KEY not in str(error.value)
        assert error.value.__suppress_context__
    api.now[0] += 899
    result = api.make().test_connection()
    assert result.success is (status == 200)
    assert KEY not in result.message
    assert KEY not in state_path(api.cache_dir).read_text()
    assert len(api.calls) == 1
    assert closed == [True]


def test_multiple_threads_share_one_inflight_attempt(api, monkeypatch):
    entered = threading.Event()
    release = threading.Event()
    calls = []

    def get(url, **kwargs):
        calls.append(url)
        entered.set()
        assert release.wait(5)
        return Response(payload())

    monkeypatch.setattr(api.module.requests, 'get', get)
    with ThreadPoolExecutor(max_workers=4) as pool:
        first = pool.submit(api.make().query, 'live_matches')
        assert entered.wait(5)
        others = [pool.submit(api.make().query, 'live_matches') for _ in range(3)]
        release.set()
        rows = first.result(timeout=5)
        assert all(future.result(timeout=5) == rows for future in others)
    assert len(calls) == 1


def test_separate_processes_share_one_attempt_and_snapshot(tmp_path):
    script = f"""
import json, pathlib, sys, time
from importlib import import_module
module = import_module({MODULE!r})
directory = pathlib.Path(sys.argv[1])
module.time.time = lambda: {START!r}
class Response:
    status_code = 200
    def raise_for_status(self): pass
    def json(self): return {payload()!r}
    def close(self): pass
def get(*args, **kwargs):
    with (directory / 'attempts').open('a') as stream: stream.write('request\\n')
    time.sleep(0.1)
    return Response()
module.requests.get = get
(directory / ('ready-' + sys.argv[2])).touch()
while not (directory / 'start').exists(): time.sleep(0.01)
handler = module.LiveTennisHandler({{'api_key': {KEY!r}, 'cache_dir': str(directory)}})
print(json.dumps(handler.query('live_matches')))
"""
    env = {**os.environ, 'PYTHONPATH': os.pathsep.join(sys.path)}
    processes = [
        subprocess.Popen(
            [sys.executable, '-c', script, str(tmp_path), str(index)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        for index in range(2)
    ]
    try:
        deadline = time.monotonic() + 15
        while len(list(tmp_path.glob('ready-*'))) < 2:
            assert time.monotonic() < deadline, 'subprocess did not reach query barrier'
            assert all(process.poll() is None for process in processes), 'subprocess exited before query barrier'
            time.sleep(0.01)
        (tmp_path / 'start').touch()
        outputs = [process.communicate(timeout=15) for process in processes]
        for process, (_, stderr) in zip(processes, outputs):
            assert process.returncode == 0, stderr
        assert json.loads(outputs[0][0]) == json.loads(outputs[1][0])
        assert json.loads(outputs[0][0])[0]['players'] == MATCH['players']
        assert (tmp_path / 'attempts').read_text().splitlines() == ['request']
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait()
