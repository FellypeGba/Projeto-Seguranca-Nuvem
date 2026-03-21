import os

# Função para ler arquivo de log de forma segura
def read_log_file(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.readlines()
        except UnicodeDecodeError:
            # Fallback para latin-1 se utf-8 falhar
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.readlines()
    else:
        print(f"Aviso: Arquivo {filepath} não encontrado.")
        return []

# Ler logs do gateway e da API
gateway_lines = read_log_file("logs/gateway.log")
api_lines = read_log_file("logs/api.log")

print("=== MÉTRICAS DE MONITORAMENTO ===\n")

# Métricas do Gateway (ponto de entrada)
print("GATEWAY (Ponto de Entrada):")
gateway_requests = [l for l in gateway_lines if "Requisição para" in l]
print(f"  Total de requisições recebidas: {len(gateway_requests)}")

gateway_data_requests = [l for l in gateway_requests if "/data" in l]
gateway_admin_requests = [l for l in gateway_requests if "/admin" in l]
gateway_users_requests = [l for l in gateway_requests if "/users" in l]

print(f"  Requisições para /data: {len(gateway_data_requests)}")
print(f"  Requisições para /admin: {len(gateway_admin_requests)}")
print(f"  Requisições para /users: {len(gateway_users_requests)}")

# Status das requisições (bem-sucedidas vs bloqueadas)
successful_requests = [l for l in gateway_requests if "Status: 200" in l]
blocked_requests = [l for l in gateway_requests if "Status: 403" in l]

print(f"  Requisições bem-sucedidas (200): {len(successful_requests)}")
print(f"  Requisições bloqueadas (403): {len(blocked_requests)}")

print()

# Métricas da API (processamento interno)
print("API (Processamento Interno):")
api_accesses = [l for l in api_lines if "endpoint accessed" in l]
print(f"  Total de acessos processados: {len(api_accesses)}")
api_data_accesses = [l for l in api_accesses if "/data" in l]
api_admin_accesses = [l for l in api_accesses if "admin" in l]
api_users_accesses = [l for l in api_accesses if "/users" in l]
api_login_attempts = [l for l in api_lines if "Tentativa de login" in l]
api_login_failures = [l for l in api_lines if "Falha de login" in l]

print(f"  Acessos ao /data: {len(api_data_accesses)}")
print(f"  Acessos ao /admin: {len(api_admin_accesses)}")
print(f"  Acessos ao /users: {len(api_users_accesses)}")
print(f"  Tentativas de login totais: {len(api_login_attempts)}")
print(f"  Falhas de login (possível Brute Force): {len(api_login_failures)}")
