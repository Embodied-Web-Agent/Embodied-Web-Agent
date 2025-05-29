# Web Environments - Quick Start Guide

This guide provides instructions for quickly setting up and launching the required web environments.

## Prerequisites

Before proceeding, ensure your system meets the following requirements:

- **Bash:** The Bourne Again SHell, for running the provided scripts. You'll need execute permissions for scripts in this directory.
- **Node.js:** Version 18.0 or newer (which includes `npm`).
- **Docker Engine:** To build and run the containerized web services.
- **Docker Compose:** For managing multi-container Docker applications. (Usually included with Docker Desktop; may require separate installation on Linux, e.g., as the `docker-compose-plugin`).
- **`wget`:** Utility for downloading files from the web, used by `build.sh`.
- **`screen`:** Terminal multiplexer, used by `host.sh` to run services in detached background sessions.

## Setup Instructions

Follow these steps to get the environments up and running:

### 1. Initial Setup: Download Resources and Install Dependencies
This one-time setup step downloads all necessary data and installs application-specific packages. *This step only needs to be performed once*:

Run the following command:

```bash
bash build.sh
```

### 2. Host All Websites
After the initial setup, you can host the website enviroment by running:

```bash
bash host.sh
```
