import sys,getopt,json,docker,socket,string,random,netifaces,os
import requests as req
from flask import Flask,redirect,request,Response
from webargs.flaskparser import use_args, parser
from webargs.flaskparser import FlaskParser as FL
from webargs import fields
from time import sleep
from io import BytesIO

# standard ports of the configurabel-http-proxy
proxy_port=8000 
proxy_api_port=8001
# internal docker network name common to "poor man's binder" 
# and all spawn containers
network_name=os.environ.get('DOCKER_NETWORK_NAME','bridge')
# docker client specifications
docli=docker.Client(base_url='unix:///var/run/docker.sock')
# the ip of the container we run "poor man's binder" in
ownip=netifaces.ifaddresses('eth0')[2][0]['addr']
# the ip or net addr where the service 
# will be visible from the outside
# ownip only works for local testing!!!
external_service_ip=os.environ.get('EXT_SERV_IP',ownip)
# service specific nameing strings
service_prefix='/koopi'
container_prefix='koopi_user_at_'
image_prefix='koopi_image_'

def spawn_container(args):
    """
    Simple function to spawn a container from an image.
    The container is connected to the same docker network
    as "poor man's binder" is.
    It is assumed that start-notebook.sh exists and
    can be run in the image as it will be our entry point.
    """
    # creating the container
    docli=args['docli']
    container_name=container_prefix+args['c_id']

    removelink='http://'+external_service_ip+       \
             ':'+str(proxy_port)+service_prefix+  \
             '/remove?c_id='+args['c_id']
    container = docli.create_container(
    image=args['image'],
    detach=True,
    name=container_name,
    command='python3 koopi_singleuser.py --KoopiUserNotebookApp.remove_url="'+\
            removelink+\
            '" --NotebookApp.base_url=/'+args['c_id']
    )

    # starting the container and connecting it to the 
    # appropriate docker network
    docli.start(container)
    docli.disconnect_container_from_network(container_name,'bridge')
    docli.connect_container_to_network(container_name,network_name)

    return container

parser = FL()
app = Flask(__name__,static_url_path='')

   
@app.route(service_prefix+'/spawn',methods=['get'])
def spawn():
    """
    Spawn container from an image and bind it to the proxy. 
    """
    # conatiner id as seen from the proxy
    c_id=''.join(random.choice(string.ascii_lowercase + string.digits) \
                 for x in range(9))

    # determine the image to be run   
    image=request.args.get('image','jupyter/scipy-notebook')

    args={ 'image': image,
           'docli': docli,
            'c_id': c_id  }

    # execute launch function
    result = spawn_container(args)
    # configureing proxy and figuring out redirect address
    proxy_rule_addr='http://0.0.0.0:'+    \
                    str(proxy_api_port)+  \
                    '/api/routes/'+       \
                    args['c_id']

    req.post(proxy_rule_addr,
             json={'target':'http://'+container_prefix+c_id+':8888'})
    # figure out redirect address
    redir_addr='http://'+               \
               external_service_ip+':'+ \
               str(proxy_port)+         \
               '/'+args['c_id']
    # we wait for 3 sec for the container to be up and running
    sleep(3)  
    # we return by redirecting the browser to the redirect address
    return redirect(redir_addr)

@app.route(service_prefix+'/remove',methods=['get'])
def remove():
    """
    Unbind container from the proxy and delete it.
    """
    c_id=request.args.get('c_id')
    container_name=container_prefix+c_id
    proxy_rule_addr='http://0.0.0.0:'+   \
                    str(proxy_api_port)+ \
                   '/api/routes/'+c_id

    req.delete(proxy_rule_addr)
    docli.remove_container(container_name,force=True)
    return "<h1>Deleted container</h1><br>"+container_name

@app.route(service_prefix+'/build',methods=['get'])
def buildimage():
    """
    Simple function to build image from git repo based on
    jupyter/scipy-notebook. If repo has requirements.txt file
    than pip install required packages.
    """
    # get link to git repo
    gitrepo=request.args.get('gitlink')
    # the name of the image is goingto be 'binder-<repo_name>' 
    tag=image_prefix+gitrepo.rsplit('/',1)[-1].rsplit('.',1)[0]
    # a simple Dockerfile to build images from
    dockerfile="""
FROM jupyter/scipy-notebook
RUN git clone %s notebooks
WORKDIR /home/jovyan/work/notebooks
USER root
RUN if [ -f requirements.txt ] ; then \
    pip install -r requirements.txt ; \
    else \
    echo "No additional packages installed" ; \
    fi;
ADD https://raw.githubusercontent.com/oroszl/koopi/master/koopi_singleuser.py /usr/local/bin/
USER jovyan
    """%(gitrepo)
    f = BytesIO(dockerfile.encode('utf-8'))
    # build the image and format the output to be a human readable
    # html stream
    resp = map(
         lambda x:eval(str(x.decode('utf-8')))['stream']+'<br>',
         docli.build(fileobj=f, rm=True, tag=tag)
         )
    return Response(resp)

@app.route(service_prefix+'/list_images')
def list_built_images():
    """
    Simple function to list images already built.
    Links are provided to spawners.
    """

    hreflink='http://'+external_service_ip+        \
             ':'+str(proxy_port)+service_prefix+   \
             '/spawn?image='

    service_images=[                               \
          '<a href="'+hreflink+                    \
          '{0}">{0}</a>'.format(                   \
          cont['RepoTags'][0])+'<br>'              \
          for cont in docli.images()               \
          if image_prefix in cont['RepoTags'][0] ]

    return '<h1>Images</h1>'+\
           ''.join(service_images)

@app.route(service_prefix+'/list_containers')
def list_running_containers():
    """
    Simple function to list containers currently running.
    """
    hreflink='http://'+external_service_ip+       \
             ':'+str(proxy_port)+service_prefix+  \
             '/remove?c_id='

    service_containers=[                           \
          '{0} '.format(cont['Names'][0])          \
          +'<a href="' + hreflink                  \
          +'{0}" '                                 \
          .format(cont['Names'][0].split('_')[-1]) \
          +'style="color:rgb(255,0,0)">'           \
          +'<font color="red">Delete</font></a>'   \
          +'<br>'                                  \
          for cont in docli.containers()           \
          if container_prefix in cont['Names'][0] ]

    return '<h1>Containers</h1>'+\
           ''.join(service_containers)

@app.route(service_prefix+'/')
def help():
    return app.send_static_file('koopi_guide.html')

if __name__ == "__main__":
  # start proxy and bind service_prefix to it
  req.post('http://0.0.0.0:'+str(proxy_api_port)+\
           '/api/routes'+service_prefix,
           json={'target':'http://'+ownip+':9001'})
  # run service 
  app.run(host=ownip, port=9001, debug=True)

