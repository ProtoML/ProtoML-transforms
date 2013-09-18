#!/usr/bin/python

# Takes in a datafile, and puts it into the output file. Can handle multiple formats.
# Does nothing to the datafile -- this is the identity transform essentially
# First we need to do optparse no matter what

from optparse import OptionParser

op = OptionParser()
op.add_option("-f","--input_file",dest='inp',action='store',type='string')
op.add_option("-o","--output_file",dest='outp',action='store',type='string')

options, args = op.parse_args()


# Error handling is good. Do that.

try:
	input_file = open(options.inp,'rb')
except IOError as ioe:
	print "Could not open file %s for reading" % options.inp, ioe

try:
	output_file = open(options.outp,'wb')
except IOError as ioe:
	print "Could not open file %s for writing" % options.outp, ioe


# Do something with input_file, in this case we're just going to take all of the bytes and write them to output_file!
output_file.write(input_file.read())

input_file.close()
output_file.close()

#Yes, writing your very own transform is that easy!
