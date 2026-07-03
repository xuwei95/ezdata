"""ezdata 语义异常。

目标:让 web/cli/mcp/AI 能统一 catch,并**结构化带出原始报错**——这对 AI 改代码很关键:
- `raise EzXxx(...) from e` 保留异常链(__cause__),完整 traceback 可查;
- `to_dict()` 把原始报错(cause_type/cause_message)+ 出错语句结构化带出,默认不含 traceback(省 token),
  需要时 `to_dict(with_traceback=True)` 再给尾部截断的栈。
"""

import traceback


class EzDataError(Exception):
    """ezdata 所有可预期错误的基类。

    携带定位上下文(source_type/statement/context)与原始异常(__cause__),供结构化上报。
    """

    def __init__(self, message: str, *, source_type: str | None = None,
                 statement: object = None, **context: object) -> None:
        super().__init__(message)
        self.source_type = source_type
        self.statement = statement
        self.context = context

    def to_dict(self, *, with_traceback: bool = False, tb_chars: int = 1500,
                cause_chars: int = 2000) -> dict:
        """结构化上报。默认精简(不含 traceback,省 token);cause_message 是 AI 改代码最有用的信息。"""
        cause = self.__cause__
        cmsg = str(cause) if cause is not None else None
        if cmsg is not None and len(cmsg) > cause_chars:
            cmsg = cmsg[:cause_chars] + '…(截断)'
        d: dict = {
            'error': type(self).__name__,
            'message': str(self),
            'source_type': self.source_type,
            'statement': self.statement,
            'context': self.context or None,
            'cause_type': type(cause).__name__ if cause is not None else None,
            'cause_message': cmsg,
        }
        if with_traceback and cause is not None:
            tb = ''.join(traceback.format_exception(type(cause), cause, cause.__traceback__))
            d['traceback'] = tb[-tb_chars:]  # 栈底最相关,尾部截断封顶
        return d


class UnknownSourceError(EzDataError):
    """未注册的数据源类型(source_type)。"""


class DependencyError(EzDataError):
    """连接器依赖/驱动缺失(装 extras 或 services.install_dependencies)。"""


class CapabilityError(EzDataError):
    """该数据源不支持所请求的能力(READ/WRITE/SCHEMA/...)。"""


class ConnectionFailed(EzDataError):
    """连接/认证失败(handler 明确知道是连接问题时抛)。"""


class QueryError(EzDataError):
    """查询/写入执行失败(包裹底层驱动异常,原文见 __cause__ / to_dict)。"""


class ReadOnlyViolation(EzDataError, ValueError):
    """只读护栏拦截(非 SELECT/只读语句)。

    多继承 ValueError:兼容既有 `except ValueError` 的调用点。
    """
