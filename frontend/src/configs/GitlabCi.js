const GitLabCIContent = `
variables:
  FLASK_API_URL: "http://54.210.95.40:5001/scan"
  REPO_URL: "https://github.com/YoussefElbadouri/tst"

stages:
  - scan

semgrep_scan:
  stage: scan
  image: curlimages/curl:latest
  script:
    - echo "📤 Envoi du dépôt à l'API Flask..."
    - |
      RESPONSE=$(curl -s -X POST "$FLASK_API_URL" \
        -H "Content-Type: application/json" \
        -d "{\"repo_url\": \"$REPO_URL\"}")
      echo "📋 Réponse :"
      echo "$RESPONSE"

      EXIT_CODE=$(echo "$RESPONSE" | grep -o '"exit_code":[0-9]*' | cut -d':' -f2)
      STATUS=$(echo "$RESPONSE" | grep -o '"status":"[^"]*"' | cut -d':' -f2 | tr -d '"')

      if [ "$EXIT_CODE" != "0" ] || [ "$STATUS" == "failed" ]; then
        echo "🚨 Vulnérabilités détectées. Le pipeline est arrêté."
        exit 1
      else
        echo "✅ Aucun problème détecté. Le pipeline continue."
      fi
`;

export default GitLabCIContent;