import requests

# URL da API do Prometheus
prometheus_url = 'http://localhost:9090/api/v1/query'

# Query para buscar o uso total de memória de todos os pods no cluster
memory_query = 'sum(container_memory_usage_bytes)'

# Query para buscar o uso total de CPU de todos os pods no cluster (taxa de uso de CPU)
cpu_usage_query = 'sum(rate(container_cpu_usage_seconds_total[5m]))'

# Query para buscar o total de núcleos de CPU alocados no cluster
cpu_limit_query = 'sum(kube_node_status_allocatable{resource="cpu"})'

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

# Obter dados de uso de CPU
cpu_usage_data = prometheus_query(cpu_usage_query)

# Obter dados de alocação de CPU
cpu_limit_data = prometheus_query(cpu_limit_query)

# Exibir uso de memória e CPU total do cluster
if memory_data:
    total_memory_usage_bytes = float(memory_data[0]['value'][1])
    total_memory_usage_megabytes = total_memory_usage_bytes / (1024 * 1024)
    
    # Uso total de CPU (em cores)
    total_cpu_usage_cores = float(cpu_usage_data[0]['value'][1])
    
    # Total de núcleos disponíveis
    total_cpu_limit_cores = float(cpu_limit_data[0]['value'][1])
    
    # Calcular uso de CPU em percentual
    cpu_usage_percent = (total_cpu_usage_cores / total_cpu_limit_cores) * 100 if total_cpu_limit_cores > 0 else 0.0

    print(f'Uso de memória total no cluster: {total_memory_usage_megabytes:.2f} MB')
    #print(f'Uso de CPU total no cluster: {total_cpu_usage_cores:.4f} cores')
    print(f'Uso de CPU total no cluster: {cpu_usage_percent:.2f}%')
else:
    print('Nenhum dado encontrado para o cluster')
