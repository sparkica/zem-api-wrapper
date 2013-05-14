
from flask import Flask, request
from zemwrapper import Wrapper

app = Flask(__name__)


# ZEMANTA API KEY - enter your API key here
zem_api_key = 'enter-your-api-key-here'


@app.route("/service", methods=['POST', 'GET'])
def suggest():
	"""Calls Zemanta API and returns NIF format"""
	args = []
	if request.method == 'POST':
		args = request.form
	elif request.method == 'GET':
		args = request.args
	wrapper = Wrapper(zem_api_key, args)

	return wrapper.nlp2rdf()


@app.route('/')
def index():
	return 'NIF wrapper for Zemanta API'

if __name__ == '__main__':
	app.run(debug=True)
