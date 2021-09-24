import pdoc
import sys
from pathlib import Path

paths = [
    "F:\\personal_work\\dev",
    "C:\\Program Files\\Adobe\\Adobe Substance 3D Designer\\resources\\python",
    "C:\\Program Files\\Adobe\\Adobe Substance 3D Designer\\plugins\\pythonsdk\\Lib\\site-packages"
]
for path in paths:
    sys.path.append(path)


path = "F:/personal_work/dev/bw_tools"
pdoc.pdoc(
    path, output_directory=Path("F:/personal_work/dev/bw_tools/doc.html")
)
