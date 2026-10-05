"""Live tennis score snapshots for the API source registry."""

from ezdata.handlers.livetennis_handler.connection_args import connection_args, connection_args_example

version = '0.0.1'
name = 'livetennis'
title = 'Live Tennis API'
family = 'api'
capabilities = ('READ', 'SCHEMA')
description = 'Live match snapshots with a shared, persistent 15 minute request floor.'


def load_handler():
    from ezdata.handlers.livetennis_handler.livetennis_handler import LiveTennisHandler

    return LiveTennisHandler


def __getattr__(attr):
    if attr == 'Handler':
        return load_handler()
    raise AttributeError(attr)


__all__ = [
    'Handler',
    'capabilities',
    'connection_args',
    'connection_args_example',
    'description',
    'family',
    'load_handler',
    'name',
    'title',
    'version',
]
