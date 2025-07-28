FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

# -----------------------------------------------------------------------------
# Odoo paths
# These are abs paths inside the container, and used by the entrypoint script
# -----------------------------------------------------------------------------
ENV ODOO_SRC_DIR="/odoo"
ENV ODOO_E_DIR="/odoo-e"
ENV CUSTOM_MODULES_DIR="/custom-odoo"
ENV USER_BIN="/usr/local/bin"

ENV HOME="/home/odoo"
ENV VENV="${HOME}/.venv"
ENV DATA_DIR="${HOME}/.odoo-data"
ENV LOG_DIR="${HOME}/.logs"

# The sub-paths in $HOME that need directory ownership by odoo
ENV ODOO_OWNED_PATHS="${VENV} ${DATA_DIR}"

# Prepend venv, Odoo source, and USER_BIN to PATH
ENV PATH="${ODOO_SRC_DIR}:${USER_BIN}:${VENV}/bin:$PATH"

# -----------------------------------------------------------------------------
# System Dependencies
# -----------------------------------------------------------------------------
RUN apt update && apt install -y --no-install-recommends \
    ansifilter \
    build-essential \
    cython3 \
    dos2unix \
    expect \
    iputils-ping \
    gnupg2 \
    libcairo2-dev \
    libev-dev \
    libffi-dev \
    libldap2-dev \
    libnss3 \
    libpq-dev \
    libsasl2-dev \
    libssl-dev \
    net-tools \
    pkg-config \
    postgresql-client \
    procps \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    wget \
    xvfb \
    # Dependencies for wkhtmltopdf
    fontconfig \
    libjpeg-turbo8 \
    libssl3 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    xfonts-75dpi \
    xfonts-base \
    # Cleanup
    && apt clean && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf 0.12.6-1 with patched Qt (official release)
RUN wget -q https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb -O /tmp/wkhtmltox.deb \
    && dpkg -i /tmp/wkhtmltox.deb \
    && rm /tmp/wkhtmltox.deb

# Install Google Chrome (necessary for web tour tests)
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN apt update && apt install -y google-chrome-stable

# Create non-root user 'odoo'
RUN groupadd -r odoo && useradd -r -g odoo -d ${HOME} -s /bin/bash odoo
RUN mkdir -p ${ODOO_OWNED_PATHS}
RUN chown -R odoo:odoo ${ODOO_OWNED_PATHS} \
    && find ${ODOO_OWNED_PATHS} -type d -exec chmod 775 {} \; \
    && find ${ODOO_OWNED_PATHS} -type f -exec chmod 664 {} \; \
    && find ${ODOO_OWNED_PATHS} -type d -exec chmod g+s {} \;

# -----------------------------------------------------------------------------
# Copy Scripts
# -----------------------------------------------------------------------------
COPY --from=custom-modules .dev-tools/scripts/entrypoint.sh ${USER_BIN}/odoo
COPY --from=custom-modules .dev-tools/scripts/odoo-shell-exec.py ${USER_BIN}/odoo-shell-exec.py
COPY --from=custom-modules /requirements.txt /tmp/custom-requirements.txt
COPY --from=odoo-src /requirements.txt /tmp/odoo-requirements.txt
RUN dos2unix ${USER_BIN}/odoo && chmod +x ${USER_BIN}/odoo
RUN dos2unix ${USER_BIN}/odoo-shell-exec.py && chmod +x ${USER_BIN}/odoo-shell-exec.py

# -----------------------------------------------------------------------------
# Python Dependencies
# -----------------------------------------------------------------------------
RUN python3 -m venv $VENV
RUN $VENV/bin/pip install --upgrade pip setuptools wheel

RUN $VENV/bin/pip install \
    debugpy \
    ipdb \
    jingtrang \
    openupgradelib \
    pdfminer.six \
    phonenumbers \
    pytest-xvfb \
    rlpycairo \
    selenium \
    setuptools \
    watchdog \
    webdriver-manager \
    websocket-client \
    wheel

RUN $VENV/bin/pip install --no-cache-dir -r /tmp/odoo-requirements.txt
RUN $VENV/bin/pip install --no-cache-dir -r /tmp/custom-requirements.txt

# -----------------------------------------------------------------------------
# Container Startup
# -----------------------------------------------------------------------------
EXPOSE 8069 5678 4000-4100
WORKDIR ${HOME}

ENTRYPOINT ["bash", "-c", "${USER_BIN}/odoo"]
