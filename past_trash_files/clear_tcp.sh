#!/bin/sh
# obtain pid with tcp port number =5555
id=$(lsof -t -i :5555 -s TCP:LISTEN)
echo "ID=${id}"
#kill the process with the pid
if [ -z "${id}"];
then echo "id is NULL";
else kill -9 "${id}";
fi

