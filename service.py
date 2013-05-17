
from flask import Flask, request
from zemwrapper import Wrapper

app = Flask(__name__)


# Enter your Zemanta API key here
zem_api_key = 'enter-your-api-key-here'


@app.route("/service", methods=['POST', 'GET'])
def suggest():
	"""Wrapper for Zemanta API providing output formats supported by rdflib"""
	args = []
	if request.method == 'POST':
		args = request.form
	elif request.method == 'GET':
		args = request.args
	wrapper = Wrapper(zem_api_key, args)
	
	print "Here we are now..."
	return wrapper.nlp2rdf()


@app.route('/')
def index():
	""" Returns information about the wrapper in RDF format """	
	args = []
	if request.method == 'POST':
		args = request.form
	elif request.method == 'GET':
		args = request.args
	wrapper = Wrapper("",args)

	return wrapper.get_info()

if __name__ == '__main__':
	app.run(debug=True)
