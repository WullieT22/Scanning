@echo off
echo Finding your network IP address...
ipconfig | findstr /i "IPv4"
echo.

cd /q:/testpython/fromwork

echo Starting server on all network interfaces using port 5500...
echo.
echo Local access: http://localhost:5500/index.html
echo Network access: http://172.11.0.4:5500/index.html
echo.
echo Clients should use your network IP to connect.
echo.
echo Press Ctrl+C to stop the server when done.

python -m http.server 5500 --bind 0.0.0.0