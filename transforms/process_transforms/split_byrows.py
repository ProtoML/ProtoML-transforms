#!/usr/bin/env python
import random
import json
import sys
import os
from base_transform import process_transform_base

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

class split_rowwise(process_transform_base):
	def read_data(self):
		infmt = self.params['Inputs']['data']['Format']
		infile = self.params['Inputs']['data']['Path']
		if infmt == 'csv':
			# Just supporting csv for now...
			try:
				self.data = np.loadtxt(infile, delimiter=',')
				self.fmt = 'np'
			except IOError as ioe:
				print >> sys.stderr, "Could not read data:", ioe
				sys.exit(-1)
		else:
			print >> sys.stderr, "Unsupported format / No data"
			sys.exit(-1)

	def process_data(self):
		if self.hyperparameters['split'] == 'random':
			split = random.randint(0,len(self.data)-1)
		else:
			split = self.hyperparameters['split']
			if split >= len(self.data):
				print >> sys.stderr, "Split is too large"
				sys.exit(-1)

		if self.fmt == 'np':
			self.odata1 = self.data[split:]
			self.odata2 = self.data[:split]

			
	def write_data(self):
		ofmt1 = self.params['Outputs']['data1']['Format']
		ofmt2 = self.params['Outputs']['data2']['Format']
		
		ofile1 = self.params['Outputs']['data1']['Path']
		ofile2 = self.params['Outputs']['data2']['Path']

		if ofmt1 == 'csv':
			try:
				np.savetxt(ofile1, self.odata1, delimiter=',')
			except IOError as ioe:
				print >> sys.stderr, "Could not write data"
				sys.exit(-1)
		if ofmt2 == 'csv':
			try:
				np.savetxt(ofile2, self.odata2, delimiter=',')
			except IOError as ioe:
				print >> sys.stderr, "Could not write data"
				sys.exit(-1)

		else:
			print >> sys.stderr, "Unsupported format / No data"
			sys.exit(-1)



