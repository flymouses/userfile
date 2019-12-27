#python Tab
import sys  
import readline  
import rlcompleter  
import atexit  
import os   
import platform
readline.parse_and_bind('tab: complete')  

if platform.system().lower() == 'windows':
    # windows
    histfile = os.path.join(os.environ['HOMEPATH'], '.pythonhistory')
else:  
    # linux
    histfile = os.path.join(os.environ['HOME'], '.pythonhistory')  
try:  
    readline.read_history_file(histfile)  
except IOError:  
    pass  
atexit.register(readline.write_history_file, histfile)  
 
del os, histfile, readline, rlcompleter
