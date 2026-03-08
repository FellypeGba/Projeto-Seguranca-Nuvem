import requests

#url = "http://localhost:5000/admin" #ataque local
url = "http://api:5000/admin" # Ataque no Docker

for i in range(5):
    r = requests.get(url)
    print(r.status_code)