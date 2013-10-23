JSON
====

The format for the JSON files should be as follows:

Transform: 
	Template (string) -- The name of the Transform
	Exclusive Input Types (list) -- Types of Inputs (i.e. categorical, ordinal, labeled, etc) it takes as primary input
	Additional Input Types (list) -- Similar but for additional input
	Exclusive Output Types (list) -- Types of Outputs it gives
	Additional Output Types (list) -- Similar
	Exec -- (string) Script/binary to execute
	Exec Flags (list of dictionaries) -- Param: --parameter, Default: default_value, Description: string
	// Each parameter will be given through the command line. Generally datasets will be pushed through as files.
	Params (map of strings to anything) -- additional information, e.g. list of data formats it takes (i.e. csv, hdfs5, pickle)

