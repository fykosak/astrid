cp -n /app/config.ini.sample /app/config/config.ini
cp -n /app/repos.ini.sample  /app/config/repos.ini

python3 -u ./main
