# =============================================================================
# Trurism Backend - Azure Deployment Script (PowerShell)
# =============================================================================
# Usage: Run each section step-by-step in PowerShell.
# Prerequisites: Azure CLI installed and logged in (az login)
#
# IMPORTANT: Replace ALL placeholder values in the Configuration section below.
# =============================================================================

# --- Configuration -----------------------------------------------------------
$RESOURCE_GROUP   = "rg-trurism"
$LOCATION         = "southeastasia"
$DB_SERVER_NAME   = "trurism-db"
$DB_NAME          = "trurism"
$DB_ADMIN_USER    = "trurismadmin"
$DB_ADMIN_PASSWORD = "Trurism@2026"          # Updated from your previous session
$APP_SERVICE_PLAN = "plan-trurism"
$APP_NAME         = "trurism-api"             # Must be globally unique
$JWT_SECRET       = "4f8e02d4b9c1a5e3f7d2b8c4a0e1d9f3b5c7a9d2e4f6b8c0a1d3e5f7b9c1d3e5" # Generated
$RAZORPAY_KEY_ID  = "YOUR_RAZORPAY_KEY"       # REPLACE THIS
$RAZORPAY_SECRET  = "YOUR_RAZORPAY_SECRET"    # REPLACE THIS
$WEBHOOK_SECRET   = "YOUR_WEBHOOK_SECRET"     # REPLACE THIS

# Constructed
$DB_HOST      = "${DB_SERVER_NAME}.postgres.database.azure.com"
$DATABASE_URL = "postgresql+asyncpg://${DB_ADMIN_USER}:${DB_ADMIN_PASSWORD}@${DB_HOST}:5432/${DB_NAME}?ssl=require"

Write-Host "=========================================="
Write-Host "Trurism Azure Deployment"
Write-Host "=========================================="

# --- Step 1: Create Resource Group -------------------------------------------
Write-Host "`n[1/8] Creating Resource Group..."
az group create `
  --name $RESOURCE_GROUP `
  --location $LOCATION `
  --output table

# --- Step 2: Create PostgreSQL Flexible Server -------------------------------
Write-Host "`n[2/8] Creating PostgreSQL Flexible Server..."
# Using a single line to avoid backtick/parsing issues in some PowerShell environments
az postgres flexible-server create --resource-group $RESOURCE_GROUP --name $DB_SERVER_NAME --location $LOCATION --admin-user $DB_ADMIN_USER --admin-password $DB_ADMIN_PASSWORD --sku-name Standard_B1ms --tier Burstable --storage-size 32 --version 15 --public-access 0.0.0.0 --output table

# --- Step 3: Create Database ------------------------------------------------
Write-Host "`n[3/8] Creating database..."
az postgres flexible-server db create `
  --resource-group $RESOURCE_GROUP `
  --server-name $DB_SERVER_NAME `
  --database-name $DB_NAME `
  --output table

# --- Step 4: Configure Firewall (Allow Azure Services) ----------------------
Write-Host "`n[4/8] Configuring firewall rules..."
az postgres flexible-server firewall-rule create `
  --resource-group $RESOURCE_GROUP `
  --name $DB_SERVER_NAME `
  --rule-name AllowAzureServices `
  --start-ip-address 0.0.0.0 `
  --end-ip-address 0.0.0.0 `
  --output table

# --- Step 5: Create App Service Plan ----------------------------------------
Write-Host "`n[5/8] Creating App Service Plan..."
az appservice plan create `
  --resource-group $RESOURCE_GROUP `
  --name $APP_SERVICE_PLAN `
  --is-linux `
  --sku B1 `
  --location $LOCATION `
  --output table

# --- Step 6: Create Web App -------------------------------------------------
Write-Host "`n[6/8] Creating Web App..."
az webapp create `
  --resource-group $RESOURCE_GROUP `
  --plan $APP_SERVICE_PLAN `
  --name $APP_NAME `
  --runtime "PYTHON:3.11" `
  --output table

# --- Step 7: Configure Environment Variables --------------------------------
Write-Host "`n[7/8] Setting environment variables and startup command..."
az webapp config appsettings set `
  --resource-group $RESOURCE_GROUP `
  --name $APP_NAME `
  --settings `
    ENVIRONMENT="production" `
    DEBUG="false" `
    DATABASE_URL="$DATABASE_URL" `
    JWT_SECRET_KEY="$JWT_SECRET" `
    REDIS_URL="none" `
    RAZORPAY_KEY_ID="$RAZORPAY_KEY_ID" `
    RAZORPAY_KEY_SECRET="$RAZORPAY_SECRET" `
    RAZORPAY_WEBHOOK_SECRET="$WEBHOOK_SECRET" `
    CORS_ORIGINS="https://${APP_NAME}.azurewebsites.net,http://localhost:3000" `
    TRUSTED_HOSTS="${APP_NAME}.azurewebsites.net,localhost" `
    RATE_LIMIT_REQUESTS="100" `
    RATE_LIMIT_PERIOD="60" `
    WEBSITES_PORT="8000" `
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" `
  --output table

az webapp config set `
  --resource-group $RESOURCE_GROUP `
  --name $APP_NAME `
  --startup-file "startup_azure.sh" `
  --output table

# --- Step 8: Deploy Code ----------------------------------------------------
Write-Host "`n[8/8] Deploying code..."
az webapp up `
  --resource-group $RESOURCE_GROUP `
  --name $APP_NAME `
  --runtime "PYTHON:3.11"

Write-Host "`n=========================================="
Write-Host "Deployment complete!"
Write-Host "=========================================="
Write-Host ""
Write-Host "App URL:  https://${APP_NAME}.azurewebsites.net"
Write-Host "Health:   https://${APP_NAME}.azurewebsites.net/health"
Write-Host "API Docs: https://${APP_NAME}.azurewebsites.net/docs (set DEBUG=true first)"
Write-Host ""
Write-Host "NEXT STEPS:"
Write-Host "  1. Run migrations locally:"
Write-Host "     `$env:DATABASE_URL = `"$DATABASE_URL`""
Write-Host "     alembic upgrade head"
Write-Host "  2. Verify health:"
Write-Host "     Invoke-WebRequest https://${APP_NAME}.azurewebsites.net/health"
Write-Host "  3. Check logs:"
Write-Host "     az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME"
