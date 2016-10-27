#!/bin/bash
#write by zhujin

filepath=$(cd "$(dirname "$0")"; pwd);cd ${filepath}
CONSUL="${filepath}/../bin/consul"
DATADIR="${filepath}/../data"
CONFDIR="${filepath}/../conf"
LOGS="${filepath}/../logs/consul.log"

node_name=$HOSTNAME
ip=$(/sbin/ifconfig | grep eth0 -A1 | grep inet | awk '{print $2}'|sed 's/[a-zA-Z].*://g')

function start(){
     nohup ${CONSUL} agent -server -bootstrap-expect=3 \
	-data-dir=${DATADIR} -node=${node_name} \
	-bind=${ip} -config-dir=${CONFDIR} > ${LOGS} 2>&1 &
}


function stop(){
    ps -ef | grep consul | grep -v grep | awk '{print $2}' | xargs kill
}


function restart(){
    stop
    start
}


function monitor(){
    consul_pid=$(ps -ef | grep consul | grep -v grep | awk '{print $2}')
    if [ "X$consul_pid" != "X" ];then
	echo "consul is running!"
    else
        start
    fi    
}


case $1 in
    start) start;;
    stop) stop;;
    restart) restart;;
    monitor) monitor;;
    *) echo "Usage: $0 start|stop|restart|monitor"
esac
