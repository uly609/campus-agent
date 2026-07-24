git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
FROM nginx:1.27

# The verified Vite production bundle is committed so Compose stays runnable
# when external registries are unavailable. CI rebuilds it from Vue sources.
COPY frontend/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
