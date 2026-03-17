#!/bin/bash
# =============================================================================
# Trurism Backend - Azure Deployment Script
# =============================================================================
# Usage: Run each section step-by-step, or execute the entire script.
# Prerequisites: Azure CLI installed and logged in (az login)
#
# IMPORTANT: Replace ALL placeholder values before running:
#   <DB_PASSWORD>       - Strong password for PostgreSQL admin
#   <JWT_SECRET>        - Generate with: python -c "import secrets; print(secrets.token_hex(32))"
#   <RAZORPAY_KEY_ID>   - From Razorpay Dashboard
#   <RAZORPAY_SECRET>   - From Razorpay Dashboard
#   <WEBHOOK_SECRET>    - From Razorpay Webhook settings
# =============================================================================

set -e

# --- Configuration -----------------------------------------------------------
RESOURCE_GROUP="rg-trurism"
LOCATION="southeastasia"
DB_SERVER_NAME="trurism-db"
DB_NAME="trurism"
DB_ADMIN_USER="trurismadmin"
DB_ADMIN_PASSWORD="<DB_PASSWORD>"          # CHANGE THIS
APP_SERVICE_PLAN="plan-trurism"
APP_NAME="trurism-api"                      # Must be globally unique
JWT_SECRET="<JWT_SECRET>"                   # CHANGE THIS
RAZORPAY_KEY_ID="<RAZORPAY_KEY_ID>"         # CHANGE THIS
RAZORPAY_SECRET="<RAZORPAY_SECRET>"         # CHANGE THIS
WEBHOOK_SECRET="<WEBHOOK_SECRET>"           # CHANGE THIS

# Constructed values
DB_HOST="${DB_SERVER_NAME}.postgres.database.azure.com"
DATABASE_URL="postgresql+asyncpg://${DB_ADMIN_USER}:${DB_ADMIN_PASSWORD}@${DB_HOST}:5432/${DB_NAME}?ssl=require"

echo "=========================================="
echo "Trurism Azure Deployment"
echo "=========================================="

# --- Step 1: Create Resource Group -------------------------------------------
echo ""
echo "[1/8] Creating Resource Group: ${RESOURCE_GROUP}..."
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output table

# --- Step 2: Create PostgreSQL Flexible Server -------------------------------
echo ""
echo "[2/8] Creating PostgreSQL Flexible Server: ${DB_SERVER_NAME}..."
az postgres flexible-server create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DB_SERVER_NAME" \
  --location "$LOCATION" \
  --admin-user "$DB_ADMIN_USER" \
  --admin-password "$DB_ADMIN_PASSWORD" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 15 \
  --public-access 0.0.0.0 \
  --output table

# --- Step 3: Create Database ------------------------------------------------
echo ""
echo "[3/8] Creating database: ${DB_NAME}..."
az postgres flexible-server db create \
  --resource-group "$RESOURCE_GROUP" \
  --server-name "$DB_SERVER_NAME" \
  --database-name "$DB_NAME" \
  --output table

# --- Step 4: Configure Firewall (Allow Azure Services) ----------------------
echo ""
echo "[4/8] Configuring firewall rules..."
az postgres flexible-server firewall-rule create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DB_SERVER_NAME" \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0 \
  --output table

# --- Step 5: Create App Service Plan ----------------------------------------
echo ""
echo "[5/8] Creating App Service Plan: ${APP_SERVICE_PLAN}..."
az appservice plan create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_SERVICE_PLAN" \
  --is-linux \
  --sku B1 \
  --location "$LOCATION" \
  --output table

# --- Step 6: Create Web App -------------------------------------------------
echo ""
echo "[6/8] Creating Web App: ${APP_NAME}..."
az webapp create \
  --resource-group "$RESOURCE_GROUP" \
  --plan "$APP_SERVICE_PLAN" \
  --name "$APP_NAME" \
  --runtime "PYTHON:3.11" \
  --output table

# --- Step 7: Configure Environment Variables --------------------------------
echo ""
echo "[7/8] Setting environment variables..."
az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --settings \
    ENVIRONMENT="production" \
    DEBUG="false" \
    DATABASE_URL="$DATABASE_URL" \
    JWT_SECRET_KEY="$JWT_SECRET" \
    REDIS_URL="none" \
    RAZORPAY_KEY_ID="$RAZORPAY_KEY_ID" \
    RAZORPAY_KEY_SECRET="$RAZORPAY_SECRET" \
    RAZORPAY_WEBHOOK_SECRET="$WEBHOOK_SECRET" \
    CORS_ORIGINS="https://${APP_NAME}.azurewebsites.net,http://localhost:3000" \
    TRUSTED_HOSTS="${APP_NAME}.azurewebsites.net,localhost" \
    RATE_LIMIT_REQUESTS="100" \
    RATE_LIMIT_PERIOD="60" \
    WEBSITES_PORT="8000" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
  --output table

# Configure startup command
# NOTE: Must be a .sh file path - Azure only activates /antenv before running .sh scripts.
# A raw "gunicorn ..." command string runs against system Python (no packages) and
# causes: ModuleNotFoundError: No module named 'uvicorn'
az webapp config set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --startup-file "startup_azure.sh" \
  --output table

# --- Step 8: Deploy Code ----------------------------------------------------
echo ""
echo "[8/8] Deploying code..."
az webapp up \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --runtime "PYTHON:3.11"

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "App URL:  https://${APP_NAME}.azurewebsites.net"
echo "Health:   https://${APP_NAME}.azurewebsites.net/health"
echo "API Docs: https://${APP_NAME}.azurewebsites.net/docs (set DEBUG=true first)"
echo ""
echo "NEXT STEPS:"
echo "  1. Run migrations: alembic upgrade head"
echo "     (Set DATABASE_URL env var locally, or use 'az webapp ssh')"
echo "  2. Verify health: curl https://${APP_NAME}.azurewebsites.net/health"
echo "  3. Check logs:    az webapp log tail --resource-group ${RESOURCE_GROUP} --name ${APP_NAME}"
echo ""
