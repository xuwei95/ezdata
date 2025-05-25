FROM continuumio/miniconda3:23.3.1-0
ADD install_full.sh /opt/install_full.sh
RUN /bin/bash -c "bash /opt/install_full.sh"
COPY nginx.conf /etc/nginx/nginx.conf
ENV TZ=Asia/Shanghai
ENV read_env=1
ENV ENV=deploy.env
ENV run_upgrade=1
ENV upgrade_packages=akshare,ccxt
ENV run_web=0
ENV web_worker=4
ENV run_scheduler=1
ENV run_flower=1
ENV run_worker=0
ENV worker_concurrency=4
ENV worker_queue=default
ENV worker_process=prefork
RUN git clone https://github.com/xuwei95/ezdata.git
WORKDIR /opt/ezdata/api
RUN cd /opt/ezdata/api
RUN pip install -r /opt/ezdata/requirements.txt -i https://pypi.doubanio.com/simple --use-deprecated=legacy-resolver
ENTRYPOINT ["bash", "init.sh"]