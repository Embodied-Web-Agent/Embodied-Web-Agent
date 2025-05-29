mkdir -p wiki
wget http://metis.lti.cs.cmu.edu/webarena-images/wikipedia_en_all_maxi_2022-05.zim

cd home
npm install

cd recipe
npm install

cd shopping
npm install

cd openstreetmap-website
cp config/example.storage.yml config/storage.yml
cp config/docker.database.yml config/database.yml
touch config/settings.local.yml
docker compose build
docker compose up -d
docker compose run --rm web bundle exec rails db:migrate
wget https://download.geofabrik.de/north-america/us/new-york-latest.osm.pbf
docker compose run --rm web osmosis \
    -verbose    \
    --read-pbf new-york-latest.osm.pbf \
    --log-progress \
    --write-apidb \
        host="db" \
        database="openstreetmap" \
        user="openstreetmap" \
        validateSchemaVersion="no"