#!/bin/bash

# 1. Load configuration
# We need to read NEXT_PUBLIC_API_URL from .env.local to pass it to the build
API_URL=$(grep "^NEXT_PUBLIC_API_URL" .env.local | cut -d '=' -f2)

if [ -z "$API_URL" ]; then
  echo "Error: Could not find NEXT_PUBLIC_API_URL in .env.local"
  exit 1
fi

echo "Using API URL: $API_URL"

# 2. Set to fixed port 3001 (Configured in .env.local, likely whitelisted)
PORT=3001
echo "Using requested port: $PORT"

# 3. Build the Docker image
# We tag it as 'admin-dashboard-local' to distinguish from prod images
echo "Building Docker image..."
docker build \
  --build-arg NEXT_PUBLIC_API_URL="$API_URL" \
  -t admin-dashboard-local .

# 4. Run the container
# Map the found host PORT to container port 3000
# Override NEXTAUTH_URL to match the localhost port
echo "Starting container on http://localhost:$PORT"

# We use --rm to clean up after exit
# We pass --env-file .env.local to load other secrets (Client ID, Secret)
# We override NEXTAUTH_URL explicitly because .env.local typically has a static value
docker run --rm \
  -p $PORT:3000 \
  --env-file .env.local \
  -e NEXTAUTH_URL="http://localhost:$PORT" \
  --name admin-dashboard-local-instance \
  admin-dashboard-local
