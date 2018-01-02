#!/usr/bin/env python

import os
import sys
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from PIL import Image as image

def comp(x,y):
	i = cmp(len(x),len(y))
	return i if i else cmp(x,y)

def getFileList(dir):
	return map(lambda x: os.path.join(dir, x),
	 sorted(os.listdir(dir), comp))

def conpdf(f_pdf, f_list, ratio=1, quality=95):
  (w, h) = landscape(A4)
  c = canvas.Canvas(f_pdf, pagesize = landscape(A4))
  i = 0
  for jpg in f_list:
    im = image.open(jpg)
    (ori_w,ori_h) = im.size
    im1 = im.resize((int(ori_w/ratio), int(ori_h/ratio)), image.ANTIALIAS)
    tmpf = "tmp%d_%d.jpg" % (os.getpid(), i)
    im1.save(tmpf, format="jpeg", quality=quality, optimize=True)
    c.drawImage(tmpf, 0, 0, w, h)
    os.remove(tmpf)
    c.showPage()
    im.close()
    im1.close()
    i = i + 1
  c.save()

  
if __name__ == "__main__":
  if len(sys.argv) not in range(2, 5):
    print "Usage: %s <jpgs_dir> [<ratio> [<quality>]]\n" % os.path.basename(sys.argv[0])
    print "       <jpgs_dir> : the directory path of jpg files\n"
    print "       <ratio>    : the ratio of jpg files to the target files\n"
    print "       <quality>  : the quality of jpg to be drawed, 1~95, 1 worst, 95, best\n"
    exit(1)
  ratio = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
  quality = int(sys.argv[3]) if len(sys.argv) > 3 else 95
  output = "result_%.2f_%d.pdf" % (ratio, quality)
  conpdf(output, getFileList(sys.argv[1]), ratio, quality)
  print "The file %s generated successfully!\n" % output
  