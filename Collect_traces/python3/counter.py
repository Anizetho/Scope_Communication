# coding: utf-8

import subprocess


#################################################################################
################################ Collect traces #################################
#################################################################################

python2_command = 'C:\Python27\python.exe Python2_test.py arg1'
python3_command = 'C:\Python36\python.exe Python3_test.py arg1'
process = subprocess.Popen(python2_command.split(), stdout=subprocess.PIPE)
output, error = process.communicate()
print("Success")

i=0
while i<100:
    process = subprocess.Popen(python3_command.split(), stdout=subprocess.PIPE)
