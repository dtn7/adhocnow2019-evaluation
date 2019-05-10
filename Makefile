default: run

docker-dtn7:
	docker build -t coreemu:dtn7-builder . -f Dockerfile.dtn7
	docker container create --name dtn7-extract coreemu:dtn7-builder
	docker container cp dtn7-extract:/dtncat ./dtn7cat
	docker container cp dtn7-extract:/dtnd ./dtn7d
	docker container rm -f dtn7-extract

docker-serval:
	docker build -t coreemu:serval-builder . -f Dockerfile.serval
	docker container create --name serval-extract coreemu:serval-builder
	docker container cp serval-extract:/serval-dna/servald ./servald
	docker container rm -f serval-extract

keyfile.pub:
	ssh-keygen -t ed25519 -N "" -f keyfile

docker-core: docker-dtn7 docker-serval keyfile.pub
	docker build -t coreemu . -f Dockerfile.core

run: docker-core
	docker run -d --rm --privileged --cap-add=NET_ADMIN --cap-add=SYS_ADMIN -p 2322:22 coreemu
	@sleep 1
	ssh -X -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i keyfile root@localhost -p 2322

shell: docker-core
	docker run -it --rm --privileged --cap-add=NET_ADMIN --cap-add=SYS_ADMIN -p 2322:22 coreemu bash

bench: docker-core
	docker run -it --rm --privileged --cap-add=NET_ADMIN --cap-add=SYS_ADMIN -p 2322:22 coreemu /bench_script.py | tee "bench_`date +%s`.csv"

clean:
	rm dtn7{cat,d} servald
