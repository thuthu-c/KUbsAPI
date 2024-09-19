from kubernetes import client, config

config.load_kube_config()

# Cria uma instância da API do Kubernetes
v1=client.CoreV1Api()
ret = v1.list_namespaced_pod(namespace="default")
for i in ret.items:
    print(f'{i.status.pod_ip}\t{i.metadata.namespace}\t{i.metadata.name}')


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

print(20 * '-')

pods = v1.list_namespaced_pod(namespace="default")

for i in pods.items:
    print(f'{i.status.pod_ip}\t{i.metadata.namespace}\t{i.metadata.name}')
