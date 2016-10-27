#!/bin/bash

filepath=$(cd "$(dirname "$0")"; pwd);cd ${filepath}
source ${filepath}/mymail.sh
source /etc/rc.d/init.d/functions

PROCESS=redis-server
SERVICE=redis-server
REDIS=/app/redis/bin/redis-server
CONF=/etc/redis.conf

function start(){
	echo -n $"Starting redis-server daemon: "
	if [[ ! -z "$(pidofproc -p /var/run/redis.pid $PROCESS)" ]]; then
		RETVAL=$?
		echo -n "already running"
	else
		daemon --check $SERVICE $REDIS $CONF
	fi
	RETVAL=$?
    	echo
    	return $RETVAL
}

function stop(){
	echo -n $"Stopping redis-server daemon: "
	pid=$(pidof ${PROCESS})
	if [ "X$pid" != "X" ];then
		#kill -9 ${pid}
		killproc $PROCESS
		#echo -n "OK"
		RETVAL=?
	else
		echo -n "Daemon is not started"
		RETVAL=1
	fi				
	echo
}

function restart(){
	stop
	start
}

function monitor(){
	pid=$(pidof ${PROCESS})
	if [ "X$pid" != "X" ];then
		echo "${PROCESS} (pid ${pid}) is running!"
	else
		start
		msg="`ps -ef | grep "${PROCESS}" | grep -v grep`"
		h=$(cat /app/readme/HostName.md | grep HOSTNAME | awk -F\= '{print $2}')
		subject="[告警]REDIS进程不存在,自动拉起 from ${h}"
		redis_sendmail "${msg}" "${subject}"
	fi	
}

case $1 in
        start) start;;
        stop) stop;;
		restart) restart;;
        monitor) monitor;;
        *) echo "Usage:./rds.sh start|stop|restart|monitor"
esac
