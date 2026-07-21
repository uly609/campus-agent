FROM ubuntu:22.04

ARG ALERTMANAGER_VERSION=0.27.0
ARG TARGETARCH
COPY infra/alertmanager/bin/alertmanager-${ALERTMANAGER_VERSION}.linux-${TARGETARCH}.tar.gz /tmp/alertmanager.tar.gz
RUN tar -xzf /tmp/alertmanager.tar.gz -C /tmp \
  && cp /tmp/alertmanager-${ALERTMANAGER_VERSION}.linux-${TARGETARCH}/alertmanager /usr/local/bin/alertmanager \
  && cp /tmp/alertmanager-${ALERTMANAGER_VERSION}.linux-${TARGETARCH}/amtool /usr/local/bin/amtool \
  && rm -rf /tmp/alertmanager*
COPY infra/alertmanager/alertmanager.yml /etc/alertmanager/alertmanager.yml

EXPOSE 9093
CMD ["alertmanager", "--config.file=/etc/alertmanager/alertmanager.yml", "--storage.path=/tmp/alertmanager"]
