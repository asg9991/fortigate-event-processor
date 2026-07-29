# FortiGate Event Processor

## Descripción

FortiGate Event Processor es un procesador de eventos para firewalls FortiGate diseñado para integrarse con Zabbix.

Su objetivo es reducir el volumen de información recibido desde Syslog, clasificar los eventos según su importancia y generar únicamente las notificaciones que realmente requieren atención.

El procesamiento se realiza en tiempo real sobre los logs generados por rsyslog, permitiendo filtrar millones de eventos diarios con un impacto mínimo sobre el servidor de monitoreo.

---

# Características

* Procesamiento continuo mediante `tail -F`
* Clasificación de eventos mediante archivo CSV
* Umbrales configurables por LogID
* Envío de eventos a Zabbix mediante `zabbix_sender`
* Configuración desacoplada del código
* Estado persistente mediante JSON
* Logging propio del servicio
* Compatible con rotación automática de logs (logrotate)
* Preparado para futuras integraciones (Discord, correo electrónico, webhooks, etc.)

---

# Arquitectura

```
                 FortiGate
                     │
                     ▼
               Syslog (UDP)
                     │
                     ▼
                 rsyslog
                     │
                     ▼
    /var/log/fortigate/fortigate.log
                     │
                     ▼
                 tail -F
                     │
                     ▼
          FortiGate Event Processor
                     │
      ┌──────────────┼───────────────┐─────────────┐
      │              │               │             |
      ▼              ▼               ▼             ▼
   IGNORE         AUDIT         THRESHOLD      IMMEDIATE
                           │
                           ▼
                      zabbix_sender
                           │
                           ▼
                      Zabbix Trapper
                           │
                           ▼
                   Triggers / Actions
```

---

# Estructura del proyecto

```
fortigate-event-processor/

├── classifier.py
├── fortigate_parser.py
├── notifier.py
├── thresholds.py
│
├── config/
│   ├── classification.csv
│   └── parser.yaml
│
├── state/
│   └── thresholds.json
│
├── logs/
│   └── parser.log
│
├── README.md
├── CHANGELOG.md
└── .gitignore
```

---

# Flujo de funcionamiento

1. FortiGate envía eventos vía Syslog.
2. rsyslog almacena los eventos en `fortigate.log`.
3. El parser monitorea continuamente el archivo mediante `tail -F`.
4. Cada línea se convierte en un objeto de evento.
5. Se consulta la clasificación correspondiente al LogID.
6. Según dicha clasificación se determina la acción a ejecutar.
7. Si corresponde, el evento es enviado a Zabbix mediante `zabbix_sender`.
8. Zabbix genera las acciones y notificaciones configuradas.

---

# Clasificación de eventos

Toda la lógica de clasificación se encuentra en:

```
config/classification.csv
```

Cada LogID pertenece a una de las siguientes categorías.

## IGNORE

El evento se descarta inmediatamente.

Se utiliza para:

* tráfico normal
* conexiones habituales
* eventos sin valor operativo

No genera registros ni alertas.

---

## AUDIT

El evento es enviado a Zabbix únicamente con fines de auditoría.

No produce alertas inmediatas.

Se utiliza para:

* eventos administrativos
* cambios de configuración
* información útil para auditorías

---

## THRESHOLD

El evento solamente será enviado cuando supere una cantidad determinada de ocurrencias dentro de una ventana de tiempo.

Ejemplo:

```
20 eventos en 300 segundos
```

Ideal para:

* intentos de acceso
* errores repetitivos
* comportamientos anómalos

---

## IMMEDIATE

Cada evento es enviado inmediatamente a Zabbix.

Se utiliza para:

* malware
* IPS
* antivirus
* eventos críticos
* bloqueos importantes
* incidentes de seguridad

---

# Thresholds

Los contadores se almacenan en:

```
state/thresholds.json
```

Este archivo contiene:

* contador de eventos
* primera aparición
* última aparición

No requiere mantenimiento manual.

Puede eliminarse sin afectar el funcionamiento del sistema.

---

# Configuración

Toda la configuración del proyecto se encuentra desacoplada del código.

## parser.yaml

Define:

* ruta del archivo Syslog
* servidor Zabbix
* host Zabbix
* clave Trapper
* ubicación del archivo de clasificación
* ubicación del archivo de estado

---

## classification.csv

Define el comportamiento de cada LogID.

Formato:

```
logid,classification,count,window,enabled
```

Ejemplo:

```
1059028705,IMMEDIATE,0,0,TRUE
0100032002,IGNORE,0,0,TRUE
0102043014,IMMEDIATE,0,0,TRUE
```

Agregar un nuevo LogID no requiere modificar el código fuente.

---

# Logging

El parser registra su actividad en:

```
logs/parser.log
```

Actualmente registra:

* inicio del servicio
* LogID desconocidos
* errores de procesamiento
* eventos enviados a Zabbix

El objetivo es facilitar el diagnóstico sin depender del log del sistema.

---

# Integración con Zabbix

El proyecto utiliza:

```
zabbix_sender
```

para enviar eventos al servidor.

Se recomienda crear:

Host:

```
FortiGate Event Processor
```

Item:

```
fortigate.event
```

Tipo:

```
Zabbix trapper
```

Sobre este único Item pueden construirse todos los Triggers necesarios.

---

# Ejecución manual

```
python3 fortigate_parser.py
```

El proceso permanecerá ejecutándose hasta recibir una interrupción.

---

# Servicio systemd

Se recomienda ejecutar el parser mediante systemd para garantizar:

* inicio automático
* reinicio automático
* ejecución en segundo plano
* integración con el sistema operativo

---

# Agregar un nuevo LogID

El procedimiento recomendado es:

1. Identificar el nuevo LogID mediante el auditor offline o parser.log.
2. Analizar su comportamiento utilizando una muestra real.
3. Definir la clasificación correspondiente.
4. Agregar una nueva línea en `classification.csv`.
5. Reiniciar el servicio.
6. Verificar el comportamiento en Zabbix.

En condiciones normales no es necesario modificar el código fuente.

---

# Requisitos

* Python 3
* rsyslog
* logrotate
* Zabbix Server
* zabbix_sender

---

# Objetivos del proyecto

* Reducir el volumen de eventos enviados a Zabbix.
* Centralizar la lógica de clasificación.
* Evitar falsas alarmas.
* Facilitar el mantenimiento.
* Permitir incorporar nuevas formas de notificación sin modificar la arquitectura existente.

---

# Licencia

Actualmente este proyecto se desarrolla para uso interno y podrá adaptarse para futuras implementaciones según las necesidades de cada cliente.
