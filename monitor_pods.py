import requests
import json

# URL da API do Prometheus
prometheus_url = 'http://localhost:9090/api/v1/query'

# Nome do namespace que você deseja monitorar
namespace = 'default'

# Query para buscar o uso de memória de todos os pods em um namespace específico
memory_query = f'sum(container_memory_usage_bytes{{namespace="{namespace}"}}) by (pod)'

# Query para buscar o uso de CPU de todos os pods em um namespace específico (taxa de uso de CPU)
cpu_usage_query = f'rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[5m]) by (pod)'

# Query para buscar o limite de CPU (cores) de cada pod
cpu_limit_query = f'sum(kube_pod_container_resource_limits_cpu_cores{{namespace="{namespace}"}}) by (pod)'

# Função para fazer requisição ao Prometheus
def prometheus_query(query):
    response = requests.get(prometheus_url, params={'query': query})
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'success':
            return data['data']['result']
        else:
            print('Falha ao consultar o Prometheus:', data['error'])
            return []
    else:
        print(f'Erro na requisição HTTP: {response.status_code}')
        return []

# Obter dados de uso de memória
memory_data = prometheus_query(memory_query)

# Obter dados de uso de CPU (taxa)
cpu_usage_data = prometheus_query(cpu_usage_query)

# Obter dados do limite de CPU
cpu_limit_data = prometheus_query(cpu_limit_query)

# Dicionário para mapear pod ao uso de CPU e limites de CPU
cpu_usage = {item['metric']['pod']: float(item['value'][1]) for item in cpu_usage_data}
cpu_limits = {item['metric']['pod']: float(item['value'][1]) for item in cpu_limit_data}

# Exibir uso de memória e CPU de cada pod
if memory_data:
    print(f'Uso de memória e CPU (em %) dos pods no namespace {namespace}:')
    for pod_data in memory_data:
        pod_name = pod_data['metric']['pod']
        memory_usage_bytes = float(pod_data['value'][1])
        memory_usage_megabytes = memory_usage_bytes / (1024 * 1024)
        
        # Uso de CPU (em cores)
        cpu_usage_pod = cpu_usage.get(pod_name, 0.0)  # Taxa de uso de CPU
        cpu_limit_pod = cpu_limits.get(pod_name, 1.0)  # Limite de CPU (padrão 1.0 core se não houver limite)

        # Calcular uso de CPU em percentual
        cpu_usage_percent = (cpu_usage_pod / cpu_limit_pod) * 100 if cpu_limit_pod > 0 else 0.0
        
        print(f'Pod {pod_name}:')
        print(f'  - Uso de memória: {memory_usage_megabytes:.2f} MB')
        print(f'  - Uso de CPU: {cpu_usage_percent:.2f}%')
else:
    print(f'Nenhum dado encontrado para o namespace {namespace}')
