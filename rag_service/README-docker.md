# RAG Service Docker Setup

This directory contains Docker configuration files for running the RAG (Retrieval-Augmented Generation) service without dealing with local dependency issues.

## Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop/)
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

## Files

- `Dockerfile` - Defines the Docker image for the RAG service
- `docker-compose.yml` - Defines the Docker service configuration
- `docker-helper.ps1` - PowerShell helper script for common Docker operations
- `docker-helper.bat` - Batch file helper script for common Docker operations

## Quick Start

### Using PowerShell

```powershell
# Build the Docker image
.\docker-helper.ps1 build

# Start the RAG service
.\docker-helper.ps1 up

# Check the logs
.\docker-helper.ps1 logs

# Test the API
.\docker-helper.ps1 test

# Stop the service when done
.\docker-helper.ps1 down
```

### Using Command Prompt

```cmd
# Build the Docker image
docker-helper.bat build

# Start the RAG service
docker-helper.bat up

# Check the logs
docker-helper.bat logs

# Test the API
docker-helper.bat test

# Stop the service when done
docker-helper.bat down
```

### Manual Commands

If you prefer to run Docker commands directly:

```powershell
# Build the image
docker-compose build

# Start the service
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## API Usage

Once the service is running, you can access the RAG service at `http://localhost:8000`. The main endpoint is `/chat`, which accepts POST requests with a JSON body:

```json
{
  "question": "Your question here",
  "conversation_context": [] // Optional: previous conversation history
}
```

## Troubleshooting

If you encounter any issues:

1. Check the logs with `.\docker-helper.ps1 logs`
2. Make sure Docker is running
3. Verify that port 8000 is not in use by another application
4. Ensure the data directory is correctly mapped in the volume
