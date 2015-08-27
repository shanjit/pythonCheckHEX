# -*- coding: utf-8 -*-
"""
Created on Tue Jun 30 15:53:47 2015

@author: tallon
"""

import argparse, sys
from PyQt4 import QtGui
from PyQt4.QtGui import QFileDialog

def process_hex(hexFile_path):
    """
    This helper function opens a .hex file and processes it in the
    following way:
        - read each line starting with a colon ":" and suppress
            leading and trailing whitespaces
        - for each line processed, creates a list of hexadecimal values
        - store the list of hexadecimal values into a bigger list, each of
            its item being the hexadecimal values of a line in the file
    input: 
        - hexFile_path: the path to a .hex file
    output: the list of hexadecimal values' lists
    """
    hexaList = []
    with open(hexFile_path, "rb") as newFile:
        for newLine in newFile.readlines():
            if newLine[0] == ":":
                stripLine = newLine.strip()[1:]
                hexaValues = [stripLine[x] + stripLine[x+1] 
                    for x in range(0, len(stripLine), 2)]
                hexaList.append(hexaValues)
        return hexaList    

def calculate_checksum(hexaValues):
    """
    This helper function calculates the checksum over a list of
    hexadecimal values; the result is then compared to the actual 
    checksum contained in the list
    input: 
        - hexaValues: a list of hexadecimal values; the last value of the
            list is the actual checksum as recorded from the .hex file
    output: if both calculated and actual checksum match, the function
        returns 0, otherwise, the function returns a tuple of
        (calculated checksum, actual checksum)
    """
    checksum = 0
    frame_chks = hexaValues[-1]
    for value in hexaValues[:-1]:
        checksum += int(value, 16)
    checksum &= 255
    checksum ^= 255
    checksum += 1
    checksum %= 256
    checksum = format(checksum, '02X')
    if checksum == frame_chks:
        return 0
    else:
        return (checksum, frame_chks)

def test_eof(hexaList, idx):
    """
    This helper function tests if the last processed line of the file
    contains the end of line identifier
    input: 
        - hexaList: the list of hexadecimal values' lists, such as the one
            returned by the process_hex() function
        - idx: the index of the FRAME_TYPE hexadecimal value
    output: if the last entry of hexaList contains the end of file
    identifier, then the function returns 0; otherwise, it returns the byte
    corresponding to the frame type of said entry
    """
    eof = hexaList[-1][idx]
    if eof == '01':
        return 0
    else:
        return eof

def test_length(hexaValues, idx_dlc, idx_data):
    """
    This helper function tests if the actual data length is matching the
    recorded data length of the corresponding line
    input: 
        - hexaValues: a list of hexadecimal values, which matches the line
            of the file processed with the process_hex() function
        - idx_dlc: the index of the FRAME_LENGTH hexadecimal value
        - idx_data: the index of the first data byte
    output: if both lengths match, the function returns 0; otherwise, it
    returns a tuple (actual length, recorded length)
    """
    value_len = int(hexaValues[idx_dlc], 16)
    dlc_len = len(hexaValues[idx_data:-1])
    if dlc_len == value_len:
        return 0
    else:
        return (dlc_len, value_len)

def main():
    
    """
    The script has 3 modes:
        - classic: command line, the path to the .hex file is entered
            manually
        - gui: the file is selected through a GUI; only .hex files can
            be selected
        - verbose: normally, the program stops whenever an error (eof
            missing, checksum not matching, etc...) occurs; the verbose
            mode goes on with the analysis until the file is fully analyzed;
            each error is reported and the total number is shown after
            analysis is done
    """
    argParser = argparse.ArgumentParser(description = "Parse a *.hex file\
    and control if eof is missing; for each line, performs both data length\
    control and checksum evaluation")
    argParser.add_argument('--gui', '-g', action = 'store_true',
                           help = "Use gui to browse files and get the hex")
    argParser.add_argument('--file_name', '-f', action = 'store',
                           help = "Enter the absolute path of an hex file")
    argParser.add_argument('--verbose', '-v', action = 'store_true',
                           help = "The verbose mode doesn't stop at the\
                           first error but processes the whole file\
                           and returns the number of errors")
                           
    args = argParser.parse_args()
    
    """
    Base indexes for the content of each line; for the record, the
    intel HEX specification divides each line into the following
    parts:
        - Start Code as an ASCII colon ":"
        - Byte Count gives the number of bytes in the Data parted; coded on
            1 bytes
        - Address for coding the data into the target device memory; coded
            on 2 bytes (not used by current implementation)
        - Record Type defining the meaning of the data field; coded from
            0x00 to 0x05 on a single byte
        - Data is a sequence of n bytes
        - Checksum is coded on a single byte
    """
    DATA_LENGTH_IDX   = 0   #index for the data length bytes
    #ADDRESS_START_IDX = 1
    FRAME_TYPE_IDX    = 3   #index for the frame type byte
    DATA_START_IDX    = 4   #index for the first data byte

    errorCount = 0          #error counter; used in verbose mode
    fileName = ''
    vMode = False
    
    #Check the flag for verbose mode; the flag is cleared by default
    if args.verbose:
        vMode = True
        
    #Call the QFileDialog that will act as the GUI to select the .hex file
    if args.gui:
        app = QtGui.QApplication(sys.argv)
        fileName = QFileDialog.getOpenFileName(caption = 'select HEX', 
        filter = "HEX (*.hex)")
        app.exit()
    
    #Check if the file exists
    elif args.file_name:
        fileName = args.file_name
    else:
        print "undefined argument"
        return -1
    
    #Check if a file has been given as an argument
    if fileName:
        hexaList = process_hex(fileName)
    else:
        raise IOError("No file selected")
    
    #Check if end of file is missing
    eof = test_eof(hexaList, FRAME_TYPE_IDX)
    if  eof != 0:
        print "Wrong data formatting: 0x01 expected at index {0} in line {1}; \
        obtained {2}".format(FRAME_TYPE_IDX, len(hexaList), eof)
        if vMode:
            errorCount += 1
        else:
            return -1
    
    #For each processed line:
    for index, hexaValues in enumerate(hexaList):
        
        #Check if the data length is matching
        length = test_length(hexaValues, DATA_LENGTH_IDX, DATA_START_IDX)
        if length != 0:
            print "Wrong data length at line {0}: expected 0x{1}, obtained 0x{2}"\
            .format(index + 1, format(length[0], '02x'), format(length[1], '02x'))
            if vMode:
                errorCount += 1
            else:
                return -1
        
        #Check if the checksum is correct
        checksum = calculate_checksum(hexaValues)
        if checksum == 0:
            print "Checksum line {0}: OK".format(index + 1)
        else:
            print "Checksum line {0}: failed, expected 0x{1}, obtained 0x{2}"\
            .format(index + 1, checksum[1], checksum[0])
            if vMode:
                errorCount += 1
            else:
                return -1
    
    #Print the total number of errors
    if vMode:
        print "Total errors: {0}".format(errorCount)

if __name__ == "__main__":
    main()