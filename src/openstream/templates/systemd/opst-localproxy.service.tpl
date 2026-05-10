[Unit]
Description=Expose OpenStream SOCKS5 proxy on selected host bind IP:${PROXY_PORT}
Requires=opst-socks.service
After=opst-socks.service
BindsTo=opst-socks.service
PartOf=opst-socks.service

[Service]
Type=simple
ExecStart=${LIBEXEC_DIR}/opst-start-localproxy.sh
Restart=always
RestartSec=5
StartLimitIntervalSec=0

[Install]
WantedBy=multi-user.target
