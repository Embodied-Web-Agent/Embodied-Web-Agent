cd home
screen -L -dmS web_home npm start

cd recipe
screen -L -dmS recipe-web npm start

cd shopping
screen -L -dmS shopping npm start

cd wiki
docker start kiwix33

cd openstreetmap-website
docker compose down
docker volume rm openstreetmap-website_db-data
docker compose up -d
docker compose run --rm web bundle exec rails db:migrate
docker compose run --rm web osmosis \
    -verbose    \
    --read-pbf new-york-latest.osm.pbf \
    --log-progress \
    --write-apidb \
        host="db" \
        database="openstreetmap" \
        user="openstreetmap" \
        validateSchemaVersion="no"