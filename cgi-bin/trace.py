import subprocess
import ast
import os

query_string = ast.literal_eval(os.environ['QUERY_STRING'])
ip = query_string['ip']

proc = subprocess.Popen(['traceroute', ip])
print(proc.stdout)