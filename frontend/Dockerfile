FROM nginx:1.27-alpine
COPY index.html overlay.html app.js overlay.js styles.css /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
