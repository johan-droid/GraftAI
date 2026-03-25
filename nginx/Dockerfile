FROM nginx:stable-alpine

# Set main configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Clean default configuration if present
RUN rm -f /etc/nginx/conf.d/default.conf

# Log to stdout for Docker logging
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
