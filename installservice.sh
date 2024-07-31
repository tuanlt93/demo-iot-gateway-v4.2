echo "Copy file to systemd"
sudo cp gateway.service /etc/systemd/system/
sudo chmod +x  /etc/systemd/system/gateway.service
echo "Daemon reload"
sudo systemctl daemon-reload
sudo systemctl start gateway.service
sudo systemctl enable gateway.service
echo "Finish adding service"
sudo systemctl status gateway.service