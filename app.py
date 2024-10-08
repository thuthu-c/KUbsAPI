import subprocess

from flask import Flask, jsonify, request
from kubernetes import client, config
import yaml

from kubernetes.client import ApiException

from prometheus_api_client import PrometheusConnect
import pandas as pd

config.load_kube_config()

app = Flask(__name__)

@app.route('/listar', methods=['GET'])
def get_pods():
    # Cria uma instância da API do Kubernetes
    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_pod(namespace="default")
    pod_info_list = []

    for pod in ret.items:
        name = pod.metadata.name
        status = pod.status.phase
        pod_info_list.append({
            "name": name,
            "status": status
        })
    return jsonify(pod_info_list)

@app.route('/scale-up/<string:n>/<int:number_of_replicas>')
def scale_up(n, number_of_replicas):
    apps_v1 = client.AppsV1Api()
    namespace = "default"
    new_replicas = number_of_replicas
    replicaset = apps_v1.read_namespaced_replica_set(name=n, namespace=namespace)
    replicaset.spec.replicas += new_replicas
    response = apps_v1.patch_namespaced_replica_set(name=n, namespace=namespace, body=replicaset)
    return get_pods()


@app.route('/scale-down/<string:n>/<int:number_of_replicas>', methods=['POST', 'PUT'])
def scale_down(n, number_of_replicas):
    apps_v1 = client.AppsV1Api()
    namespace = "default"
    new_replicas = number_of_replicas
    replicaset = apps_v1.read_namespaced_replica_set(name=n, namespace=namespace)
    replicaset.spec.replicas -= new_replicas
    response = apps_v1.patch_namespaced_replica_set(name=n, namespace=namespace, body=replicaset)
    return get_pods()


@app.route('/status/<string:n>', methods=['GET'])
def status(n):
    apps_v1 = client.AppsV1Api()
    namespace = "default"

    replicaset = apps_v1.list_namespaced_replica_set(namespace=namespace)
    replicaset_name = n

    for rs in replicaset.items:
        if rs.metadata.name == replicaset_name:
            status = {
                "replicaset": rs.metadata.name,
                "desired_replicas": rs.spec.replicas,
                "available_replicas": rs.status.available_replicas,
                "ready_replicas": rs.status.ready_replicas,
                "conditions": rs.status.conditions
            }
            return jsonify(status)

@app.route('/criar/<int:replicas>', methods=['GET'])
def create_replicaset(n, number_of_replicas):
    namespace="default"
    nome_replicaset=n
    nome_app="meu-app"
    imagem="nginx:latest"  # Substitua pela imagem desejada
    replicas= number_of_replicas # Quantidade de réplicas

    # Define o cliente para a API AppsV1
    apps_v1 = client.AppsV1Api()

    try:
        # Tenta buscar o ReplicaSet pelo nome
        apps_v1.read_namespaced_replica_set(name=nome_replicaset, namespace=namespace)
        print(f"ReplicaSet '{nome_replicaset}' já existe no namespace '{namespace}'. Nenhuma ação foi tomada.")
    except ApiException as e:
        if e.status == 404:
            # Se o ReplicaSet não existir (Erro 404), cria o ReplicaSet
            print(f"ReplicaSet '{nome_replicaset}' não encontrado. Criando um novo ReplicaSet...")

            # Definir o template de Pod do ReplicaSet
            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": nome_app}),
                spec=client.V1PodSpec(containers=[client.V1Container(
                    name=nome_app,
                    image=imagem,
                    ports=[client.V1ContainerPort(container_port=80)]
                )])
            )

            # Configurar a especificação do ReplicaSet
            spec = client.V1ReplicaSetSpec(
                replicas=replicas,
                selector=client.V1LabelSelector(match_labels={"app": nome_app}),
                template=template
            )

            # Definir o objeto ReplicaSet
            replicaset = client.V1ReplicaSet(
                metadata=client.V1ObjectMeta(name=nome_replicaset),
                spec=spec
            )

            # Criar o ReplicaSet no namespace especificado
            response = apps_v1.create_namespaced_replica_set(namespace=namespace, body=replicaset)
            print(f"ReplicaSet '{nome_replicaset}' criado com {replicas} réplicas no namespace '{namespace}'.")
        else:
            print(f"Erro ao verificar a existência do ReplicaSet: {e}")
    return get_pods()


@app.route("/write_yaml/<int:replicas>", methods=['GET'])
def generate_deployment_yaml(replicas):
    with open("nginx-deployment.yaml", 'r') as stream:
        deployment = yaml.safe_load(stream)

        deployment['spec']['replicas'] = replicas

    with open("nginx-deployment.yaml", 'w') as outfile:
        yaml.safe_dump(deployment, outfile)

    return deployment



@app.route("/comando/<string:file_path>", methods=['POST'])
def apply_yaml_file(file_path):
    try:
        # Executa o comando `kubectl apply -f <file_path>`
        result = subprocess.run(
            ["kubectl", "apply", "-f", file_path],
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"



def scale_deployment(namespace, deployment_name, replicas):
    apps_v1 = client.AppsV1Api()
    scale = apps_v1.read_namespaced_deployment_scale(name=deployment_name, namespace=namespace)
    scale.spec.replicas = replicas
    apps_v1.replace_namespaced_deployment_scale(name=deployment_name, namespace=namespace, body=scale)



@app.route("/scale-deployment/<int:replicas>", methods=['GET'])
def scale(replicas):
    try:
        scale_deployment("default", "nginx-deployment", replicas)
        return {"status": "success", "message": f"Deployment scaled to {replicas} replicas"}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route('/monitorar', methods=['GET'])
def cpu_memory_monitor():
    # Configurações fixas
    prometheus_url = "http://localhost:9090"
    namespace = "default"
    total_cpu_milicores = 1000  # Exemplo: 1 núcleo de CPU
    total_memory_bytes = 8 * 1024 * 1024 * 1024  # Exemplo: 8 GB de RAM

    # Conectar ao Prometheus
    prom = PrometheusConnect(url=prometheus_url, disable_ssl=True)

    # Consulta PromQL para obter o uso de CPU de cada pod no namespace especificado
    cpu_usage_query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}"}}[5m])) by (pod) * 1000'
    
    # Consulta PromQL para obter o uso de memória de cada pod no namespace especificado
    memory_usage_query = f'sum(container_memory_usage_bytes{{namespace="{namespace}"}}) by (pod)'

    # Executar as consultas
    cpu_usage = prom.custom_query(cpu_usage_query)
    memory_usage = prom.custom_query(memory_usage_query)

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
        scale_up(df.iloc[0, 0], 2)


    # Verificar se algum pod tem mais de 1% de uso de Memória
    if has_high_memory_usage:
        print("\nTem pod com mais de 1% de uso de Memória.")
        scale_up(df.iloc[0, 0], 2)
    
    return get_pods()

app.run()
