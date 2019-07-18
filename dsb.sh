#!/bin/bash

for i in "$@"
do
case $i in
    -u=*|--user=*)
    USER="${i#*=}"

    ;;
    -p=*|--pass=*)
    PASSWORD="${i#*=}"
    ;;
    *)
            # unknown option
    ;;
esac
done

# Default base64 on macOS doesn't have the -w option 
BASETEST=$(base64 --help | grep -E "\--wrap")
if [ "$BASETEST" ]
then
	BASEARG="-w 0"
else
	BASEARG=""
fi

LOGINPAGE=$(curl -X GET -H "User-Agent: Mozilla/5.0 " https://www.dsbmobile.de/Login.aspx) 
EV=$(echo "{$LOGINPAGE}" | grep -E id=\"__EVENTVALIDATION\"\ value=\"[^\"]+\" | cut -d'"' -f8)
VS=$(echo "{$LOGINPAGE}" | grep -E id=\"__VIEWSTATE\"\ value=\"[^\"]+\" | cut -d'"' -f8)

COOKIE=$(curl -I https://www.dsbmobile.de/Login.aspx | grep -E "Cookie:" | cut -f2 -d' ')
DSBCOOKIE=$(curl -X POST -H "User-Agent: Mozilla/5.0" -F "txtUser=${USER}" -F "txtPass=${PASSWORD}" -F "__VIEWSTATE=${VS}" -F "__EVENTVALIDATION=${EV}" -F 'ctl03=Anmelden' -H "Cookie: ${COOKIE}" https://www.dsbmobile.de/Login.aspx?ReturnUrl=%2fDefault.aspx -D - | grep -E "Cookie: DSB" | cut -f2 -d' ')
curl -XGET -H "Cookie: ${COOKIE} ${DSBCOOKIE}" -H 'User-Agent: Mozilla/5.0' 'https://www.dsbmobile.de/Default.aspx'
DSBDATA=$(echo '{"UserId":"","UserPw":"","Abos":[],"AppVersion":"2.3","Language":"de","OsVersion":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0","AppId":"","Device":"WebApp","PushId":"","BundleId":"de.heinekingmedia.inhouse.dsbmobile.web","Date":"2019-07-05T14:28:11.729Z","LastUpdate":"2019-07-05T14:28:11.729Z"}' | gzip -cf | base64 ${BASEARG})
curl -X POST -H "User-Agent: Mozilla/5.0" -H "Content-Type: application/json;charset=utf-8" -H "Cookie: ${COOKIE} ${DSBCOOKIE}" https://www.dsbmobile.de/JsonHandlerWeb.ashx/GetData --data "{\"req\":{\"Data\":\"${DSBDATA}\",\"DataType\":1}}" -H "Bundle_ID: de.heinekingmedia.inhouse.dsbmobile.web" -H "Referer: https://www.dsbmobile.de/" | cut -d'"' -f4 | base64 --decode | gzip -dc | jq '.ResultMenuItems[0].Childs[1].Root.Childs[] | select(.Title | index("Foyer")).Childs[0].Detail'
