#!/usr/bin/env python

# Takes in a datafile, and puts it into the output file. Can handle multiple formats.
# This is the base for a process transform -- it reads the file, reads the parameters, calls 'process', then writes the result
# This particular script does nothing i.e. an identity transform. Inherit from it for other data process pattern transforms.
import json
import os
import sys
import shutil

class process_transform_base:
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
			if params[p]['Value'] == "":
				newparams[p] = None
				continue
			if type(params[p]['Type']) == list:
				for opt in params[p]['Type']:
					#Quick hack. Order your possible types in most-constrained to least constrained
					try:
						newparams[p] = type_map[opt](params[p]['Value'])
					except ValueError:
						continue
					break
				continue
			newparams[p] = type_map[params[p]['Type']](params[p]['Value'])

		return newparams


	#TODO: Better way to get error dict in here
	def __init__(self, params_file_s):	
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
		try:
			self.idata_file = open(self.params['Inputs']['data'], 'r')
		except IOError as ioe:
			print >> sys.stderr, "Could not open input file", ioe
			sys.exit(-1)
		
		try:
			self.odata_file = open(self.params['Outputs']['data'], 'w')
		except IOError as ioe:
			print >> sys.stderr, "Could not open output file", ioe
			sys.exit(-1)

		self.params['Parameters'] = map_types(self.params['Parameters'])


	def read_data(self):	
		""" Reads input. Base version just stores file"""
		self.idata = self.idata_file
		
	def process_data(self):
		""" Main meat of it, does something with self.idata and puts the result in self.odata. Base version just copies """
		self.odata = self.idata

	def write_data(self):
		""" Writes output. Base version just copies the input file """
		shutil.copyfileobj(self.odata,self.odata_file)

	def cleanup(self):
		""" Primarily just close up whatever files were used """
		for i in self.__dict__:
			if isinstance(self.__dict__[i], file):
				self.__dict__[i].close()

	def run(self):
		self.read_data()
		self.process_data()
		self.write_data()
		self.cleanup()

if __name__ == '__main__':
	params_file = sys.argv[1]
	transform = process_transform_base(params_file)
	transform.run()
