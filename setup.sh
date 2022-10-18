#!/bin/sh

project_dir="$( cd "$( dirname "$0" )" && pwd )"

OUTFILE=/lib/systemd/system/homedashboard.service
EXECUTE="cd $project_dir && source venv/bin/activate && python app.py"
sudo out=$OUTFILE exec="$EXECUTE" sh -c 'cat << EOF > $out
[Unit]
Description=Home Dashboard Service
After=multi-user.target

[Service]
Type=idle
Restart=on-failure
User=root
ExecStart=/bin/bash -c "$exec"

[Install]
WantedBy=multi-user.target
EOF'

python_app=$project_dir"/app.py"

sudo chmod 644 /lib/systemd/system/homedashboard.service
sudo chmod 755 "$python_app"

sudo systemctl daemon-reload
sudo systemctl enable homedashboard.service
sudo systemctl start homedashboard.service
service_status=$(sudo systemctl status homedashboard.service)
echo "$service_status"
