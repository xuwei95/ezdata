supervisord -c supervisord.ini
python init_system.py
if [ $run_upgrade == 1 ]; then
  echo "检查升级版本"
  # 执行命令，检查升级版本
  pip install --upgrade ez-etl
  pip install --upgrade akshare
fi
if [ $run_web == 1 ]; then
  echo "开启web服务"
  # 执行命令，开启web服务
  supervisorctl start web_api
fi

if [ $run_scheduler == 1 ]; then
  echo "开启任务调度"
    supervisorctl start scheduler
fi

if [ $run_flower == 1 ]; then
  echo "开启flower"
  # 以守护进程启动
  supervisorctl start celery_flower
fi

if [ $run_worker == 1 ]; then
  echo "开启celery worker"
  supervisorctl start celery_worker
fi

tail -f /dev/null
