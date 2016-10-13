#!/usr/bin/env python3

# @author Thomas Gubler <thomasgubler@gmail.com>
# License: GPLv3, see LICENSE.txt

import argparse
import datetime
import os
from subprocess import check_output


class Scan2Archive(object):

    """
    Scan2Archive scans, rotates and performs OCR over multiple pages.
    The output is a pdf and OCR data (embedded in the pdf or as text file).
    The class can be used to archive documents relatively quickly.
    """

    def __init__(self, filename, ocrLanguage, device,
                 mode, verbose, pdfsandwich, resolution, createTxt,
                 preOcrCheck, noOcr):
        """ Constructor """

        self.filename = filename
        self.ocrLanguage = ocrLanguage
        if device is None:
            self.device = self.find_device()
        else:
            self.device = device
        self.mode = mode
        self.verbose = verbose
        self.resolution = int(resolution)
        self.createTxt = createTxt
        self.preOcrCheck = preOcrCheck
        self.noOcr = noOcr

        self.pdfsandwich = pdfsandwich
        if pdfsandwich:
            print("Using pdfsandwich")
        else:
            print("Using tesseract directly")

    def find_device(self):
        """Use scanimage to find device"""
        output = check_output("scanimage -L", shell=True).decode('utf-8')

        if output.find("No scanners were identified") >= 0:
            raise Exception("No scanners found, try `scanimage -L`")

        # If we get more than one result from scanimage, we don't know which
        # device to choose and give up.
        if len(output.splitlines(True)) > 1:
            raise Exception("More than one scanner found, check `scanimage -L`")

        start = output.find("`")
        end = output.find("'")
        device = output[start+1:end]
        return device

    def run(self):
        """Scan and parse multiple documents """

        finished = False
        fileIndex = 0
        scanFiles = ""
        convertFiles = ""
        ocrFiles = ""
        pageRotation = 0.

        while not finished:
            rotationInput = input(
                "Put Page " +
                str(fileIndex) +
                " into scanner!\nEnter rotation in degrees cw [" +
                str(pageRotation) +
                "]:")
            if rotationInput:
                pageRotation = float(rotationInput)

            pageFilename = self.filename + "_" + str(fileIndex)

            # scan page
            print("Starting scan")
            scanimageArguments = ""
            if self.device:
                scanimageArguments += "--device '" + self.device + "'"
                scanimageArguments += " -x 215 -y 296.9 --resolution " + \
                    str(self.resolution)
                scanimageArguments += " --contrast 50"
                scanimageArguments += " --mode " + self.mode
                scanimageOutputFilename = pageFilename + ".tiff"
                scanimageOutput = " > " + scanimageOutputFilename
                scanCommand = "scanimage " + \
                    scanimageArguments + " " + scanimageOutput

            if self.verbose:
                print(scanCommand)

            # try this 3 times
            for i in range(3):
                ret = os.system(scanCommand)
                if ret == 0:
                    break
                print("Scanimage returned %d, trying again" % ret)
            else:
                raise Exception("%d unsuccessful tries, giving up" % i)
            scanFiles += scanimageOutputFilename + " "
            print("Scan finished")

            # rotate file (tiff to rotated tiff)
            rotateimageOutputFilename = scanimageOutputFilename
            if pageRotation != 0.:
                print("Starting rotation")
                rotateCommand = "convert -rotate " + \
                    str(pageRotation) + " " + scanimageOutputFilename + " " + \
                    rotateimageOutputFilename
                if self.verbose:
                    print(rotateCommand)
                os.system(rotateCommand)
                print("Rotation finished")

            preOcrCheckOk = True
            if self.preOcrCheck and not self.noocr:
                userInput = input(
                    "Page " +
                    str(fileIndex) +
                    " finished. Continue with OCR? Does the TIFF look ok?" +
                    " [Y/n]")
                if userInput == "n" or userInput == "N":
                    preOcrCheckOk = False

            if not self.pdfsandwich and preOcrCheckOk and not self.noOcr:
                # ocr (on rotated tiff)
                print("OCR (direct) started")
                # tesseract adds the '.txt' itself
                ocrOutputFilename = pageFilename
                ocrCommandBase = "tesseract -l " + self.ocrLanguage + " " + \
                    rotateimageOutputFilename + " " + ocrOutputFilename
                if self.createTxt:
                    # also create txt file with ocr output
                    if self.verbose:
                        print(ocrCommandBase)
                    os.system(ocrCommandBase)
                    ocrFiles += ocrOutputFilename + ".txt "

                # OCR and create pdf (tiff to pdf with OCR)
                ocrCommandPdf = ocrCommandBase + " pdf"
                if self.verbose:
                    print(ocrCommandPdf)
                os.system(ocrCommandPdf)
                convertFiles += ocrOutputFilename + ".pdf "
                print("OCR finished")
            elif preOcrCheckOk:
                # convert file (rotated tiff to pdf), prepare for pdfsandwich
                print("Starting file conversion")
                convertOutputFilename = pageFilename + ".pdf"
                convertCommand = "convert " + \
                    rotateimageOutputFilename + " " + convertOutputFilename
                if self.verbose:
                    print(convertCommand)
                os.system(convertCommand)
                convertFiles += convertOutputFilename + " "
                print("File conversion finished")

            if not preOcrCheckOk and self.noOcr:
                raise Exception("Logic error")

            # check if this was the last page
            if preOcrCheckOk:
                userInput = input(
                    "Page " +
                    str(fileIndex) +
                    " finished. Continue? Is the next page in the scanner?" +
                    " Repeat? [Y/n/r]")
                fileIndexAdd = 1
                if userInput == "n" or userInput == "N":
                    finished = True
                elif userInput == "r" or userInput == "R":
                    fileIndexAdd = 0

                fileIndex += fileIndexAdd

        # Merge everything
        print("Merging pages")
        pdfUniteOutputFilename = self.filename + ".pdf"
        if fileIndex > 1:
            # pdf unite
            print("Starting pdf unite")
            pdfuniteCommand = "pdfunite " + \
                convertFiles + " " + pdfUniteOutputFilename
            if self.verbose:
                print(pdfuniteCommand)
            os.system(pdfuniteCommand)
            print("Finished pdf unite")
        else:
            # only one file, copy instead of pdfunite
            cpCommand = "cp " + convertFiles + " " + pdfUniteOutputFilename
            if self.verbose:
                print(cpCommand)
            os.system(cpCommand)

        if self.pdfsandwich:
            # use pdfsandwich
            print("OCR (pdfsandwich for whole pdf) started")
            ocrCommand = "pdfsandwich -lang " + self.ocrLanguage + " " + \
                pdfUniteOutputFilename + " -o " + pdfUniteOutputFilename
            if self.verbose:
                ocrCommand += " -verbose"
                print(ocrCommand)
            os.system(ocrCommand)
            print("OCR finished")
        else:
            if self.createTxt:
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
        rmCommand = "rm " + scanFiles + convertFiles + ocrFiles
        if self.verbose:
            print(rmCommand)
        os.system(rmCommand)
        print("Cleaned up and done")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Scan and archive documents',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-o',
        dest='filename',
        action='store',
        default=datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S"),
        help='filename')
    parser.add_argument(
        '-v',
        dest='verbose',
        action='store_true',
        help='verbose mode')
    parser.add_argument(
        '-l',
        dest='ocrLanguage',
        default='deu',
        action='store',
        help='Language for OCR: eng, deu')
    parser.add_argument(
        '-d',
        dest='device',
        action='store',
        default=None,
        help='scanner device name, get with scanimage -L')
    parser.add_argument(
        '-m',
        dest='mode',
        action='store',
        default="Gray",
        help='Gray or Color')
    parser.add_argument(
        '--pdfsandwich',
        dest='pdfsandwich',
        action='store_true',
        default=False,
        help='Use pdfsandwich')
    parser.add_argument(
        '--txt',
        dest='createTxt',
        action='store_true',
        default=False,
        help='Also create text file with OCR data (only without --pdfsandwich)')
    parser.add_argument(
        '-r',
        dest='resolution',
        default=600,
        action='store',
        help='Resolution')
    parser.add_argument(
        '--preocrcheck',
        dest='preocrcheck',
        default=False,
        action='store_true',
        help='Ask user to check TIFF before OCR')
    parser.add_argument(
        '--noocr',
        dest='noocr',
        default=False,
        action='store_true',
        help='Disable OCR')

    args = parser.parse_args()
    # XXX check compatible flags

    archiver = Scan2Archive(args.filename, args.ocrLanguage, args.device,
                            args.mode, args.verbose, args.pdfsandwich,
                            args.resolution, args.createTxt, args.preocrcheck,
                            args.noocr)
    archiver.run()
