#!/usr/bin/python
# coding=utf-8
import requests, json, os, factory, re
from collections import defaultdict
from argparse import ArgumentParser
from faker import Faker
from faker import Factory
from collections import defaultdict 
import time


parser = ArgumentParser()
parser.add_argument("key", help="Access key to Open Calais API")
parser.add_argument("input", help="Directory where to find files to be processed")
parser.add_argument("output", help="Directory where outputs will be written")
parser.add_argument("max", type=int, help="maximum number of file processed, all file will be processed if negative")
parser.add_argument("-o", "--one", help="l'anonymisation se fait fichier par fichier", action="store_true")

args = parser.parse_args()
key = args.key
input_directory = args.input #Répertoire racine de l'arborescence de mails
output_directory = args.output #Répertoire racine de l'arborescence de fichiers transformé
entities_path = output_directory + "{}entities.json".format("/" if output_directory[-1] != "/" else "")
keys_path = output_directory + "{}keys.json".format("/" if output_directory[-1] != "/" else "")
rev_keys_path = output_directory + "{}rkeys.json".format("/" if output_directory[-1] != "/" else "")
anon_keys_path = output_directory + "{}anon_keys.json".format("/" if output_directory[-1] != "/" else "")

ID=0 #ID unique pour les entités
anon_tmp = "_CEN{}SURE_" #template for censorship
LEXIQUE = {"EmailAddress": set(), "Person": set(), "Company": set()} #listes d'entités par type
ENTITIES = {} #lien entre une entité et ses différentes instances
NAME2KEY = defaultdict(lambda: gen_key()) #nom de l'entité -> code de censure
KEY2MAIN = defaultdict(lambda: str()) #code de censure ->
number_cap = args.max

calais_url = "https://api.thomsonreuters.com/permid/calais"
calais_headers = {'X-AG-Access-Token' : key, 'x-calais-language': 'French', 'Content-Type' : 'text/raw', 'outputFormat' : 'application/json', 'omitOutputtingOriginalText' : 'true'}

def get_OC_entities(_path):
	global KEY2MAIN, LEXIQUE
	cmpt = 0
	print(_path, os.path.getsize(_path), "bytes")
	with open(_path, "rb") as f:
		response = requests.post(calais_url, data=f, headers=calais_headers, timeout=80)
		result_json =  eval(response.text)
		entities = defaultdict(lambda: defaultdict(lambda:[]))
		for k,v in result_json.items():
			if "_type" in v.keys():
				cmpt +=1
				if v["_type"] in ["Person","Company", "EmailAddress"]:
					name = v["name"]
					LEXIQUE[v["_type"]].add(name)
					forms = {i["exact"] for i in v["instances"]}
					entities[v["_type"]][name] = list(forms)
					anon_key = NAME2KEY[name]
					KEY2MAIN[anon_key] = name
					for form in forms:
						NAME2KEY[form] = anon_key
	print("\t", cmpt, "entities found")
	return entities

#Remplace toutes les instances d'une entité par son
def censor(_path, entities):
	with open(_path, "r") as f:
		text = f.read()
		for t, v in entities.items():
			if t in ["Person", "Company", "EmailAddress"]:
				for n, forms in v.items():
					for form in sorted(forms, key= lambda x: len(x), reverse=True):
						text = re.sub(form, NAME2KEY[n], text)
		output_path =output_directory+"{}".format("/" if not output_directory[-1] == "/" else "")+_path.split(input_directory)[-1].strip('/')+".ann.tmp"
		output_dir_tmp = "/".join(output_path.replace("\\","/").split("/")[:-1])
		if not os.path.exists(output_dir_tmp):
			os.makedirs(output_dir_tmp)
		with open(output_path, "w") as g:
			g.write(text)

#remplace les 			
def anonymiser(_path, k2a):
	temp_path =output_directory+"{}".format("/" if not output_directory[-1] == "/" else "")+_path.split(input_directory)[-1].strip('/')+".ann.tmp"
	output_path =  ".".join(temp_path.split(".")[:-1])
	with open(temp_path, "r") as f:
		text = f.read()
		for k, a in k2a.items():
			reg = re.compile(k)
			text = re.sub(reg,a, text)
		with open(output_path, "w") as g:
			g.write(text)

def merge(e =None):
	global ENTITIES
	if e:
		for t,ns in e.items():
			if not t in ENTITIES.keys():
				ENTITIES[t] = {}
			for n, f in ns.items():
				if not n in ENTITIES[t].keys():
					ENTITIES[t][n] = []
				ENTITIES[t][n].extend(e[t][n])

def gen_key():
	global ID
	ID = ID + 1
	return anon_tmp.format(ID)
	
def get_files_r(_path):
	path_list = []
	if os.path.isfile(_path):
		if (os.path.getsize(_path)) <  4500000:
			return [_path]
		else:
			return []
	for root, directories, filenames in os.walk(_path):
		for filename in filenames:
			path_list.extend(get_files_r(os.path.join(root,filename)))
	return sorted(path_list, key=lambda x: os.path.getsize(x), reverse=True)

def main(directory = "emails/scott-s/sent_items/", w_directory = "test", cap = 50):#si cap est négatif, tout les fichiers seront traités
	global ENTITIES
	global NAME2KEY
	global KEY2MAIN
	global LEXIQUE
	
	if not os.path.exists(w_directory):#crée le répertoire de travail si inexistant
		os.makedirs(w_directory)
	path_list = get_files_r(directory)#récupère une liste plate des cap plus gros(sans toute fois dépasser le seuil de OpenCalai) fichiers de l'arborescence
	if cap > 0:
		path_list = path_list[:min(len(path_list),cap)]
	#extraction des entités 
	for path in path_list:
		print("waiting for 1 second")
		time.sleep(1)# pour ne pas dépasser le nombre de requètes autorisés par OpenCalais
		entities = get_OC_entities(path)
		merge(e = entities)
	#association nom, mail
	mail2name = defaultdict(lambda: None)
	name2mail = defaultdict(lambda: None)
	for email in LEXIQUE["EmailAddress"]:
		b = True
		for name in LEXIQUE["Person"]:
			if factory.test_ownership(name, email):
				mail2name[email] = name
				name2mail[name] = email
				b = False
				break
		if b:
			mail2name[email] = None
	#défini un générateur de nom de domaine avec une white list. 
	#ICI, ENRON.COM sera conservé comme nom de domaine possible 
	#car tellement présent et partagé qu'il ne révèle rien
	domains = factory.generate_domains(mail2name.keys())
	#crée un couple nom, mail
	name2forgedID = {n: factory.fuzzy_profile(domains, n, name2mail[n]) for n in LEXIQUE["Person"]}
	name2forged = {n: name2forgedID[n]["names"][n] for n in LEXIQUE["Person"]}
	for m in LEXIQUE["EmailAddress"]:
		if mail2name[m] != None and m in name2forgedID[mail2name[m]]["emails"].keys():
			name2forged[m] = name2forgedID[mail2name[m]]["emails"][m]
		else:
			name2forged[m] = factory.fuzzy_profile(domains,None, m)["emails"][m]
	#name2forged.update({m: (factory.fuzzy_profile(domains,None, m)["emails"][m] if mail2name[m]== None else name2forgedID[mail2name[m]]["emails"][m]) for m in LEXIQUE["EmailAddress"]})
	name2forged.update({o: factory.generator.company() for o in LEXIQUE["Company"]}	)
	
	#Associe les clés de censure au nouvelles entités
	key2forged = {k:name2forged[KEY2MAIN[k]] for k in KEY2MAIN.keys()}
	
	
	#Anonymisation
	for path in path_list:
		censor(path, ENTITIES)
		anonymiser(path, key2forged)
	
	
	with open(entities_path, "w") as f:
		f.write(json.dumps(ENTITIES))
	with open(keys_path, "w") as f:
		f.write(json.dumps(NAME2KEY))
	with open(rev_keys_path, "w") as f:
		f.write(json.dumps(KEY2MAIN))
	with open(anon_keys_path, "w") as f:
		f.write(json.dumps(name2forged))
	
if __name__ == "__main__":
	main(directory = input_directory, w_directory = output_directory, cap = number_cap)
