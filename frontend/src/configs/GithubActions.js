const GitHubActionsContent = `
name: Semgrep Security Scan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  FLASK_API_URL: "http://safeops:5000/scan"
  REPO_URL: "https://github.com/username/repo_name"

jobs:
  semgrep_scan:
    runs-on: ubuntu-latest

    steps:
      - name:  Checkout Code
        uses: actions/checkout@v3

      - name:  Install curl & jq
        run: sudo apt-get update && sudo apt-get install -y curl jq

      - name:  Send Repository to Flask API
        run: |
          echo " Sending repo to Flask API..."
          RESPONSE=$(curl -s -X POST "$FLASK_API_URL" \
            -H "Content-Type: application/json" \
            -d "{\"repo_url\": \"$REPO_URL\"}")

          echo " Response from Flask API:"
          echo "$RESPONSE"

          EXIT_CODE=$(echo "$RESPONSE" | jq -r '.exit_code // 0')
          STATUS=$(echo "$RESPONSE" | jq -r '.status')

          if [ "$EXIT_CODE" != "0" ] || [ "$STATUS" == "failed" ]; then
            echo " Vulnérabilités détectées. Le workflow est arrêté."
            exit 1
          else
            echo " Aucun problème détecté. The workflow continues."
          fi
`;

export default GitHubActionsContent;