#!/bin/bash
#write by zhujin
#email: 527593036@qq.com
#视情况可自行添加mysql安装

filepath=$(cd "$(dirname "$0")"; pwd)

#基础包安装
apt-get install -y autoconf cmake libxml2-dev libfreetype6-dev git libmemcached-dev libmemcached11\
	zlib1g-dev curl libcurl3 libcurl3-dev libjpeg-dev libgcrypt-dev \
	libmcrypt-dev libncurses5-dev libpcre3-dev psmisc libpcre3  libssl-dev \
	libpng-dev libgd-dev libbz2-dev libmcrypt-dev mcrypt libmhash2 libmhash-dev \
	libicu-dev libltdl-dev libtool libmysqld-dev libaio-dev #build-essential


#iconv的安装
cd ${filepath}/
tar -zxf libiconv-1.14.tar.gz 
cd libiconv-1.14
./configure --prefix=/usr/local
cd srclib/
sed -ir -e '/gets is a security/d' ./stdio.in.h
cd ../
make -j4 
make install
echo "/usr/local/lib" >> /etc/ld.so.conf
ldconfig


#openssl模块
cd ${filepath}/
tar -zxf openssl-1.0.2h.tar.gz
cd openssl-1.0.2h
./config
make -j4


#pcre模块
cd ${filepath}/
tar -zxf pcre-8.38.tar.gz
cd pcre-8.38
./configure 
make -j4


#nginx
cd ${filepath}/
tar -zxf tengine-2.1.2.tar.gz
cd tengine-2.1.2
./configure --prefix=/app/nginx-2.1.2 --with-http_ssl_module \
	--with-http_dav_module --with-http_stub_status_module \
	--with-http_flv_module --with-http_gzip_static_module \
	--with-openssl=../openssl-1.0.2h --with-pcre=../pcre-8.38 \
	--with-http_spdy_module --with-http_v2_module
make -j4
make install
cd /app && ln -sf nginx-2.1.2 nginx


#ora驱动
cd ${filepath}/
dpkg -i oracle-instantclient11.2-basic_11.2.0.4.0-1_amd64.deb 
dpkg -i oracle-instantclient11.2-devel_11.2.0.4.0-1_amd64.deb
dpkg -i oracle-instantclient11.2-sqlplus_11.2.0.4.0-1_amd64.deb
export ORACLE_HOME=/usr/lib/oracle/11.2/client64
export PATH=$PATH:$ORACLE_HOME/bin
ln -s /usr/include/oracle/11.2/client64 $ORACLE_HOME/include


#php安装
cd ${filepath}/
tar -xf php-7.0.9.tar
cd php-7.0.9
./configure --prefix=/app/php-7.0.9 --enable-sockets --enable-soap --enable-zip \
	--enable-zend-signals --enable-mysqlnd --enable-opcache --enable-pcntl \
	--enable-embedded-mysqli --enable-mbstring --enable-intl --enable-exif \
	--enable-calendar --enable-bcmath --with-curl --with-openssl --enable-fpm \
	--with-fpm-user=nobody    --with-fpm-group=nobody --with-config-file-path=/etc/ \
	--with-config-file-scan-dir=/app/php/etc/conf.d --with-mcrypt --enable-re2c-cgoto \
	--disable-short-tags --enable-ftp --with-mysql --with-mysqli --with-pdo-mysql --with-kerberos \
	--with-zlib --with-gd --with-freetype-dir=/usr --enable-shmop --enable-sysvsem --with-mhash \
	--with-xmlrpc  --with-jpeg-dir  --with-png-dir --with-iconv=/usr/local  \
	--with-oci8=instantclient,/usr/lib/oracle/11.2/client64/lib --with-pdo-oci=instantclient,/usr,11.2
make -j4
make install
cd /app && ln -sf php-7.0.9 php


#php memcache扩展安装(php7不支持memcache,需要libmemecached+php-memecached扩展)
cd ${filepath}/
git clone https://github.com/php-memcached-dev/php-memcached
cd php-memcached
git checkout php7
git pull
/app/php/bin/phpize 
./configure --with-php-config=/app/php/bin/php-config  --disable-memcached-sasl
make -j4
make install


#php redis扩展安装
cd ${filepath}/
tar -zxf redis-3.0.0.tgz 
cd redis-3.0.0
/app/php/bin/phpize 
./configure --with-php-config=/app/php/bin/php-config
make -j4
make install


#php mongo扩展
cd ${filepath}/
tar -zxf mongodb-1.1.8.tgz 
cd mongodb-1.1.8/
/app/php/bin/phpize 
./configure --with-php-config=/app/php/bin/php-config
make -j4
make install


#php phalcon扩展
cd ${filepath}/
export PATH=$PATH:/app/php/bin
tar -zxf cphalcon.tar.gz
cd cphalcon/build
./install


#php amqp扩展安装
cd ${filepath}/
tar -zxf rabbitmq-c-0.8.0.tar.gz
cd rabbitmq-c-0.8.0/
mkdir build && cd build
cmake ..
cmake --build  .
make -j4
make install


cd ${filepath}/
tar -zxf amqp-1.7.1.tgz
cd amqp-1.7.1/
/app/php/bin/phpize
./configure --with-php-config=/app/php/bin/php-config --with-amqp
make -j4
make install

#新建nginx，php日志目录
mkdir -p /app/logs/{nginx,php}
mkdir /app/wwwroot
