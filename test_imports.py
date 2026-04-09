import sys

results = []
results.append(f"Python: {sys.version}")

try:
    import numpy as np
    results.append("numpy: OK")
except Exception as e:
    results.append(f"numpy: FAILED - {e}")

try:
    import trimesh
    results.append("trimesh: OK")
except Exception as e:
    results.append(f"trimesh: FAILED - {e}")

try:
    from OpenGL.GL import glClearColor
    results.append("OpenGL: OK")
except Exception as e:
    results.append(f"OpenGL: FAILED - {e}")

try:
    from PyQt5.QtWidgets import QApplication, QOpenGLWidget
    results.append("QOpenGLWidget: OK")
except Exception as e:
    results.append(f"QOpenGLWidget: FAILED - {e}")

with open(r"c:\Users\benkr\OneDrive\can_project\test_result.txt", "w") as f:
    f.write("\n".join(results))
