FROM nginx/nginx-unprivileged:1.30.6-alpine3.24@sha256:44e74ca483234093081138b6d7b6f561d55557756a2deefc3a5056148defeb99
USER root
RUN apk upgrade --no-cache
COPY nginx.conf /etc/nginx/nginx.conf
COPY index.html /usr/share/nginx/html/index.html
ARG VCS_REF=development
LABEL org.opencontainers.image.revision=$VCS_REF
ARG ROLLOUT_DEMO=false
RUN if [ "$ROLLOUT_DEMO" = "true" ]; then sed -i 's/RAHBAR/RAHBAR Rollout Demo/g' /usr/share/nginx/html/index.html; fi
USER 101:101
EXPOSE 8080
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
