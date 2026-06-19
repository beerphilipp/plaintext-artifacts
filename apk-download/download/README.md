# Google Play APK Downloader

Tool to download apps from the Google Play Store.
This tool is a modified version of [`apkeep`](https://github.com/EFForg/apkeep) and [`rs-google-play`](https://github.com/EFForg/rs-google-play), extended to allow downloads using a Google Pixel 6a device.
`apkeep` and `rs-google-play` are licensed under the [MIT license](apkeep/LICENSE) and [MIT license](rs-google-play/LICENSE), respectively.

## File structure

- [`apkeep-fork/`](apkeep/) - CLI for downloading APKs (clone of [EFForg/apkeep](https://github.com/EFForg/apkeep))
- [`rs-google-play/`](rs-google-play/) - Rust-based Google Play API used by `apkeep` (modified [EFForg/rs-google-play](https://github.com/EFForg/rs-google-play))
- [`Dockerfile`](Dockerfile) - Build file for running the downloader in a container
- [`run.sh`](run.sh) - Utility script for downloading bulks of apps

## Install and Run

You can run the downloader locally or via Docker.

### Retrieve Google Play Credentials

- see [here](https://github.com/EFForg/apkeep/blob/master/USAGE-google-play.md) for an explanation on how to retrieve an AAS token to download apps from the Google Play Store.

### Run Locally

> [!NOTE]
> **Prerequisites**:
> - Rust >= 1.86 (refer to [this guide](https://www.rust-lang.org/tools/install) to install it)

- Build `rs-google-play`:
```sh
cargo build --release --manifest-path rs-google-play/Cargo.toml
```

- Build `apkeep`:
```sh
cargo build --release --manifest-path apkeep-fork/Cargo.toml
```

- Run `apkeep`
```sh
apkeep-fork/target/release/apkeep-fork -a <PACKAGE_NAME> -d google-play -e '<EMAIL>' -t '<TOKEN>' -o split_apk=1,device=custom_px_8,locale=at,include_additional_files=1 <OUT_DIR> 
```
Replace:
- `<PACKAGE_NAME>` with the package name you want to download
- `<OUT_DIR>` with the output directory you want to save the APK to
- `<EMAIL>` and `<TOKEN>` with the Google credentials

## Troubleshooting

#### error: package `XYZ` cannot be built because it requires rustc X.YZ or newer, while the currently active rustc version is X.YZ

You have to update your installed version of Rust, e.g., using [rustup](https://rustup.rs/).

#### error: failed to run custom build command for `openssl-sys v0.9.105`

The openssl-sys crate can’t find your OpenSSL installation. Install the OpenSSL development libraries: (`apt install pkg-config lbssl-dev`).

#### I get `sh: 1: cannot open /dev/tty: No such device or address` when I run the tool using Docker

You can safely ignore this message.