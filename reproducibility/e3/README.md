# Experiment 3 — Measurement Results

Brings up a local MongoDB populated from the database snapshot and a Jupyter container with the evaluation notebooks, so the figures and tables from the paper can be regenerated from the original measurement data.

## Requirements

- `docker`
- `mongorestore` on the host (used to restore the snapshots into the dockerized Mongo)
- The MongoDB snapshot directory provided with the artifact
- `gplay.sqlite` (Google Play metadata DB) provided with the artifact

## Files

| File                  | Purpose                                                                                  |
|-----------------------|------------------------------------------------------------------------------------------|
| `e3.sh`               | Main experiment script.                                                                  |
| `docker-compose.yaml` | Stack: MongoDB 7, mongo-express, and a Jupyter container built from `../../evaluation_scripts`. |

## Running

```bash
./e3.sh <DB_SNAPSHOT_DIR> <GPLAY_SQLITE>
```

| Argument           | Description                                                                          |
|--------------------|--------------------------------------------------------------------------------------|
| `DB_SNAPSHOT_DIR`  | Path to the MongoDB snapshot directory (must contain `webview-backup/webview` and `webview-network-backup/webview`). |
| `GPLAY_SQLITE`     | Path to `gplay.sqlite`; mounted read-only into the Jupyter container at `/data/gplay.sqlite`. |

## What `e3.sh` does

1. Validates the two arguments and resolves `GPLAY_SQLITE` to an absolute path (it is consumed by `docker-compose.yaml` via the `GPLAY_SQLITE` env var).
2. Starts the Compose stack:
   - **mongo** (`mongo:7`) on host port `27019` (container `27017`), with a persistent `mongo-data` volume.
   - **mongo-express** on `http://localhost:8081` for browsing the database.
   - **jupyter** built from `../../evaluation_scripts/Dockerfile`, sharing the network namespace of the Mongo container, exposed on host port `8888`.
3. Restores the database results.

## After the script

Open `http://localhost:8888` and run the notebooks in `evaluation_scripts/` to regenerate the figures and macros used in the paper. Use `http://localhost:8081` (mongo-express) to browse the restored collections.