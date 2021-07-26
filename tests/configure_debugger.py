import sys

debugpy_path = 'F:\\personal_work\\dev\\bw_tools\\env\\Lib\\site-packages'
debugpy_port = 5678
designer_py_interpreter = 'C:\\Program Files\\Adobe\\Adobe Substance 3D Designer\\plugins\\pythonsdk\\python.exe'

if not debugpy_path in sys.path:
    sys.path.append(debugpy_path)

import debugpy

debugpy.configure(python=designer_py_interpreter)
debugpy.listen(debugpy_port)