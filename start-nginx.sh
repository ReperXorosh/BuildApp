#!/bin/sh
CERT="/etc/letsencrypt/live/stroykompleksjob.ru/fullchain.pem"
KEY="/etc/letsencrypt/live/stroykompleksjob.ru/privkey.pem"

if [ -f "$CERT" ] && [ -f "$KEY" ]; then
    echo "✅ Сертификаты найдены, включаем HTTPS"
    cp /etc/nginx/https.conf /etc/nginx/default.conf
else
    echo "⚠️ Сертификаты не найдены, запускаем только HTTP"
    cp /etc/nginx/http-only.conf /etc/nginx/default.conf
fi

exec nginx -g "daemon off;"
