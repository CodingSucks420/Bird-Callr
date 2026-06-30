import re

with open("requirements.txt", "r", encoding="utf-8") as f:
    reqs = f.read()

# Replace tensorflow with conditional environment markers
reqs = reqs.replace("tensorflow", "tensorflow; sys_platform == 'win32'\ntflite-runtime; sys_platform != 'win32'")

with open("requirements.txt", "w", encoding="utf-8") as f:
    f.write(reqs)
