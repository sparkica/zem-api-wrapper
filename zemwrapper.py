#!/usr/bin/env python

"""wrapper.py: Simple NIF Wrapper for Zemanta API. You need to obtain an api key."""
### BUCA; ne bi rabila vsega spravljat v RDF :)))
### ZA NIF RABIM SAMO MARKUP

import urllib
import hashlib
import simplejson

from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef
from rdflib import plugin
from rdflib import RDF, RDFS, XSD
from rdflib.serializer import Serializer



plugin.register('pretty-xml', Serializer,
		'rdflib.plugins.serializers.rdfxml', 'PrettyXMLSerializer')


gateway = 'http://api.zemanta.com/services/rest/0.0/'

STRING = Namespace("http://nlp2rdf.lod2.eu/schema/string/")
SSO =  Namespace("http://nlp2rdf.lod2.eu/schema/sso/")
ZEM = Namespace("http://s.zemanta.com/ns#")
ZEM_TARGETS = Namespace("http://s.zemanta.com/ns/targets/#")
ZEM_OBJ = Namespace("http://s.zemanta.com/obj/")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
FREEBASE = Namespace("http://rdf.freebase.com/ns/")
NIF = Namespace("http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#")


class Wrapper():

	def __init__(self, api_key, args):
		self.args = args
		self.zem_args = {'method': 'zemanta.suggest',
						'api_key': api_key,
						'text': '',
						'format': 'json'}
		self.graph = Graph()


	def parse_parameters(self):

		msg = ""
		status = "ok"
		if 'method' in self.args:
			self.zem_args['method'] = self.args['method']
		else:
			self.zem_args['method'] = 'zemanta.suggest_markup'

		if 'input' in self.args:
			self.zem_args['text'] = self.args['input']

		if 'input' in self.args and 'text' in self.args:
			print 'Input and text in parameters'
			if self.args['input'] != self.args['text']:
				msg = "Parameters input and text do not match. Set either input or text or set them both to same value."
				status = "error"
				print "ERROR"

		if 'nif' in self.args:
			nif = self.args['nif']
		
		return (status, msg)


	def nlp2rdf(self):
		
		(status, msg) = self.parse_parameters()
		if status == "error":
			return self.generate_error_response(msg, "pretty-xml")
		
		nif = False

		#make zem-api call
		result = self.fake_zem_api_call()

		# define namespaces

		rid = result['rid']
		docuri = "http://d.zemanta.com/rid/%s" % (rid)

		self.graph.bind('string', STRING)
		self.graph.bind('sso', SSO)
		self.graph.bind('z', ZEM)
		self.graph.bind('zobj', ZEM_OBJ)
		self.graph.bind('ztarget', ZEM_TARGETS)
		self.graph.bind('rdf', RDF)
		self.graph.bind('rdfs', RDFS)
		self.graph.bind('owl', OWL)
		self.graph.bind('nif', NIF)
		self.graph.bind('base', docuri)

		doc_id = URIRef(docuri)

		
		#NIF does not need all this data
		if nif:
			self.graph.add((URIRef(doc_id + '#char=0'), RDF.type, NIF.Context))
		else:
			# add document
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
				self.create_markup(result['markup'], doc_id)

		#print self.graph.serialize(format="n3")
		#return self.graph.serialize(format="n3", encoding="utf-8")
		# FORMATS
		# "rdfxml" | "ntriples" | "turtle" | "n3" | "json" 
		return self.graph.serialize(format="pretty-xml", encoding="utf-8")


	# TODO: other optional parameters
	# nif = "true" | "nif-1.0" 
	# format = "rdfxml" | "ntriples" | "turtle" | "n3" | "json" 
	# prefix = uriprefix 
	# urirecipe = "offset" | "context-hash" 
	# context-length = integer
	# debug = "true" | "false"

	def create_document(self, doc_id, rid):
		self.graph.add((doc_id, RDF.type, ZEM.Document))		
		self.graph.add((doc_id, ZEM.text, Literal(self.zem_args['text'])))
		#self.graph.add((doc_id, ZEM.signature, Literal(result['signature'])))
		self.graph.add((doc_id, ZEM.rid, Literal(rid)))

	
	def create_articles(self, articles, doc_id):
			#articles
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
			#self.graph.add((image_id, RDF.Description, Literal("#Image%i" % (n + 1))))
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
			#self.graph.add((keyword_id, RDF.Description, Literal("#Keyword%i" % (n + 1))))
			self.graph.add((keyword_id, RDF.type, ZEM.Keyword))
			self.graph.add((keyword_id, ZEM.doc, doc_id))
			self.graph.add((keyword_id, ZEM.confidence, Literal(k['confidence'], datatype = XSD.float)))
			self.graph.add((keyword_id,ZEM.name, Literal(k['name'])))
			self.graph.add((keyword_id,ZEM.scheme, Literal(k['scheme'])))

	def create_categories(self, categories, doc_id):
		for n, c in enumerate(categories):
			category_id = URIRef("#Category %i" % (n + 1))
			#self.graph.add((category_id,RDF.Description,Literal("#Category %i" % (n + 1))))
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
			print "Target[type]: ", target['type']		
			if target['type'] == 'rdf':
				self.graph.add((object_id, OWL.sameAs, URIRef(target['url'])))
				#	tx.attrib['rdf:about'] = "http://s.zemanta.com/obj/"  +m.hexdigest() #Object%i" % (n + 1)
				#	tx = None
			target_id = URIRef(target['url'])
			self.graph.add((object_id, ZEM.target, target_id))
			self.graph.add((target_id, RDF.type, ZEM.target))
			self.graph.add((target_id, ZEM.title, Literal(target['title'])))
			self.graph.add((target_id, ZEM.targetType, URIRef(ZEM_TARGETS + target['type'])))



	#TODO: don't hardcode rdfxml, response depends on the format
	def generate_error_response(self, msg, output_format):
		
		ERROR = Namespace("http://nlp2rdf.lod2.eu/schema/error/")

		e_graph = Graph()
		e_graph.bind('error', ERROR)
		
		error = URIRef(ERROR.Error)
		e_graph.add((error, ERROR.fatal, Literal(1)))
		e_graph.add((error, ERROR.hasMessage, Literal(msg)))	
	
		#msg = """ 
		#	<rdf:RDF 
		#	  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" 
		#	  xmlns:error="http://nlp2rdf.lod2.eu/schema/error/">
		#	  <rdf:Description>
		#	    <rdf:type rdf:resource="http://nlp2rdf.lod2.eu/schema/error/Error"/>
		#	    <error:fatal>1</error:fatal>
		#	    <error:hasMessage>There was an error.</error:hasMessage>
		#	  </rdf:Description>
		#	</rdf:RDF>
		#			"""
		return e_graph.serialize(format="pretty-xml", encoding="utf-8")

	
	def fake_zem_api_call(self):

		#rsp = {"status": "ok", "markup": {"text": "", "links": [{"relevance": 0.64744199999999996, "confidence": 0.89068700000000001, "entity_type": ["/location/location"], "target": [{"url": "http://maps.google.com/maps?ll=52.5005555556,13.3988888889&spn=0.1,0.1&q=52.5005555556,13.3988888889 (Berlin)&t=h", "type": "geolocation", "title": "Berlin"}, {"url": "http://www.berlin.de/international/index.en.php", "type": "homepage", "title": "Berlin"}, {"url": "http://en.wikipedia.org/wiki/Berlin", "type": "wikipedia", "title": "Berlin"}], "anchor": "Berlin"}]}, "rid": "c5885ce5-2a9e-40d3-b3c4-9aaa35342a2c", "signature": "<div class=\"zemanta-pixie\"><a class=\"zemanta-pixie-a\" href=\"http://www.zemanta.com/?px\" title=\"Enhanced by Zemanta\"><img class=\"zemanta-pixie-img\" src=\"http://img.zemanta.com/zemified_e.png?x-id=c5885ce5-2a9e-40d3-b3c4-9aaa35342a2c\" alt=\"Enhanced by Zemanta\" /></a></div>"}

		rsp = {"status": "ok", "articles": [{"confidence": 0.018346999999999999, "published_datetime": "2013-05-11T15:59:35Z", "title": "Berlin! Berlin! Wir fahren nach Berlin! (We're going to Berlin!)", "url": "http://arikvictor.wordpress.com/2013/05/11/berlin-berlin-wir-fahren-nach-berlin-were-going-to-berlin/", "retweets": 1, "text_preview": "It's been quite the trip thus far. I left Newark airport around 6pm and arrived in Berlin just after 8am. I only managed to sleep a little on the plane but probably more impressively stayed awake all of Friday and even went out too.\nI look excited. This one looks stressed and worried per usual.\nMy first day I did quite a bit of walking, some by...", "article_id": 168056420, "zemified": 0}, {"confidence": 0.0087620000000000007, "published_datetime": "2013-05-07T23:04:58Z", "title": "Berliner!", "url": "http://ledaringfox.wordpress.com/2013/05/08/berliner/", "retweets": 0, "text_preview": "Oh how I love this beautiful city! It was especially gorgeous last weekend in the sun and I spent most of my time in parks. Weinbergspark in the cool Mitte district, not far from the Rosenthaler Platz UBahn stop, is a quieter alternative to the busy Mauerpark. However, Mauerpark on a Sunday is definitely a must.", "article_id": 166881924, "zemified": 0}, {"confidence": 0.0083800000000000003, "published_datetime": "2013-05-04T15:36:54Z", "title": "Beautiful Berlin", "url": "http://surpriseact.wordpress.com/2013/05/04/beautiful-berlin/", "retweets": 0, "text_preview": "I got back from Berlin yesterday, and the memories are still fresh. There's a gallery (where you can read about the camera settings, how AWESOME is that?!), meaning you can wait ages for your computer to load that crap and view it full-sized. I haven't had time to edit anything yet, so this is what you get. Raw, unedited: Berlin as it is.\nP.S.", "article_id": 165913102, "zemified": 0}, {"confidence": 0.0082430000000000003, "published_datetime": "2013-05-11T14:39:13Z", "title": "Berlin", "url": "http://lauranathalietravels.wordpress.com/2013/05/11/berlin/", "retweets": 0, "text_preview": "Maybe it was because I just came back from New York or maybe it just wasn't my city. I didn't got blown away by Berlin when I came there. It was a little gray and depressing. It doesn't mean that I didn't had a good time! I was traveling with my friends for three nights. One friend actually lived in Berlin for six months to do an internship so we...", "article_id": 168081638, "zemified": 0}, {"confidence": 0.0077629999999999999, "published_datetime": "2013-05-11T21:37:05Z", "title": "Berlin", "url": "http://clairemcgowanphotography.wordpress.com/2013/05/11/berlin/", "retweets": 0, "text_preview": "A couple of weeks ago I went to Berlin for a short break with my boyfriend.  It was the first time i'd been to the city and i'll definitely be going back for another visit.  We only went for 2 days but I could have happily stayed for a week.  I took a lot of photos so i'm gonna split this into two posts.\nDay 1.\nAlexanderplatz. Holocaust Memorial.", "article_id": 168098261, "zemified": 0}, {"confidence": 0.0077530000000000003, "published_datetime": "2013-05-06T00:01:56Z", "title": "When Odessa Meets Rio for Coffee in Berlin...", "url": "http://theflowgermany.wordpress.com/2013/05/06/when-odessa-meets-rio-for-coffee-in-berlin/", "retweets": 1, "text_preview": "Sometimes the perfect world is having coffee with your lover on a rooftop terrace in Berlin. Or so says Odessa Express, a chill new jazz band on the city's circuit. Granted, we don't all have access to Berlin's signature terraces, which define the city's winning combo of coastal ease and continental sophistication.", "article_id": 166217914, "zemified": 0}, {"confidence": 0.0074310000000000001, "published_datetime": "2013-05-11T05:30:44Z", "title": "Marley Berlin", "url": "http://marleyzelinkovasmith.wordpress.com/2013/05/11/marley-berlin/", "retweets": 0, "text_preview": "We've been to Berlin twice, and would like to go again and again. And again. It ticks all our Holiday Boxes, namely: Big city with decent public transport system Cool places to stay in the centre of all the fun japes Art galleries History Interesting new food to try / great places to eat Hipster [...", "article_id": 167988687, "zemified": 0}, {"confidence": 0.0074070000000000004, "published_datetime": "2013-05-09T16:23:09Z", "title": "Berlin", "url": "http://writingonthewaldron.wordpress.com/2013/05/09/berlin/", "retweets": 0, "text_preview": "I just quickly chose a few of my favorite pictures from our second day in Berlin.  Berlin is so full of difficult history, very \"raw and German\"(in the words of a Polish friend). And now I'm enjoying time with my sisters in beautiful, full-spring Poland.    It's hard to imagine that in a few months Nate and I will be returning to the US, leaving...", "article_id": 167446680, "zemified": 0}, {"confidence": 0.0073920000000000001, "published_datetime": "2013-04-28T08:00:35Z", "title": "\"JR owns the biggest art gallery in the world\"", "url": "http://berlinlovesyou.com/2013/04/28/jr-owns-the-biggest-art-gallery-in-the-world/", "retweets": 1, "text_preview": "~ ... this blog is about why berlin loves you and why it sometimes doesn`t\n\"JR owns the biggest art gallery in the world\"\n28 Sunday Apr 2013\n\u2248 Leave a Comment\nTags\nBerlin , Berlin Ausstellungen , Berlin exhibition , Berlin jr-art.net , Berlin Street Art , Berlin Streetart , Galerie Springmann , Gallery Weekend , Inside Out Project , Mitte , Street...", "article_id": 163887245, "zemified": 0}, {"confidence": 0.0072030000000000002, "published_datetime": "2013-05-12T14:31:22Z", "title": "!Atlantic 88335755 Berlin Corner TV Stand", "url": "http://atlantic88335755berlincornerstandsaledm01.wordpress.com/2013/05/12/atlantic-88335755-berlin-corner-tv-stand/", "retweets": 0, "text_preview": "You can buy !Atlantic 88335755 Berlin Corner TV Stand here. yes, we have \"!Atlantic 88335755 Berlin Corner TV Stand\" for sale. You can buy !Atlantic 88335755 Berlin Corner TV Stand Shops & Purchase Online.\nProduct Description\nEnjoy both organization and style with the Berlin Corner TV Stand. This unit has great style, functionality and design.", "article_id": 168249679, "zemified": 0}], "markup": {"text": "", "links": [{"relevance": 0.64720900000000003, "confidence": 0.88577399999999995, "entity_type": ["/location/location"], "target": [{"url": "http://maps.google.com/maps?ll=52.5005555556,13.3988888889&spn=0.1,0.1&q=52.5005555556,13.3988888889 (Berlin)&t=h", "type": "geolocation", "title": "Berlin"}, {"url": "http://www.berlin.de/international/index.en.php", "type": "homepage", "title": "Berlin"}, {"url": "http://en.wikipedia.org/wiki/Berlin", "type": "wikipedia", "title": "Berlin"}], "anchor": "Berlin"}]}, "images": [{"url_m_h": 219, "confidence": 0.5, "url_s_h": 75, "attribution": "Berlin, Germany (Photo credit: <a href=\"http://www.flickr.com/photos/34586311@N05/4821497601\">OSU Special Collections &amp; Archives : Commons</a>)", "description": "Berlin, Germany", "license": "No known copyright restrictions", "url_l_w": 500, "url_s": "http://farm5.static.flickr.com/4120/4821497601_41beedfc93_s.jpg", "source_url": "http://www.flickr.com/photos/34586311@N05/4821497601", "url_m": "http://farm5.static.flickr.com/4120/4821497601_41beedfc93_m.jpg", "url_l": "http://farm5.static.flickr.com/4120/4821497601_41beedfc93.jpg", "url_l_h": 457, "url_s_w": 75, "url_m_w": 240}, {"url_m_h": 161, "confidence": 0.5, "url_s_h": 75, "attribution": "Berlin Wall from Above (Photo credit: <a href=\"http://www.flickr.com/photos/24736216@N07/3341403306\">roger4336</a>)", "description": "Berlin Wall from Above", "license": "License CreativeCommons ShareAlike", "url_l_w": 500, "url_s": "http://farm4.static.flickr.com/3411/3341403306_3dcc994a46_s.jpg", "source_url": "http://www.flickr.com/photos/24736216@N07/3341403306", "url_m": "http://farm4.static.flickr.com/3411/3341403306_3dcc994a46_m.jpg", "url_l": "http://farm4.static.flickr.com/3411/3341403306_3dcc994a46.jpg", "url_l_h": 335, "url_s_w": 75, "url_m_w": 240}, {"url_m_h": 0, "confidence": 0.5, "url_s_h": 0, "attribution": "berlin gdr urban model 1987 (Photo credit: <a href=\"http://www.flickr.com/photos/38306946@N02/3528025610\">pardonreeds</a>)", "description": "berlin gdr urban model 1987", "license": "License CreativeCommons NonCommercial NoDerivs", "url_l_w": 0, "url_s": "http://farm4.static.flickr.com/3579/3528025610_d570c1fabf_s.jpg", "source_url": "http://www.flickr.com/photos/38306946@N02/3528025610", "url_m": "http://farm4.static.flickr.com/3579/3528025610_d570c1fabf_m.jpg", "url_l": "http://farm4.static.flickr.com/3579/3528025610_d570c1fabf.jpg", "url_l_h": 0, "url_s_w": 0, "url_m_w": 0}, {"url_m_h": 184, "confidence": 1.0063489999999999, "url_s_h": 46, "attribution": "City-State Berlin in Germany and EU. (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:Berlin_in_Germany_and_EU.png\">Wikipedia</a>)", "description": "City-State Berlin in Germany and EU.", "license": "GNU Free Documentation License", "url_l_w": 2580, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Berlin_in_Germany_and_EU.png/75px-Berlin_in_Germany_and_EU.png", "source_url": "http://commons.wikipedia.org/wiki/File:Berlin_in_Germany_and_EU.png", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Berlin_in_Germany_and_EU.png/300px-Berlin_in_Germany_and_EU.png", "url_l": "http://upload.wikimedia.org/wikipedia/commons/a/a5/Berlin_in_Germany_and_EU.png", "url_l_h": 1585, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 190, "confidence": 0.92696199999999995, "url_s_h": 47, "attribution": "English: Berlin at night. Seen from the Allianz building in Treptow, showing the Universal building on the right at the river Spree and the TV-Tower at Alexanderplatz (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:Berlin_night.jpg\">Wikipedia</a>)", "description": "English: Berlin at night. Seen from the Allianz building in Treptow, showing the Universal building on the right at the river Spree and the TV-Tower at Alexanderplatz", "license": "CC Attribution 2.0 license", "url_l_w": 585, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Berlin_night.jpg/75px-Berlin_night.jpg", "source_url": "http://commons.wikipedia.org/wiki/File:Berlin_night.jpg", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Berlin_night.jpg/300px-Berlin_night.jpg", "url_l": "http://upload.wikimedia.org/wikipedia/commons/7/74/Berlin_night.jpg", "url_l_h": 370, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 226, "confidence": 0.852711, "url_s_h": 57, "attribution": "English: The Fall of the Berlin Wall, 1989. The photo shows a part of a public photo documentation wall at Former Check Point Charlie, Berlin. The photo documentation is permanently placed in the public. T\u00fcrk\u00e7e: Berlin Duvar\u0131, 1989 sonbahar\u0131 (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:Thefalloftheberlinwall1989.JPG\">Wikipedia</a>)", "description": "English: The Fall of the Berlin Wall, 1989. The photo shows a part of a public photo documentation wall at Former Check Point Charlie, Berlin. The photo documentation is permanently placed in the public. T\u00fcrk\u00e7e: Berlin Duvar\u0131, 1989 sonbahar\u0131", "license": "Public domain", "url_l_w": 661, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Thefalloftheberlinwall1989.JPG/75px-Thefalloftheberlinwall1989.JPG", "source_url": "http://commons.wikipedia.org/wiki/File:Thefalloftheberlinwall1989.JPG", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Thefalloftheberlinwall1989.JPG/300px-Thefalloftheberlinwall1989.JPG", "url_l": "http://upload.wikimedia.org/wikipedia/commons/5/52/Thefalloftheberlinwall1989.JPG", "url_l_h": 498, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 180, "confidence": 0.84243500000000004, "url_s_h": 45, "attribution": "Flag of Berlin Espa\u00f1ol: Bandera de Berl\u00edn Nederlands: Vlag van Berlijn Polski: Flaga Berlina (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:Flag_of_Berlin.svg\">Wikipedia</a>)", "description": "Flag of Berlin Espa\u00f1ol: Bandera de Berl\u00edn Nederlands: Vlag van Berlijn Polski: Flaga Berlina", "license": "Public domain", "url_l_w": 1000, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Flag_of_Berlin.svg/75px-Flag_of_Berlin.svg.png", "source_url": "http://commons.wikipedia.org/wiki/File:Flag_of_Berlin.svg", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Flag_of_Berlin.svg/300px-Flag_of_Berlin.svg.png", "url_l": "http://upload.wikimedia.org/wikipedia/commons/e/ec/Flag_of_Berlin.svg", "url_l_h": 600, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 493, "confidence": 0.79325000000000001, "url_s_h": 123, "attribution": "Coat of arms of Berlin. Espa\u00f1ol: Escudo de Berl\u00edn. Eesti: Berliini vapp. Fran\u00e7ais : Blason de Berlin. Polski: Herb Berlina. Svenska: Berlins vapen. (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:Coat_of_arms_of_Berlin.svg\">Wikipedia</a>)", "description": "Coat of arms of Berlin. Espa\u00f1ol: Escudo de Berl\u00edn. Eesti: Berliini vapp. Fran\u00e7ais : Blason de Berlin. Polski: Herb Berlina. Svenska: Berlins vapen.", "license": "Public domain", "url_l_w": 450, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Coat_of_arms_of_Berlin.svg/75px-Coat_of_arms_of_Berlin.svg.png", "source_url": "http://commons.wikipedia.org/wiki/File:Coat_of_arms_of_Berlin.svg", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Coat_of_arms_of_Berlin.svg/300px-Coat_of_arms_of_Berlin.svg.png", "url_l": "http://upload.wikimedia.org/wikipedia/commons/d/d9/Coat_of_arms_of_Berlin.svg", "url_l_h": 739, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 162, "confidence": 0.76701699999999995, "url_s_h": 41, "attribution": "Berlin Hauptbahnhof (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:BlnHauptbahnhof28.jpg\">Wikipedia</a>)", "description": "Berlin Hauptbahnhof", "license": "Public domain", "url_l_w": 1396, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/BlnHauptbahnhof28.jpg/75px-BlnHauptbahnhof28.jpg", "source_url": "http://commons.wikipedia.org/wiki/File:BlnHauptbahnhof28.jpg", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/BlnHauptbahnhof28.jpg/300px-BlnHauptbahnhof28.jpg", "url_l": "http://upload.wikimedia.org/wikipedia/commons/f/f1/BlnHauptbahnhof28.jpg", "url_l_h": 754, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 225, "confidence": 0.71160199999999996, "url_s_h": 56, "attribution": "This image was selected as a picture of the week on the Czech Wikipedia for th week, 2006. (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:Berlinermauer.jpg\">Wikipedia</a>)", "description": "This image was selected as a picture of the week on the Czech Wikipedia for th week, 2006.", "license": "GNU Free Documentation License", "url_l_w": 400, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Berlinermauer.jpg/75px-Berlinermauer.jpg", "source_url": "http://commons.wikipedia.org/wiki/File:Berlinermauer.jpg", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Berlinermauer.jpg/300px-Berlinermauer.jpg", "url_l": "http://upload.wikimedia.org/wikipedia/commons/5/5d/Berlinermauer.jpg", "url_l_h": 300, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 169, "confidence": 0.651501, "url_s_h": 42, "attribution": "Construction site of the main terminal of the new Airport Berlin Brandenburg (BER). (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:BBI_2010-07-23_5.JPG\">Wikipedia</a>)", "description": "Construction site of the main terminal of the new Airport Berlin Brandenburg (BER).", "license": "CC Attribution ShareAlike 3.0 license", "url_l_w": 1920, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/2/22/BBI_2010-07-23_5.JPG/75px-BBI_2010-07-23_5.JPG", "source_url": "http://commons.wikipedia.org/wiki/File:BBI_2010-07-23_5.JPG", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/2/22/BBI_2010-07-23_5.JPG/300px-BBI_2010-07-23_5.JPG", "url_l": "http://upload.wikimedia.org/wikipedia/commons/2/22/BBI_2010-07-23_5.JPG", "url_l_h": 1080, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 113, "confidence": 0.64800999999999997, "url_s_h": 28, "attribution": "Reichstag building seen from the west, before sunset Fran\u00e7ais : Le Palais du Reichstag cot\u00e9 Ouest avant le coucher de soleil (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:Reichstag_building_Berlin_view_from_west_before_sunset.jpg\">Wikipedia</a>)", "description": "Reichstag building seen from the west, before sunset Fran\u00e7ais : Le Palais du Reichstag cot\u00e9 Ouest avant le coucher de soleil", "license": "CC Attribution ShareAlike 3.0 license", "url_l_w": 8347, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Reichstag_building_Berlin_view_from_west_before_sunset.jpg/75px-Reichstag_building_Berlin_view_from_west_before_sunset.jpg", "source_url": "http://commons.wikipedia.org/wiki/File:Reichstag_building_Berlin_view_from_west_before_sunset.jpg", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Reichstag_building_Berlin_view_from_west_before_sunset.jpg/300px-Reichstag_building_Berlin_view_from_west_before_sunset.jpg", "url_l": "http://upload.wikimedia.org/wikipedia/commons/c/c7/Reichstag_building_Berlin_view_from_west_before_sunset.jpg", "url_l_h": 3157, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 225, "confidence": 0.58906400000000003, "url_s_h": 56, "attribution": "Ishtar Gate. Pergamon Berlin Museum. (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:Ishtar_Gate_at_Berlin_Museum.jpg\">Wikipedia</a>)", "description": "Ishtar Gate. Pergamon Berlin Museum.", "license": "CC Attribution 2.0 license", "url_l_w": 1024, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Ishtar_Gate_at_Berlin_Museum.jpg/75px-Ishtar_Gate_at_Berlin_Museum.jpg", "source_url": "http://commons.wikipedia.org/wiki/File:Ishtar_Gate_at_Berlin_Museum.jpg", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Ishtar_Gate_at_Berlin_Museum.jpg/300px-Ishtar_Gate_at_Berlin_Museum.jpg", "url_l": "http://upload.wikimedia.org/wikipedia/commons/e/e3/Ishtar_Gate_at_Berlin_Museum.jpg", "url_l_h": 768, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 223, "confidence": 0.58640000000000003, "url_s_h": 56, "attribution": "Picture taken at Zoological Garden of Berlin. (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:Giraffe-berlin-zoo.jpg\">Wikipedia</a>)", "description": "Picture taken at Zoological Garden of Berlin.", "license": "GNU Free Documentation License", "url_l_w": 2263, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Giraffe-berlin-zoo.jpg/75px-Giraffe-berlin-zoo.jpg", "source_url": "http://commons.wikipedia.org/wiki/File:Giraffe-berlin-zoo.jpg", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Giraffe-berlin-zoo.jpg/300px-Giraffe-berlin-zoo.jpg", "url_l": "http://upload.wikimedia.org/wikipedia/commons/c/cf/Giraffe-berlin-zoo.jpg", "url_l_h": 1680, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 205, "confidence": 0.56310400000000005, "url_s_h": 51, "attribution": "English: Berlin Map from 1688, from: Historischer Atlas von Berlin in VI Grundrissen nach gleichem Ma\u00dfstabe von 1415 bis 1800. Gezeichnet von J.M.F. Schmidt. Berlin: Simon Schropp und Kamp 1835. (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:ZLB-Berliner_Ansichten-Januar.jpg\">Wikipedia</a>)", "description": "English: Berlin Map from 1688, from: Historischer Atlas von Berlin in VI Grundrissen nach gleichem Ma\u00dfstabe von 1415 bis 1800. Gezeichnet von J.M.F. Schmidt. Berlin: Simon Schropp und Kamp 1835.", "license": "Public domain", "url_l_w": 4961, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/9/96/ZLB-Berliner_Ansichten-Januar.jpg/75px-ZLB-Berliner_Ansichten-Januar.jpg", "source_url": "http://commons.wikipedia.org/wiki/File:ZLB-Berliner_Ansichten-Januar.jpg", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/9/96/ZLB-Berliner_Ansichten-Januar.jpg/300px-ZLB-Berliner_Ansichten-Januar.jpg", "url_l": "http://upload.wikimedia.org/wikipedia/commons/9/96/ZLB-Berliner_Ansichten-Januar.jpg", "url_l_h": 3390, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 0, "confidence": 0.5, "url_s_h": 0, "attribution": "Est Berlin, Ostkreuz station - Berlin (Germany) (Photo credit: <a href=\"http://www.flickr.com/photos/19892856@N03/2358818265\">DanteAlighieri</a>)", "description": "Est Berlin, Ostkreuz station - Berlin (Germany)", "license": "License CreativeCommons NonCommercial ShareAlike", "url_l_w": 0, "url_s": "http://farm3.static.flickr.com/2184/2358818265_848ed0c268_s.jpg", "source_url": "http://www.flickr.com/photos/19892856@N03/2358818265", "url_m": "http://farm3.static.flickr.com/2184/2358818265_848ed0c268_m.jpg", "url_l": "http://farm3.static.flickr.com/2184/2358818265_848ed0c268.jpg", "url_l_h": 0, "url_s_w": 0, "url_m_w": 0}, {"url_m_h": 240, "confidence": 0.5, "url_s_h": 75, "attribution": "\u2588\u2550\u2550\u2550\u2550\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2500\u2500\u2500\u2500\u2500\u2500 Berlin wallrest Wilhelmstr -_- 300 times/day fotographt (Photo credit: <a href=\"http://www.flickr.com/photos/41894194462@N01/16750660\">! /streetart#__+__www.\u2665.tk \ufd3e\u0361\u0e4f\u032f\u0361\u0e4f\ufd3f</a>)", "description": "\u2588\u2550\u2550\u2550\u2550\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2500\u2500\u2500\u2500\u2500\u2500 Berlin wallrest Wilhelmstr -_- 300 times/day fotographt", "license": "License CreativeCommons NonCommercial", "url_l_w": 397, "url_s": "http://farm1.static.flickr.com/14/16750660_948d5d3017_s.jpg", "source_url": "http://www.flickr.com/photos/41894194462@N01/16750660", "url_m": "http://farm1.static.flickr.com/14/16750660_948d5d3017_m.jpg", "url_l": "http://farm1.static.flickr.com/14/16750660_948d5d3017.jpg", "url_l_h": 500, "url_s_w": 75, "url_m_w": 191}, {"url_m_h": 225, "confidence": 0.55643299999999996, "url_s_h": 56, "attribution": "english: Berlin Olympic Stadium during the Bundesliga-footballmatch Hertha BSC Berlin vs. Borussia Dortmund. german: Berliner Olympiastadion w\u00e4hrend des Bundesliga-Spiels Hertha BSC Berlin gg. Borussia Dortmund. (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:Berlin_Olympiastadion_during_footballmatch_herta_bsc_berlin_vs_borussia_dortmund_02_20070421.jpg\">Wikipedia</a>)", "description": "english: Berlin Olympic Stadium during the Bundesliga-footballmatch Hertha BSC Berlin vs. Borussia Dortmund. german: Berliner Olympiastadion w\u00e4hrend des Bundesliga-Spiels Hertha BSC Berlin gg. Borussia Dortmund.", "license": "CC Attribution ShareAlike 3.0 license", "url_l_w": 2272, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Berlin_Olympiastadion_during_footballmatch_herta_bsc_berlin_vs_borussia_dortmund_02_20070421.jpg/75px-Berlin_Olympiastadion_during_footballmatch_herta_bsc_berlin_vs_borussia_dortmund_02_20070421.jpg", "source_url": "http://commons.wikipedia.org/wiki/File:Berlin_Olympiastadion_during_footballmatch_herta_bsc_berlin_vs_borussia_dortmund_02_20070421.jpg", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Berlin_Olympiastadion_during_footballmatch_herta_bsc_berlin_vs_borussia_dortmund_02_20070421.jpg/300px-Berlin_Olympiastadion_during_footballmatch_herta_bsc_berlin_vs_borussia_dortmund_02_20070421.jpg", "url_l": "http://upload.wikimedia.org/wikipedia/commons/b/b4/Berlin_Olympiastadion_during_footballmatch_herta_bsc_berlin_vs_borussia_dortmund_02_20070421.jpg", "url_l_h": 1704, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 193, "confidence": 0.54860799999999998, "url_s_h": 48, "attribution": "English: Diagram of the population development in Berlin 1880\u20132007 Deutsch: Die Einwohnerentwicklung (Bev\u00f6lkerungsstand) von Berlin (schwarz) und der Metropolregion (grau) 1880 bis 2007. Daten u.a. aus http://www.statistik-berlin.de/statistiken/Bevoelkerung/inhalt-bevoelkerung.htm#be und http://www.statistik-berlin-brandenburg.de/daten/daten-bev1.pdf. (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:Berlin_Population_Development_1880-2007.svg\">Wikipedia</a>)", "description": "English: Diagram of the population development in Berlin 1880\u20132007 Deutsch: Die Einwohnerentwicklung (Bev\u00f6lkerungsstand) von Berlin (schwarz) und der Metropolregion (grau) 1880 bis 2007. Daten u.a. aus http://www.statistik-berlin.de/statistiken/Bevoelkerung/inhalt-bevoelkerung.htm#be und http://www.statistik-berlin-brandenburg.de/daten/daten-bev1.pdf.", "license": "GNU Free Documentation License", "url_l_w": 1024, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Berlin_Population_Development_1880-2007.svg/75px-Berlin_Population_Development_1880-2007.svg.png", "source_url": "http://commons.wikipedia.org/wiki/File:Berlin_Population_Development_1880-2007.svg", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Berlin_Population_Development_1880-2007.svg/300px-Berlin_Population_Development_1880-2007.svg.png", "url_l": "http://upload.wikimedia.org/wikipedia/commons/6/67/Berlin_Population_Development_1880-2007.svg", "url_l_h": 660, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 171, "confidence": 0.53724099999999997, "url_s_h": 43, "attribution": "View from Berliner Dom in the direction of Potsdamer Platz. (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:%C3%9Cber_den_D%C3%A4chern_von_Berlin.jpg\">Wikipedia</a>)", "description": "View from Berliner Dom in the direction of Potsdamer Platz.", "license": "Public domain", "url_l_w": 1155, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/5/53/%C3%9Cber_den_D%C3%A4chern_von_Berlin.jpg/75px-%C3%9Cber_den_D%C3%A4chern_von_Berlin.jpg", "source_url": "http://commons.wikipedia.org/wiki/File:%C3%9Cber_den_D%C3%A4chern_von_Berlin.jpg", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/5/53/%C3%9Cber_den_D%C3%A4chern_von_Berlin.jpg/300px-%C3%9Cber_den_D%C3%A4chern_von_Berlin.jpg", "url_l": "http://upload.wikimedia.org/wikipedia/commons/5/53/%C3%9Cber_den_D%C3%A4chern_von_Berlin.jpg", "url_l_h": 658, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 474, "confidence": 0.51317900000000005, "url_s_h": 118, "attribution": "the Kaiser Wilhelm Memorial Church in Berlin-Charlottenburg. (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:Ged%C3%A4chtniskirche1.JPG\">Wikipedia</a>)", "description": "the Kaiser Wilhelm Memorial Church in Berlin-Charlottenburg.", "license": "GNU Free Documentation License", "url_l_w": 1608, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Ged%C3%A4chtniskirche1.JPG/75px-Ged%C3%A4chtniskirche1.JPG", "source_url": "http://commons.wikipedia.org/wiki/File:Ged%C3%A4chtniskirche1.JPG", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Ged%C3%A4chtniskirche1.JPG/300px-Ged%C3%A4chtniskirche1.JPG", "url_l": "http://upload.wikimedia.org/wikipedia/commons/f/fd/Ged%C3%A4chtniskirche1.JPG", "url_l_h": 2539, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 131, "confidence": 0.51051299999999999, "url_s_h": 33, "attribution": "Berlin Mitte in the 21st century. Some landmarks from top left to bottom right: Hauptbahnhof (main station), Charit\u00e9 hospital, Berliner Dom, City hall, TV tower at Alexanderplatz, Spree river, East Side Gallery, O2 World. (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:SkylineBerlin.JPG\">Wikipedia</a>)", "description": "Berlin Mitte in the 21st century. Some landmarks from top left to bottom right: Hauptbahnhof (main station), Charit\u00e9 hospital, Berliner Dom, City hall, TV tower at Alexanderplatz, Spree river, East Side Gallery, O2 World.", "license": "GNU Free Documentation License", "url_l_w": 3888, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/SkylineBerlin.JPG/75px-SkylineBerlin.JPG", "source_url": "http://commons.wikipedia.org/wiki/File:SkylineBerlin.JPG", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/SkylineBerlin.JPG/300px-SkylineBerlin.JPG", "url_l": "http://upload.wikimedia.org/wikipedia/commons/d/d8/SkylineBerlin.JPG", "url_l_h": 1692, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 225, "confidence": 0.50622, "url_s_h": 56, "attribution": "Neue Nationalgalerie, Berlin, Germany, view from Tiergarten (Kulturforum) (Photo credit: <a href=\"http://commons.wikipedia.org/wiki/File:Neue_nationalgalerie_treppen.jpg\">Wikipedia</a>)", "description": "Neue Nationalgalerie, Berlin, Germany, view from Tiergarten (Kulturforum)", "license": "GNU Free Documentation License", "url_l_w": 640, "url_s": "http://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Neue_nationalgalerie_treppen.jpg/75px-Neue_nationalgalerie_treppen.jpg", "source_url": "http://commons.wikipedia.org/wiki/File:Neue_nationalgalerie_treppen.jpg", "url_m": "http://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Neue_nationalgalerie_treppen.jpg/300px-Neue_nationalgalerie_treppen.jpg", "url_l": "http://upload.wikimedia.org/wikipedia/commons/c/c3/Neue_nationalgalerie_treppen.jpg", "url_l_h": 480, "url_s_w": 75, "url_m_w": 300}, {"url_m_h": 160, "confidence": 0.5, "url_s_h": 75, "attribution": "Charlottenstrasse, Berlin, 1992 (Photo credit: <a href=\"http://www.flickr.com/photos/62464349@N00/459347793\">Genial23</a>)", "description": "Charlottenstrasse, Berlin, 1992", "license": "License CreativeCommons NonCommercial NoDerivs", "url_l_w": 500, "url_s": "http://farm1.static.flickr.com/250/459347793_d60238e6b1_s.jpg", "source_url": "http://www.flickr.com/photos/62464349@N00/459347793", "url_m": "http://farm1.static.flickr.com/250/459347793_d60238e6b1_m.jpg", "url_l": "http://farm1.static.flickr.com/250/459347793_d60238e6b1.jpg", "url_l_h": 334, "url_s_w": 75, "url_m_w": 240}], "signature": "<div class=\"zemanta-pixie\"><a class=\"zemanta-pixie-a\" href=\"http://www.zemanta.com/?px\" title=\"Enhanced by Zemanta\"><img class=\"zemanta-pixie-img\" src=\"http://img.zemanta.com/zemified_e.png?x-id=0cdef32c-8683-4bd1-bf0e-ee6fad3c0541\" alt=\"Enhanced by Zemanta\" /></a></div>", "keywords": [{"confidence": 0.78451400000000004, "scheme": "general", "name": "Berlin"}, {"confidence": 0.108131, "scheme": "general", "name": "Germany"}, {"confidence": 0.055939000000000003, "scheme": "general", "name": "States"}, {"confidence": 0.051561000000000003, "scheme": "general", "name": "Brandenburg Gate"}, {"confidence": 0.047156999999999998, "scheme": "general", "name": "Alexanderplatz"}, {"confidence": 0.041880000000000001, "scheme": "general", "name": "Travel and Tourism"}, {"confidence": 0.034986000000000003, "scheme": "general", "name": "Mitte"}, {"confidence": 0.031758000000000002, "scheme": "general", "name": "Amsterdam"}], "rid": "0cdef32c-8683-4bd1-bf0e-ee6fad3c0541", "categories": [], "rich_objects": [{"title": "Berlin", "url": "http://maps.google.com/maps?ll=52.5005555556,13.3988888889&spn=0.1,0.1&q=52.5005555556,13.3988888889 (Berlin)&t=h", "thumbnail_width": 75, "height": 250, "width": 300, "html": "<iframe width=\"300\" height=\"250\" frameborder=\"0\" scrolling=\"no\" marginheight=\"0\" marginwidth=\"0\" src=\"http://maps.google.com/?ie=UTF8&amp;center=52.5005555556,13.3988888889&amp;spn=0.1,0.1&amp;q=52.5005555556,13.3988888889 (Berlin)&amp;t=h&amp;output=embed&amp;sensor=false&amp;s=AARTsJqzARj-Z8VnW5pkPMLMmZbqrJcYpw\"></iframe><br/><small><a href=\"http://maps.google.com/?ie=UTF8&amp;center=52.5005555556,13.3988888889&amp;spn=0.1,0.1&amp;q=52.5005555556,13.3988888889 (Berlin)&amp;t=h&amp;source=embed&amp;sensor=false\" style=\"color:#0000FF;text-align:left\">View Larger Map</a></small>", "thumbnail_height": 75, "thumbnail_url": "http://maps.google.com/staticmap?size=300x250&sensor=false&center=52.5005555556,13.3988888889&zoom=12"}]}

		return rsp



