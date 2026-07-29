# Changelog

Todas las modificaciones relevantes del proyecto serán registradas en este archivo.

---

## v0.1.0

### Agregado

* Recepción de eventos FortiGate mediante Syslog.
* Parser de eventos en tiempo real.
* Clasificación de eventos mediante archivo CSV.
* Procesamiento por categorías: IGNORE, AUDIT, THRESHOLD e IMMEDIATE.
* Persistencia de umbrales mediante archivo JSON.
* Integración con Zabbix utilizando `zabbix_sender`.
* Configuración desacoplada mediante `parser.yaml`.
* Registro de actividad del parser.
* Compatibilidad con rotación automática de logs.

### Estado

Versión funcional inicial utilizada para el desarrollo y validación de la arquitectura base del procesador de eventos.
