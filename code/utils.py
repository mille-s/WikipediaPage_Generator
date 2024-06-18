#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
import codecs
import json
from xml.dom import minidom
import re
import glob
from google.colab import files

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
      
def get_prop_index_from_table(selected_properties, list_triple_objects):
  """ Generate list of indices of properties selected by user (index in the list of Triple objects that contains all retrieved triples)
  selected_poperties is a widgets.SelectMultiple(...) thingy, as on the following line
    SelectMultiple(description='Properties', index=(0, 1, 2), layout=Layout(width='642px'), options=('0 - birthPlace: Lecce', '1 - birthDate: 1973-08-19', '2 - managerClub: Chennaiyin_FC', '3 - height: 193.0', '4 - height: 1.93', '5 - position: Defender_(association_football)', '6 - team: S.S._Lazio', '7 - team: Trapani_Calcio', '8 - team: A.C.R._Messina', '9 - team: Everton_F.C.', '10 - team: Carpi_FC_1909', '11 - team: Italy_national_football_team', '12 - team: Chennaiyin_FC', '13 - team: Inter_Milan', '14 - team: Lupa_Roma_F.C.', '15 - team: Perugia_Calcio', '16 - team: S.C._Marsala'), rows=17, value=('0 - birthPlace: Lecce', '1 - birthDate: 1973-08-19', '2 - managerClub: Chennaiyin_FC'))
  list_triple_objects is a list of object of class Triple, as defined in the queryDBpediaProps module
  """
  properties_selected_by_user = []
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

def create_xml(triple_objects, properties_selected_by_user, input_category, triple2predArgPath):
  """ Create the XML file with the triples to be converted to PredArg"""
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
  entry.setAttribute('eid', '1')
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
  while x < len(triple_objects):
  # for triple_object in triple_objects:
    triple_object = triple_objects[x]
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
  save_path_file = os.path.join(triple2predArgPath, str(removeReservedCharsFileName(triple_object.DBsubj))+".xml")
  with open(save_path_file, "w") as f:
      f.write(xml_str)
  return list_triples_text 

def create_GPT_Prompt(entity_name, language, list_triples_text):
  language_map = {'EN': 'English', 'GA': 'Irish', 'ES': 'Spanish'}
  with codecs.open(f'GPT_prompt_{entity_name}.txt', 'w', 'utf-8') as fo_gpt:
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
