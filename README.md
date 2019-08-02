# dtn7-go Experiments for AdHoc-Now 2019

This repo contains everything needed for executing the dtn7-go experiments.

## Docker
For reproducing the experiments from our AdHoc-Now 2019 paper, you need first to install Docker and Docker Compose on you system. 
Follow the official guides to install [Docker](https://docs.docker.com/install/) and [Docker Compose](https://docs.docker.com/compose/install/).

## MACI
Since our experimts are set up with MACI for reproducibility, you have to prepare MACI in the first step.

```sh
git clone --recursive https://github.com/umr-ds/maci-docker-compose dtn7

# remove the default maci_data folder
cd dtn7
rm -rf maci_data
```

Before executing the experiments, you need to clone this experiment repo as the new `maci_data` folder:

```sh
git clone https://github.com/dtn7/adhocnow2019-evaluation.git maci_data
```

## Execution
### MACI Backend
At this point, you have to run the MACI backend. This can be done with the following command in the root MACI Docker Compose folder you checked out in the first step:

```sh
docker-compose up -d
```

You need to know the IP address of the machine where you started the MACI backend for a later step.

### Experiments
Now, you have to build the Docker container for the experiments and start it pointing to the MACI backend. With Docker Compose, this can be done in a single step (this can take a while, since we have to build dtn7-go, Serval and IBR-DTN):

```sh
cd maci_data
BACKEND=<IP_TO_MACI_BACKEND> DISPLAY= docker-compose up -d --build
```

### Start Experiments
To start the experiments go to the following URL with your web browser: `http://<IP_TP_MACI_BACKEND>:63658/`.
Then, click on "Create Experiment Study" and load "dtn7" in the "Experiment Templates" section in the top right section.
Finally, scroll to the very bottom of the page and click on "Run Experiment" and wait until all experiments are finished (you can check the state in the "Experiment Studies" page).
You have to know the Experiment ID of you experiment for the evaluation step later on, so remember it.

## Evaluation
Use the provided Jupyter Notebook file to evaluate the results.
To do so, go to your web browser at open the following URL: `http://<IP_TO_MACI_BACKEND>:8888/`.
First, open the `chain_cpu-network.ipynb` notebook and set the `EXPERIMENT_ID` variable to the ID from the step above.
Now you can simply execute all cells in the notebook and the results will be evaluated.
Repeat these steps in the `chain_runtimes.ipynb` notebook to finilize the evaluation.
