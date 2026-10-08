#!/bin/bash
echo "Setting up Virtual Environment..."
python -m venv venv
source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

echo "Creating data directories..."
mkdir -p data/raw data/staging data/cleaned data/analytical data/model_ready data/rejected models

if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo "Setup complete!"
