#!/usr/bin/python
import json
import cPickle as pickle
import sys
import numpy as np
from optparse import OptParse

op = OptParse()

op.add_option('-e','--executor',dest='executor',action='store_true',default=False,help="If true, just read lmodel and execute it on readfile")
op.add_option('-f','--readfile',dest='inputf',action='store',type='string',help="Input dataset")
op.add_option('-t','--filetype',dest='inputft',action='store',type='string',help="Input file type")
op.add_option('-fmt','--format',dest='inputfmt',action='store',type='string'help="Input file type format")
op.add_option('-l', '--loadmodel',dest='lmodel',action='store',type='string',help="Put serialized model here for warm start (generator)/executor")
op.add_option('-o','--savemodel',dest='omodel',action='store',type='string',help="If generator, save serialized model here")
op.add_option('-p','--params',dest='paramf',action='store',type='string',help="Read the model's initialization parameters from here")
op.add_option('-m','--modelpackage',dest='modelp',action='store',type='string',help="Fully qualified package name of model, will check to make sure it's in sklearn.")

error_dict = {
		'IncorrectPackage': 1,
		'CouldNotOpenTrainData': 2,
		'BadParameters': 3,
		'BadPickle': 4,
		'CouldNotOpenPickle': 5,
		'BadPackage':6,
		'CouldNotOpenParams':7,
		'BadJSONParams':8,
		'InvalidUse':9
		}



options, args = op.parse_args()

try:
	train_dataf = open(options.inputf,'r')
except IOError as ioe:
	print "Could not open training data", ioe
	sys.exit(error_dict['CouldNotOpenTrainData'])
paramf = options.paramf
module_name = options.modelp
lmodel = options.lmodel
omodel = options.omodel
executor = options.executor
inputf = options.inputf

# Importing

if module_name.split('.')[0] != 'sklearn':
	print "This transform is only for scikit-learn modules."
	sys.exit(error_dict['IncorrectPackage'])

try:
	__import__(module_name)
except ImportError as ime:
	print "Could not import %s:" % module_name, ime
	sys.exit(error_dict['BadPackage'])

model_module = sys.modules[module_name]

# Opening Data File
# Two things need to be satisfied -- file type and file format. Handling all file formats is a bitch, so for now I'll just handle csv
# TODO: Make utility function to handle multiple format types that I can just import
data = np.loadtxt(inputf,delimiter=',')
# So np.loadtxt will not handle missing data, and frankly neither will scikit-learn. Ideally this transform's data loading should be transparent from
# the file to the model, so this should be the most direct way of doing it. Data preprocessing transforms will take care of missing/categorical/etc data.

# For now, I'll assume this has been taken care of -- automated type system would make sense.

# Executor / Generator Logic
if options.lmodel != None:
	# We need to load the module
	# We're using pickle (protocol 2) for pickling, so assume that a model is contained in a pickle.
	try:
		model = open(lmodel,'r')
	except IOError as ioe:
		print "Could not open model:", ioe
		sys.exit(error_dict['CouldNotOpenPickle'])
	try:
		clustering_obj = pickle.load()
	except pickle.UnpicklingError as upe:
		print "Problem unpickling:", upe
		sys.exit(error_dict['BadPickle']) #Not sure if this will work...
	# Alright, now we can use the clustering thingie... not sure if this will ever happen but this pattern is nice to develop
	if executor:
		# We're just executing a trained model, so simply run the cluster on the data
	else:
		# We're warm starting, so retrain loaded model on new data

else:
	# We're initializing the model
	# Make sure we're not expected to be in the executor context
	if executor:
		print "Executor cannot create a model"
		sys.exit(error_dict['InvalidUse'])
	
	try:
		paramsf = open(paramf,'r')
	except IOError as ioe:
		print "Could not open parameter file:", ioe
		sys.exit(error_dict['CouldNotOpenParams'])

	try:
		params = json.load(paramsf)
	except ValueError as vae:
		print "Could not decode parameters:", vae
		sys.exit(error_dict['BadJSONParams'])
	try:
		clustering_obj = model_module(**params)
	except TypeError as te:
		print "Wrong type of parameters for the %s module" % module_name.split('.')[-1]
		sys.exit(error_dict['BadParameters'])

	# Now it's time to train the model on the data
	
		

