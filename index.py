import asyncio
import os

from deepclient import DeepClientOptions, DeepClient
from flask import Flask, jsonify, request
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport

app = Flask(__name__)

GQL_URN = os.environ.get("GQL_URN", "3006-deepfoundation-dev-adxmoff7bpv.ws-eu103.gitpod.io/gql")
GQL_SSL = os.environ.get("GQL_SSL", 0)
TEMPLATE_CODE = """
async def fn(arg):
    data = arg['data']
    # Place your logic here
{{USER_CODE}}

global result;
result = asyncio.run(fn({{params}}))
"""
async def execute_handler(code, args):
    python_handler_context = {'args': args}
    generated_code = f"{code}\npython_handler_context['result'] = fn(python_handler_context['args'])"
    code_object = compile(generated_code, 'python_handler', 'exec')
    exec(code_object, dict(python_handler_context=python_handler_context))
    result = python_handler_context['result']
    return result

def make_deep_client(token):
    if not token:
        raise ValueError("No token provided")
    url = "https://3006-deepfoundation-dev-adxmoff7bpv.ws-eu103.gitpod.io/gql"
    transport = AIOHTTPTransport(url=url, headers={'Authorization': f"Bearer {token}"})
    client = Client(transport=transport, fetch_schema_from_transport=True)
    options = DeepClientOptions(gql_client=client)
    deep_client = DeepClient(options)
    return deep_client

@app.route('/healthz', methods=['GET'])
def healthz():
    return jsonify({})

@app.route('/init', methods=['POST'])
def init():
    return jsonify({})

@app.route('/call', methods=['POST'])
def call():
    body = request.json
    params = body['params']
    user_code = '\n'.join(['    ' + line for line in params['code'].splitlines()])
    full_code = TEMPLATE_CODE.replace("{{USER_CODE}}", user_code).replace("{{params}}", str(params))
    global deep;
    deep = make_deep_client(params['jwt'])
    exec(full_code)
    result = globals()['result']
    return jsonify({'resolved': result})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=os.environ.get("PORT"), use_reloader=False, threaded=True)
