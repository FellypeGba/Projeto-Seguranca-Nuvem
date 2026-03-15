import requests

#url = "http://localhost:5000/admin" #ataque local
url = "http://gateway:5000/admin" # Ataque no Docker via Gateway

for i in range(5):
    r = requests.get(url)
    print(r.status_code)

# Testar /users
url_users = "http://gateway:5000/users"
r_users = requests.get(url_users) # Testar acesso ao endpoint /users
print(f"Users response: {r_users.json()}")