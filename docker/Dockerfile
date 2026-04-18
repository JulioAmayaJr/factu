FROM odoo:18.0

USER root

RUN pip3 install --no-cache-dir --break-system-packages \
    "pyjwt>=2.0.0" \
    "xmltodict>=0.13.0" \
    "cryptography>=41.0.0" \
    || pip3 install --no-cache-dir "pyjwt>=2.0.0" "xmltodict>=0.13.0"

USER odoo
