@echo off
echo Starting API polling script...
cd /q:/testpython/fromwork
start "Picking API Service" /min cmd /c python picking_request.py
echo Script is now running in a minimized window.