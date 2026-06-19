CSV_FILE="$1"
OUT_DIR="$2"
LOG_DIR="$3"
EMAIL="$4"
TOKEN="$5"


if [[ $# -ne 5  ]]; then
	echo "Usage: $0 INPUT_FILE OUT_DIR LOG_DIR EMAIL TOKEN"
	exit 1
fi

if [[ ! -f "$CSV_FILE" ]]; then
	echo "CSV file not found"
	exit 1
fi

cat "$CSV_FILE" | \
	parallel \
		--joblog "${LOG_DIR}/joblog.log" \
		--resume \
		--results "${LOG_DIR}" \
		--progress \
		--delay 7 \
		--eta \
		--jobs 4 \
		apkeep-fork/target/release/apkeep -a {} -d google-play -e "${EMAIL}" -t "${TOKEN}" -o split_apk=1,device=custom_px_8,device_properties=./device.properties,include_additional_files=1,include_dex_metadata=1  "${OUT_DIR}"

