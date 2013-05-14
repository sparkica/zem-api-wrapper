import logging

from flask import Flask, request

from zemwrapper import Wrapper


app = Flask(__name__)


### Debugging settings
if app.debug:
    from logging.handlers import StreamHandler
    stream_handler = StreamHandler()
    stream_handler.setLevel(logging.INFO)
    app.logger.addHandler(stream_handler)
    app.looger.info("Logging in DEBUG mode...")

else:
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(filename='log-recon.log', maxBytes=1024, backupCount=3, encoding='utf-8')
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

# ZEMANTA API KEY - enter your API key here
zem_api_key = 'vsuyfg0krcw3fgnjeohifwlv'


@app.route("/service", methods=['POST', 'GET'])
def suggest():
	"""Calls Zemanta API and returns NIF format"""
	args = []
	print "in service..."
	if request.method == 'POST':
		print "POST"
		args = request.form
	elif request.method == 'GET':
		print "GET"
		args = request.args

	print "ARGS: ", args	
	wrapper = Wrapper(zem_api_key, args)

	return wrapper.nlp2rdf()

	


@app.route('/')
def index():
	return 'This is NIF wrapper for Zemanta API'

if __name__ == '__main__':
	app.run(debug=True)
