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
			'real':float,
			'string':str,
			'bool':bool
	}
	newparams = dict()

	for p in params:
		if params[p]['Value'] == "":
			newparams[p] = None
			continue
		newparams[p] = type_map[params[p]['Type']](params[p]['Value']) # assume that this works because the validator should've checked it
	
	return newparams

class sklearn_transform_base:
	def __init__(self, params_file_s):
		""" Initializes the transform. Only takes a relative path to a JSON file that contains all of the system parameters """
		try:
			params_file = open(params_file_s, 'r')
		except IOError as ioe:
			# Not sure if I should raise an error or exit -- feel free to suggest which
			print >> sys.stderr, "Could not open system parameters", ioe
			sys.exit(-1)

		try:
			self.params = json.load(params_file)
		except ValueError as vae:
			print >> sys.stderr, "Could not decode parameters:", vae
			sys.exit(-1)

		params_file.close()
		self.module_name = str(self.params['Parameters']['module name'])

		relative_name = self.module_name.split('.')[-1] # Final module name, e.g. AffinityPropagation or KMeans

		# Importing
		try:
			mods = __import__(str('.'.join(self.module_name.split('.')[:-1])), globals(), locals(), [relative_name], -1)
		except ImportError as ime:
			print >> sys.stderr, "Could not import %s:" % self.params['Parameters']['module name'], ime
			sys.exit(-1)

		self.model_module = getattr(mods, relative_name)

	def read_hyperparams(self):
		""" Reads the input files based on their formats """
		# TODO: Decide if we're putting hyperparams in the json parameters or as a different file
		"""
		try:
			self.hyperparams_file = open(self.params['hyperparameters file'],'r')
		except IOError as ioe:
			print >> sys.stderr, "Could not open hyper parameters", ioe
			sys.exit(-1)
		
		try:
			self.hyperparams = map_types(json.load(self.hyperparams_file))
		except ValueError as vae:
			print >> sys.stderr, "Could not decode hyperparameters:", vae
			sys.exit(-1)
		"""
		self.hyperparams = map_types(self.params['HyperParameters'])
	def read_data(self):
		""" Reads input data file """
		# We need to take the data and turn it into a numpy array
		dataformatx = self.params['Inputs']['datax']['Format']
		idatax_filen = self.params['Inputs']['datax']['Path']

		# Load labels, if training
		try:
			dataformaty = self.params['Inputs']['datay']['Format']
			idatay_filen = self.params['Inputs']['datay']['Path']
		except KeyError:
			self.idatay = None
			dataformaty = ''
			idatay_filen = ''

		if dataformatx == 'csv':
			try:
				#TODO: set dtype from parameters (perhaps inputs/data/type)
				self.idatax = np.loadtxt(idatax_filen,delimiter=',')
			except IOError as ioe:
				# I would expand the error handling here to handle each case if it makes sense to do so -- but if this is not the error handling approach we're taking I won't put time into it.
				print >> sys.stderr, "Could not open dataset file:", ioe
				sys.exit(-1)
		
		else:# if dataformatx != '':
			print >> sys.stderr, "Unsupported X data input format"
			sys.exit(-1)


		if dataformaty == 'csv':
			try:
				self.idatay = np.loadtxt(idatay_filen,delimiter=',')
			except IOError as ioe:
				print >> sys.stderr, "Could not open dataset file:", ioe
				sys.exit(-1)

		else if dataformaty != '':
			print >> sys.stderr, "Unsupported y data input format"
			sys.exit(-1)



	def load_model(self):
		""" Loads the model from the imodel field """
		try:
			model_filen = self.params['InputStates']['model']['Path']
			modelfmt = self.params['InputStates']['model']['Format']
		except KeyError:
			return False
		try:
			imodelfile = open(model_filen, 'r')
		except IOError as ioe:
			print >> sys.stderr, "Could not open model file:", ioe
			sys.exit(-1)

		if modelfmt == 'pickle':
			try:
				self.imodel = pickle.load(imodelfile)
			except pickle.UnpicklingError as upe:
				print >> sys.stderr, "Problem unpickling:", upe
				sys.exit(-1)
		else:# if modelfmt != '':
			print >> sys.stderr, "Unsupported model input format"
			sys.exit(-1)

		return True
	
	def generator(self):
		""" Handle generator transform """
		warm_start = self.load_model()
		if warm_start:
			try:
				self.imodel.set_params(**self.hyperparams)
			except TypeError as tpe:
				print >> sys.stderr, "Wrong hyper parameters", tpe
				sys.exit(-1)
		else:
			try:
				self.imodel = self.model_module(**self.hyperparams)
			except TypeError as tpe:
				print >> sys.stderr, "Wrong hyper parameters", tpe
				sys.exit(-1)

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
			sys.exit(-1)

		self.odatay = self.imodel.predict(self.idatax)
	
	def write_model(self):
		""" Write the serialized model if one was generated """
		try:
			omodel_filen = self.params['OutputStates']['model']['Path']
			modelfmt = self.params['OutputStates']['model']['Format']
		except KeyError:
			return False
		try:
			omodelfile = open(omodel_filen, 'w')
		except IOError as ioe:
			print >> sys.stderr, "Could not open model file for writing:", ioe
			sys.exit(-1)

		if modelfmt == 'pickle':
			try:
				pickle.dump(self.omodel, omodelfile)
			except pickle.PicklingError as pke:
				print >> sys.stderr, "Could not pickle the model", pke
				sys.exit(-1)
		else:# if modelfmt != '':
			print >> sys.stderr, "Unsupported model output format"
			sys.exit(-1)

	def write_data(self):
		""" Write the predictions, transformed data (if there is any) """
		try:
			dataformatx = self.params['Outputs']['datax']['Format']
			odatax_filen = self.params['Outputs']['datax']['Path']
		except KeyError:
			odatax = None
			dataformatx = ''
			odatax_filen = ''

		dataformaty = self.params['Outputs']['datay']['Format']
		odatay_filen = self.params['Outputs']['datay']['Path']

		if dataformatx == 'csv':
			try:
				np.savetxt(odatax_filen, self.odatax, delimiter=',')
			except IOError as ioe:
				print >> sys.stderr, "Could not save transformed data file:", ioe
				sys.exit(-1)	
		
		else if dataformatx != '':
			print >> sys.stderr, "Unsupported data output format"
			sys.exit(-1)


		if dataformaty == 'csv':
			try:
				np.savetxt(odatay_filen, self.odatay, delimiter=',')
			except IOError as ioe:
				print >> sys.stderr, "Could not save labels file:", ioe
				sys.exit(-1)

		else:# if dataformaty != '':
			print >> sys.stderr, "Unsupported data output format"
			sys.exit(-1)

	def cleanup(self):
		""" Primarily just close up whatever files were used """
		for i in self.__dict__:
			if isinstance(self.__dict__[i], file):
				self.__dict__[i].close()

	def run(self):
		self.read_hyperparams()
		self.read_data()
		if self.params['Parameters']['mode'] == 'executor':
			self.executor()
			self.write_data()
		else if self.params['Parameters']['mode'] == 'generator':
			self.generator()
			self.write_model()
		self.cleanup()

		
if __name__ == "__main__": 
	""" This is how this is supposed to be run """
	params_file = sys.argv[1]
	transform = sklearn_transform_base(params_file)
	transform.run()


