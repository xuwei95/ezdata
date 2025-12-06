FROM continuumio/miniconda3:23.3.1-0
ENV LANG C.UTF-8
ENV TZ=Asia/Shanghai
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/opt/conda/bin:$PATH
RUN sed -i s@/archive.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list
RUN sed -i s@/security.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list
RUN apt-get clean
RUN apt-get update
RUN apt-get install wget tmux htop vim net-tools git -y
RUN apt install -y tzdata \
    && ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/xuwei95/ezdata.git /opt/ezdata
WORKDIR /opt/ezdata/api
RUN cd /opt/ezdata/api
RUN pip install -r requirements.txt --use-deprecated=legacy-resolver

# 安装 MindsDB handlers 的依赖
# 通过环境变量 MINDSDB_HANDLERS 指定要安装的 handler 列表（逗号分隔）
ARG MINDSDB_HANDLERS="elasticsearch,clickhouse,influxdb,mongodb,mssql"
ENV MINDSDB_HANDLERS=${MINDSDB_HANDLERS}
RUN python install_handlers.py || echo "部分 handler 安装失败，继续执行"
RUN pip install -r etl/requirements.txt
CMD ["tail -f /dev/null"]