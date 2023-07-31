# PDF TO DOCX CONVERTER

# Before running this script, install the following packages:
# pip install pdf2docx
from pdf2docx import Converter
pdf_file = 'sample.pdf'
docx_file = 'sample.docx'
# convert pdf to docx
cv = Converter(pdf_file)
cv.convert(docx_file, start=0, end=None) # start and end page
cv.close()