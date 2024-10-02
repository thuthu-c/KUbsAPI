#!/bin/bash

# Deleta o Minikube existente (caso exista)
echo "Deletando Minikube..."
minikube delete

# Inicia o Minikube
echo "Iniciando Minikube..."
minikube start

# Aplica a configuração de deployment do Prometheus
echo "Aplicando o arquivo deployment_test.yaml..."
kubectl apply -f deployment_test.yaml

# Cria o namespace 'monitoring'
echo "Criando o namespace 'monitoring'..."
kubectl create namespace monitoring

# Instala o Prometheus usando o Helm
echo "Instalando Prometheus com Helm..."
helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring

# Verifica os pods no namespace 'monitoring'
echo "Verificando pods no namespace 'monitoring'..."
kubectl get pods -n monitoring

# Configura o port-forwarding para o serviço Prometheus
echo "Configurando port-forwarding para o Prometheus na porta 9090..."
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090 -n monitoring &

# Configura o port-forwarding para o serviço nginx-service
echo "Configurando port-forwarding para o serviço Nginx na porta 8080..."
kubectl port-forward svc/nginx-service 8080:80 -n default &

# Executa o Apache Benchmark (ab) para fazer 1000 requisições com 10 conexões simultâneas
echo "Executando Apache Benchmark (ab)..."
ab -n 1000 -c 10 http://localhost:8080/

# Finaliza a execução
echo "Processo concluído."
