with open("logs/api.log") as f:
    lines = f.readlines()

# todos os eventos gravados no log
print("Eventos registrados (linhas totais):", len(lines))

# contar apenas hits ao endpoint admin
admin_hits = [l for l in lines if "admin endpoint accessed" in l]
print("Acessos ao /admin:", len(admin_hits))
