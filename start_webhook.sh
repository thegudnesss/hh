#!/bin/bash

echo "========================================"
echo "Starting Click Payment Webhook Server"
echo "========================================"
echo ""
echo "Server will start on http://localhost:8000"
echo ""
echo "Webhook URL: http://localhost:8000/payments/click/webhook"
echo "Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "========================================"
echo ""

python -m uvicorn webhook_server.main:app --host 0.0.0.0 --port 8000 --reload
