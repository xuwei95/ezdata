from logging.handlers import BufferingHandler
import requests
import logging
import json
import traceback


class ClickhouseMemoryHandler(BufferingHandler):
    """
    A handler class which buffers logging records in memory, periodically
    flushing them to a target handler. Flushing occurs whenever the buffer
    is full, or when an event of a certain severity or greater is seen.
    """
    def __init__(self, capacity, wait_on_flush=False,
                 ch_conn='http://localhost:8123', ch_table=None,
                 logging_build_in_columns_to_ch=None):
        """
        Initialize the handler with the buffer size, the level at which
        flushing should occur and an optional target.
        Note that without a target being set either here or via setTarget(),
        a MemoryHandler is no use to anyone!
        """
        BufferingHandler.__init__(self, capacity)
        self.wait_on_flush = wait_on_flush
        if not ch_table:
            raise ValueError('ch_table must be provided')
        self.ch_table = ch_table
        self.ch_conn = ch_conn
        self.build_in_keys_to_ch = logging_build_in_columns_to_ch or ['message', 'levelname', 'filename',
                                                                      'module', 'lineno,', 'exc_info',
                                                                      'created', 'msecs',
                                                                      'relativeCreated', 'asctime']
        self.build_in_log_keys = ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 'module',
                                  'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName', 'created', 'msecs',
                                  'relativeCreated', 'thread', 'threadName', 'processName', 'process']

    def shouldFlush(self, record):
        """
        Check for buffer full or a record at the flushLevel or higher.
        """
        return len(self.buffer) >= self.capacity

    def flush(self):
        """
        For a MemoryHandler, flushing means just sending the buffered
        records to the target, if there is one. Override if you want
        different behaviour.
        The record buffer is also cleared by this operation.
        """
        self.acquire()
        try:
            if len(self.buffer) > 0:
                _data = ''
                for record in self.buffer:
                    message_dict = record.__dict__.copy()

                    if record.exc_info:
                        ex = record.exc_info
                        message_dict['exc_info'] = ('\n'.join(traceback.format_exception(etype=ex[0],
                                                                                         value=ex[1],
                                                                                         tb=ex[2])))
                    try:
                        if record.stack_info and not message_dict.get('stack_info'):
                            message_dict['stack_info'] = self.formatStack(record.stack_info)
                    except AttributeError:
                        # Python2.7 doesn't have stack_info.
                        pass

                    for key in list(message_dict.keys()):
                        if key in self.build_in_log_keys and key not in self.build_in_keys_to_ch:
                            del message_dict[key]

                    _data += json.dumps(message_dict) + '\n'

                if _data:
                    sql = f'insert into {self.ch_table} format JSONEachRow'
                    try:
                        res = requests.post(url=self.ch_conn, params={'query': sql,
                                                                      'input_format_skip_unknown_fields': 1},
                                            data=_data)
                        res.raise_for_status()
                    except requests.exceptions.RequestException:
                        self.handleError(record)
                        record.__dict__['msg'] = res.__dict__.get('_content', 'There is no response text.')
                        self.handleError(record)
                self.buffer = []
        finally:
            self.release()

    def close(self):
        """
        Flush, set the target to None and lose the buffer.
        """
        try:
            self.flush()
        finally:
            self.acquire()
            try:
                BufferingHandler.close(self)
            finally:
                self.release()


def getLogger(name, capacity=100000, filename=None,
              file_handler_format='%(levelname) -10s %(asctime)s %(module)s:%(lineno)s %(funcName)s %(message)s',
              file_handler_date_format='%Y-%m-%d %H:%M:%S',
              level=logging.INFO, wait_on_flush=True,
              ch_conn=None, ch_table=None):
    logger = logging.getLogger(name)
    handler = ClickhouseMemoryHandler(capacity=capacity, wait_on_flush=wait_on_flush, ch_conn=ch_conn,
                                      ch_table=ch_table)
    if filename:
        file_handler = logging.FileHandler(filename)
        formatter = logging.Formatter(file_handler_format, file_handler_date_format)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger