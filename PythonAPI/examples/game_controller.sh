#!/bin/bash 
echo "Controller Started" 
sudo xboxdrv --silent &
sleep 5
echo "Controller Mapped" 
antimicro --hidden --no-tray
