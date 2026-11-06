FROM nginxinc/nginx-unprivileged:1.28.0-alpine
USER root
RUN apk upgrade --no-cache
COPY nginx.conf /etc/nginx/nginx.conf
COPY index.html /usr/share/nginx/html/index.html
USER 101:101
EXPOSE 8080
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
