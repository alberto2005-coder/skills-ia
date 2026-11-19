# Referencia de Costes y Reglas FinOps (Estándar)

## Umbrales de Detección de Desperdicio

- **Recursos Huérfanos**: 100% de coste considerado desperdicio (Volúmenes EBS desasociados, EIPs sin asociar, balanceadores sin targets activos).
- **Subutilización de Cómputo**: Promedio mensual de CPU < 10% -> Candidato a reducción de tamaño (ahorro estimado del 50%).
- **Subutilización moderada**: Promedio mensual de CPU entre 10% y 25% -> Candidato a revisión de rendimiento.

## Categorías de Instancias Evaluadas

- Cómputo (Compute Instances)
- Almacenamiento (Block Storage & Object Storage)
- Redes (Elastic IPs & NAT Gateways)
- Bases de Datos Gestionadas (Relational DBs)
