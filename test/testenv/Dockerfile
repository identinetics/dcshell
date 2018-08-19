FROM alpine

RUN apk update \
 && apk add bash openssh outils-sha256 python3


ARG TIMEZONE='UTC'
COPY manifest2.sh /opt/bin/manifest2.sh
RUN chmod +x /opt/bin/manifest2.sh \
 && mkdir -p $HOME/.config/pip \
 && printf "[global]\ndisable-pip-version-check = True\n" > $HOME/.config/pip/pip.conf
