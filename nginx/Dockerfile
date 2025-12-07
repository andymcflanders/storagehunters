FROM nginx:alpine

# Install openssl for certificate checking
RUN apk add --no-cache openssl

# Create directories
RUN mkdir -p /etc/nginx/certs /var/www/certbot

# Copy configuration
COPY nginx.conf /etc/nginx/nginx.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh

EXPOSE 80 443

ENTRYPOINT ["/docker-entrypoint.sh"]
