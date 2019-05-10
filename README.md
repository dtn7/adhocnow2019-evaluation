# CORE EMU Dockerfile

Dockercontainers to execute CORE and access its GUI through SSH and create a
CORE Worker with `dtn7`.

If CORE complains about missing `ebtables`, your kernel modules might not be
available inside the container. To fix this issue, execute `modprobe ebtables`
on your host and restart the container.

```bash
# To build the container and run CORE-GUI
# The container will stop itself after closing the CORE-GUI.
make

# For benchmarks, see bench_*.py
make bench

# For a shell
make shell

# To build the CORE Worker
make docker-core_worker
```

## Related Work

- <https://github.com/umr-ds/maci-serval_core_worker>
- <https://github.com/D3f0/coreemu_vnc>
