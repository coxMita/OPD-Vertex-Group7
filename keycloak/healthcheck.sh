#!/bin/sh
exec 3<>/dev/tcp/localhost/8080
printf 'HEAD /realms/master HTTP/1.0\r\nHost: localhost\r\nConnection: close\r\n\r\n' >&3
cat <&3 | grep -q '200 OK' && exit 0 || exit 1
