from flask import Flask, request, Response
import os
import cherrypy
import json
import logging
import paste.translogger
import requests
import base64, boto3

app = Flask(__name__)

logger = logging.getLogger("aws-ecr-getlogin")

APITOKEN = os.environ.get("SESAM_JWT_TOKEN", "")
LOCALIP = os.environ.get("LOCALIP", "")

@app.route('/', methods=['GET'])
def root():

    # obtain docker login token
    ecr_client = boto3.client('ecr', region_name='eu-central-1')
    token = ecr_client.get_authorization_token()
    username, password = base64.b64decode(token['authorizationData'][0]['authorizationToken']).decode().split(':')

    # write it to sesam secrets
    headers = { "Content-Type" : "application/json", "Authorization" : "Bearer " + APITOKEN}
    url = "http://"+LOCALIP+":9042/api/secrets"
    data = { "AWS_ECR_TOKEN" : password }

    r = requests.put(url, headers=headers, json=data)

    if r.status_code == requests.codes.ok:
        print("success")
        response_json = []
        property_json = {}
        property_json["_id"] = "ecr_token_updated"
        response_json.append(property_json)
        return Response(response=json.dumps(response_json), status=200)
    else:
        print("failed to write secrets " + str(r.status_code))
        return Response(status=400, response="Not working.")

if __name__ == '__main__':
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Log to stdout, change to or add a (Rotating)FileHandler to log to a file
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(stdout_handler)

    # Comment these two lines if you don't want access request logging
    app.wsgi_app = paste.translogger.TransLogger(app.wsgi_app, logger_name=logger.name,
                                                 setup_console_handler=False)
    app.logger.addHandler(stdout_handler)

    logger.propagate = False
    logger.setLevel(logging.INFO)

    cherrypy.tree.graft(app, '/')

    # Set the configuration of the web server to production mode
    cherrypy.config.update({
        'environment': 'production',
        'engine.autoreload_on': False,
        'log.screen': True,
        'server.socket_port': 5001,
        'server.socket_host': '0.0.0.0'
    })

    # Start the CherryPy WSGI web server
    cherrypy.engine.start()
    cherrypy.engine.block()


