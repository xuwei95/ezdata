import os


class Config:
    # 默认沿用测试 compose 的端口（前端 80）；可用环境变量指向其它环境（如 dev 栈的 12580）
    frontend_url = os.getenv('TEST_FRONTEND_URL', 'http://localhost:80')
    backend_url = os.getenv('TEST_BACKEND_URL', 'http://localhost:9099')
