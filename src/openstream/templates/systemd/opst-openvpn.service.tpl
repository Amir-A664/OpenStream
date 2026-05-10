[Unit]
Description=OpenStream OpenVPN client inside ${NS_NAME}
Requires=opst-setup.service
After=opst-setup.service
BindsTo=opst-setup.service

[Service]
Type=simple
ExecStart=/usr/sbin/ip netns exec ${NS_NAME} /usr/sbin/openvpn --config ${CURRENT_OVPN} --verb 3
Restart=always
RestartSec=5
StartLimitIntervalSec=0

[Install]
WantedBy=multi-user.target
