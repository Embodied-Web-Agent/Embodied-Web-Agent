cd home
screen -L -dmS web_home npm start

cd recipe
screen -L -dmS recipe-web npm start

cd shopping
screen -L -dmS shopping npm start

cd wiki
docker start kiwix33

cd openstreetmap-website
docker compose up -d