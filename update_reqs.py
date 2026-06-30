import re

with open("requirements.txt", "r", encoding="utf-8") as f:
    reqs = f.read()

# Replace tflite-runtime with tensorflow
reqs = reqs.replace("tflite-runtime", "tensorflow")

with open("requirements.txt", "w", encoding="utf-8") as f:
    f.write(reqs)
