Wrapper service for Zemanta API
===============

* Supports NIF
* Additional output formats for Zemanta: n3, ntriple, turtle
* Supports GET, POST

Requirements
---------
* Zemanta API key: you can register at Zemanta's developer network <http://developer.zemanta.com/member/register/>
* virtualenv and pip

Check [Getting started with Virtualenv and pip](http://jontourage.com/2011/02/09/virtualenv-pip-basics/)

Dependencies
------------
* Flask
* rdflib
* rdflib_rdfjson
* simplejson


Install
-----------
1. Set up and activate virtualenv

        virtualenv mywrapper

2. Clone this repo in it

3. Install dependencies using requirements.txt

        pip install -r requirements.txt


Run
------------
To run the wrapper service run service.py. It starts by default on localhost on port 5000, but you can easily change this.

    python service.py


Use
-------------
Wrapper supports all Zemanta parameters and additional NIF parameters. You can set Zemanta api_key in the service.py or pass it as a parameter.
Zemanta supports only plain text as an input, therefore nif parameter input-type is defaulted to _text_

### NIF parameters
<table>
  <tr>
    <th>Parameter</th><th>values</th>
  </tr>
  <tr>
    <td>input-type</td><td>text</td>
  </tr>
  <tr>
    <td>input</td><td>&lt;url encoded plain text&gt;</td>
  </tr>
  <tr>
    <td>format</td><td>rdfxml | ntriples | turtle | n3 | json  </td>
  </tr>
  <tr>
    <td>nif</td><td>true</td>
  </tr>
</table>

### Using the service as a NIF wrapper
* set parameter _nif=true_
* use either _input_ or _text_ parameter for supplying text
* specify nif output format
* provide your api_key

Defaults for Zemanta API:
* method=zemanta.suggest_markup
* format=json (this is not the same output format that will be used for results)

Examples:

http://127.0.0.1:5000/service?input=I+Love+Berlin&format=n3&nif=true&api_key=your-api-key-here

http://127.0.0.1:5000/service?input=I+Love+Berlin&format=n3&nif=true&api_key=your-api-key-here


### Using the service as a RDF wrapper
* provide all required parameters specified in [Zemanta API documentation](http://developer.zemanta.com/docs/)
* in addition to ouput formats specified there, you can also use _n3_, _ntriple_, or _turtle_

Example:

http://127.0.0.1:5000/service?text=I+Love+Berlin&format=n3&method=zemanta.suggest&api_key=your-api-key-here
