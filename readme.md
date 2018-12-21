# Scan2Archive

Scan2Archive scans, rotates and performs OCR over multiple pages. The output is a pdf and OCR data (embedded in the pdf or as text file).
The script can be used to archive documents relatively quickly.

run scan2archive.py --help for an argument list

## Dependencies

### Arch Linux

```
pacman -S sane
pacman -S tesseract tesseract-data-deu tesseract-data-eng
```

## Troubleshooting

### PDF files not found, convert operation not allowed

If the PDFs are not found:
```
rm: cannot remove '2018-12-21_12_49_44_0.pdf': No such file or directory
```

And you also see:
```
convert: attempt to perform an operation not allowed by the security policy `PDF' @ error/constitute.c/IsCoderAuthorized/408.
```

Add this line to `/etc/ImageMagick-7/policy.xml`:
```
<policy domain="coder" rights="read | write" pattern="PDF" />
```
