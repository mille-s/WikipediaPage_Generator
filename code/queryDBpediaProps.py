#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Query DBpedia for a given entity
# From ChatGPT. Prompt: "Thanks! Now please write a sparql query that can be used in Python to get all the properties related to Olga Bondareva on DBpedia. For example, birthDate, birthPlace, etc."
from SPARQLWrapper import SPARQLWrapper, JSON
import os
import re
import codecs
import sys
import pickle
import requests

# print('There are '+str(len(list_properties))+' different property labels.')
# print(sorted(list_properties))

# The following mapping list was obtained from this post: https://stackoverflow.com/questions/39850833/how-i-can-know-the-equivalent-dbpedia-and-wikidata-properties.
# I haven't checked all mappings yet.
dico_map_dbp_wkd = {'P743': 'abbreviation', 'P1457': 'absoluteMagnitude', 'P106': 'activity', 'P969': 'address', 'P742': 'alias', 'P69': 'almaMater', 'P1562': 'amgid', 'P85': 'anthem', 'P1215': 'apparentMagnitude', 'P84': 'architect', 'P149': 'architecturalStyle', 'P473': 'areaCode', 'P2046': 'areaTotal', 'P175': 'artist', 'P1086': 'atomicNumber', 'P50': 'author', 'P166': 'award', 'P1432': 'bSide', 'P144': 'basedOn', 'P607': 'battle', 'P1015': 'bibsysId', 'P569': 'birthDate', 'P1477': 'birthName', 'P19': 'birthPlace', 'P569': 'birthYear', 'P268': 'bnfId', 'P2769': 'budget', 'P176': 'builder', 'P36': 'capital', 'P509': 'causeOfDeath', 'P169': 'ceo', 'P40': 'child', 'P1057': 'chromosome', 'P344': 'cinematography', 'P27': 'citizenship', 'P131': 'city', 'P77': 'classis', 'P94': 'coatOfArms', 'P1159': 'coden', 'P462': 'colour', 'P86': 'composer', 'P1247': 'compressionRatio', 'P400': 'computingPlatform', 'P59': 'constellation', 'P186': 'constructionMaterial', 'P30': 'continent', 'P247': 'cosparId', 'P17': 'country', 'P131': 'county', 'P736': 'coverArtist', 'P880': 'cpu', 'P170': 'creator', 'P1029': 'crewMember', 'P177': 'crosses', 'P38': 'currency', 'P498': 'currencyCode', 'P585': 'date', 'P1036': 'dcc', 'P509': 'deathCause', 'P570': 'deathDate', 'P20': 'deathPlace', 'P287': 'designer', 'P178': 'developer', 'P2386': 'diameter', 'P708': 'diocese', 'P57': 'director', 'P746': 'disappearanceDate', 'P101': 'discipline', 'P575': 'discovered', 'P61': 'discoverer', 'P557': 'diseasesDb', 'P750': 'distributor', 'P131': 'district', 'P184': 'doctoralAdvisor', 'P185': 'doctoralStudent', 'P591': 'ecNumber', 'P1040': 'editing', 'P98': 'editor', 'P69': 'education', 'P232': 'einecsNumber', 'P2044': 'elevation', 'P1087': 'elo', 'P158': 'emblem', 'P108': 'employer', 'P582': 'endDate', 'P2348': 'era', 'P172': 'ethnicity', 'P1340': 'eyeColor', 'P53': 'family', 'P22': 'father', 'P41': 'flag', 'P156': 'followedBy', 'P155': 'follows', 'P571': 'formationDate', 'P112': 'foundedBy', 'P112': 'founder', 'P571': 'foundingDate', 'P1211': 'fuelSystem', 'P2031': 'functionStartYear', 'P408': 'gameEngine', 'P505': 'generalManager', 'P136': 'genre', 'P74': 'genus', 'P1125': 'giniCoefficient', 'P2139': 'gross', 'P1884': 'hairColor', 'P552': 'handedness', 'P159': 'headquarter', 'P2048': 'height', 'P610': 'highestPoint', 'P16': 'highwaySystem', 'P504': 'homeport', 'P229': 'iataAirlineCode', 'P238': 'iataLocationIdentifier', 'P230': 'icaoAirlineCode', 'P239': 'icaoLocationIdentifier', 'P494': 'icd10', 'P493': 'icd9', 'P1142': 'ideology', 'P110': 'illustrator', 'P345': 'imdbId', 'P227': 'individualisedGnd', 'P452': 'industry', 'P200': 'inflow', 'P374': 'inseeCode', 'P2109': 'installedCapacity', 'P1303': 'instrument', 'P361': 'isPartOf', 'P212': 'isbn', 'P957': 'isbn', 'P791': 'isil', 'P213': 'isniId', 'P297': 'iso31661Code', 'P298': 'iso31661Code', 'P299': 'iso31661Code', 'P218': 'iso6391Code', 'P219': 'iso6392Code', 'P220': 'iso6393Code', 'P635': 'istat', 'P157': 'killedBy', 'P75': 'kingdom', 'P620': 'landingDate', 'P619': 'launchDate', 'P448': 'launchSite', 'P375': 'launchVehicle', 'P244': 'lccnId', 'P118': 'league', 'P2043': 'length', 'P275': 'license', 'P131': 'locatedInArea', 'P126': 'maintainedBy', 'P286': 'manager', 'P176': 'manufacturer', 'P463': 'member', 'P486': 'meshId', 'P7779': 'militaryBranch', 'P25': 'mother', 'P135': 'movement', 'P434': 'musicBrainzArtistId', 'P86': 'musicBy', 'P175': 'musicalArtist', 'P138': 'namedAfter', 'P27': 'nationality', 'P1395': 'nciId', 'P349': 'ndlId', 'P2295': 'netIncome', 'P1567': 'nisCode', 'P409': 'nlaId', 'P800': 'notableWork', 'P649': 'nrhpReferenceNumber', 'P1128': 'numberOfEmployees', 'P2196': 'numberOfStudents', 'P605': 'nutsCode', 'P106': 'occupation', 'P771': 'ofsCode', 'P721': 'okatoCode', 'P3362': 'operatingIncome', 'P496': 'orcidId', 'P70': 'order', 'P91': 'orientation', 'P364': 'originalLanguage', 'P127': 'owner', 'P1830': 'owningOrganisation', 'P102': 'party', 'P638': 'pdb', 'P1448': 'personName', 'P119': 'placeOfBurial', 'P1082': 'populationTotal', 'P413': 'position', 'P281': 'postalCode', 'P6': 'primeMinister', 'P443': 'pronunciation', 'P131': 'province', 'P742': 'pseudonym', 'P264': 'recordLabel', 'P577': 'releaseDate', 'P140': 'religion', 'P551': 'residence', 'P2139': 'revenue', 'P650': 'rkdArtistsId', 'P2047': 'runtime', 'P906': 'selibrId', 'P131': 'settlement', 'P21': 'sex', 'P3373': 'sibling', 'P109': 'signature', 'P26': 'spouse', 'P161': 'starring', 'P580': 'startDate', 'P269': 'sudocId', 'P5973': 'synonym', 'P6': 'taoiseach', 'P54': 'team', 'P1653': 'terytCode', 'P245': 'ulanId', 'P1937': 'unloCode', 'P214': 'viafId', 'P990': 'voice', 'P2067': 'weight', 'P3039': 'wheelbase', 'P2049': 'width', 'P2257': 'year', 'P281': 'zipCode'}

class Triple:
  def __init__(self, prop, subj_value, obj_value):
    self.DBprop = prop
    self.DBsubj = subj_value
    self.DBobj = obj_value

# Make a class CheckedTriple (extends Triple) adds: expected, acutal, domain, range
class CheckedTriple(Triple):
  def __init__(self, prop, subj_value, obj_value, expected, actual, domain, range):
    super().__init__(prop, subj_value, obj_value)
    self.expected = expected
    self.actual = actual
    self.domain = domain
    self.range = range

def get_triples_seen(results, subj_name, triple_source, list_properties, ignore_properties_list, dico_map_dbp_wkd = dico_map_dbp_wkd, entity_is_sbjORobj = 'Subj', tripleValidation=False):
  # Process and print the results
  list_triple_objects = []
  for result in results:
    # property_uri is something like this: http://dbpedia.org/property/deathPlace
    property_uri = result["property"]["value"]
    # value is a string (1937-04-27) or an entity uri (http://dbpedia.org/resource/Saint_Petersburg)
    value = ''
    if triple_source == 'Ontology' or triple_source == 'Infobox':
      value = result["value"]["value"]
    elif triple_source == 'Wikidata':
      value = result["valueLabel"]["value"]
    # print(f'TEST prop/value: {property_uri} {value}')
    # Get the strings for property and object
    if len(value) > 0:
      url_triples = ''
      if triple_source == 'Ontology':
        url_triples = 'http://dbpedia.org/ontology/'
      elif triple_source == 'Infobox':
        url_triples = 'http://dbpedia.org/property/'
      elif triple_source == 'Wikidata':
        url_triples = 'http://www.wikidata.org/prop/direct/'
      # Look for uris that contain the target url
      if re.search(url_triples, property_uri):
        # Get the property name, which is at the end of the uri, after the last forward slash
        prop_name = property_uri.rsplit('/', 1)[1]
        obj_name = value
        if re.search('http://', value):
          obj_name = value.rsplit('/', 1)[1]
        obj_name_final = ''
        subj_name_final = ''
        if entity_is_sbjORobj == 'Subj':
          subj_name_final = subj_name
          obj_name_final = obj_name
        elif entity_is_sbjORobj == 'Obj':
          subj_name_final = obj_name
          obj_name_final = subj_name
        # If we use Wikidata as source, we need to map the Wikidata property label to the DBpedia one
        if triple_source == 'Wikidata':
          if prop_name in dico_map_dbp_wkd:
            prop_name = dico_map_dbp_wkd[prop_name]
        # print(f'TEST prop_name: {prop_name}')
        if prop_name in list_properties and not prop_name in ignore_properties_list:
          # print(f"{prop_name}: {obj_name}")
          if tripleValidation == False:
            triple_object = Triple(prop_name, subj_name_final, obj_name_final)
            list_triple_objects.append(triple_object)
          else:
            # To be implemented - get expected and actual values for domain and range.
            pass
  return list_triple_objects

def get_properties_of_entity(uri, look_for_entity_as_sbjORobj):
  # Define the DBpedia SPARQL endpoint URL
  sparql_endpoint = "https://dbpedia.org/sparql"
  sparql_query = None
  # Compose the SPARQL query
  if look_for_entity_as_sbjORobj == 'Subj':
    sparql_query = f"""
    SELECT ?property ?value
    WHERE {{
      <{uri}> ?property ?value.
    }}
    """
  elif look_for_entity_as_sbjORobj == 'Obj':
    sparql_query = f"""
    SELECT ?value ?property
    WHERE {{
      ?value ?property <{uri}>.
    }}
    """
  # Create a SPARQLWrapper object and set the query
  sparql = SPARQLWrapper(sparql_endpoint)
  sparql.setQuery(sparql_query)
  # Set the return format to JSON
  sparql.setReturnFormat(JSON)
  # Execute the query and parse the results
  results = sparql.query().convert()
  results_final = results["results"]["bindings"]
  return results_final

def get_wikidata_id(entity_label):
  # Define the Wikidata API endpoint
  wikidata_api_url = "https://www.wikidata.org/w/api.php"

  # Set the parameters for the API request
  params = {
    "action": "wbsearchentities",
    "format": "json",
    "language": "en",  # You can change the language if needed
    "search": entity_label,
  }

  try:
    # Send a GET request to the Wikidata API
    response = requests.get(wikidata_api_url, params=params)
    response.raise_for_status()
    # Parse the JSON response
    data = response.json()
    # Check if any entities were found
    if "search" in data and data["search"]:
      # Get the first entity (assuming it's the most relevant)
      entity_id = data["search"][0]["id"]
      return entity_id
    return None  # Entity not found

  except requests.exceptions.RequestException as e:
    print("Error connecting to the Wikidata API:", e)
    return None

def get_wikidata_properties_of_entity(wikidata_id, look_for_entity_as_sbjORobj):
  """
  Retrieves properties and their values for a given Wikidata entity.
  Args:
    wikidata_id: The Wikidata ID of the entity (e.g., "Q12345").
  Returns:
    A list of dictionaries, where each dictionary represents a property and its value.
  """
  sparql_endpoint = "https://query.wikidata.org/sparql"
  sparql_query = None
  if look_for_entity_as_sbjORobj == 'Subj':
    sparql_query = f"""
      SELECT ?property ?valueLabel
      WHERE {{
        wd:{wikidata_id} ?property ?value .
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
      }}
    """
  elif look_for_entity_as_sbjORobj == 'Obj':
    sparql_query = f"""
      SELECT ?valueLabel ?property
      WHERE {{
        ?value ?property wd:{wikidata_id}.
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
      }}
    """
  sparql = SPARQLWrapper(sparql_endpoint)
  sparql.setQuery(sparql_query)
  sparql.setReturnFormat(JSON)
  results = sparql.query().convert()
  # properties = []
  # for result in results["results"]["bindings"]:
  #   property_uri = result["property"]["value"]
  #   value_label = result["valueLabel"]["value"]
  #   properties.append({"property": property_uri, "value": value_label})
  # print(properties)
  results_final = results["results"]["bindings"]
  return results_final

  # if __name__ == "__main__":
  #   props_list_path = sys.argv[1]
  #   entity_name = sys.argv[2]
  #   triple_source = sys.argv[3]
  #   ignore_properties_str = sys.argv[4]
  #   out_folder = sys.argv[5]

def get_dbpedia_properties(props_list_path, entity_name, triple_source, ignore_properties_str, get_triples_where_entity_is_subj = True, get_triples_where_entity_is_obj = False):
  ignore_properties_input = ignore_properties_str.split(',')
  ignore_properties_list = []
  for ignored_property in ignore_properties_input:
    ignore_properties_list.append(ignored_property.strip())

  # Read file with all covered properties
  fd = codecs.open(props_list_path, 'r', 'utf-8')
  lines_properties = fd.readlines()
  list_properties = []
  for line_properties in lines_properties:
    line_prop_list = line_properties.strip().split('-')
    for prop in line_prop_list:
      list_properties.append(prop)

  selected_uri = "http://dbpedia.org/resource/"+entity_name
  # selected_uri = "http://dbpedia.org/resource/Olga_Bondareva"
  subj_name = selected_uri.rsplit('/', 1)[1]
  # Get all properties for entity
  results_subj = ''
  results_obj = ''
  if triple_source == 'Ontology' or triple_source == 'Infobox':
    if get_triples_where_entity_is_subj == True:
      results_subj = get_properties_of_entity(selected_uri, 'Subj')
    if get_triples_where_entity_is_obj == True:
      results_obj = get_properties_of_entity(selected_uri, 'Obj')
  elif triple_source == 'Wikidata':
    wikidata_id = get_wikidata_id(entity_name)
    # print(wikidata_id)
    if get_triples_where_entity_is_subj == True:
      results_subj = get_wikidata_properties_of_entity(wikidata_id, 'Subj')
    if get_triples_where_entity_is_obj == True:
      results_obj = get_wikidata_properties_of_entity(wikidata_id, 'Obj')
      
  # Get properties covered by the generator and their respective objets
  list_triple_objects = []
  if get_triples_where_entity_is_subj == True:
    list_triple_objects.extend(get_triples_seen(results_subj, subj_name, triple_source, list_properties, ignore_properties_list, entity_is_sbjORobj = 'Subj', tripleValidation=False))
  if get_triples_where_entity_is_obj == True:
    list_triple_objects.extend(get_triples_seen(results_obj, subj_name, triple_source, list_properties, ignore_properties_list, entity_is_sbjORobj = 'Obj', tripleValidation=False))

  # Check
  # print('Subject: '+subj_name)
  # for triple_object in list_triple_objects:
  #   print(triple_object.DBprop+' : '+triple_object.DBobj)

  list_prop = []
  list_obj = []
  list_propObj =[]

  for n, triple_object in enumerate(list_triple_objects):
    list_prop.append(triple_object.DBprop)
    list_obj.append(triple_object.DBobj)
    list_propObj.append(str(n)+' - '+triple_object.DBprop+': '+triple_object.DBobj)

  # print(list_propObj)
  return list_triple_objects, list_propObj, list_obj

  # with open(os.path.join(out_folder, 'list_PropObj'), 'wb') as fh:
  #   pickle.dump(list_propObj, fh)
    
  # with open(os.path.join(out_folder, 'list_triple_objects'), 'wb') as fh:
  #   pickle.dump(list_triple_objects, fh)
    
  # with open(os.path.join(out_folder, 'list_obj'), 'wb') as fh:
  #   pickle.dump(list_obj, fh)
