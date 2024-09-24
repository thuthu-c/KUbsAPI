from flask import Flask, jsonify
from kubernetes import client, config

from kubernetes.client import ApiException

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
    response = apps_v1.replace_namespaced_replica_set(name=n, namespace=namespace, body=replicaset)
    return get_pods()


@app.route('/scale-down/<string:n>/<int:number_of_replicas>', methods=['POST', 'PUT'])
def scale_down(n, number_of_replicas):
    apps_v1 = client.AppsV1Api()
    namespace = "default"
    new_replicas = number_of_replicas
    replicaset = apps_v1.read_namespaced_replica_set(name=n, namespace=namespace)
    replicaset.spec.replicas -= new_replicas
    response = apps_v1.replace_namespaced_replica_set(name=n, namespace=namespace, body=replicaset)
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

@app.route('/criar/<string:n>/<int:number_of_replicas>', methods=['GET'])
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

app.run()
