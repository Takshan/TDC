"""wrapper for download various dataset 
"""
import requests
from zipfile import ZipFile 
import os, sys
import pandas as pd
import numpy as np
import pickle
from pandas.errors import EmptyDataError
from tqdm import tqdm

from ..metadata import name2type, name2id, temp2id, dataset_list, dataset_names, benchmark_names, benchmark2id, benchmark2type
from ..metadata import property_names, paired_dataset_names, single_molecule_dataset_names
from ..metadata import retrosyn_dataset_names, forwardsyn_dataset_names, molgenpaired_dataset_names, generation_datasets
from ..metadata import oracle2id, receptor2id, download_oracle_names, trivial_oracle_names, oracle_names, oracle2type 
from collections import defaultdict 

receptor_names = list(receptor2id.keys())
sys.path.append('../')

from .misc import fuzzy_search, print_sys

def temp_data_download_wrapper(name, path, dataset_names):
	"""wrapper for downloading a dataset given the name and path - zip file, automatically unzipping
	
	Args:
	    name (str): the rough dataset query name
	    path (str): the path to save the dataset
	    dataset_names (list): the list of available dataset names to search the query dataset
	
	Returns:
	    str: the exact dataset query name
	"""
	name = fuzzy_search(name, dataset_names)
	server_path = 'https://dataverse.harvard.edu/api/access/datafile/'

	dataset_path = temp2id[name]

	if not os.path.exists(path):
		os.mkdir(path)

	if os.path.exists(os.path.join(path, name)):
		print_sys('Found local copy...')
	else:
		print_sys('Downloading...')
		googledrive_download(dataset_path, path, name, name2type)
		print_sys('Extracting zip file...')
		with ZipFile(os.path.join(path, name + '.zip'), 'r') as zip:
			zip.extractall(path = os.path.join(path))
		print_sys("Done!")
	return name

def download_wrapper(name, path, dataset_names):
	"""wrapper for downloading a dataset given the name and path, for csv,pkl,tsv files
	
	Args:
	    name (str): the rough dataset query name
	    path (str): the path to save the dataset
	    dataset_names (list): the list of available dataset names to search the query dataset
	
	Returns:
	    str: the exact dataset query name
	"""
	name = fuzzy_search(name, dataset_names)
	server_path = 'https://dataverse.harvard.edu/api/access/datafile/'

	dataset_path = server_path + str(name2id[name])

	if not os.path.exists(path):
		os.mkdir(path)

	if os.path.exists(os.path.join(path, name + '.' + name2type[name])):
		print_sys('Found local copy...')
	else:
		print_sys("Downloading...")
		dataverse_download(dataset_path, path, name, name2type)

	return name

def zip_data_download_wrapper(name, path, dataset_names):
	"""wrapper for downloading a dataset given the name and path - zip file, automatically unzipping
	
	Args:
	    name (str): the rough dataset query name
	    path (str): the path to save the dataset
	    dataset_names (list): the list of available dataset names to search the query dataset
	
	Returns:
	    str: the exact dataset query name
	"""
	name = fuzzy_search(name, dataset_names)
	server_path = 'https://dataverse.harvard.edu/api/access/datafile/'

	dataset_path = server_path + str(name2id[name])

	if not os.path.exists(path):
		os.mkdir(path)

	if os.path.exists(os.path.join(path, name)):
		print_sys('Found local copy...')
	else:
		print_sys('Downloading...')
		dataverse_download(dataset_path, path, name, name2type)
		print_sys('Extracting zip file...')
		with ZipFile(os.path.join(path, name + '.zip'), 'r') as zip:
			zip.extractall(path = os.path.join(path))
		print_sys("Done!")
	return name

def googledrive_download(url, path, name, types):
	os.system(f'wget --load-cookies /tmp/cookies.txt \"https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate \'https://docs.google.com/uc?export=download&id={url}\' -O- | sed -rn \'s/.*confirm=([0-9A-Za-z_]+).*/\\1\\n/p\')&id={url}\" -O {name}.{types[name]} && rm -rf /tmp/cookies.txt && mv {name}.{types[name]} {path}')

def dataverse_download(url, path, name, types):
	"""dataverse download helper with progress bar
	
	Args:
	    url (str): the url of the dataset
	    path (str): the path to save the dataset
	    name (str): the dataset name
	    types (dict): a dictionary mapping from the dataset name to the file format
	"""
	save_path = os.path.join(path, name + '.' + types[name])
	response = requests.get(url, stream=True)
	total_size_in_bytes= int(response.headers.get('content-length', 0))
	block_size = 1024
	progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
	with open(save_path, 'wb') as file:
		for data in response.iter_content(block_size):
			progress_bar.update(len(data))
			file.write(data)
	progress_bar.close()


def oracle_download_wrapper(name, path, oracle_names):
	"""wrapper for downloading an oracle model checkpoint given the name and path
	
	Args:
	    name (str): the rough oracle query name
	    path (str): the path to save the oracle
	    dataset_names (list): the list of available exact oracle names
	
	Returns:
	    str: the exact oracle query name
	"""
	name = fuzzy_search(name, oracle_names)
	if name in trivial_oracle_names:
		return name

	server_path = 'https://dataverse.harvard.edu/api/access/datafile/'
	dataset_path = server_path + str(oracle2id[name])

	if not os.path.exists(path):
		os.mkdir(path)

	if os.path.exists(os.path.join(path, name + '.' + oracle2type[name])):
		print_sys('Found local copy...')
	else:
		print_sys("Downloading Oracle...")
		dataverse_download(dataset_path, path, name, oracle2type) ## to-do to-check
		print_sys("Done!")
	return name


def receptor_download_wrapper(name, path):
	"""wrapper for downloading an receptor pdb file given the name and path
	
	Args:
	    name (str): the exact pdbid
	    path (str): the path to save the oracle
	
	Returns:
	    str: the exact pdbid
	"""

	server_path = 'https://dataverse.harvard.edu/api/access/datafile/'
	dataset_paths = [server_path + str(receptor2id[name][0]), server_path + str(receptor2id[name][1])] 

	if not os.path.exists(path):
		os.mkdir(path)

	if os.path.exists(os.path.join(path, name + '.pdbqt')) and os.path.exists(os.path.join(path, name + '.pdb')):
		print_sys('Found local copy...')
	else:
		print_sys("Downloading receptor...")
		receptor2type = defaultdict(lambda:'pdbqt')
		dataverse_download(dataset_paths[0], path, name, receptor2type) ## to-do to-check
		receptor2type = defaultdict(lambda:'pdb')
		dataverse_download(dataset_paths[1], path, name, receptor2type) ## to-do to-check
		print_sys("Done!")
	return name


def bm_download_wrapper(name, path):
	"""wrapper for downloading a benchmark group given the name and path
	
	Args:
	    name (str): the rough benckmark group query name
	    path (str): the path to save the benchmark group
	    dataset_names (list): the list of available benchmark group names
	
	Returns:
	    str: the exact benchmark group query name
	"""
	name = fuzzy_search(name, list(benchmark_names.keys()))
	server_path = 'https://dataverse.harvard.edu/api/access/datafile/'
	dataset_path = server_path + str(benchmark2id[name])

	if not os.path.exists(path):
		os.mkdir(path)

	if os.path.exists(os.path.join(path, name)):
		print_sys('Found local copy...')
	else:
		print_sys('Downloading Benchmark Group...')
		dataverse_download(dataset_path, path, name, benchmark2type)
		print_sys('Extracting zip file...')
		with ZipFile(os.path.join(path, name + '.zip'), 'r') as zip:
			zip.extractall(path = os.path.join(path))
		print_sys("Done!")
	return name

def pd_load(name, path):
	"""load a pandas dataframe from local file.
	
	Args:
	    name (str): dataset name
	    path (str): the path where the dataset is saved
	
	Returns:
	    pandas.DataFrame: loaded dataset in dataframe
	
	Raises:
	    ValueError: the file format is not supported. currently only support tab/csv/pkl/zip
	"""
	try:
		if name2type[name] == 'tab':
			df = pd.read_csv(os.path.join(path, name + '.' + name2type[name]), sep = '\t')
		elif name2type[name] == 'csv':
			df = pd.read_csv(os.path.join(path, name + '.' + name2type[name]))
		elif name2type[name] == 'pkl':
			df = pd.read_pickle(os.path.join(path, name + '.' + name2type[name]))
		elif name2type[name] == 'zip':
			df = pd.read_pickle(os.path.join(path, name + '/' + name + '.pkl'))
		else:
			raise ValueError("The file type must be one of tab/csv/pickle/zip.")
		try:
			df = df.drop_duplicates()
		except:
			pass
		return df
	except (EmptyDataError, EOFError) as e:
		import sys
		sys.exit("TDC is hosted in Harvard Dataverse and it is currently under maintenance, please check back in a few hours or checkout https://dataverse.harvard.edu/.")

def property_dataset_load(name, path, target, dataset_names):
	"""a wrapper to download, process and load single-instance prediction task datasets
	
	Args:
	    name (str): the rough dataset name
	    path (str): the dataset path to save/retrieve
	    target (str): for multi-label dataset, retrieve the label of interest
	    dataset_names (list): a list of availabel exact dataset names
	
	Returns:
	    pandas.Series: three series (entity representation, label, entity id)
	"""
	if target is None:
		target = 'Y'
	name = download_wrapper(name, path, dataset_names)
	print_sys('Loading...')
	df = pd_load(name, path)
	try:
		if target is not None:
			target = fuzzy_search(target, df.columns.values)
		# df = df.T.drop_duplicates().T ### does not work
		# df2 = df.loc[:,~df.T.duplicated(keep='first')]  ### does not work 
		df2 = df.loc[:,~df.columns.duplicated()] ### remove the duplicate columns 
		df = df2 
		df = df[df[target].notnull()].reset_index(drop = True)
	except:
		with open(os.path.join(path, name + '.' + name2type[name]), 'r') as f:
			if name2type[name] == 'pkl':
				import pickle 
				file_content = pickle.load(open(os.path.join(path, name + '.' + name2type[name]), 'rb'))
			else:
				file_content = ' '.join(f.readlines())
			flag = 'Service Unavailable' in ' '.join(file_content)
			# flag = 'Service Unavailable' in ' '.join(f.readlines())
			if flag:
				import sys
				sys.exit("TDC is hosted in Harvard Dataverse and it is currently under maintenance, please check back in a few hours or checkout https://dataverse.harvard.edu/.")
			else:
				import sys 
				sys.exit("Please report this error to contact@tdcommons.ai, thanks!")
	try:
		return df['X'], df[target], df['ID']
	except:
		return df['Drug'], df[target], df['Drug_ID']

def interaction_dataset_load(name, path, target, dataset_names, aux_column):
	"""a wrapper to download, process and load two-instance prediction task datasets
	
	Args:
	    name (str): the rough dataset name
	    path (str): the dataset path to save/retrieve
	    target (str): for multi-label dataset, retrieve the label of interest
	    dataset_names (list): a list of availabel exact dataset names
	
	Returns:
	    pandas.Series: three series (entity 1 representation, entity 2 representation, entity id 1, entity id 2, label)
	"""
	name = download_wrapper(name, path, dataset_names)
	print_sys('Loading...')
	df = pd_load(name, path)
	try:
		if target is None:
			target = 'Y'
		if target not in df.columns.values:
			# for binary interaction data, the labels are all 1. negative samples can be sampled from utils.NegSample function
			df[target] = 1
		if target is not None:
			target = fuzzy_search(target, df.columns.values)
		df = df[df[target].notnull()].reset_index(drop = True)
		if aux_column is None:
			return df['X1'], df['X2'], df[target], df['ID1'], df['ID2'], '_'
		else:
			return df['X1'], df['X2'], df[target], df['ID1'], df['ID2'], df[aux_column]

	except:
		with open(os.path.join(path, name + '.' + name2type[name]), 'r') as f:
			flag = 'Service Unavailable' in ' '.join(f.readlines())
			if flag:
				import sys
				sys.exit("TDC is hosted in Harvard Dataverse and it is currently under maintenance, please check back in a few hours or checkout https://dataverse.harvard.edu/.")
			else:
				import sys
				sys.exit("Please report this error to cosamhkx@gmail.com, thanks!")


def multi_dataset_load(name, path, dataset_names):
	"""a wrapper to download, process and load multiple(>2)-instance prediction task datasets. assume the downloaded file is already processed
	
	Args:
	    name (str): the rough dataset name
	    path (str): the dataset path to save/retrieve
	    target (str): for multi-label dataset, retrieve the label of interest
	    dataset_names (list): a list of availabel exact dataset names
	
	Returns:
	    pandas.DataFrame: the raw dataframe
	"""
	name = download_wrapper(name, path, dataset_names)
	print_sys('Loading...')
	df = pd_load(name, path)
	return df

def generation_paired_dataset_load(name, path, dataset_names, input_name, output_name):
	"""a wrapper to download, process and load generation-paired task datasets
	
	Args:
	    name (str): the rough dataset name
	    path (str): the dataset path to save/retrieve
	    target (str): for multi-label dataset, retrieve the label of interest
	    dataset_names (list): a list of availabel exact dataset names
	
	Returns:
	    pandas.Series: two series (entity 1 representation, label)
	"""
	name = download_wrapper(name, path, dataset_names)
	print_sys('Loading...')
	df = pd_load(name, path)
	return df[input_name], df[output_name]

def three_dim_dataset_load(name, path, dataset_names):
	"""a wrapper to download, process and load 3d molecule task datasets
	
	Args:
	    name (str): the rough dataset name
	    path (str): the dataset path to save/retrieve
	    dataset_names (list): a list of availabel exact dataset names
	
	Returns:
	    pandas.DataFrame: the dataframe holds 3d information
	    str: the path of the dataset
	    str: the name of the dataset
	"""
	name = zip_data_download_wrapper(name, path, dataset_names)
	print_sys('Loading...')
	df = pd_load(name, path)
	return df, os.path.join(path, name), name

def distribution_dataset_load(name, path, dataset_names, column_name):
	"""a wrapper to download, process and load molecule distribution learning task datasets. assume the downloaded file is already processed
	
	Args:
	    name (str): the rough dataset name
	    path (str): the dataset path to save/retrieve
	    dataset_names (list): a list of availabel exact dataset names
	    column_name (str): the column specifying where molecule locates
	
	Returns:
	    pandas.Series: the input list of molecules representation
	"""
	name = download_wrapper(name, path, dataset_names)
	print_sys('Loading...')
	df = pd_load(name, path)
	return df[column_name]

def bi_distribution_dataset_load(name, path, dataset_names, return_pocket=False, threshold=15, remove_Hs=True, keep_het=False, allowed_atom_list = ['C', 'N', 'O', 'S', 'H', 'B', 'Br', 'Cl', 'P', 'I', 'F']):
	"""a wrapper to download, process and load protein-ligand conditional generation task datasets. assume the downloaded file is already processed
	
	Args:
	    name (str): the rough dataset name
	    path (str): the dataset path to save/retrieve
	    dataset_names (list): a list of availabel exact dataset names
	
	Returns:
	    pandas.Series: the input list of molecules representation
	"""
	name = fuzzy_search(name, dataset_names)
	if name == 'pdbbind':
		print_sys('Loading...')
		protein, ligand = process_pdbbind(path, name, return_pocket, remove_Hs, keep_het, allowed_atom_list)
	else:
		name = temp_data_download_wrapper(name, path, dataset_names)
		if name == 'dude':
			print_sys('Loading...')
			protein, ligand = process_dude(path, name, return_pocket, remove_Hs, keep_het, allowed_atom_list)
		elif name == 'scPDB':
			print_sys('Loading...')
			protein, ligand = process_scpdb(path, name, return_pocket, remove_Hs, keep_het, allowed_atom_list)
		elif name == 'crossdock':
			print_sys('Loading...')
			protein, ligand = process_crossdock(path, name, return_pocket, remove_Hs, keep_het, allowed_atom_list)
	
	return protein, ligand

def generation_dataset_load(name, path, dataset_names):
	"""a wrapper to download, process and load generation task datasets. assume the downloaded file is already processed
	
	Args:
	    name (str): the rough dataset name
	    path (str): the dataset path to save/retrieve
	    dataset_names (list): a list of availabel exact dataset names
	
	Returns:
	    pandas.Series: the data series
	"""
	name = download_wrapper(name, path, dataset_names)
	print_sys('Loading...')
	df = pd_load(name, path)
	return df['input'], df['target']

def oracle_load(name, path = './oracle', oracle_names = oracle_names):
	"""a wrapper to download, process and load oracles. 
	
	Args:
	    name (str): the rough oracle name
	    path (str): the oracle path to save/retrieve, defaults to './oracle'
	    dataset_names (list): a list of availabel exact oracle names
	
	Returns:
	    str: exact oracle name
	"""
	name = oracle_download_wrapper(name, path, oracle_names)
	return name


def receptor_load(name, path = './oracle'):
	"""a wrapper to download, process and load pdb file. 
	
	Args:
	    name (str): the rough pdbid name
	    path (str): the oracle path to save/retrieve, defaults to './oracle'
	
	Returns:
	    str: exact pdbid name
	"""
	name = receptor_download_wrapper(name, path)
	return name	


def bm_group_load(name, path):
	"""a wrapper to download, process and load benchmark group
	
	Args:
	    name (str): the rough benchmark group name
	    path (str): the benchmark group path to save/retrieve
	
	Returns:
	    str: exact benchmark group name
	"""
	name = bm_download_wrapper(name, path)
	return name


def process_pdbbind(path, name='pdbbind', return_pocket=False, remove_Hs=True, keep_het=False, allowed_atom_list = ['C', 'N', 'O', 'S', 'H', 'B', 'Br', 'Cl', 'P', 'I', 'F']):
	"""a processor to process pdbbind dataset
		
		Args:
		    name (str): the name of the dataset
		    path (str): the path to save the data file
		    print_stats (bool): whether to print the basic statistics of the dataset
		    return_pocket (bool): whether to return only protein pocket or full protein
			threshold (int): only enabled when return_pocket is to True, if pockets are not provided in the raw data,
			 				 the threshold is used as a radius for a sphere around the ligand center to consider protein pocket
			remove_Hs (int): whether to remove H atoms from protein or not
			keep_het (bool): whether to keep het atoms (e.g. cofactors) in protein
			allowed_atom_list (list(str)): atom types allowed to include
		
		Returns:
			protein (dict): a dict of protein features
			ligand (dict): a dict of ligand features
	"""
	try:
		from biopandas.pdb import PandasPdb
	except:
		raise ImportError("Please install biopandas by 'pip install biopandas'! ")
	from rdkit import Chem
	if os.path.exists(path):
		print_sys("Processing...")	
		protein_coords, protein_atom_types = [], []
		ligand_coords, ligand_atom_types = [], []
		files = os.listdir(path)
		failure = 0
		for idx, file in enumerate(tqdm(files)):
			if file == 'readme' or file == 'index':
				continue
			try:
				if return_pocket:
					protein = PandasPdb().read_pdb(os.path.join(path, f"{file}/{file}_pocket.pdb"))
				else:
					protein = PandasPdb().read_pdb(os.path.join(path, f"{file}/{file}_protein.pdb"))
				ligand = Chem.SDMolSupplier(os.path.join(path, f"{file}/{file}_ligand.sdf"), sanitize=False)[0]
				ligand = extract_atom_from_mol(ligand, allowed_atom_list)
                # if ligand contains unallowed atoms
				if ligand is None:
					continue
				else:
					ligand_coord, ligand_atom_type = ligand 
				protein_coord, protein_atom_type = extract_atom_from_protein(protein.df["ATOM"], protein.df["HETATM"], remove_Hs, keep_het, allowed_atom_list)
				protein_coords.append(protein_coord)
				ligand_coords.append(ligand_coord)
				protein_atom_types.append(protein_atom_type)
				ligand_atom_types.append(ligand_atom_type)
			except:
				failure += 1
				print ('failure', failure)
				continue
		protein = {"coord": protein_coords, "atom_type": protein_atom_types}
		ligand = {"coord": ligand_coords, "atom_type": ligand_atom_types}
	else:
		sys.exit("Wrong path!")
	return protein, ligand

def process_crossdock(path, name='crossdock', return_pocket=False, threshold=15, remove_Hs=True, keep_het=False, allowed_atom_list = ['C', 'N', 'O', 'S', 'H', 'B', 'Br', 'Cl', 'P', 'I', 'F']):
	"""a processor to process crossdock dataset
		
		Args:
		    name (str): the name of the dataset
		    path (str): the path to save the data file
		    print_stats (bool): whether to print the basic statistics of the dataset
		    return_pocket (bool): whether to return only protein pocket or full protein
			threshold (int): only enabled when return_pocket is to True, if pockets are not provided in the raw data,
			 				 the threshold is used as a radius for a sphere around the ligand center to consider protein pocket
			remove_Hs (int): whether to remove H atoms from protein or not
			keep_het (bool): whether to keep het atoms (e.g. cofactors) in protein
			allowed_atom_list (list(str)): atom types allowed to include
		
		Returns:
			protein (dict): a dict of protein features
			ligand (dict): a dict of ligand features
	"""
	try:
		from biopandas.pdb import PandasPdb
	except:
		raise ImportError("Please install biopandas by 'pip install biopandas'! ")
	from rdkit import Chem
	protein_coords, protein_atom_types = [], []
	ligand_coords, ligand_atom_types = [], []
	failure = 0
	path = os.path.join(path, name)
	index_path = os.path.join(path, 'index.pkl')
	index = pickle.load(open(index_path, 'rb'))
	path = os.path.join(path, 'crossdocked_pocket10')
	for idx, (pocket_fn, ligand_fn, _, rmsd) in enumerate(tqdm(index)):
		if pocket_fn is None or ligand_fn is None:
			continue
		if return_pocket:
			protein = PandasPdb().read_pdb(os.path.join(path, pocket_fn))
		else:
			# full protein not stored in the preprocessed crossdock by Luo et al 2021
			protein = PandasPdb().read_pdb(os.path.join(path, pocket_fn))
		try:
			ligand = Chem.SDMolSupplier(os.path.join(path, ligand_fn), sanitize=False)[0]
			ligand = extract_atom_from_mol(ligand, allowed_atom_list)
			if ligand is None:
				continue
			else:
				ligand_coord, ligand_atom_type = ligand 
			protein_coord, protein_atom_type = extract_atom_from_protein(protein.df["ATOM"], protein.df["HETATM"], remove_Hs, keep_het, allowed_atom_list)
			protein_coords.append(protein_coord)
			ligand_coords.append(ligand_coord)
			protein_atom_types.append(protein_atom_type)
			ligand_atom_types.append(ligand_atom_type)
		except:
			failure += 1
			print ('failure', failure)
			continue
	protein = {"coord": protein_coords, "atom_type": protein_atom_types}
	ligand = {"coord": ligand_coords, "atom_type": ligand_atom_types}
	return protein, ligand

def process_dude(path, name='dude', return_pocket=False, threshold=15, remove_Hs=True, keep_het=False, allowed_atom_list = ['C', 'N', 'O', 'S', 'H', 'B', 'Br', 'Cl', 'P', 'I', 'F']):
	"""a processor to process DUD-E dataset
		
		Args:
		    name (str): the name of the dataset
		    path (str): the path to save the data file
		    print_stats (bool): whether to print the basic statistics of the dataset
		    return_pocket (bool): whether to return only protein pocket or full protein
			threshold (int): only enabled when return_pocket is to True, if pockets are not provided in the raw data,
			 				 the threshold is used as a radius for a sphere around the ligand center to consider protein pocket
			remove_Hs (int): whether to remove H atoms from protein or not
			keep_het (bool): whether to keep het atoms (e.g. cofactors) in protein
			allowed_atom_list (list(str)): atom types allowed to include
		
		Returns:
			protein (dict): a dict of protein features
			ligand (dict): a dict of ligand features
	"""
	try:
		from biopandas.pdb import PandasPdb
	except:
		raise ImportError("Please install biopandas by 'pip install biopandas'! ")
	from rdkit import Chem
	protein_coords, protein_atom_types = [], []
	ligand_coords, ligand_atom_types = [], []
	path = os.path.join(path, name)
	files = os.listdir(path)
	failure = 0
	for idx, file in enumerate(tqdm(files)):
		protein = PandasPdb().read_pdb(os.path.join(path, f"{file}/receptor.pdb"))
		if not os.path.exists(os.path.join(path, f"{file}/actives_final.sdf")):
			os.system(f'gzip -d {path}/{file}/actives_final.sdf.gz')
		crystal_ligand = Chem.MolFromMol2File(os.path.join(path, f"{file}/crystal_ligand.mol2"), sanitize=False)
		crystal_ligand = extract_atom_from_mol(crystal_ligand, allowed_atom_list)
		if crystal_ligand is None:
			continue
		else:
			crystal_ligand_coord, crystal_ligand_atom_type = crystal_ligand 
		ligands = Chem.SDMolSupplier(os.path.join(path, f"{file}/actives_final.sdf"), sanitize=False)
		protein_coord, protein_atom_type = extract_atom_from_protein(protein.df["ATOM"], protein.df["HETATM"], remove_Hs, keep_het, allowed_atom_list)
		if return_pocket:
			lig_center = crystal_ligand_coord.mean(axis=0)
			protein_atom_dist_to_lig = np.sqrt(np.sum(np.square(protein_coord-lig_center),axis=-1))
			protein_mask = protein_atom_dist_to_lig <= threshold 
			protein_coord = protein_coord[protein_mask]
		protein_coords.append(protein_coord)
		ligand_coords.append(crystal_ligand_coord)
		protein_atom_types.append(protein_atom_type)
		ligand_atom_types.append(crystal_ligand_atom_type)
		for ligand in ligands:
			try:
				ligand = extract_atom_from_mol(ligand, allowed_atom_list)
				# if ligand contains unallowed atoms
				if ligand is None:
					continue
				else:
					ligand_coord, ligand_atom_type = ligand 
				protein_coords.append(protein_coord)
				ligand_coords.append(ligand_coord)
				protein_atom_types.append(protein_atom_type)
				ligand_atom_types.append(ligand_atom_type)
			except:
				failure += 1
				print ('failure', failure)
				continue
	protein = {"coord": protein_coords, "atom_type": protein_atom_types}
	ligand = {"coord": ligand_coords, "atom_type": ligand_atom_types}
	return protein, ligand

def process_scpdb(path, name='scPDB', return_pocket=False, remove_Hs=True, keep_het=False, allowed_atom_list = ['C', 'N', 'O', 'S', 'H', 'B', 'Br', 'Cl', 'P', 'I', 'F']):
	"""a processor to process scpdb dataset
		
		Args:
		    name (str): the name of the dataset
		    path (str): the path to save the data file
		    print_stats (bool): whether to print the basic statistics of the dataset
		    return_pocket (bool): whether to return only protein pocket or full protein
			threshold (int): only enabled when return_pocket is to True, if pockets are not provided in the raw data,
			 				 the threshold is used as a radius for a sphere around the ligand center to consider protein pocket
			remove_Hs (int): whether to remove H atoms from protein or not
			keep_het (bool): whether to keep het atoms (e.g. cofactors) in protein
			allowed_atom_list (list(str)): atom types allowed to include
		
		Returns:
			protein (dict): a dict of protein features
			ligand (dict): a dict of ligand features
	"""
	try:
		from biopandas.pdb import PandasPdb
	except:
		raise ImportError("Please install biopandas by 'pip install biopandas'! ")
	from rdkit import Chem
	protein_coords, protein_atom_types = [], []
	ligand_coords, ligand_atom_types = [], []
	path = os.path.join(path, name)
	files = os.listdir(path)
	failure = 0
	for idx, file in enumerate(tqdm(files)):
		if return_pocket:
			protein = PandasMol2().read_mol2(os.path.join(path, f"{file}/site.mol2"))
		else:
			protein = PandasMol2().read_mol2(os.path.join(path, f"{file}/protein.mol2"))
		try:
			ligand = Chem.SDMolSupplier(os.path.join(path, f"{file}/ligand.sdf"), sanitize=False)[0]
			ligand = extract_atom_from_mol(ligand, allowed_atom_list)
			# if ligand contains unallowed atoms
			if ligand is None:
				continue
			else:
				ligand_coord, ligand_atom_type = ligand 
			protein_coord, protein_atom_type = extract_atom_from_protein(protein.df, None, remove_Hs=remove_Hs, keep_het=False, allowed_atom_list=allowed_atom_list)
			protein_coords.append(protein_coord)
			ligand_coords.append(ligand_coord)
			protein_atom_types.append(protein_atom_type)
			ligand_atom_types.append(ligand_atom_type)
		except:
			failure += 1
			print ('failure', failure)
			continue
	protein = {"coord": protein_coords, "atom_type": protein_atom_types}
	ligand = {"coord": ligand_coords, "atom_type": ligand_atom_types}
	return protein, ligand

def atom_to_one_hot(atom, allowed_atom_list):
	"""a helper to convert atom to one-hot encoding

		Args:
			atom (str): the atom to convert
			allowed_atom_list (list(str)): atom types allowed to include

		Returns:
			new_atom (numpy.array): atom one-hot encoding vector
	"""
	length = len(allowed_atom_list)
	atom = allowed_atom_list.index(atom)
	new_atom = np.zeros(shape=(length,))
	new_atom[atom] = 1
	return new_atom

def extract_atom_from_mol(rdmol, allowed_atom_list):
	"""a helper to extract molecule atom information 

		Args:
			rdmol (rdkit.rdmol): rdkit molecule
			allowed_atom_list (list(str)): atom types allowed to include

		Returns:
			coord (numpy.array): atom types
			atom_type (numpy.array): atom coordinates
	"""
	for atom in rdmol.GetAtoms():
		if atom.GetSymbol() not in allowed_atom_list:
			return None
	coord = [list(rdmol.GetConformer(0).GetAtomPosition(idx)) for idx in range(rdmol.GetNumAtoms())]
	atom_type = [atom_to_one_hot(atom.GetSymbol(), allowed_atom_list) for atom in rdmol.GetAtoms()]
	return np.array(coord), np.array(atom_type)

def extract_atom_from_protein(data_frame, data_frame_het, remove_Hs, keep_het, allowed_atom_list):
	"""a helper to extract protein atom information

		Args:
			data_frame (pandas.dataframe): protein atom 
			data_frame_het (pandas.dataframe): protein het atom
			remove_Hs (int): whether to remove H atoms from protein or not
			keep_het (bool): whether to keep het atoms (e.g. cofactors) in protein
			allowed_atom_list (list(str)): atom types allowed to include

		Returns:
			coord (numpy.array): atom types
			atom_type (numpy.array): atom coordinates
	"""
	if keep_het:
		data_frame = pd.concat([data_frame, data_frame_het])
	if remove_Hs:
		data_frame = data_frame[data_frame["atom_name"].str.startswith("H") == False]
		data_frame.reset_index(inplace=True, drop=True)
	x = data_frame['x_coord'].to_numpy() if 'x_coord' in data_frame else data_frame['x'].to_numpy()
	y = data_frame['y_coord'].to_numpy() if 'y_coord' in data_frame else data_frame['y'].to_numpy()
	z = data_frame['z_coord'].to_numpy() if 'z_coord' in data_frame else data_frame['z'].to_numpy()
	x = np.expand_dims(x, axis=1)
	y = np.expand_dims(y, axis=1)
	z = np.expand_dims(z, axis=1)
	coord = np.concatenate((x,y,z), axis=1)
	atom_type = data_frame['atom_name'].to_numpy()
	atom_type = [
                atom_to_one_hot(atom[0], allowed_atom_list)
                for atom in atom_type if atom in allowed_atom_list
            ]
	return coord, np.array(atom_type)