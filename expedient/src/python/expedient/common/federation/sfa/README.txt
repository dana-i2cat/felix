
Introduction
============

This directory ('sfa') contains code from PlanetLab. The code in this
directory is subject to the PlanetLab license (see "License"
below). There are a small number of modifications to the code. These
modifications are documented in the "Modifications" section below.

This code is based on revision a47009da40674dd0a91b37c75eaf605c2de76330 
(Sept. 21, 2010) of the master branch of the  PlanetLab Git repository
(git.planet-lab.org/git/sfa.git).


License
=======

Copyright (c) 2008 Board of Trustees, Princeton University

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and/or hardware specification (the "Work") to
deal in the Work without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Work, and to permit persons to whom the Work
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Work.

THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS 
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS 
IN THE WORK.


Modifications
=============

1. util/sfalogging.py was modified so that it does not use the root
   logger. Instead, it uses a logger named 'sfa'.

   Old:

     logger=logging.getLogger()

   New:

     logger=logging.getLogger('sfa')

2. All Python source files were modified to include the following
Princeton copyright notice:

#----------------------------------------------------------------------
# Copyright (c) 2008 Board of Trustees, Princeton University
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and/or hardware specification (the "Work") to
# deal in the Work without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Work, and to permit persons to whom the Work
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Work.
#
# THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS 
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS 
# IN THE WORK.
#----------------------------------------------------------------------
