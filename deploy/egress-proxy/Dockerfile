# 沙箱出网代理:构建期装好 tinyproxy(避免运行时 apk 抖动),运行时按白名单生成配置。
FROM alpine:3.19
RUN apk add --no-cache tinyproxy
COPY entrypoint.sh /egress/entrypoint.sh
ENTRYPOINT ["sh", "/egress/entrypoint.sh"]
