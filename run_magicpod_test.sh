OS=mac
FILENAME=magicpod-api-client
curl -L "https://app.magicpod.com/api/v1.0/magicpod-clients/api/${OS}/latest/" -H "Authorization: Token ${MAGICPOD_API_TOKEN}" --output ${FILENAME}.zip
unzip -q ${FILENAME}.zip

export MAGICPOD_ORGANIZATION=MagicPod-ishii
export MAGICPOD_PROJECT=testrail

TEST_SETTING_NUMBER=1
./magicpod-api-client batch-run -S ${TEST_SETTING_NUMBER}
