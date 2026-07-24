FROM nginx:1.27

# The verified Vite production bundle is committed so Compose stays runnable
# when external registries are unavailable. CI rebuilds it from Vue sources.
COPY frontend/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
