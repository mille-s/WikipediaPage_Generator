# WikipediaPage_Generator

A live demo for Irish and English is available [here](http://ec2-18-224-151-90.us-east-2.compute.amazonaws.com:3000/).

**Important notice#1**: this tool is still at an early stage of development; it can generate text that is unnatural, and sometimes ungrammatical. 

The tool is intended to generate seed Wikipedia pages in several languages for people to edit, and possibly upload on Wikipedia. Our generator is fully rule-based and open-source; its general quality is lower than that of the best large language models, but unlike them, it is extremely data and resource efficient. If you like rule-based NLG systems, you may want to check [this one](https://arxiv.org/ftp/arxiv/papers/2311/2311.14808.pdf) too.

## Quick start

1. Click on *Wikipedia_generator.ipynb* above and then click on *Open in Colab* at the top of the next page.
2. In Colab, run cell of Step 1 to download the resources needed (click the play button just below *Step 1*); it takes a couple of minutes to install.
3. Run first cell of Step 2 to set parameters (click the play button just below *Set parameters*; see below for more about parameters).
4. Run second cell of Step 2 to fetch DBpedia properties (click the play button just below *Get DBpedia properties*)
5. Optional: select one or more properties in the resulting table using Ctrl+click on each desired property (if none specified, all will be generated).
6. Run all 17 cells of Step 3 to generate a text (click the play button just below *Step 3*).
7. Run the cell of Step 4 to show the text in a mock Wikipedia page (click the play button just below *Show text*).

The code essentially outputs 2 files, which can be downloaded from the file browser on the left (click the folder icon on the left edge if you don't see the browser):
- the output file, which contains the generated text (*all_[languageID]_[split]_out.txt*).
- a file that contains a ready-made prompt designed for ChatGPT, the top line for this task (*GPT_prompt_[entityName].txt*).

## Parameters

**Basic parameters**

*name*: the name of the entity you want to generate a text about, e.g. "Titanic" or "Barack Obama".

*category*: the category the entity belongs to; it is usually not needed but can help the generation process.

*language*: choose the output language; currently supported: English (EN) and Irish (GA).

**Advanced parameters**

*triple_source*: choose where to get the triples from, either the DBpedia Ontology (Ontology, generally more quality) or the Wikipedia infoboxes ('Infobox', generally more coverage). 

*ignore_properties*: list here the properties (separated by a comma) that you don't want to generate (e.g. "width" often has bad values on DBpedia, so it's recommended to ignore it).

*generate_intermediate_representations*: Select 'no' if you're only interested in the output, 'yes' to get all intermediate linguistic representations in the native .str format.

*split*: set to 'test' for Wikipedia page generation.

## How it works

[Irish Wikipedia generation poster](documents/2023_START-ER-poster.pdf)

## References

Simon Mille, Elaine Uí Dhonnchadha, Lauren Cassidy, Brian Davis, Stamatia Dasiopoulou, Anya Belz. 2023. Generating Irish Text with a Flexible Plug-and-Play Architecture. In *Proceedings of the Second Workshop on Pattern-based Approaches to NLP in the Age of Deep Learning (Pan-DL'23@EMNLP)*, pages 25--42, Singapore. [Paper PDF](https://aclanthology.org/2023.pandl-1.4)

Simon Mille, Elaine Uí Dhonnchadha, Stamatia Dasiopoulou, Lauren Cassidy, Brian Davis, Anya Belz. 2023. DCU/TCD-FORGe at WebNLG’23: Irish rules!. In *Proceedings of the Workshop on Multimodal, Multilingual Natural Language Generation and Multilingual WebNLG Challenge (MM-NLG@INLG)*, pages 87--92, Prague, Czech Republic. [Paper PDF](https://aclanthology.org/2023.mmnlg-1.10)

## Acknowledgements
The project was funded by the European Union under the Marie Skłodowska-Curie grant agreement No 101062572 (M-FleNS).

[M-FleNS Website](https://sites.google.com/adaptcentre.ie/m-flens/home/resources)
