# TODO: Move this Jinja to pillar.
{% set dhcp_prefix = '10.73.17' %}
{% set dhcp_lowest = '100' %}
{% set dhcp_highest = '199' %}
{% set dhcp_netmask = '255.255.255.0' %}
{% set gateway = '10.73.17.254' %}
{% set dns_server = '10.73.17.251' %}

install DHCP server:
  pkg.installed:
    - name: dnsmasq

configure DHCP server:
  file.managed:
    - name: /etc/dnsmasq.d/dhcp.conf
    - user: root
    - group: root
    - mode: 0644
    - contents: |
        dhcp-range={{ dhcp_prefix }}.{{ dhcp_lowest }},{{ dhcp_prefix }}.{{ dhcp_highest }},{{ dhcp_netmask }},12h
        dhcp-option=option:router,{{ gateway }}
        dhcp-option=option:dns-server,{{ dns_server }}
  cmd.run:
    - name: service dnsmasq restart
    - onchanges:
      - file: configure DHCP server
