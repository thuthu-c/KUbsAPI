from kubernetes import client, config
from kubernetes.client.rest import ApiException

def criar_replicaset_se_nao_existir(namespace, nome_replicaset, nome_app, imagem, replicas):
    # Carrega a configuração do kubeconfig
    config.load_kube_config()

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

# Exemplo de uso
criar_replicaset_se_nao_existir(
    namespace="default",
    nome_replicaset="frontend-rs",
    nome_app="meu-app",
    imagem="nginx:latest",  # Substitua pela imagem desejada
    replicas=3  # Quantidade de réplicas
)