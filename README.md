A basic SSH honeypot with downloader, written in Python.

In order to run, you will need Docker. It is preferable to run the honeypot on a VM, a test machine, or an EC2 instance.

Secure SSH access by assigning the firewall to forward port 22 to a non-privileged port, such as 22222. This will allow the Docker-contained honeypot to be run as a non-admin user.
To setup port forwarding from 22 to 22222, add a rule to iptables:

- iptables -A PREROUTING -t nat -p tcp --dport 22 -j REDIRECT --to-port 22222

Create a SSH key for the honeypot:

- ssh-keygen -t rsa -f server.key

Rename the public key:

- mv server.key.pub server.pub

Verify the honeypot directory contains the following files:

- .env
- basic_ssh_honeypot.py
- docker-compose.yml
- Dockerfile
- requirements.txt
- server.ppk
- server.pub
- ssh_honeypot_downloader.py

Build the docker image:

- docker-compose build

Start the honeypot:

- docker-compose up

Connect with the honeypot:

- ssh test@[ip-of-honeypot]

Verify connection appears in the logfile ssh_honeypot.log.
