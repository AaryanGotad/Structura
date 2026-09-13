FROM alpine:3.21 AS assets

WORKDIR /site
COPY index.html script.js styles.css ./

FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=assets /site/ /usr/share/nginx/html/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]