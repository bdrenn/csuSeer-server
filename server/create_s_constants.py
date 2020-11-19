import os
import json

HMACkey = str(os.urandom(64))
json_dump = json.dumps(HMACkey)

file = open("secret_constants.json", "w")
file.write(json_dump)
file.close()
