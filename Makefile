default: run

keyfile.pub:
	ssh-keygen -t ed25519 -N "" -f keyfile

docker: keyfile.pub
	docker build -t coreemu .

run: docker
	docker run -d --rm --privileged --cap-add=NET_ADMIN --cap-add=SYS_ADMIN -p 2322:22 coreemu
	@sleep 1
	ssh -X -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i keyfile root@localhost -p 2322

shell: docker
	docker run -it --rm --privileged --cap-add=NET_ADMIN --cap-add=SYS_ADMIN -p 2322:22 coreemu bash

bench: docker
	docker run -it --rm --privileged --cap-add=NET_ADMIN --cap-add=SYS_ADMIN -p 2322:22 coreemu /bench_script.py | tee "bench_`date +%s`.csv"
