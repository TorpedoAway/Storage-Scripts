#!/var/www/flask-apps/bin/python3


import base64, sys

if len(sys.argv) != 3:
    print("b64tool.sh requires 2 arguments.")
    print("USAGE: ./b64tool.sh <encode|decode> <passwd>")
    print("Exiting...")
    sys.exit()


action = sys.argv[1]
pw = sys.argv[2]

if action == 'encode':
    encodedpw = base64.b64encode(pw.encode('ascii'))
    print(encodedpw)
elif action == 'decode':
    decodedpw = base64.b64decode(pw.encode('utf-8')).decode('utf-8')
    print(decodedpw)
else:
    print("Unknown action: " + action)

