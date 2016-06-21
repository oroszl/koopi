FROM ubuntu
USER root
RUN apt-get update
RUN apt-get install -y python3 python3-pip curl build-essential tmux vim 
RUN curl -sL https://deb.nodesource.com/setup_4.x |  bash -
RUN apt-get install -y nodejs
RUN npm install -g configurable-http-proxy
RUN pip3 install --upgrade pip
RUN pip3 install ipython requests flask webargs docker-py netifaces
#RUN useradd poorman
#USER poorman
ADD koopi /srv/koopi
WORKDIR /srv/koopi

CMD { configurable-http-proxy --log-level debug & python3 /srv/koopi/koopi.py; } 2>&1  


