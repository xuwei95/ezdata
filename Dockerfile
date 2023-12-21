FROM continuumio/miniconda3:23.3.1-0
ENV LANG C.UTF-8
ENV TZ=Asia/Shanghai
ENV DEBIAN_FRONTEND=noninteractive
RUN sed -i s@/archive.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list
RUN sed -i s@/security.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list
RUN apt-get clean
RUN apt-get update
RUN apt-get install tmux htop vim net-tools -y
RUN apt install -y tzdata \
    && ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/ezdata
ADD . /opt/ezdata
RUN cd /opt/ezdata
RUN pip install -r /opt/ezdata/requirements.txt -i https://pypi.doubanio.com/simple --use-deprecated=legacy-resolver
CMD ["tail -f /dev/null"]