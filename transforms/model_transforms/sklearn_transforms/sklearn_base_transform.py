#!/usr/bin/env python
import json
import cPickle as pickle
import sys, os
import numpy as np
import importlib

# TODO: PUT THIS SOMEWHERE ELSE, Extend it for more primitives
def map_types(params):
	""" Takes a dict of params in the form i:{'value':'val','type':type} and maps them to i:value according to type """
	type_map = {
			'int':int,
			'float':float,
			'string':str,
			'bool':bool
	}
	newparams = dict()

	for p in params:
		if params[p]['value'] == "":
			newparams[p] = None
			continue
		if type(params[p]['type']) == list:
			for opt in params[p]['type']:
				#Quick hack. Order your possible types in most-constrained to least constrained
				try:
					newparams[p] = type_map[opt](params[p]['value'])
				except ValueError:
					continue
				break
			continue
		newparams[p] = type_map[params[p]['type']](params[p]['value'])

	return newparams

class sklearn_transform_base:
	def __init__(self, params_file_s):
		""" Initializes the transform. Only takes a relative path to a JSON file that contains all of the system parameters """
		try:
			edfile = open('%s/transforms/error_dict.json' % os.environ['PROTOML_BASE'])
		except KeyError:
			print >> sys.stderr, "FATAL: PROTOML Environment variable not set"
			sys.exit(-1)
		self.error_dict = json.load(edfile)
		edfile.close()
		try:
			params_file = open(params_file_s, 'r')
		except IOError as ioe:
			# Not sure if I should raise an error or exit -- feel free to suggest which
			print >> sys.stderr, "Could not open system parameters", ioe
			sys.exit(self.error_dict['CouldNotOpenSystemParams'])

		try:
			self.params = json.load(params_file)
		except ValueError as vae:
			print >> sys.stderr, "Could not decode parameters:", vae
			sys.exit(self.error_dict['CouldNotParseSystemParams'])

		params_file.close()
		self.module_name = str(self.params['params']['module name'])

		relative_name = self.module_name.split('.')[-1] # Final module name, e.g. AffinityPropagation or KMeans

		# Importing
		try:
			mods = __import__(str('.'.join(self.module_name.split('.')[:-1])), globals(), locals(), [relative_name], -1)
		except ImportError as ime:
			print >> sys.stderr, "Could not import %s:" % self.params['params']['module name'], ime
			sys.exit(self.error_dict['IncorrectPackage'])

		self.model_module = getattr(mods, relative_name)

	def read_hyperparams(self):
		""" Reads the input files based on their formats """
		# TODO: Decide if we're putting hyperparams in the json parameters or as a different file
		"""
		try:
			self.hyperparams_file = open(self.params['hyperparameters file'],'r')
		except IOError as ioe:
			print >> sys.stderr, "Could not open hyper parameters", ioe
			sys.exit(self.error_dict['CouldNotOpenHyperParameters'])
		
		try:
			self.hyperparams = map_types(json.load(self.hyperparams_file))
		except ValueError as vae:
			print >> sys.stderr, "Could not decode hyperparameters:", vae
			sys.exit(self.error_dict['CouldNotParseHyperParams'])
		"""
		self.hyperparams = map_types(self.params['hyperparameters'])
	def read_data(self):
		""" Reads input data file """
		# We need to take the data and turn it into a numpy array
		dataformatx = self.params['inputs']['datax']['fmt']
		idatax_filen = self.params['inputs']['datax']['file']
		dataformaty = self.params['inputs']['datay']['fmt']
		idatay_filen = self.params['inputs']['datay']['file']
		if idatay_filen == None:
			self.idata = None
		if dataformatx == 'csv':
			try:
				#TODO: set dtype from parameters (perhaps inputs/data/type)
				self.idatax = np.loadtxt(idatax_filen,delimiter=',')
			except IOError as ioe:
				# I would expand the error handling here to handle each case if it makes sense to do so -- but if this is not the error handling approach we're taking I won't put time into it.
				print >> sys.stderr, "Could not open dataset file:", ioe
				sys.exit(self.error_dict['CouldNotOpenData'])
		
		else if dataformatx != None:
			print >> sys.stderr, "Unsupported data output format"
			sys.exit(self.error_dict['BadDataFormat'])


		if dataformaty == 'csv':
			try:
				self.idatay = np.loadtxt(idatay_filen,delimiter=',')
			except IOError as ioe:
				print >> sys.stderr, "Could not open dataset file:", ioe
				sys.exit(self.error_dict['CouldNotOpenData'])

		else if dataformaty != None:
			print >> sys.stderr, "Unsupported data output format"
			sys.exit(self.error_dict['BadDataFormat'])



	def load_model(self):
		""" Loads the model from the imodel field """
		model_filen = self.params['inputs']['model']['file']
		modelfmt = self.params['inputs']['model']['fmt']
		if model_filen == '':
			return False
		try:
			imodelfile = open(model_filen, 'r')
		except IOError as ioe:
			print >> sys.stderr, "Could not open model file:", ioe
			sys.exit(self.error_dict['CouldNotOpenModelFile'])

		if modelfmt == 'pickle':
			try:
				self.imodel = pickle.load(imodelfile)
			except pickle.UnpicklingError as upe:
				print >> sys.stderr, "Problem unpickling:", upe
				sys.exit(self.error_dict['CouldNotParseModelFile'])
		else if modelfmt != None:
			print >> sys.stderr, "Unsupported model input format"
			sys.exit(self.error_dict['UnsupportedModelFormat'])

		return True
	
	def generator(self):
		""" Handle generator transform """
		warm_start = self.load_model()
		if warm_start:
			try:
				self.imodel.set_params(**self.hyperparams)
			except TypeError as tpe:
				print >> sys.stderr, "Wrong hyper parameters", tpe
				sys.exit(self.error_dict['BadHyperParams'])
		else:
			try:
				self.imodel = self.model_module(**self.hyperparams)
			except TypeError as tpe:
				print >> sys.stderr, "Wrong hyper parameters", tpe
				sys.exit(self.error_dict['BadHyperParams'])

		# TODO: Integrate kwargs for fit functions
		if self.idatay != None: # Supervised
			self.imodel.fit(self.idatax, self.idatay)
		else: #Unsupervised
			self.imodel.fit(self.idatax)

		self.omodel = self.imodel
			
	def executor(self):
		""" Handle executor transform """
		if not self.load_model():
			print >> sys.stderr, "Executor cannot create a model, please supply one."
			sys.exit(self.error_dict['InvalidExecutor'])

		self.odatay = self.imodel.predict(self.idatax)
	
	def write_model(self):
		""" Write the serialized model if one was generated """
		omodel_filen = self.params['outputs']['model']['file']
		modelfmt = self.params['outputs']['model'['fmt']
		if omodel_filen == None:
			return False
		try:
			omodelfile = open(omodel_filen, 'w')
		except IOError as ioe:
			print >> sys.stderr, "Could not open model file for writing:", ioe
			sys.exit(self.error_dict['CouldNotOpenModelFile'])

		if modelfmt == 'pickle':
			try:
				pickle.dump(self.omodel, omodelfile)
			except pickle.PicklingError as pke:
				print >> sys.stderr, "Could not pickle the model", pke
				sys.exit(self.error_dict['CouldNotWriteModelFile'])
		else if modelfmt != None:
			print >> sys.stderr, "Unsupported model output format"
			sys.exit(self.error_dict['BadModelFormat'])

	def write_data(self):
		""" Write the predictions, transformed data (if there is any) """
		dataformatx = self.params['outputs']['datax']['fmt']
		odatax_filen = self.params['outputs']['datax']['file']
		dataformaty = self.params['outputs']['datay']['fmt']
		odatay_filen = self.params['outputs']['datay']['file']

		if dataformatx == 'csv':
			try:
				np.savetxt(odatax_filen, self.odatax, delimiter=',')
			except IOError as ioe:
				print >> sys.stderr, "Could not save transformed data file:", ioe
				sys.exit(self.error_dict['CouldNotWriteData'])	
		
		else if dataformatx != None:
			print >> sys.stderr, "Unsupported data output format"
			sys.exit(self.error_dict['BadDataFormat'])


		if dataformaty == 'csv':
			try:
				np.savetxt(odatay_filen, self.odatay, delimiter=',')
			except IOError as ioe:
				print >> sys.stderr, "Could not save labels file:", ioe
				sys.exit(self.error_dict['CouldNotWriteData'])

		else if dataformaty != None:
			print >> sys.stderr, "Unsupported data output format"
			sys.exit(self.error_dict['BadDataFormat'])

	def cleanup(self):
		""" Primarily just close up whatever files were used """
		for i in self.__dict__:
			if isinstance(self.__dict__[i], file):
				self.__dict__[i].close()

	def run(self):
		self.read_hyperparams()
		self.read_data()
		if self.params['params']['mode'] == 'executor':
			self.executor()
			self.write_data()
		elif self.params['params']['mode'] == 'generator':
			self.generator()
			self.write_model()
		self.cleanup()

		
if __name__ == "__main__": 
	""" This is how this is supposed to be run """
	params_file = sys.argv[1]
	transform = sklearn_transform_base(params_file)
	transform.run()


