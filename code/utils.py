#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
import codecs
import json
from xml.dom import minidom
import re
import glob
import xmltodict
from colored import Fore, Back, Style
# from google.colab import files

class TripleSet:
  def __init__(self, triples_list, category, eid, shape, shape_type):
    self.triples = triples_list
    self.category = category
    self.eid = eid
    self.size = len(triples_list)
    self.shape = shape
    self.shape_type = shape_type
    self.entities_by_frequency = []
    # The main entity is the one that has the most occurrences as subject or object (if several have the same num of occurrences, "max" returns the first one)
    entity_counter_dico = {}
    for triple in self.triples:
      if triple.DBsubj not in entity_counter_dico.keys():
        entity_counter_dico[triple.DBsubj] = 1
      else:
        entity_counter_dico[triple.DBsubj] += 1
      if triple.DBobj not in entity_counter_dico.keys():
        entity_counter_dico[triple.DBobj] = 1
      else:
        entity_counter_dico[triple.DBobj] += 1
    self.entities_by_frequency = sorted(entity_counter_dico, key=entity_counter_dico.get, reverse=True)
    # print(entity_counter_dico)
    # print(self.entities_by_frequency)

class Triple_withID:
  def __init__(self, prop, subj_value, obj_value, triple_id):
    self.DBprop = prop
    self.DBsubj = subj_value
    self.DBobj = obj_value
    self.id = triple_id
    
def clear_files(folder):
  """Function to clear files from a folder."""
  if os.path.exists(folder) and os.path.isdir(folder):
    for filename in os.listdir(folder):
      file_path = os.path.join(folder, filename)
      try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
          os.unlink(file_path)
        elif os.path.isdir(file_path):
          shutil.rmtree(file_path)
      except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))

def clear_folder(folder):
  "Function to clear whole folders."
  if os.path.exists(folder) and os.path.isdir(folder):
    try:
      shutil.rmtree(folder)
    except Exception as e:
      print('Failed to delete %s. Reason: %s' % (folder, e))

def get_first_n_instances_of_props(list_triple_objects, max_num_of_instances_of_prop_desired, properties_that_can_happen_once_only):
  """
  Function that selects the first n occurrences of a triple that contains the same property.
  Input list_triple_objects: a list of triple objects, each triple should have 3 attributes: DBsubj, DBprop, DBobj.
  Input max_num_of_instances_of_prop_desired: an integer that specifies the maximum number of occurrences of each property in the triple set.
  Input properties_that_can_happen_once_only; a list of property labels that cannot have 2 or more values for the same subject, even though they do have more than one on the queried resource.
  Output: a list of ist indices, e.g [0, 1, 2, 3, 4, 5, 6, 8, 9].
  """    
  # Dico to keep track of properties already added for each subject
  dico_dbSubj_properties = {}
  # Dico to keep track of how many times each property is found in the triple set
  dico_num_instances_of_prop_found = {}

  selected_properties = []
  for i, triple_object in enumerate(list_triple_objects):
    # Add property to the list of properties in the triple set and initialise count
    if triple_object.DBprop not in dico_num_instances_of_prop_found.keys():
      dico_num_instances_of_prop_found[triple_object.DBprop] = 1
      selected_properties.append(i)
    # For the second and more instance of a property, increase counter and if the resulting number is below that of the maximum number of instances of each property specified in the input, then add the id to the selected list
    else:
      dico_num_instances_of_prop_found[triple_object.DBprop] += 1
      if dico_num_instances_of_prop_found[triple_object.DBprop] <= max_num_of_instances_of_prop_desired:
        # Only add a 2nd or 3rd property if (i) that property is not in the list of props that can happen only once, or (ii) if it is in that list but the subject doesn't already have that property in the triple set
        if (triple_object.DBprop not in properties_that_can_happen_once_only) or (triple_object.DBsubj not in dico_dbSubj_properties.keys()) or (triple_object.DBprop not in dico_dbSubj_properties[triple_object.DBsubj]):
          selected_properties.append(i)
    
    # Now that we processed a triple, fill up dico_dbSubj_properties
    # For the first instance of a property, create dico entry and add id of triple_object to the list of selected properties
    if triple_object.DBsubj not in dico_dbSubj_properties.keys():
      dico_dbSubj_properties[triple_object.DBsubj] = []
    # Add property to the list of properties used for a subject
    if triple_object.DBprop not in dico_dbSubj_properties[triple_object.DBsubj]:
      dico_dbSubj_properties[triple_object.DBsubj].append(triple_object.DBprop)
  # print(dico_dbSubj_properties)
  return selected_properties

def get_prop_index_from_table(selected_properties, list_triple_objects):
  """ Generate list of indices of properties selected by user (index in the list of Triple objects that contains all retrieved triples)
  selected_poperties is a widgets.SelectMultiple(...) thingy, as on the following line
    SelectMultiple(description='Properties', index=(0, 1, 2), layout=Layout(width='642px'), options=('0 - birthPlace: Lecce', '1 - birthDate: 1973-08-19', '2 - managerClub: Chennaiyin_FC', '3 - height: 193.0', '4 - height: 1.93', '5 - position: Defender_(association_football)', '6 - team: S.S._Lazio', '7 - team: Trapani_Calcio', '8 - team: A.C.R._Messina', '9 - team: Everton_F.C.', '10 - team: Carpi_FC_1909', '11 - team: Italy_national_football_team', '12 - team: Chennaiyin_FC', '13 - team: Inter_Milan', '14 - team: Lupa_Roma_F.C.', '15 - team: Perugia_Calcio', '16 - team: S.C._Marsala'), rows=17, value=('0 - birthPlace: Lecce', '1 - birthDate: 1973-08-19', '2 - managerClub: Chennaiyin_FC'))
  list_triple_objects is a list of object of class Triple, as defined in the queryDBpediaProps module
  """
  properties_selected_by_user = []
  # In case we already receive the IDs, just copy the list
  if isinstance(selected_properties, list):
    properties_selected_by_user = selected_properties
  # Otherwise, extract the list from the data structure
  else:
    if len(selected_properties.value) == 0:
      x = 0
      while x < len(list_triple_objects):
        properties_selected_by_user.append(x)
        x += 1
    else:
      for selected_property in selected_properties.value:
        properties_selected_by_user.append(int(selected_property.split(' - ')[0]))
  return properties_selected_by_user

def removeReservedCharsFileName(entityName):
  # reservedChars = ['#', '%', '&', '\{', '\}', '\\', '<', '>', '\*', '\?', '/', ' ', '\$', '!', "'", '"', ':', '@', '\+', '`', '\|', '=']
  newEntityName = str(entityName)
  # for reservedChar in reservedChars:
  while re.search(r'[#%&\{\}\\<>\*\?/ \$!\'":@\+`\|=]', newEntityName):
    newEntityName = re.sub(r'[#%&\{\}\\<>\*\?/ \$!\'":@\+`\|=]', "", newEntityName)
  return newEntityName

def create_xml(triple_objects, properties_selected_by_user, input_category, triple2predArgPath, entity_name = None, eid = 1):
  """ Create the XML file with the triples to be converted to PredArg. """
  n = len(properties_selected_by_user)
  list_triples_text = []
  # Create nodes
  root = minidom.Document()
  xml = root.createElement('benchmark')
  entries = root.createElement('entries')
  entry = root.createElement('entry')
  original_ts = root.createElement('originaltripleset')
  modified_ts = root.createElement('modifiedtripleset')
  lex = root.createElement('lex')
  # Create structure between nodes
  root.appendChild(xml)
  xml.appendChild(entries)
  entries.appendChild(entry)
  entry.appendChild(original_ts)
  entry.appendChild(modified_ts)
  entry.appendChild(lex)
  # Create main attributes
  entry.setAttribute('category', str(input_category))
  entry.setAttribute('eid', str(eid))
  entry.setAttribute('shape', '(X (X) (X) (X) (X))')
  entry.setAttribute('shape-type', 'sibling')
  entry.setAttribute('size', str(n))
  # Create lex attributes
  lex.setAttribute('comment', '')
  lex.setAttribute('lid', 'id1')
  lex.setAttribute('lang', 'ga')
  fake_text = root.createTextNode('Some Irish text.')
  lex.appendChild(fake_text)
  # Fill in otriple and mtriple fields with the same info
  x = 0
  dbsubj = 'Ukn'
  while x < len(triple_objects):
  # for triple_object in triple_objects:
    triple_object = triple_objects[x]
    # If there is no info about the entity, use the first triple's subject as filename
    if x == 0:
      if entity_name == None:
        dbsubj = str(triple_object.DBsubj)
      else:
        dbsubj = entity_name
    if x in properties_selected_by_user:
      text1 = root.createTextNode(triple_object.DBsubj+' | '+triple_object.DBprop+' | '+triple_object.DBobj)
      list_triples_text.append(f'{triple_object.DBsubj} | {triple_object.DBprop} | {triple_object.DBobj}')
      otriple = root.createElement('otriple')
      original_ts.appendChild(otriple)
      otriple.appendChild(text1)
      text2 = root.createTextNode(triple_object.DBsubj+' | '+triple_object.DBprop+' | '+triple_object.DBobj)
      mtriple = root.createElement('mtriple')
      modified_ts.appendChild(mtriple)
      mtriple.appendChild(text2)
    x += 1
  xml_str = root.toprettyxml(indent ="  ")
  save_path_file = os.path.join(triple2predArgPath, str(removeReservedCharsFileName(dbsubj))+".xml")
  with open(save_path_file, "w") as f:
      f.write(xml_str)
  return list_triples_text 

def create_GPT_Prompt(entity_name, language, list_triples_text, dest_folder):
  language_map = {'EN': 'English', 'GA': 'Irish', 'ES': 'Spanish'}
  if not os.path.exists(dest_folder):
    os.makedirs(dest_folder)
  with codecs.open(os.path.join(dest_folder, f'GPT_prompt_{entity_name}.txt'), 'w', 'utf-8') as fo_gpt:
    lg_text = language_map[language]
    line = f'Write the following triples as fluent {lg_text} text.\nTriples:"""\n'
    # line = 'Please verbalise the following list of DBpedia triples in English in a Wikipedia style; do not add any content, do not remove any content.\nTriples:\n'
    # line = 'Please verbalise the following list of DBpedia triples in English in a Wikipedia style; do not add any content, do not remove any content.\n'
    for triple_text in list_triples_text:
      line = line + str(triple_text)
      line = f'{line}\n'
    line = f'{line}"""\nText:'
    fo_gpt.write(line)

def count_expected_texts(root_folder):
  FORGe_log = open(os.path.join(root_folder, 'FORGe', 'log', 'summary.txt'), 'r')
  lines_log = FORGe_log.readlines()
  # Get number of expected texts
  count_strs_all_FORGe = 0
  for line in lines_log:
    if line.startswith('Outputs: '):
      count_strs_all_FORGe = int(line.strip().split('Outputs: ')[-1])
  return count_strs_all_FORGe

def create_jsons_SubjAndObj(entity_name, list_obj, path_triple2predArg):
  """ Creates json files needed by the code that gets the class and gender info """
  # In the current Wikipedia page generator, only one subject is possible
  list_subj = []
  list_subj.append(entity_name)
  list_subj_str = '"'+str(list_subj)+'"'
  list_obj_str = '"'+str(list_obj)+'"'
  json_subj = json.dumps(list_subj)
  json_obj = json.dumps(list_obj)
  filepath_subj = os.path.join(path_triple2predArg, 'classMembership', 'new_subj_values.json')
  filepath_obj = os.path.join(path_triple2predArg, 'classMembership', 'new_obj_values.json')
  with codecs.open(filepath_subj, 'w', 'utf-8') as fo1:
    fo1.write(json_subj)
  with codecs.open(filepath_obj, 'w', 'utf-8') as fo2:
    fo2.write(json_obj)
  return filepath_subj, filepath_obj

def prepare_variables_xml2CoNLL_conversion(str_PredArg_folder, language, entity_name, path_triple2predArg):
  # empty FORGe input folder
  clear_files(str_PredArg_folder)
  language_t2p = language.lower()
  # The following line needs a forward slash at the ends; I think this path is being concatenated ater on
  path_t2p_out = os.path.join(path_triple2predArg, 'out/')
  clear_files(path_t2p_out)
  name_conll_templates = ''
  if language == 'GA':
    name_conll_templates = '221130_WebNLG23_GA.conll'
  else:
    name_conll_templates = '230528-WebNLG23_EN.conll'
  new_triple2predArg = path_triple2predArg+'/'
  newEntityName = removeReservedCharsFileName(entity_name)
  return new_triple2predArg, name_conll_templates, path_t2p_out, language_t2p, newEntityName

def check_postProcessed_outputs(root_folder, prefinal_output_folder, count_strs_all_FORGe):
  list_filepaths = glob.glob(os.path.join(prefinal_output_folder, '*_postproc.txt'))
  count_strs_all_postproc = []
  for filepath in sorted(list_filepaths):
    count_strs_all = 0
    head, tail = os.path.split(filepath)
    fd = codecs.open(filepath, 'r', 'utf-8')
    lines = fd.readlines()
    x = 0
    for line in lines:
      if not line == '\n':
        count_strs_all += 1
      x += 1
    count_strs_all_postproc.append(count_strs_all)
  
  with codecs.open(os.path.join(root_folder, 'FORGe', 'log', 'summary.txt'), 'a', 'utf-8') as fo:
    fo.write('\nPost-processing debug\n==================\n\n')
    if not sum(count_strs_all_postproc) == count_strs_all_FORGe:
      print('\nERROR! Mismatch with FORGe outputs!')
      fo.write('ERROR! Mismatch with FORGe outputs!\n')
    print('\nThere are '+str(sum(count_strs_all_postproc))+' texts.')
    fo.write('There are '+str(sum(count_strs_all_postproc))+' texts.\n')
    print('Texts per file: '+str(count_strs_all_postproc))
    fo.write('Texts per file: '+str(count_strs_all_postproc)+'\n')
    fo.write('---------------------------------\n')

def concatenate_files(root_folder, morph_output_folder, temp_input_folder_morph, split, language, count_strs_all_FORGe):
  list_clean_outputs = ''
  if language == 'GA':
    list_clean_outputs = glob.glob(os.path.join(morph_output_folder, '*_out_postproc.txt'))
  else:
    list_clean_outputs = glob.glob(os.path.join(temp_input_folder_morph, split, '*_postproc.txt'))
  print(list_clean_outputs)
  
  filename = 'all_'+language+'_'+split+'_out.txt'
  
  with codecs.open(filename, 'w', 'utf-8') as outfile:
    # Files need to be sorted to be concatenated in the right order
    for fname in sorted(list_clean_outputs):
      print('Processing '+fname)
      with open(fname) as infile:
        outfile.write(infile.read())
  
  # Check
  with codecs.open(os.path.join(root_folder, 'FORGe', 'log', 'summary.txt'), 'a', 'utf-8') as fo:
    fo.write('\nConcatenate debug\n==================\n\n')
    count_texts_all = len(codecs.open(filename).readlines())
    if not count_texts_all == count_strs_all_FORGe:
      print('\nERROR! Mismatch with FORGe outputs!')
      fo.write(('ERROR! Mismatch with FORGe outputs!\n'))
    print('\nThere are '+str(count_texts_all)+' texts.')
    fo.write('There are '+str(count_texts_all)+' texts.\n')

  return filename

def concatenate_files_UI(root_folder, morph_output_folder, temp_input_folder_morph, split, language, count_strs_all_FORGe, entity_name, dest_folder):
  if not os.path.exists(dest_folder):
    os.makedirs(dest_folder)
    
  list_clean_outputs = ''
  if language == 'GA':
    list_clean_outputs = glob.glob(os.path.join(morph_output_folder, '*_out_postproc.txt'))
  else:
    list_clean_outputs = glob.glob(os.path.join(temp_input_folder_morph, split, '*_postproc.txt'))
  print(list_clean_outputs)
  
  filename = entity_name+'_'+language+'.txt'
  
  with codecs.open(os.path.join(dest_folder, filename), 'w', 'utf-8') as outfile:
    # Files need to be sorted to be concatenated in the right order
    for fname in sorted(list_clean_outputs):
      print('Processing '+fname)
      with open(fname) as infile:
        outfile.write(infile.read())
  
  # Check
  with codecs.open(os.path.join(root_folder, 'FORGe', 'log', 'summary.txt'), 'a', 'utf-8') as fo:
    fo.write('\nConcatenate debug\n==================\n\n')
    count_texts_all = len(codecs.open(os.path.join(dest_folder, filename)).readlines())
    if not count_texts_all == count_strs_all_FORGe:
      print('\nERROR! Mismatch with FORGe outputs!')
      fo.write(('ERROR! Mismatch with FORGe outputs!\n'))
    print('\nThere are '+str(count_texts_all)+' texts.')
    fo.write('There are '+str(count_texts_all)+' texts.\n')

  return filename

def balanced_split_with_max(N1, N2):
  """
  Function that splits as evenly as possible a number N1 into smaller numbers each as close as possible to another number N2 without being larger than N2.
  For example, if N1 == 50 and N2 == 20, the output is 17, 17 16.
  """
  assert N1 >= N2, "N1 must be greater than or equal to N2"
  assert N2 >= 1, "N1 must be at least 1"
  # Start with the minimal number of parts needed to respect the max constraint
  for k in range(N1 // N2, N1 + 1):
    # print(f'k: {k}')
    base = N1 // k
    remainder = N1 % k
    # print(f'N1//N2, N1+1: {N1//N2}, {N1+1}')
    # print(f'base: {base}')
    # print(f'remainder: {remainder}')
    # print()
    # The largest part will be base + 1 (if remainder > 0)
    if base + (1 if remainder > 0 else 0) <= N2:
      result = [base + 1] * remainder + [base] * (k - remainder)
      return result

def extract_info_from_WebNLG_XML (path_input_XML):
  """
  path_input_XML: Path to an XML file that contains triple sets, e.g. as provided in the WebNLG shared tasks.
  returns a list of TripleSet objects. Each object contains as attributes: triples (a list of Triple objects), category, eid, size, shape, main_entity
  """
  with codecs.open(path_input_XML, 'r', 'utf-8') as file:
    XML_file = file.read()
    XML_dict = xmltodict.parse(XML_file)
    print(f'    Reading file {path_input_XML}..')
    # triple_sets_list will be a list of objects of class TripleSet
    total_number_of_triples = 0
    triple_sets_list = []    
    if isinstance(XML_dict['benchmark']['entries']['entry'], list):
      print(f"      There are {len(XML_dict['benchmark']['entries']['entry'])} inputs in the original XML file.")
      for entry in XML_dict['benchmark']['entries']['entry']:
        category = entry['@category']
        eid = entry['@eid']
        size = entry['@size']
        shape = entry['@shape']
        shape_type = entry['@shape-type']
        # mtriples_list will be a list of objects of class Triple
        mtriples_list = []
        # Get modified triples
        if isinstance(entry['modifiedtripleset']['mtriple'], list):
          for triple_id, mtriple in enumerate(entry['modifiedtripleset']['mtriple']):
            triple_object = Triple_withID(mtriple.split(' | ')[1], mtriple.split(' | ')[0], mtriple.split(' | ')[2], triple_id)
            mtriples_list.append(triple_object)
        else:
          mtriples_list.append(entry['modifiedtripleset']['mtriple'])
        assert int(size) == len(mtriples_list), f'Error: found size {size} but found {len(mtriples_list)} triples.'
        total_number_of_triples += len(mtriples_list)
        # Create object of class TripleSet
        tripleSet_object = TripleSet(mtriples_list, category, eid, shape, shape_type)
        triple_sets_list.append(tripleSet_object)
    else:
      print(f"      There is 1 input in the original XML file.")
      category = XML_dict['benchmark']['entries']['entry']['@category']
      eid = XML_dict['benchmark']['entries']['entry']['@eid']
      size = XML_dict['benchmark']['entries']['entry']['@size']
      shape = XML_dict['benchmark']['entries']['entry']['@shape']
      shape_type = XML_dict['benchmark']['entries']['entry']['@shape-type']
      # Block repeated from above
      # mtriples_list will be a list of objects of class Triple
      mtriples_list = []
      # Get modified triples
      if isinstance(XML_dict['benchmark']['entries']['entry']['modifiedtripleset']['mtriple'], list):
        for triple_id, mtriple in enumerate(XML_dict['benchmark']['entries']['entry']['modifiedtripleset']['mtriple']):
          triple_object = Triple_withID(mtriple.split(' | ')[1], mtriple.split(' | ')[0], mtriple.split(' | ')[2], triple_id)
          mtriples_list.append(triple_object)
      else:
        mtriples_list.append(XML_dict['benchmark']['entries']['entry']['modifiedtripleset']['mtriple'])
      assert int(size) == len(mtriples_list), f'Error: found size {size} but found {len(mtriples_list)} triples.'
      total_number_of_triples += len(mtriples_list)
      # Create object of class TripleSet
      tripleSet_object = TripleSet(mtriples_list, category, eid, shape, shape_type)
      triple_sets_list.append(tripleSet_object)

    print(f"      There are {total_number_of_triples} input triples in the original XML file.")

  return triple_sets_list

def sort_WebNLG_XMLs (path_input_XML, path_DBprops_count):
  """
  path_input_XML: Path to an XML file that contains triple sets, e.g. as provided in the WebNLG shared tasks. The code expects that all triples mention the same entity, as subject or object.
  path_DBprops_count: Path to a json file that contains DBpedia properties as keys (e.g. "http://dbpedia.org/ontology/birthPlace") and number of occurrences on DBpedia as values (e.g 1486579).
  This function returns a list of TripleSets objects. TripleSet.triples contains Triple objects; in each triple set, Triple objects are sorted by "importance" (i.e. sorted by frequency of entity in the triple set, and by frequency of property on DBpedia)
  """
  print('  Sorting triples sets by frequency of entity in the triple set, and by frequency of respective properties on DBpedia...')
  dico_count_occurrences_dbp_props = json.loads(codecs.open(path_DBprops_count, 'r', 'utf-8').read())
  triple_sets_list = extract_info_from_WebNLG_XML (path_input_XML)
  new_triple_set_Objects_list = []
  total_number_of_triples = 0
  for triple_set in triple_sets_list:
    # print(triple_set.eid, triple_set.category, triple_set.size, triple_set.entities_by_frequency[0])
    # Make a list where we will store the order of the triples using their index in the triple_set list
    # E.g. list_triple_indices = [0, 4, 5, 2, 3, 1]
    list_triple_indices = []
    # Process entities by their respective importance in the triple set, so the most frequently found entity will go first, the second most frequently found will go second, and so on.
    for entity_name in triple_set.entities_by_frequency:
      # print(f'  {entity_name}')
      # Make a list of property labels with the http://dbpedia.org/ontology/ prefix, one with the properties where the entity is subject, and one with the properties where the entity is object
      # The properties in the ..._Subj list will go first, the properties in the ..._Obj list will go after. 
      list_dico_count_occurrences_dbp_props_keys_Subj = [[f'http://dbpedia.org/ontology/{triple.DBprop}', triple.id] for triple in triple_set.triples if triple.DBsubj == entity_name]
      list_dico_count_occurrences_dbp_props_keys_Obj = [[f'http://dbpedia.org/ontology/{triple.DBprop}', triple.id] for triple in triple_set.triples if triple.DBobj == entity_name]
      # Order that list according to the count in path_DBprops_count
      sorted_list_dico_count_occurrences_dbp_props_keys_Subj = sorted(list_dico_count_occurrences_dbp_props_keys_Subj, key=lambda x: dico_count_occurrences_dbp_props[x[0]], reverse=True)
      sorted_list_dico_count_occurrences_dbp_props_keys_Obj = sorted(list_dico_count_occurrences_dbp_props_keys_Obj, key=lambda x: dico_count_occurrences_dbp_props[x[0]], reverse=True)
      # print(f'    {sorted_list_dico_count_occurrences_dbp_props_keys_Subj}')
      # print(f'    {sorted_list_dico_count_occurrences_dbp_props_keys_Obj}')
      # Now put all the triple indices for the current entity in list_triple_indices, starting with the triples in which the entity is subject
      for list_triple_indices_Subj in sorted_list_dico_count_occurrences_dbp_props_keys_Subj:
        # To avoid duplicated triples:
        if list_triple_indices_Subj[1] not in list_triple_indices:
          list_triple_indices.append(list_triple_indices_Subj[1])
      for list_triple_indices_Obj in sorted_list_dico_count_occurrences_dbp_props_keys_Obj:
        if list_triple_indices_Obj[1] not in list_triple_indices:
          list_triple_indices.append(list_triple_indices_Obj[1])

    #Now add the triples in a list, ordering the triples as defined in list_triple_indices (the create_xml function expects the triples ordered already)
    new_triples_list = [triple_set.triples[i] for i in list_triple_indices]
    assert len(new_triples_list) == len(triple_set.triples), f'Expected {len(triple_set.triples)} triples, found {len(new_triples_list)}'
    total_number_of_triples += len(new_triples_list)
    # print(len(new_triples_list), [new_triples_list[x].id for x in range(len(new_triples_list))])
    new_triple_set_Objects_list.append(TripleSet(new_triples_list, triple_set.category, triple_set.eid, triple_set.shape, triple_set.shape_type))
  assert len(new_triple_set_Objects_list) == len(triple_sets_list), f'Expected {len(triple_sets_list)} triple sets, found {len(new_triple_set_Objects_list)}'
  print(f'    There are {len(new_triple_set_Objects_list)} sorted triple sets...')
  print(f'    There are {total_number_of_triples} input triples in the sorted XML file.')

  return new_triple_set_Objects_list

def split_XMLs (path_input_XML, path_DBprops_count, max_num_triples, path_save_XMLs, DEBUG = False):
  """
  path_input_XML: Path to an XML file that contains triple sets, e.g. as provided in the WebNLG shared tasks. The code expects that all triples mention the same entity, as subject or object.
  path_DBprops_count: Path to a json file that contains DBpedia properties as keys (e.g. "http://dbpedia.org/ontology/birthPlace") and number of occurrences on DBpedia as values (e.g 1486579).
  max_num_triples: the maximum number of triples desired in an XML
  path_save_XMLs: the path where the output XMLs should be created
  This function creates individual XML files for each split triple set.
  """
  print('Splitting XML file...')
  clear_folder(path_save_XMLs)
  os.makedirs(path_save_XMLs)
  # Get the list of TripleSet objects with the triples re-ordered. The object contains the following:
  # self.triples, self.category, self.eid, self.size, self.shape, self.shape_type, self.entities_by_frequency
  new_triple_set_Objects_list = sort_WebNLG_XMLs(path_input_XML, path_DBprops_count)
  total_number_of_XMLs = 0
  total_number_of_triples = 0
  for new_triple_set in new_triple_set_Objects_list:
    if DEBUG:
      print(new_triple_set.size, new_triple_set.entities_by_frequency[0])
    # Get "ideal" triple set split (see balanced_split_with_max function)
    even_slices = None
    if new_triple_set.size > max_num_triples:
      # balanced_split_with_max returns a sequence of numbers that stand for a number of properties.
      groups = balanced_split_with_max(new_triple_set.size, max_num_triples)
      # Let's convert that to a sequence of numbers that correspond to list slices: [10, 10, 5] becomes [10, 20, 25]
      even_slices = [sum(groups[:i]) for i in range(len(groups)+1)]
    else:
      even_slices = [0] + [new_triple_set.size]
    if DEBUG:
      print(f'  Before: {even_slices}')

    # Initialise new list
    new_slices = [0]
    # Now we need to check if the split happened between two occurrences of the same property, which we'd like to avoid
    # even_slices has at least 2 numbers, 0 and the end of the first or only slice.
    if len(even_slices) > 2:
      # Check for intermediate group boundaries (i.e. exclude the first boundary, which is 0, and the last one, because there is no property after it)
      for boundary in even_slices[1:-1]:
        previous_same_property = 0
        # Since in the way even_slices is built, the last slices are the smallest ones, it's better to move boundaries to the left.
        while new_triple_set.triples[boundary+previous_same_property].DBprop == new_triple_set.triples[boundary+previous_same_property-1].DBprop:
          previous_same_property -= 1
        if previous_same_property < 0:
          new_slices.append(boundary+previous_same_property)
          if DEBUG:
            print(f'  {Fore.red}{Back.yellow}!!! Changed split {boundary}, {previous_same_property}!{Style.reset}')
        else:
          new_slices.append(boundary)
      # Add last boundary
      new_slices.append(even_slices[-1])
    else:
      # Add second and last boundary
      new_slices.append(even_slices[1])
    if DEBUG:
      print(f'  After: {new_slices}')

    # Create XMLs
    # Set parameters for calling function that creates XMLs
    input_category = new_triple_set.category
    folder_name = input_category+'_max'+str(max_num_triples)
    entity_name = new_triple_set.entities_by_frequency[0]
    eid = new_triple_set.eid
    # Clear/Create output folder
    if not os.path.exists(os.path.join(path_save_XMLs, folder_name)):
      os.makedirs(os.path.join(path_save_XMLs, folder_name))

    # For each slice of the triple set, create an XML file
    count_files_created = 0
    for count_files, i in enumerate(range(len(new_slices)-1)):
      list_triple_objects = new_triple_set.triples[new_slices[i]:new_slices[i+1]]
      properties_selected_by_user = [i for i in range(len(list_triple_objects))] # Use all properties
      unique_entity_name = entity_name+'_'+str(count_files)
      list_triples_text = create_xml(list_triple_objects, properties_selected_by_user, input_category, os.path.join(path_save_XMLs, folder_name), entity_name=unique_entity_name, eid = eid)  
      count_files_created += 1
      total_number_of_triples += len(list_triple_objects)
    total_number_of_XMLs += count_files_created

  print(f'  Created {total_number_of_XMLs} split XML files that contain up to approximately {max_num_triples} triples.')
  print(f'  There are {total_number_of_triples} input triples in the split XML files.')
