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
    && rm -rf /var/lib/apt/lists/* \
RUN git clone https://github.com/xuwei95/ezdata.git
WORKDIR /opt/ezdata
RUN cd /opt/ezdata
RUN pip install -r /opt/ezdata/requirements.txt -i https://pypi.doubanio.com/simple --use-deprecated=legacy-resolver
RUN pip install -r /opt/ezdata/exetl/requirements.txt -i https://pypi.doubanio.com/simple --use-deprecated=legacy-resolver
CMD ["tail -f /dev/null"]