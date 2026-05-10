[Unit]
Description=OpenStream SOCKS5 proxy inside ${NS_NAME} on port ${PROXY_PORT}
Requires=opst-openvpn.service
After=opst-openvpn.service
BindsTo=opst-openvpn.service
PartOf=opst-openvpn.service

[Service]
Type=simple
ExecStart=/usr/sbin/ip netns exec ${NS_NAME} ${LIBEXEC_DIR}/opst-start-socks.sh
Restart=always
RestartSec=5
StartLimitIntervalSec=0

[Install]
WantedBy=multi-user.target
