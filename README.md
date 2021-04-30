# Combine Django Authentication with Jitsi Meet

Use all the possibilites of Django authentication with Jitsi Meet JWT authentication.

This example project uses LDAP to generate tokens to prevent anonymous "zoombombing" in school meetings. The code differentiates between teacher and pupils.

## Integration


This Ansible code documents how to integrate with a Jitsi Meet server

```yaml
- name: Configure Django JWT_APPID
  lineinfile:
    line: "JWT_APPID = '{{ meet_jwt_appid }}'"
    path: /opt/jauth/jitsi-auth/meet_authenticator/settings.py
    regexp: '^JWT_APPID '
  become_user: jitsi-auth
- name: Configure Django JWT_APPSECRET
  lineinfile:
    line: "JWT_APPSECRET = '{{ meet_jwt_appsecret }}'"
    path: /opt/jauth/jitsi-auth/meet_authenticator/settings.py
    regexp: '^JWT_APPSECRET '
  become_user: jitsi-auth

- name: Configure Django MEET_HOST
  lineinfile:
    line: "MEET_HOST = '{{ meet_domain }}'"
    path: /opt/jauth/jitsi-auth/meet_authenticator/settings.py
    regexp: '^MEET_HOST '
  become_user: jitsi-auth

- name: Configure Django DEBUG
  lineinfile:
    line: "DEBUG = False"
    path: /opt/jauth/jitsi-auth/meet_authenticator/settings.py
    regexp: '^DEBUG '
  become_user: jitsi-auth

- name: Configure Django ALLOWED_HOSTS
  lineinfile:
    line: "ALLOWED_HOSTS = ['{{ meet_domain }}']"
    path: /opt/jauth/jitsi-auth/meet_authenticator/settings.py
    regexp: '^ALLOWED_HOSTS '
  become_user: jitsi-auth

- name: Configure Django AUTH_LDAP_SERVER_URI
  lineinfile:
    line: "AUTH_LDAP_SERVER_URI = '{{ meet_ldap_url }}'"
    path: /opt/jauth/jitsi-auth/meet_authenticator/settings.py
    regexp: '^AUTH_LDAP_SERVER_URI '
  become_user: jitsi-auth

- name: Run migrate on the application
  community.general.django_manage:
    command: migrate
    project_path: "/opt/jauth/jitsi-auth"
    virtualenv: "/opt/jauth/venv/jitsi-auth/"
  become_user: jitsi-auth

- name: copy systemd unit
  copy:
    dest: /etc/systemd/system/jitsi-auth.service
    mode: 0755
    content: |
      [Unit]
      Description = JitsiAuth
      After = network.target
      
      [Service]
      PermissionsStartOnly = true
      PIDFile = /run/jitsi-auth/jitsi-auth.pid
      User = jitsi-auth
      Group = jitsi-auth
      WorkingDirectory = /opt/jauth/jitsi-auth
      ExecStartPre = /bin/mkdir /run/jitsi-auth
      ExecStartPre = /bin/chown -R jitsi-auth:jitsi-auth /run/jitsi-auth
      ExecStart = /usr/bin/env /opt/jauth/venv/jitsi-auth/bin/gunicorn meet_authenticator.wsgi -b 127.0.0.1:5111 --pid /run/jitsi-auth/jitsi-auth.pid
      ExecReload = /bin/kill -s HUP $MAINPID
      ExecStop = /bin/kill -s TERM $MAINPID
      ExecStopPost = /bin/rm -rf /run/jitsi-auth
      PrivateTmp = true
      
      [Install]
      WantedBy = multi-user.target
  notify:
    - restart auth

- name: enable service jitsi-auth
  systemd:
    name: jitsi-auth
    enabled: yes
    daemon_reload: yes


- name: configure gunicorn upstream for jitsi-auth in nginx
  blockinfile:
    marker: "# {mark} ANSIBLE MANAGED BLOCK for upstream gunicorn"
    path: /etc/nginx/sites-enabled/{{ meet_domain }}.conf
    insertafter: "^server_names_hash_bucket_size"
    block: |
      upstream jauth {
        server 127.0.0.1:5111 fail_timeout=0;
      }
  notify:
    - restart nginx

- name: configure nginx for jitsi-auth
  blockinfile:
    marker: "# {mark} ANSIBLE MANAGED BLOCK for nginx jitsi-auth config"
    path: /etc/nginx/sites-enabled/{{ meet_domain }}.conf
    insertbefore: "^[ ]+# ensure all static"
    block: |
      location ~ ^/astatic/(.*)$ {
        add_header 'Access-Control-Allow-Origin' '*';
        alias /opt/jauth/jitsi-auth/meet_app/static/$1;
      }
      location ~ ^/auth/(.*) {
          proxy_set_header X-Forwarded-For $remote_addr;
          proxy_set_header Host $host;
          proxy_redirect off;
        proxy_pass http://jauth;
      }
      location ~ ^/accounts/(.*) {
        proxy_set_header X-Forwarded-For $remote_addr;
          proxy_set_header Host $host;
          proxy_redirect off;

        proxy_pass http://jauth;
      }

  notify:
    - restart nginx

```

# License

3-clause BSD
