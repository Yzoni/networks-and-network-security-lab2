import ast
import os
import subprocess

query_string = ast.literal_eval(os.environ['QUERY_STRING'])

if query_string:
    if 'ip' in query_string:
        ip = query_string['ip']
        proc = subprocess.Popen(['traceroute', ip], stderr=subprocess.STDOUT)
        print(proc.stdout)
    else:
        print('ip not set')
else:
    print('ip not set')
