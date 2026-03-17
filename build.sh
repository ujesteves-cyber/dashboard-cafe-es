#!/usr/bin/env bash
set -o errexit

# Build frontend
cd frontend
npm install --legacy-peer-deps
npm run build
cd ..

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..

echo "Build completed successfully!"
