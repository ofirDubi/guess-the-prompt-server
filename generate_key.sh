openssl genrsa -des3 -out gtp-server.key 2048
openssl req -new -key gtp-server.key -out gtp-server.csr

cp gtp-server.key gtp-server.key.org
openssl rsa -in gtp-server.key.org -out gtp-server.key
openssl x509 -req -days 365 -in gtp-server.csr -signkey gtp-server.key -out gtp-server.crt