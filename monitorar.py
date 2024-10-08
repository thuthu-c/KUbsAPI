from prometheus_api_client import PrometheusConnect
import pandas as pd

# Conectar ao Prometheus (substitua pela URL correta se necessário)
prom = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)

# Consulta PromQL para obter o uso de CPU de cada pod no namespace "default" em milicores
cpu_usage_query = 'sum(rate(container_cpu_usage_seconds_total{namespace="default"}[5m])) by (pod) * 1000'

# Consulta PromQL para obter o uso de memória de cada pod no namespace "default" em bytes
memory_usage_query = 'sum(container_memory_usage_bytes{namespace="default"}) by (pod)'

# Executar as consultas
cpu_usage = prom.custom_query(cpu_usage_query)
memory_usage = prom.custom_query(memory_usage_query)

# Defina o total de CPU disponível para cada nó (em milicores)
total_cpu_milicores = 1000  # Exemplo: 1 núcleo de CPU

# Defina o total de memória disponível para cada nó (em bytes)
total_memory_bytes = 8 * 1024 * 1024 * 1024  # Exemplo: 8 GB de RAM

# Listas para armazenar os dados
pod_names = []
cpu_percentages = []
memory_percentages = []

# Variáveis de controle para verificar se há algum pod com mais de 1% de uso de CPU ou memória
has_high_cpu_usage = False
has_high_memory_usage = False

# Processar os resultados de CPU
for item in cpu_usage:
    pod_name = item['metric']['pod']
    cpu_value_milicores = float(item['value'][1])  # O valor em milicores
    cpu_percentage = (cpu_value_milicores / total_cpu_milicores) * 100  # Calcular a porcentagem
    
    # Adicionar os dados às listas
    pod_names.append(pod_name)
    cpu_percentages.append(cpu_percentage)
    
    # Verificar se o uso de CPU é maior que 1%
    if cpu_percentage > 1:
        has_high_cpu_usage = True

# Processar os resultados de memória
for item in memory_usage:
    pod_name = item['metric']['pod']
    memory_value_bytes = float(item['value'][1])  # O valor em bytes
    memory_percentage = (memory_value_bytes / total_memory_bytes) * 100  # Calcular a porcentagem
    
    # Adicionar os dados às listas
    # Verifica se o pod já está na lista, caso contrário, adiciona-o
    if pod_name not in pod_names:
        pod_names.append(pod_name)
        cpu_percentages.append(0)  # Percentagem de CPU desconhecida

    memory_percentages.append(memory_percentage)

    # Verificar se o uso de memória é maior que 1%
    if memory_percentage > 1:
        has_high_memory_usage = True

# Criar um DataFrame do pandas
df = pd.DataFrame({
    'Pod Name': pod_names,
    'CPU Usage (%)': cpu_percentages,
    'Memory Usage (%)': memory_percentages
})

# Exibir os dados em formato tabular
print("\nUso percentual de CPU e Memória de cada pod:")
print(df)

# Verificar se algum pod tem mais de 1% de uso de CPU
if has_high_cpu_usage:
    print("\nTem pod com mais de 1% de uso de CPU.")

# Verificar se algum pod tem mais de 1% de uso de Memória
if has_high_memory_usage:
    print("\nTem pod com mais de 1% de uso de Memória.")

print(type(df.iloc[0, 0]))
