#!/usr/bin/env python
import random
import json
import sys
import os
from base_transform import process_transform_base
 
class split_rowwise(process_transform_base):
	def read_data(self):
		infmt = self.params['inputs']['data']['fmt']
		infile = self.params['inputs']['data']['file']
		if infmt == 'csv':
			# Just supporting csv for now...
			try:
				self.data = np.loadtxt(infile, delimiter=',')
				self.fmt = 'np'
			except IOError as ioe:
				print >> sys.stderr, "Could not read data:", ioe
				sys.exit(self.error_dict['CouldNotOpenData'])
		else:
			print >> sys.stderr, "Unsupported format / No data"
			sys.exit(self.error_dict['BadDataFormat'])

	def process_data(self):
		if self.params['params']['split']['value'] == 'random':
			split = random.randint(0,len(self.data)-1)
		else:
			split = int(self.params['split'])
			if split >= len(self.data):
				print >> sys.stderr, "Split is too large"
				sys.exit(-1)

		if self.fmt == 'np':
			self.odata1 = self.data[split:]
			self.odata2 = self.data[:split]

			
	def write_data(self):
		ofmt1 = self.params['outputs']['data1']['fmt']
		ofmt2 = self.params['outputs']['data2']['fmt']
		
		ofile1 = self.params['outputs']['data1']['file']
		ofile2 = self.params['outputs']['data2']['file']

		if ofmt1 == 'csv':
			try:
				np.savetxt(ofile1, self.odata1, delimiter=',')
			except IOError as ioe:
				print >> sys.stderr, "Could not write data"
				sys.exit(self.error_dict['CouldNotWriteData'])
		if ofmt2 == 'csv':
			try:
				np.savetxt(ofile2, self.odata2, delimiter=',')
			except IOError as ioe:
				print >> sys.stderr, "Could not write data"
				sys.exit(self.error_dict['CouldNotWriteData'])

		else:
			print >> sys.stderr, "Unsupported format / No data"
			sys.exit(self.error_dict['BadDataFormat'])



