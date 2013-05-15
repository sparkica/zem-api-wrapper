
NIF wrapper for Zemanta API
===============

Important
---------
Requires Zemanta API key.

Dependencies
------------
* Flask
* rdflib
* rdflib_rdfjson
* simplejson


How to use
-----------
* Set up virtualenv
* Install dependencies using requirements.txt
* run: python service.py

Supports: GET, POST

Input parameters:
<table>
  <tr>
    <th>NIF parameter</th><th>values</th>
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

