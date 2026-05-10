[Unit]
Description=Prepare OpenStream network namespace
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=${LIBEXEC_DIR}/opst-netns.sh up
ExecStop=${LIBEXEC_DIR}/opst-netns.sh down

[Install]
WantedBy=multi-user.target
