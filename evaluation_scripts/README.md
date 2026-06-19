# Evaluation Scripts

Jupyter notebooks that consume the raw measurement results in MongoDB and produce the figures, tables, and numeric macros used in the paper. For a fully scripted, end-to-end run see `reproducibility/e3/e3.sh` (Experiment 3 of the artifact), which restores the database snapshot and starts a Jupyter container built from the `Dockerfile` here.

## Requirements

The notebooks expect:

- A MongoDB instance reachable on `localhost:27017` populated with the raw results (collections in the `webview` and `webview-network` databases).
- The Google Play metadata SQLite database (`gplay.sqlite`) mounted at `/data/gplay.sqlite`.
- Access to the APK dataset for the notebooks that need it.

`reproducibility/e3/e3.sh` provisions all of the above automatically.

## Running

Run the notebooks **in numerical order** — later notebooks depend on collections written by earlier ones.

Via E3 (recommended):

```bash
cd reproducibility/e3
./e3.sh <DB_SNAPSHOT_DIR> <GPLAY_SQLITE>
# then open http://localhost:8888
```

Standalone (assuming MongoDB and `gplay.sqlite` are already available):

```bash
pip install -r requirements.txt
jupyter lab
```

## Notebooks

| #   | Notebook                                  | Paper section / artifact                       |
|-----|-------------------------------------------|------------------------------------------------|
| 1   | `1_generate_macros_dataset.ipynb`         | Section 4.1 — Dataset                          |
| 2   | `2_generate_macros_success.ipynb`         | Section 5.1 — Success Rate                     |
| 3   | `3_generate_macros_network_policy.ipynb`  | Section 5.2 — HTTPS-By-Default Opt-Out         |
| 4   | `4_generate_cleartext_figure.ipynb`       | Section 5.2 — Figure 2                         |
| 5   | `5_generate_macros_webview_usage.ipynb`   | Section 5.3 — WebViews Explored                |
| 6   | `6_generate_macros_top_level.ipynb`       | Section 5.4 — Insecure `loadUrl` Navigations   |
| 7   | `7_generate_macros_enforcement_gaps.ipynb`| Section 5.5 — Mixed Content Enforcement Gaps   |
| 8   | `8_generate_macros_policy_weakening.ipynb`| Section 5.6 — Systematic Policy Weakening      |
| 9   | `9_generate_table_webview_capabilies.ipynb`| Section 5.7 - WebView Capabilities                |
| 10  | `10_generate_macros_loaded_content.ipynb` | Section 5.8 / Table 5 — Loaded Content         |
| 11  | `11_generate_fyber_apps.ipynb`            | Section 6.2 — App Interference (Fyber)         |

Refer to the artifact appendix for the full mapping of notebook outputs to figures, tables, and macros in the paper.
