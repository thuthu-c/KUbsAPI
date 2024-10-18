import requests

# URL da API do Prometheus
prometheus_url = 'http://localhost:9090/api/v1/query'

# Query para buscar o uso de memória de cada nó
memory_query = 'sum(container_memory_usage_bytes) by (node)'

# Query para buscar o uso de CPU de cada nó (taxa de uso de CPU)
cpu_usage_query = 'sum(rate(container_cpu_usage_seconds_total[5m])) by (node)'

# Query para buscar o total de núcleos de CPU alocados para cada nó
cpu_limit_query = 'sum(kube_node_status_allocatable{resource="cpu"}) by (node)'

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

# Exibir uso de memória e CPU de cada nó
if memory_data:
    print('Uso de memória e CPU dos nós:')
    for node_data in memory_data:
        node_name = node_data['metric']['node']
        memory_usage_bytes = float(node_data['value'][1])
        memory_usage_megabytes = memory_usage_bytes / (1024 * 1024)
        
        # Uso de CPU (em cores)
        cpu_usage_node = next((float(item['value'][1]) for item in cpu_usage_data if item['metric']['node'] == node_name), 0.0)
        
        # Limite de CPU (número total de núcleos disponíveis)
        cpu_limit_node = next((float(item['value'][1]) for item in cpu_limit_data if item['metric']['node'] == node_name), 1.0)  # Padrão 1.0 se não houver
        
        # Calcular uso de CPU em percentual
        cpu_usage_percent = (cpu_usage_node / cpu_limit_node) * 100 if cpu_limit_node > 0 else 0.0
        
        print(f'Nó {node_name}:')
        print(f'  - Uso de memória: {memory_usage_megabytes:.2f} MB')
        #print(f'  - Uso de CPU: {cpu_usage_node:.4f} cores')
        print(f'  - Uso de CPU: {cpu_usage_percent:.2f}%')
else:
    print('Nenhum dado encontrado para os nós')
