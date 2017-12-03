# TODO: Move this Jinja to pillar.
{% set interface = 'eth0' %}
{% set address = '10.73.17.251' %}
{% set netmask = '255.255.255.0' %}
{% set gateway = '10.73.17.254' %}

set fixed IP address:
  file.managed:
    - name: /etc/network/interfaces.d/{{ interface }}
    - user: root
    - group: root
    - mode: 0644
    - contents: |
        auto {{ interface }}
        iface {{ interface }} inet static
          address {{ address }}
          netmask {{ netmask }}
          gateway {{ gateway }}
  cmd.run:
    - name: 'ifdown eth0; ifup eth0'
    - runas: root
    - onchanges:
      - file: set fixed IP address
