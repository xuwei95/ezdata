sed -i 's/\r$//' init.sh
unlink /var/run/supervisor.sock
supervisord -c supervisord.ini
if [ $run_upgrade == 1 ]; then
  echo "检查升级版本"
  # 执行命令，检查升级版本
  # 按逗号切分字符串，遍历每个包名执行 pip install --upgrade 命令
  IFS=',' read -ra package_list <<< "$upgrade_packages"
  for package in "${package_list[@]}"; do
      # 移除首尾空格
      package=$(echo "$package" | awk '{$1=$1};1')
      # 执行 pip install --upgrade 命令
      pip install --upgrade "$package" -i https://pypi.doubanio.com/simple
  done
fi
python init_system.py
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
