#!/usr/bin/env python

"""wrapper.py: Simple NIF Wrapper for Zemanta API. You need Zemanta API key."""


import urllib
import hashlib
import simplejson as json

from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef
from rdflib import plugin
from rdflib import RDF, RDFS, XSD
from rdflib.serializer import Serializer

plugin.register('pretty-xml', Serializer, 'rdflib.plugins.serializers.rdfxml', 'PrettyXMLSerializer')
plugin.register('n3', Serializer, 'rdflib.plugins.serializers.n3', 'N3Serializer')
plugin.register('turtle', Serializer, 'rdflib.plugins.serializers.turtle', 'TurtleSerializer')
plugin.register('xml', Serializer, 'rdflib.plugins.serializers.rdfxml', 'XMLSerializer')
plugin.register('nt', Serializer, 'rdflib.plugins.serializers.nt', 'NTSerializer')

plugin.register("rdf-json", Serializer, "rdflib_rdfjson.rdfjson_serializer", "RdfJsonSerializer")


gateway = 'http://api.zemanta.com/services/rest/0.0/'

STRING = Namespace("http://nlp2rdf.lod2.eu/schema/string/")
SSO =  Namespace("http://nlp2rdf.lod2.eu/schema/sso/")
ZEM = Namespace("http://s.zemanta.com/ns#")
ZEM_TARGETS = Namespace("http://s.zemanta.com/ns/targets/#")
ZEM_OBJ = Namespace("http://s.zemanta.com/obj/")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
FREEBASE = Namespace("http://rdf.freebase.com/ns/")
NIF = Namespace("http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
ITSRDF = Namespace("http://www.w3.org/2005/11/its/rdf#")

FORMAT_MAPPINGS = {
	'rdfxml': 'pretty-xml',
	'ntriples': 'nt',
	'turtle': 'turtle',
	'n3': 'n3',
	'json': 'rdf-json'
}

FORMATS_ZEMANTA = ['xml', 'json','wnjson', 'rdfxml']

class Wrapper():

	def __init__(self, api_key, args):
		self.args = args
		self.format = "json"

		self.nif = False
		self.isGraph = False
		self.zem_args = {}
		self.graph = Graph()

	# input-type = "text" it is always text
	def parse_parameters(self):

		msg = ""
		status = "ok"

		#NIF parameters
		# nif = "true" | "nif-1.0"
		if 'nif' in self.args:
			self.nif = True

		if self.nif:

			# NIF PARAMETERS
			# input-type = "text"
			if 'input-type' in self.args:
				if self.args['input-type'] != 'text':
					status = 'error'
					msg = "Zemanta only supports plain text input."

			# NIF: input = "some text"
			# Zemanta: text = "some text" 
			if 'input' in self.args:
				self.zem_args['text'] = self.args['input']
				if ('text' in self.args):
					if self.args['input'] != self.args['text']:
						msg = "Parameters input and text do not match."
						status = "error"
			elif 'text' in self.args:
				self.zem_args['text'] = self.args['text']
			else:
				msg = "No text is provided."
				status = "error"

			# output format = "rdfxml" | "ntriples" | "turtle" | "n3" | "json"  
			if ('format' in self.args):
				self.zem_args['format'] = 'json'
				if self.args['format'] in FORMAT_MAPPINGS.keys():
					self.format = FORMAT_MAPPINGS[self.args['format']]
				else:
					status = 'error'
					msg = "Invalid output format. It should be one of the following: rdfxml, ntriples, turtle, n3, json."
			else: 
				status = 'error'
				msg = "Please specify output format."

			# Default zemanta parameters
			if 'method' in self.args:
				self.zem_args['method'] = self.args['method']
			else:
				self.zem_args['method'] = 'zemanta.suggest_markup' # default

			if 'api_key' in self.args:
				self.zem_args['api_key'] = self.args['api_key']

		else:
			self.zem_args = self.args

			if 'format' in self.args:
				#wrapper for turtle, n3, ntriples
				if self.args['format'] not in FORMATS_ZEMANTA:
					self.zem_args['format'] = 'json'
					self.format = FORMAT_MAPPINGS[self.args['format']]
					self.isGraph = True
			else: #default format
				self.zem_args['format'] = 'xml'

		return (status, msg)


	def nlp2rdf(self):
		"""Converts Zemanta result into triples and NIF format"""
		(status, msg) = self.parse_parameters()
		if status == "error":
			return self.generate_error_response(msg)
		
		result = {} 
		#make zem-api call
		result = self.make_zem_api_request()

		if self.isGraph == False:
			return result

		# Parse result into triples
		rid = result['rid']
		docuri = "http://d.zemanta.com/rid/%s" % (rid)

		doc_id = URIRef(docuri)
		markup = []
		if result.has_key('markup'):
			markup = result['markup']
		
		# create binds
		self.graph.bind('z', ZEM)
		self.graph.bind('zobj', ZEM_OBJ)
		self.graph.bind('ztarget', ZEM_TARGETS)
		self.graph.bind('rdf', RDF)
		self.graph.bind('rdfs', RDFS)
		self.graph.bind('owl', OWL)
		self.graph.bind('xsd', XSD)
		self.graph.bind('base', docuri)

		# NIF specific binds
		self.graph.bind('nif', NIF)
		self.graph.bind('itsrdf', ITSRDF)


		if self.nif:
			self.create_nif(doc_id, markup)
		
		else: 
			self.create_document(doc_id, rid)

			if result.has_key('articles'):
				self.create_articles(result['articles'], doc_id)
			if result.has_key('images'):
				self.create_images(result['images'], doc_id)
			if result.has_key('keywords'):
				self.create_keywords(result['keywords'], doc_id)
			if result.has_key('categories'):
				self.create_categories(result['categories'], doc_id)
			if result.has_key('markup'):
				self.create_markup(markup, doc_id)

		return self.graph.serialize(format=self.format, encoding="utf-8")


	def create_nif(self, doc_id, markup):
				
		context_id = URIRef(doc_id + '#char=0,')

		# Context
		self.graph.add((context_id, RDF.type, NIF.Context))
		self.graph.add((context_id, RDF.type, NIF.String))
		self.graph.add((context_id, RDF.type, NIF.RFC5147String))
		self.graph.add((context_id, NIF.isString, Literal(self.zem_args['text'])))

		# Entity linking
		for n,k in enumerate(markup['links']):

			#first occurence of the entity
			start_index = self.zem_args['text'].find(k['anchor'])
			end_index = start_index + len(k['anchor'])

			if start_index < 1:
				msg = "Invalid entity start index."
				return generate_error_response(msg)

			entity_id = URIRef(doc_id+'#char=%i,%i' % (start_index, end_index))
			
			self.graph.add((entity_id, RDF.type, NIF.String))
			self.graph.add((entity_id, RDF.type, NIF.RFC5147String))
			self.graph.add((entity_id, NIF.referenceContext, context_id))
			self.graph.add((entity_id, NIF.beginIndex, Literal(start_index, datatype=XSD.int)))
			self.graph.add((entity_id, NIF.beginIndex, Literal(end_index, datatype = XSD.int)))
			self.graph.add((entity_id, NIF.anchorOf, Literal(k['anchor'])))
			self.graph.add((entity_id, ITSRDF.taConfidence, Literal(k['confidence'], datatype=XSD.float)))

			# entity types
			for entity_type in k.get("entity_type", []):
				self.graph.add((entity_id, ITSRDF.taClassRef, URIRef(FREEBASE.schema + entity_type)))

			# targets
			for target in k['target']:		
				print "Target[type]: ", target['type']		
				if target['type'] == 'rdf':
					self.graph.add((entity_id, ITSRDF.taIdentRef, URIRef(target['url'])))
				else:
					target_id = URIRef(target['url'])
					self.graph.add((entity_id, ITSRDF.taIdentRef, target_id))
					self.graph.add((target_id, RDF.type, ZEM.target))
					self.graph.add((target_id, ZEM.targetType, URIRef(ZEM_TARGETS + target['type'])))

	def create_document(self, doc_id, rid):

		#bindings
		self.graph.add((doc_id, RDF.type, ZEM.Document))		
		self.graph.add((doc_id, ZEM.text, Literal(self.zem_args['text'])))
		self.graph.add((doc_id, ZEM.rid, Literal(rid)))

	
	def create_articles(self, articles, doc_id):
		for n,a in enumerate(articles):
			article_id = URIRef('#Related%i' % (n+1))
			self.graph.add((article_id, RDF.type, ZEM.Related))
			self.graph.add((article_id, ZEM.doc, doc_id))
			self.graph.add((article_id, ZEM.confidence, Literal(a['confidence'], datatype=XSD.float)))

			target_id = URIRef(a['url'])
			self.graph.add((article_id, ZEM.target, target_id))
			self.graph.add((target_id, RDF.type, ZEM.Target))
			self.graph.add((target_id, ZEM.targetType, ZEM_TARGETS.article))
			self.graph.add((target_id, ZEM.article_id, Literal(a['article_id'])))
			self.graph.add((target_id, ZEM.published_datetime, Literal(a['published_datetime'], datatype=XSD.date)))
			self.graph.add((target_id, ZEM.title, Literal(a['title'])))
			self.graph.add((target_id, ZEM.zemified, Literal(a['zemified'])))
			
			self.graph.add((target_id, ZEM.text_preview, Literal(a['text_preview'])))
			self.graph.add((target_id, ZEM.retweets, Literal(a['retweets'], datatype=XSD.integer)))


	def create_images(self, images, doc_id):
		for n,a in enumerate(images):
			image_id = URIRef("#Image%i" % (n + 1))
			self.graph.add((image_id, RDF.type, ZEM.Image))
			self.graph.add((image_id, ZEM.doc, doc_id))
			self.graph.add((image_id, ZEM.description, Literal(a['description'])))
			self.graph.add((image_id, ZEM.attribution, Literal(a['attribution'])))
			self.graph.add((image_id, ZEM.license_text, Literal(a['license'])))
			self.graph.add((image_id, ZEM.source_url, URIRef(a['source_url'])))
			self.graph.add((image_id, ZEM.confidence, Literal(a['confidence'], datatype=XSD.float)))

			self.graph.add((image_id, ZEM.url_s, URIRef(a['url_s'])))
			self.graph.add((image_id, ZEM.url_s_w, Literal(a['url_s_w'])))
			self.graph.add((image_id, ZEM.url_s_h, Literal(a['url_s_h'])))
			self.graph.add((image_id, ZEM.url_m, URIRef(a['url_m'])))
			self.graph.add((image_id, ZEM.url_m_w, Literal(a['url_m_w'])))
			self.graph.add((image_id, ZEM.url_m_h, Literal(a['url_m_h'])))
			self.graph.add((image_id, ZEM.url_m, URIRef(a['url_l'])))
			self.graph.add((image_id, ZEM.url_m_w, Literal(a['url_l_w'])))
			self.graph.add((image_id, ZEM.url_m_h, Literal(a['url_l_h'])))


	def create_keywords(self, keywords, doc_id):
		for n,k in enumerate(keywords):
			keyword_id =  URIRef("#Keyword%i" % (n + 1))
			self.graph.add((keyword_id, RDF.type, ZEM.Keyword))
			self.graph.add((keyword_id, ZEM.doc, doc_id))
			self.graph.add((keyword_id, ZEM.confidence, Literal(k['confidence'], datatype = XSD.float)))
			self.graph.add((keyword_id,ZEM.name, Literal(k['name'])))
			self.graph.add((keyword_id,ZEM.scheme, Literal(k['scheme'])))

	def create_categories(self, categories, doc_id):
		for n, c in enumerate(categories):
			category_id = URIRef("#Category %i" % (n + 1))
			self.graph.add((category_id,RDF.type, ZEM.Category))
			self.graph.add((category_id,ZEM.doc, doc_id))
			self.graph.add((category_id,ZEM.confidence,Literal(c['confidence'], datatype = XSD.float)))
			self.graph.add((category_id,ZEM.name, Literal(c['name'])))
			self.graph.add((category_id,ZEM.categorization, Literal(c['categorization'])))

	def create_markup(self, markup, doc_id):
		for n,k in enumerate(markup['links']):
			link_id = URIRef("#Recognition%i" % (n+1))
			self.graph.add((link_id, RDF.type, ZEM.Recognition))
			self.graph.add((link_id, ZEM.doc, doc_id))
			self.graph.add((link_id, ZEM.confidence, Literal(k['confidence'], datatype=XSD.float)))
			self.graph.add((link_id, ZEM.relevance, Literal(k['relevance'], datatype=XSD.float)))
			self.graph.add((link_id, ZEM.anchor, Literal(k['anchor'])))			
			
			object_id = URIRef("#Object%i" % (n + 1))
			self.graph.add((link_id, ZEM.object, object_id))
			self.graph.add((object_id, RDF.type, ZEM.Object))
		
			#entity types
			for entity_type in k.get("entity_type", []):
				self.graph.add((object_id, ZEM.entity_type, URIRef(FREEBASE.schema + entity_type)))

			# targets
			for target in k['target']:		
				if target['type'] == 'rdf':
					self.graph.add((object_id, OWL.sameAs, URIRef(target['url'])))
				target_id = URIRef(target['url'])
				self.graph.add((object_id, ZEM.target, target_id))
				self.graph.add((target_id, RDF.type, ZEM.target))
				self.graph.add((target_id, ZEM.title, Literal(target['title'])))
				self.graph.add((target_id, ZEM.targetType, URIRef(ZEM_TARGETS + target['type'])))

	def generate_error_response(self, msg):
		
		ERROR = Namespace("http://nlp2rdf.lod2.eu/schema/error/")

		e_graph = Graph()
		e_graph.bind('error', ERROR)
		
		error = URIRef(ERROR.Error)
		e_graph.add((error, ERROR.fatal, Literal(1)))
		e_graph.add((error, ERROR.hasMessage, Literal(msg)))	
	
		return e_graph.serialize(format=self.format, encoding="utf-8")

	def make_zem_api_request(self):
		gateway = 'http://api.zemanta.com/services/rest/0.0/'
		args_enc = urllib.urlencode(self.zem_args)
		raw_output = urllib.urlopen(gateway, args_enc).read()

		if self.isGraph == False:
			return raw_output

		output = json.loads(raw_output)
		if 'status' in output and output['status'] == 'ok':
			return output
		else:
			msg = "Error calling Zemanta API."
			return self.generate_error_response(msg)

	def get_info(self):
		info = Graph()
		
		NS0 = Namespace("http://usefulinc.com/ns/doap#")
		NS1 = Namespace("http://nlp2rdf.org/")
		wrapper_id = URIRef(NS1 + 'implementations/zemanta')
		BASE = Namespace(wrapper_id)

		info.bind("rdf", RDF)
		info.bind("ns0", NS0)
		info.bind("ns1", NS1)

		content = "NIF wrapper for Zemanta API."		
		info.add((wrapper_id, NS0.homepage, URIRef("http://www.zemanta.com")))
		info.add((wrapper_id, NS1.additionalparameter, Literal("You need Zemanta API key. For other parameters check Zemanta API documentation.")))
		info.add((wrapper_id, NS1.status, Literal("NIF 2.0 compliant without RDF/XML input and JSON output")))
		info.add((wrapper_id, NS1.webserviceurl, Literal(" - Add URL here - ")))
		info.add((wrapper_id, NS1.demo, Literal(" - Add URL here - ")))
		info.add((wrapper_id, NS1.code, URIRef("https://github.com/sparkica/zem-api-wrapper")))

		return info.serialize(format=self.format, encoding="utf-8")




