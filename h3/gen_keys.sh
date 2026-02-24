# WebTransport with serverCertificateHashes requires cert valid for <= 14 days
openssl ecparam -name prime256v1 -genkey -noout -out key.pem && openssl req -new -x509 -key key.pem -out cert.pem -days 14 -nodes -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost"


