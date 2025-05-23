FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system packages then clean up to minimize image size
RUN apt-get update \
 && apt-get install --no-install-recommends -y \
      build-essential \
      curl \
      default-jre-headless \
      file \
      gpg-agent \
      libarchive-dev \
      libffi-dev \
      libgd-dev \
      libpq-dev \
      libsasl2-dev \
      libvips-dev \
      libxml2-dev \
      libxslt1-dev \
      locales \
      postgresql-client \
      ruby3.0 \
      ruby3.0-dev \
      software-properties-common \
      tzdata \
      unzip \
 && curl https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - \
 && add-apt-repository -y -U https://deb.nodesource.com/node_18.x \
 && apt-get install --no-install-recommends -y \
      nodejs \
 && npm install --global yarn \
 && add-apt-repository -y ppa:mozillateam/ppa \
 && echo "Package: *\nPin: release o=LP-PPA-mozillateam\nPin-Priority: 1001" > /etc/apt/preferences.d/mozilla-firefox \
 && apt-get install --no-install-recommends -y \
      firefox-geckodriver \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Install compatible Osmosis to help users import sample data in a new instance
RUN curl -OL https://github.com/openstreetmap/osmosis/releases/download/0.47.2/osmosis-0.47.2.tgz \
 && tar -C /usr/local -xzf osmosis-0.47.2.tgz

ENV DEBIAN_FRONTEND=dialog

# Setup app location
RUN mkdir -p /app
WORKDIR /app

# Install Ruby packages
ADD Gemfile Gemfile.lock /app/
RUN gem install bundler \
 && bundle install

# Install NodeJS packages using yarn
ADD package.json yarn.lock /app/
ADD bin/yarn /app/bin/
RUN bundle exec bin/yarn install
