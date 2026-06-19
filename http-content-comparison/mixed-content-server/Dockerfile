FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache openssl

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY server.js index_http.html index_https.html empty_http.html empty_https.html ./
COPY static ./static

RUN openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem \
    -days 365 -subj "/CN=mixed-content.test" \
    -addext "subjectAltName=DNS:mixed-content.test"

EXPOSE 80 443

CMD ["node", "server.js"]
