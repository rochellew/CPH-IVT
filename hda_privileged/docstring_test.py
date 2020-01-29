import os
from pyment import PyComment

filename = 'test.py'

c = PyComment(filename)
c.proceed()
c.diff(os.path.basename(filename) + ".patch")
for s in c.get_output_docs():
    print(s)
