"""ezdata.interface:传输适配层(web / mcp / cli / skill)。

★护栏:本文件保持为空,绝不 import 任何子包——否则 `import ezdata.interface`
会把 fastapi/mcp/typer 等各入口的依赖一次性拖进来,破坏"用哪个才加载哪个"。
各子包(如 ezdata.interface.web)自带自己的启动入口与(可选)重依赖。
"""
