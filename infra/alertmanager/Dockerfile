FROM quay.io/prometheus/alertmanager:v0.27.0

COPY infra/alertmanager/alertmanager.yml /etc/alertmanager/alertmanager.yml

EXPOSE 9093
ENTRYPOINT ["/bin/alertmanager"]
CMD ["--config.file=/etc/alertmanager/alertmanager.yml", "--storage.path=/alertmanager"]
