## Intel HEX Format Checker
This is a simple script that can be used to check an Intel HEX file.
The following tests are performed:
* Missing end of file
* Checksum verification
* Data length verification
The script relies on argparse library and can be called from the command line with the following arguments:
* gui/g: the .hex file is selected through a standard Qt visual interface; only .hex files can be selected.
* file_name/f: the path to the .hex file is entered manually.
* verbose/v: the default working method for the script is to stop at the first error; in verbose mode, the script won't stop until all the lines have been checked; the total number of errors is counted and displayed.
