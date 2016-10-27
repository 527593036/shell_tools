#!/bin/bash

filepath=$(cd "$(dirname "$0")"; pwd);cd ${filepath}
source ${filepath}/mymail.sh
source /etc/rc.d/init.d/functions

port=11215
PROCESS=memcached
SERVICE=memcached
MEMCACHED=/app/memcache/bin/memcached
MEMCACHED_ARGS="-m 8192 -u root -p ${port} -P /tmp/memcached.pid"

function start(){
	echo -n $"Starting memcached daemon: "
	if [[ ! -z "$(pidofproc -p /tmp/$SERVICE.pid $PROCESS)" ]]; then
		RETVAL=$?
		echo -n "already running"
	else
		daemon --check $SERVICE $MEMCACHED -d $MEMCACHED_ARGS
		#/app/memcache/bin/memcached -d -m 8192 -u root -p ${port} -P /tmp/memcached.pid
	fi
	RETVAL=$?
    	echo
    	return $RETVAL
}

function stop(){
	echo -n $"Stopping memcache daemon: "
	pid=$(pidof memcached)
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
	pid=$(pidof memcached)
	if [ "X$pid" != "X" ];then
		echo "memcached (pid ${pid}) is running!"
	else
		start
		msg="`ps -ef | grep memcached | grep -v grep`"
		h=$(cat /app/readme/HostName.md | grep HOSTNAME | awk -F\= '{print $2}')
		subject="[告警]memcached进程不存在,自动拉起 from ${h}"
		memcached_sendmail "${msg}" "${subject}"
	fi	
}

case $1 in
        start) start;;
        stop) stop;;
		restart) restart;;
        monitor) monitor;;
        *) echo "Usage:./memcache.sh start|stop|restart|monitor"
esac
