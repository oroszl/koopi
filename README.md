# Koopi userguide
Koopi intends to be a "poor man's [binder](http://mybinder.org)". At the moment it is a simple [`flask`](http://flask.pocoo.org/) script and uses jupyter's [`configurable-http-proxy`](https://github.com/jupyterhub/configurable-http-proxy)
In case of our demo service use  `KOOPI_URL=grail06.elet.hu` and `KOOPI_PORT=8000`.
### Build images
To build images from a github repository containing [jupyter](http://jupyter.org) notebooks and an optional `pip` installable  `requirements.txt`
call 

```c
http://KOOPI_URL:KOOPI_PORT/koopi/build?gitlink=GIT_CLONEABLE_LINK
```
for example
```c
http://KOOPI_URL:KOOPI_PORT/koopi/build?gitlink=https://github.com/icsabai/grnadesign.git
```
Use only **lowercase** letters ! The built image will be available for spawning with image name `koopi_image_GIT_REPO_NAME` that is in the above example we create `koopi_image_grnadesign`. The images are built on top of `jupyter/scipy-notebook` docker container.
### Spawn a container 
To spawn a container call
```c
http://KOOPI_URL:KOOPI_PORT/koopi/spawn?image=koopi_image_GIT_REPO_NAME
```
This will spawn a container based on the image `koopi_image_GIT_REPO_NAME`  if no image name is supplied `jupyter/scipy-notebook` based container is spawned.
The container name will be `koopi_user_at_CONTAINER_ID` where `CONTAINER_ID` is a random string unique to the container.
### List images currently available
To list images currently built visit 
```c
http://KOOPI_URL:KOOPI_PORT/koopi/list_images
```
Clicking an element of the list an appropriate container is spawned.
### List currently running containers
To list containers currently running visit 
```c
http://KOOPI_URL:KOOPI_PORT/koopi/list_container
```

### Remove running containers
To remove a container
```c
http://KOOPI_URL:KOOPI_PORT/koopi/remove?c_id=CONTAINER_ID
```



