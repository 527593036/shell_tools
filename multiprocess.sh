#!/bin/bash
#
#Created on 2016年4月1日
#
#@author: zhujin
#

function multiprocess(){
    func=$1 #function or cmd
    ips=$2
    trap "exec 1000>&-;exec 1000<&-;exit 0" 2

    mkfifo testfifo
    exec 1000<>testfifo
    rm -rf testfifo

    for((n=1;n<=10;n++))
    do
        echo >&1000
    done

    start=`date +%s`
    for ip in ${ips}
    do
        read -u1000
        {
            echo "$ip: $(${func} ${ip})";sleep 1
            echo >&1000
        } &
    done

    wait

    end=`date +%s`
    echo "TIME: `expr $end - $start`"
    exec 1000>&-
    echo 1000<&-
}


function test(){
	echo "test"
}


ips="192.168.33.11 192.168.33.12"

multiprocess test ${ips}