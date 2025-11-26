#!/bin/bash
cd /home/kavia/workspace/code-generation/nasa-astronomy-picture-viewer-46916-46926/backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

