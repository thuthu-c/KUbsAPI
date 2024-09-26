from prometheus_api_client import PrometheusConnect

prom = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)

cpu_usage_query = 'sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)'
cpu_usage = prom.custom_query(cpu_usage_query)
print(cpu_usage)