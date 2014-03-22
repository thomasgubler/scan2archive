#!/usr/bin/env python

#@author Thomas Gubler <thomasgubler@gmail.com>
#License: GPLv3, see LICENSE.txt

import argparse
import datetime
import os
from subprocess import call


class Scan2Archive(object):
    '''
    classdocs
    '''


    def __init__(self, filename, ocrLanguage, device, mode, verbose, pdfsandwich):
        """ Constructor """
        
        self.filename = filename
        self.ocrLanguage = ocrLanguage
        self.device = device;
        self.mode = mode
        self.verbose = verbose
        
        self.pdfsandwich = pdfsandwich
        if pdfsandwich:
            print("Using pdfsandwich")
        else:
            print("Using tesseract directly")
        
    def run(self):
        """Scan and parse multiple documents """
        
        finished = False
        fileIndex = 0
        scanFiles = ""
        convertFiles = ""
        ocrFiles = ""
        
        while not finished:
            
            pageFilename =  self.filename + "_" + str(fileIndex)
            
            # scan page
            print("Starting scan")
            scanimageArguments = ""
            if self.device:
                scanimageArguments +=  "--device " + self.device
            scanimageArguments += " -x 215 -y 297 --resolution 150"
            scanimageArguments +=  " --mode " + self.mode
            scanimageOutputFilename = pageFilename + ".tiff"
            scanimageOutput = " > " + scanimageOutputFilename
            scanCommand = "scanimage " + scanimageArguments + " " + scanimageOutput
               
            if self.verbose: print(scanCommand)
            os.system(scanCommand)
            scanFiles += scanimageOutputFilename  + " ";
            print("Scan finished")

            # convert file
            print("Starting file conversion")
            convertOutputFilename = pageFilename + ".pdf"
            convertCommand = "convert " + scanimageOutputFilename + " " + convertOutputFilename
            if self.verbose: print(convertCommand)
            os.system(convertCommand)
            convertFiles += convertOutputFilename + " ";
            print("File conversion finished")
            
            #ocr
            if not self.pdfsandwich:
                print("OCR (direct) started")
                ocrOutputFilename = pageFilename # tesseract adds the '.txt' itself
                ocrCommand = "tesseract -l " + self.ocrLanguage + " " +  scanimageOutputFilename + " " + ocrOutputFilename
                if self.verbose: print(ocrCommand)
                os.system(ocrCommand)
                ocrFiles += ocrOutputFilename + ".txt "
                print("OCR finished")
                
                
                
            # check if this was the last page
            userInput = input("Page " + str(fileIndex) + " finished. Continue? Is the next page in the scanner? [Y/n]")
            if userInput == "n" or userInput == "N":
                finished = True
            
            fileIndex += 1
            
        # Merge everything
        print("Merging pages")
        pdfUniteOutputFilename = self.filename + ".pdf"
        if fileIndex > 1:
            # pdf unite
            print("Starting pdf unite")
            pdfuniteCommand = "pdfunite " + convertFiles + " " + pdfUniteOutputFilename
            if self.verbose: print(pdfuniteCommand)
            os.system(pdfuniteCommand)
            print("Finished pdf unite")
        else:
            # only one file, copy instead of pdfunite
            cpCommand = "cp " + convertFiles + " " + pdfUniteOutputFilename
            if self.verbose: print(cpCommand)
            os.system(cpCommand)
        
        if self.pdfsandwich:
            # use pdfsandwich
            print("OCR (pdfsandwich for whole pdf) started")
            ocrOutputFilename = pageFilename + "_ocr.pdf"
            ocrCommand = "pdfsandwich -lang " + self.ocrLanguage + " " +  pdfUniteOutputFilename + "-o " + pdfUniteOutputFilename                
            if self.verbose:
                ocrCommand += " -verbose"
                print(ocrCommand)
                os.system(ocrCommand)
            print("OCR finished")            
        else:
            print("Start merging text files")
            txtmergeOutputFilename = self.filename + "_ocr.txt"
            with open(txtmergeOutputFilename, 'w') as outfile:
                for fname in ocrFiles.split():
                    with open(fname) as infile:
                        for line in infile:
                            outfile.write(line)
            print("Finished merging text files")

        
        
        print("Merging finished")
        
        # Clean up
        rmCommand = "rm " + scanFiles + convertFiles + ocrFiles;
        if self.verbose: print(rmCommand);
        os.system(rmCommand)
        print("Cleaned up and done")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scan and archive documents')
    parser.add_argument('-o', dest='filename', action='store', default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), help='filename')
    parser.add_argument('-v', dest='verbose', action='store_true', help='verbose mode')
    parser.add_argument('-l', dest='ocrLanguage', default='deu', action='store', help='Language for OCR: eng, deu')
    parser.add_argument('-d', dest='device', action='store', default="" , help='scanner device name, get with imagescan -L')
    parser.add_argument('-m', dest='mode', action='store', default="Gray" , help='Gray or Color')
    parser.add_argument('--pdfsandwich', dest='pdfsandwich', action='store_true', default=False , help='Use pdfsandwich (NOT WORKING)')
    
    args = parser.parse_args()
    
    archiver = Scan2Archive(args.filename, args.ocrLanguage, args.device, args.mode, args.verbose, args.pdfsandwich);    
    archiver.run()
        