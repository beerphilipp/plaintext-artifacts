# Artifact Evaluation Experiments

This folder contains utility scripts to run the experiments defined in the artifact appendix.

## Folder Structure

- `e1/e1.sh` - Test script for experiment 1: HTTP content behavior
- `e2/e2.sh` - Test script for experiment 2: Analysis pipeline
- `e3.sh` - Test script for experiment 3: Measurement results
- `start_emulator.sh` - Script to start an Android emulator

## APK Dataset

**Reviewers:** Please follow the instructions in the artifact appendix.

**Users:** You may request access to the APK dataset by contacting the authors. 

## Prepare and Run the Experiments

>[!NOTE]
> To produce the results in the paper, we used a device running MacOS 26.5 (ARM) with 32 GB of RAM and 10 cores

### Install the Prerequisites

- Install docker as per [the official instructions](https://docs.docker.com/get-docker/).
- Install Android Studio [see here](https://developer.android.com/studio).

### Run the Experiments

Please refer to the artifact appendix (Section A.4) for instructions on how to run and reproduce the experiments, the expected outcomes of the experiments, and the approximate resources necessary.

## Troubleshooting

#### Permission denied: `./e1.sh` / `./e2.sh` / `./e3.sh`

- Make sure the script is executable. Run the following command:
    ```sh
    chmod +x ./e1.sh
    ```
- Then run it again:
  ```sh
  ./e1.sh
  ```