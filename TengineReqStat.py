#!/usr/bin/env python
#-*-coding: utf-8-*-
'''
Created on 2016年7月7日

@author: zhujin
'''

'''
1、需要安装tengine

2、reqstat模块文档说明http://tengine.taobao.org/document_cn/http_reqstat_cn.html

3、某reqstat测试结果：
ansible.api.xz.com,192.168.33.11:80,164,456,2,2,2,0,0,0,0,12,2,12,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
192.168.33.11,192.168.33.11:23456,7317,6482,6,20,18,0,2,0,0,0,0,0,0,18,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0

4、todo
修正新增域名监控，跳出异常的逻辑bug
'''

import argparse
import httplib2
import shutil
import time
import json
import logging

import sys
import os
PATH = os.path.split(os.path.realpath(__file__))[0]

ENDPOINT = os.environ['PS1_HOSTNAME']    
    
def mylogger(logtag, logfile):
    # 创建一个logger
    logger = logging.getLogger(logtag)
    logger.setLevel(logging.DEBUG)

    # 创建一个handler，用于写入日志文件
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)

    # 再创建一个handler，用于输出到控制台
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.DEBUG)

    # 定义handler的输出格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    # ch.setFormatter(formatter)

    # 给logger添加handler
    logger.addHandler(fh)
    # logger.addHandler(ch)

    return logger
    
    
logger = mylogger("TENGINE STATUS", PATH+'/../logs/nginx_status.log')
            

def http_api(api,method='GET',metrics=None):
    ret = []
    http = httplib2.Http()
    logger = mylogger("NGINX STATUS", PATH+'/../logs/nginx_status.log')
    req_body = json.dumps(metrics)
    logger.info(req_body)
    try:
        if method == 'GET':
            response, content = http.request(api,'GET')
            content = content.split('\n')
            ret = [response,content]
        elif method == 'POST':
            response, content = http.request(api,'POST',body=req_body, headers={'Content-Type': 'application/json'})
            ret = [response,content]
        logger.info(ret)
        return ret
    except httplib2.HttpLib2Error, e:
        logger.info(e)
        raise e
        
        
class TengineReqStat(object):
    def __init__(self,req_stat_url,domain_list):
        self.req_stat_url = req_stat_url
        self.req_stat_ret = self._req_stat_ret()
        self.domain_list = domain_list
        self.ts = int(time.time())
        
    def _req_stat_ret(self):
        ret = http_api(self.req_stat_url)[1]
        req_stat = []
        for line in ret:
            line = line.split(',')
            req_stat.append(line)
        return req_stat
        
    def bindwith(self):
        '''
        流量维度
        stat[2] = bytes_in,stat[3] = bytes_out
        bytes_in 从客户端接收流量总和,bytes_out 发送到客户端流量总和
        换算成Kbit/s
        '''
        bindwith_fp = PATH+'/../logs/bindwith.nginx.monitor'
        bindwith_fp_tmp = PATH+'/../logs/bindwith.nginx.tmp'
            
        fp1 = open(bindwith_fp_tmp,'a')
        
        # 当前请求的结果
        ret1 = {}
        for stat in self.req_stat_ret:
            if stat[0] in self.domain_list:
                fp1.write(stat[0]+','+stat[1]+','+stat[2]+','+stat[3]+'\n')
                ret1[stat[0]] = [stat[1],stat[2],stat[3]]
        fp1.close()
        
        #如果是第一次请求
        if not shutil.os.path.isfile(bindwith_fp):
            shutil.copy(bindwith_fp_tmp,bindwith_fp)
            
        # 上一次请求的结果  
        fp = open(bindwith_fp,'r')      
        ret2 = {}
        for line in fp:
            line = line.strip().split(',')
            ret2[line[0]] = [line[1],line[2],line[3]]
        fp.close()
        
        #按域名获取带宽的metrics,合成列表格式(包含字典)
        ret = []
        for domain in self.domain_list:
            bindwith_in = int(float(int(ret1[domain][1]) - int(ret2[domain][1]))/1024*8)
            bindwith_out = int(float(int(ret1[domain][2]) - int(ret2[domain][2]))/1024*8)
            endpoint = ENDPOINT + '_' + ret1[domain][0].split(':')[1]
            
            bind_with_in_metric = {
                'endpoint': endpoint,
                'metric': 'Kbit_in',
                'timestamp': self.ts,
                'step': 60,
                'value': bindwith_in,
                'counterType': 'GAUGE',
                'tags': 'domain=%s' % domain
            }
            ret.append(bind_with_in_metric)
            
            bind_with_out_metric = {
                'endpoint': endpoint,
                'metric': 'Kbit_out',
                'timestamp': self.ts,
                'step': 60,
                'value': bindwith_out,
                'counterType': 'GAUGE',
                'tags': 'domain=%s' % domain
            }
            
            ret.append(bind_with_out_metric)
            
        shutil.os.remove(bindwith_fp)
        shutil.move(bindwith_fp_tmp,bindwith_fp)
        logger.info(ret)
        return ret
        
    def conn_total(self):
        '''
        并发连接数维度
        stat[0]=host,stat[1]=ip:port,stat[4]=conn_total
        conn_total 处理过的连接总数
        '''
        conn_total_fp = PATH+'/../logs/conn_total.nginx.monitor'
        conn_total_fp_tmp = PATH+'/../logs/conn_total.nginx.tmp'
            
        fp1 = open(conn_total_fp_tmp,'a')
        
        # 当前请求的结果
        ret1 = {}
        for stat in self.req_stat_ret:
            if stat[0] in self.domain_list:
                fp1.write(stat[0]+','+stat[1]+','+stat[4]+'\n')
                ret1[stat[0]] = [stat[1],stat[4]]
        fp1.close()
        
        #如果是第一次请求
        if not shutil.os.path.isfile(conn_total_fp):
            shutil.copy(conn_total_fp_tmp,conn_total_fp)
            
        # 上一次请求的结果        
        fp = open(conn_total_fp,'r')
        ret2 = {}
        for line in fp:
            line = line.strip().split(',')
            ret2[line[0]] = [line[1],line[2]]
        fp.close()
        
        #按域名获取总连接数的metrics,合成列表格式(包含字典)
        ret = []
        for domain in self.domain_list:
            endpoint = ENDPOINT + '_' + ret1[domain][0].split(':')[1]
            conn_total = int(ret1[domain][1]) - int(ret2[domain][1])
            conn_total_metric = {
                'endpoint': endpoint,
                'metric': 'conn',
                'timestamp': self.ts,
                'step': 60,
                'value': conn_total,
                'counterType': 'GAUGE',
                'tags': 'domain=%s' % domain
            }
            
            ret.append(conn_total_metric)
            
        shutil.os.remove(conn_total_fp)
        shutil.move(conn_total_fp_tmp,conn_total_fp)
        logger.info(ret)
        return ret
        
    def http_code(self):
        '''
        stat[0]=host,stat[1]=ip:port,stat[5]=req_total
        stat[6]=http_2xx,stat[7]=http_3xx,stat[8]=http_4xx
        stat[9]=http_5xx,stat[10]=httpotherstatus
        req_total 处理过的总请求数
        http_2xx 2xx请求的总数
        http_3xx 3xx请求的总数
        http_4xx 4xx请求的总数
        http_5xx 5xx请求的总数
        httpotherstatus 其他请求的总数
        '''
        http_code_fp = PATH+'/../logs/http_code.nginx.monitor'
        http_code_fp_tmp = PATH+'/../logs/http_code.nginx.tmp'
            
        fp1 = open(http_code_fp_tmp,'a')
        
        # 当前请求的结果
        ret1 = {}
        for stat in self.req_stat_ret:
            if stat[0] in self.domain_list:
                fp1.write(stat[0]+','+stat[1]+','+stat[5]+','+stat[6]+','+stat[7]+','+stat[8]+','+stat[9]+','+stat[10]+'\n')
                ret1[stat[0]] = [stat[1],stat[5],stat[6],stat[7],stat[8],stat[9],stat[10]]
        fp1.close()
        
        #如果是第一次请求
        if not shutil.os.path.isfile(http_code_fp):
            shutil.copy(http_code_fp_tmp,http_code_fp)
            
        #上一次请求的结果        
        fp = open(http_code_fp,'r')
        ret2 = {}
        for line in fp:
            line = line.strip().split(',')
            ret2[line[0]] = [line[1],line[2],line[3],line[4],line[5],line[6],line[7]]
        fp.close()
        
        #按域名获取请求数的metrics,合成列表格式(包含字典)
        ret = []
        for domain in self.domain_list:
            req_total = int(ret1[domain][1]) - int(ret2[domain][1])
            http_2xx = int(ret1[domain][2]) - int(ret2[domain][2])
            http_3xx = int(ret1[domain][3]) - int(ret2[domain][3])
            http_4xx = int(ret1[domain][4]) - int(ret2[domain][4])
            http_5xx = int(ret1[domain][5]) - int(ret2[domain][5])
            http_other = int(ret1[domain][6]) - int(ret2[domain][6])
            endpoint = ENDPOINT + '_' + ret1[domain][0].split(':')[1]
            
            req_total_metric = {
               'endpoint': endpoint,
               'metric': 'req_total',
               'timestamp': self.ts,
               'step': 60,
               'value': req_total,
               'counterType': 'GAUGE',
               'tags': 'domain=%s' % domain 
            }
            ret.append(req_total_metric)
            
            http_2xx_metric = {
                'endpoint': endpoint,
                'metric': 'http_2xx',
                'timestamp': self.ts,
                'step': 60,
                'value': http_2xx,
                'counterType': 'GAUGE',
                'tags': 'domain=%s' % domain
            }
            ret.append(http_2xx_metric)
            
            http_3xx_metric = {
                'endpoint': endpoint,
                'metric': 'http_3xx',
                'timestamp': self.ts,
                'step': 60,
                'value': http_3xx,
                'counterType': 'GAUGE',
                'tags': 'domain=%s' % domain
            }
            ret.append(http_3xx_metric)
            
            http_4xx_metric = {
                'endpoint': endpoint,
                'metric': 'http_4xx',
                'timestamp': self.ts,
                'step': 60,
                'value': http_4xx,
                'counterType': 'GAUGE',
                'tags': 'domain=%s' % domain
            }
            ret.append(http_4xx_metric)
            
            http_5xx_metric = {
                'endpoint': endpoint,
                'metric': 'http_5xx',
                'timestamp': self.ts,
                'step': 60,
                'value': http_5xx,
                'counterType': 'GAUGE',
                'tags': 'domain=%s' % domain
            }
            ret.append(http_5xx_metric)
            
            httpotherstatus_metric = {
                'endpoint': endpoint,
                'metric': 'http_other_status',
                'timestamp': self.ts,
                'step': 60,
                'value': http_other,
                'counterType': 'GAUGE',
                'tags': 'domain=%s' % domain
            }
            ret.append(httpotherstatus_metric)
            
        shutil.os.remove(http_code_fp)
        shutil.move(http_code_fp_tmp,http_code_fp)
        logger.info(ret)
        return ret
        
    # req的平均时间维度
    def req_time(self):
        '''
        stat[0]=host,stat[1]=ip:port,stat[5]=req_total
        stat[11]=rt,stat[12]=ups_req,stat[13]=ups_rt
        stat[11]/stat[5]:总时间平均
        req_total 处理过的总请求数
        rt rt的总数,是请求的响应时间总和
        ups_req 需要访问upstream的请求总数    
        ups_rt 访问upstream的总rt,是后端的响应时间总和
        单位ms
        '''
        req_time_fp = PATH+'/../logs/req_time.nginx.monitor'
        req_time_fp_tmp = PATH+'/../logs/req_time.nginx.tmp'
            
        fp1 = open(req_time_fp_tmp,'a')
        
        # 当前请求的结果
        ret1 = {}
        for stat in self.req_stat_ret:
            if stat[0] in self.domain_list:
                fp1.write(stat[0]+','+stat[1]+','+stat[5]+','+stat[11]+','+stat[12]+','+stat[13]+'\n')
                ret1[stat[0]] = [stat[1],stat[5],stat[11],stat[12],stat[13]]
        fp1.close()
        
        #如果是第一次请求
        if not shutil.os.path.isfile(req_time_fp):
            shutil.copy(req_time_fp_tmp,req_time_fp)
                
        # 上一次请求的结果  
        fp = open(req_time_fp,'r')     
        ret2 = {}
        for line in fp:
            line = line.strip().split(',')
            ret2[line[0]] = [line[1],line[2],line[3],line[4],line[5]]
        fp.close()
        
        # 平均时间消耗计算
        ret = []
        for domain in self.domain_list:
            cur_req_time = int(ret1[domain][2])-int(ret2[domain][2])
            cur_req_count = int(ret1[domain][1])-int(ret2[domain][1])
            cur_ups_req_time = int(ret1[domain][4])-int(ret2[domain][4])
            cur_ups_req_count = int(ret1[domain][3])-int(ret2[domain][3])
            # 总平均耗时
            cur_req_avg_time = round(float(cur_req_time)/cur_req_count,1) if cur_req_count else 0
            # upstream总平均耗时
            cur_ups_req_avg_time = round(float(cur_ups_req_time)/cur_ups_req_count,1) if cur_ups_req_count else 0
            endpoint = ENDPOINT + '_'+ ret1[domain][0].split(':')[1]
                
            req_rt = {
                'endpoint': endpoint,
                'metric': 'req_rt',
                'timestamp': self.ts,
                'step': 60,
                'value': cur_req_avg_time,
                'counterType': 'GAUGE',
                'tags': 'domain=%s' % domain
            }
            ret.append(req_rt)
                
            ups_rt = {
                'endpoint': endpoint,
                'metric': 'ups_rt',
                'timestamp': self.ts,
                'step': 60,
                'value': cur_ups_req_avg_time,
                'counterType': 'GAUGE',
                'tags': 'domain=%s' % domain
            }
            ret.append(ups_rt)
            
        shutil.os.remove(req_time_fp)
        shutil.move(req_time_fp_tmp,req_time_fp)
        logger.info(ret)
        return ret
        
    def ups_req(self):
        '''
        upstream维度
        ups_req 需要访问upstream的请求总数 
        httpups4xx upstream返回4xx响应的请求总数
        httpups5xx upstream返回5xx响应的请求总数
        '''
        ups_req_fp = PATH+'/../logs/ups_req.nginx.monitor'
        ups_req_fp_tmp = PATH+'/../logs/ups_req.nginx.tmp'
            
        fp1 = open(ups_req_fp_tmp,'a')
        
        # 当前请求的结果
        ret1 = {}
        for stat in self.req_stat_ret:
            if stat[0] in self.domain_list:
                fp1.write(stat[0]+','+stat[1]+','+stat[12]+','+stat[29]+','+stat[30]+'\n')
                ret1[stat[0]] = [stat[1],stat[12],stat[29],stat[30]]
        fp1.close()
        
        #如果是第一次请求
        if not shutil.os.path.isfile(ups_req_fp):
            shutil.copy(ups_req_fp_tmp,ups_req_fp)
                
        # 上一次请求的结果  
        fp = open(ups_req_fp,'r')     
        ret2 = {}
        for line in fp:
            line = line.strip().split(',')
            ret2[line[0]] = [line[1],line[2],line[3],line[4]]
        fp.close()
        
        #按域名获取ups请求数的metrics,合成列表格式(包含字典)
        ret = []
        for domain in self.domain_list:
            ups_req = int(ret1[domain][1]) - int(ret2[domain][1])
            ups_http_4xx = int(ret1[domain][2]) - int(ret2[domain][2])
            ups_http_5xx = int(ret1[domain][3]) - int(ret2[domain][3])
            endpoint = ENDPOINT + '_' + ret1[domain][0].split(':')[1]
            
            ups_req_metric = {
                'endpoint': endpoint,
                'metric': 'ups_req',
                'timestamp': self.ts,
                'step': 60,
                'value': ups_req,
                'counterType': 'GAUGE',
                'tags': 'domain=%s' % domain
            }
            ret.append(ups_req_metric)
            
            ups_http_4xx_metric = {
                'endpoint': endpoint,
                'metric': 'ups_http_4xx',
                'timestamp': self.ts,
                'step': 60,
                'value': ups_http_4xx,
                'counterType': 'GAUGE',
                'tags': 'domain=%s' % domain
            }
            ret.append(ups_http_4xx_metric)
            
            http_ups_5xx_metric = {
                'endpoint': endpoint,
                'metric': 'ups_http_5xx',
                'timestamp': self.ts,
                'step': 60,
                'value': ups_http_5xx,
                'counterType': 'GAUGE',
                'tags': 'domain=%s' % domain
            }
            ret.append(http_ups_5xx_metric)
            
        shutil.os.remove(ups_req_fp)
        shutil.move(ups_req_fp_tmp,ups_req_fp)
        logger.info(ret)
        return ret
    

def main():
    #ret_stat_url = 'http://127.0.0.1:2000/req.status'
    #open_falcon_api = 'http://127.0.0.1:1988/v1/push'
    parser = argparse.ArgumentParser()
    parser.add_argument('-domains', action="store", dest='domains', help='domains: www.test.com,www.test1.com')
    parser.add_argument('-req_stats_api', action="store", dest='req_stats_api', help='req_stats_api: http://127.0.0.1:2000/req.status')
    parser.add_argument('-open_falcon_api', action="store", dest='open_falcon_api', help='open_falcon_api: http://127.0.0.1:1988/v1/push')
    
    args = parser.parse_args()
    
    domains = args.domains
    domain_list = domains.split(',')
    req_stats_api = args.req_stats_api
    open_falcon_api = args.open_falcon_api
    
    ng_req_stat = TengineReqStat(req_stats_api,domain_list)
    mymetrics = ng_req_stat.bindwith() + ng_req_stat.conn_total() + ng_req_stat.http_code() + ng_req_stat.req_time() + ng_req_stat.ups_req()
    print(mymetrics)
    print(http_api(open_falcon_api,method='POST',metrics=mymetrics))
    

if __name__ == '__main__':
    main()
