# TODO: Move this Jinja to pillar.

install DNS server:
  pkg.installed:
    - name: dnsmasq

configure DNS server:
  file.managed:
    - name: /etc/dnsmasq.d/dns.conf
    - user: root
    - group: root
    - mode: 0644
    - contents: |
        no-resolv
        server=8.8.8.8
        server=8.8.4.4
  cmd.run:
    - name: service dnsmasq restart
    - onchanges:
      - file: configure DNS server
