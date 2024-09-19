from crypt import methods

from flask import Flask, jsonify, request
from kubernetes import client, config
from datetime import datetime

config.load_kube_config()

app = Flask(__name__)

@app.route('/listar', methods=['GET'])
def obter_pods():
    # Cria uma instância da API do Kubernetes
    v1=client.CoreV1Api()
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
    #return jsonify(ret.to_dict())
"""
@app.route('/scale-up')
def scale_up():
    # Cria uma instância da API do Kubernetes do replicaset
    apps_v1 = client.AppsV1Api()

    # Nome do ReplicaSet e namespace
    name = "frontend-rs"
    namespace = "default"

    # Define o novo número de réplicas
    new_replicas = 1

    # Pega o ReplicaSet atual
    replicaset = apps_v1.read_namespaced_replica_set(name=name, namespace=namespace)

    # Atualiza o número de réplicas com um pod a mais
    replicaset.spec.replicas += new_replicas

    # Aplica a atualização no cluster
    response = apps_v1.replace_namespaced_replica_set(name=name, namespace=namespace, body=replicaset)

    return obter_pods()
"""

@app.route('/scale-up/<string:n>/<int:number_of_replicas>')
def scale_up(n, number_of_replicas):
    apps_v1 = client.AppsV1Api()
    namespace = "default"
    new_replicas = number_of_replicas
    replicaset = apps_v1.read_namespaced_replica_set(name=n, namespace=namespace)
    replicaset.spec.replicas += new_replicas
    response = apps_v1.replace_namespaced_replica_set(name=n, namespace=namespace, body=replicaset)
    return obter_pods()

@app.route('/scale-down/<string:n>/<int:number_of_replicas>', methods=['POST'])
def scale_down(n,number_of_replicas):
    apps_v1 = client.AppsV1Api()
    namespace = "default"
    new_replicas = number_of_replicas
    replicaset = apps_v1.read_namespaced_replica_set(name=n, namespace=namespace)
    replicaset.spec.replicas -= new_replicas
    response = apps_v1.replace_namespaced_replica_set(name=n, namespace=namespace, body=replicaset)
    return obter_pods()

app.run()