# Linked Solutions API Documentation

A web application for documenting the Linked Solutions API with HTTP methods, routes, parameters, and user descriptions.

## Features

- **Endpoint Management**: Add, edit, and delete API endpoints
- **Filtering**: Filter endpoints by HTTP method, route, and controller
- **Basic Authentication**: Secure access with username/password (default: `admin/admin`)
- **SQLite Database**: Easy deployment with built-in database

## Tech Stack

- **Backend**: Node.js + Express
- **Frontend**: HTML/CSS/JavaScript (Vanilla)
- **Database**: SQLite
- **Authentication**: bcrypt with HTTP Basic Auth

## Quick Start

### Using Docker

```bash
# Clone the repository
git clone https://github.com/linked-dev/LinkedApiDoc.git
cd LinkedApiDoc

# Build and run with Docker Compose
docker-compose up -d

# Access the application
# Open http://localhost:3000
```

### Manual Setup

```bash
# Install dependencies
npm install

# Start the server
npm start

# Access the application
# Open http://localhost:3000
```

## Default Credentials

- **Username**: `admin`
- **Password**: `admin`

## API Endpoints

### GET /api/endpoints
Get all endpoints with optional filtering.

**Query Parameters:**
- `method` - Filter by HTTP method
- `route` - Filter by route (partial match)
- `controller` - Filter by controller

**Response:**
```json
[
  {
    "id": 1,
    "http_method": "GET",
    "route": "/api/TRS_TIERS/SelectOrderTiers",
    "parameters": "{\"sec\": \"string\"}",
    "description": "",
    "controller": "TRS_TIERS",
    "created_at": "2024-01-01 00:00:00",
    "updated_at": "2024-01-01 00:00:00"
  }
]
```

### POST /api/endpoints
Create a new endpoint.

**Request Body:**
```json
{
  "http_method": "GET",
  "route": "/api/USERS/GetAll",
  "parameters": "",
  "description": "Get all users",
  "controller": "USERS"
}
```

### PUT /api/endpoints/:id
Update an existing endpoint.

### DELETE /api/endpoints/:id
Delete an endpoint.

## Database Schema

```sql
CREATE TABLE api_endpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    http_method TEXT NOT NULL,
    route TEXT NOT NULL,
    parameters TEXT,
    description TEXT DEFAULT '',
    controller TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Sample Data

The application initializes with sample data:

```sql
INSERT INTO api_endpoints (http_method, route, parameters, description, controller)
VALUES
    ('GET', '/api/TRS_TIERS/SelectOrderTiers', '{"sec": "string"}', '', 'TRS_TIERS'),
    ('POST', '/api/TRS_TIERS/ChangeActivity', '{"ids": "List<string>", "act": "string"}', '', 'TRS_TIERS');
```

## Docker Commands

```bash
# Build the image
docker build -t linked-api-doc .

# Run the container
docker run -d -p 3000:3000 --name linked-api-doc linked-api-doc

# View logs
docker logs linked-api-doc

# Stop and remove
docker-compose down
```

## User Guide

### Adding an Endpoint

1. Click the **+ Add Endpoint** button
2. Fill in the required fields:
   - **HTTP Method**: Select GET, POST, PUT, DELETE, or PATCH
   - **Route**: Enter the API route (e.g., `/api/TRS_TIERS/SelectOrderTiers`)
   - **Controller**: Enter the controller name (e.g., `TRS_TIERS`)
   - **Parameters**: Enter expected parameters in JSON format
   - **Description**: Add a description of what the endpoint does
3. Click **Save Endpoint**

### Editing an Endpoint

1. Click the **Edit** button next to the endpoint
2. Modify the desired fields
3. Click **Save Endpoint**

### Deleting an Endpoint

1. Click the **Delete** button next to the endpoint
2. Confirm the deletion in the dialog

### Filtering Endpoints

Use the filter section to search for specific endpoints:
- **HTTP Method**: Select a method from the dropdown
- **Route**: Enter partial route text to search
- **Controller**: Select a controller to filter by

Click **Apply Filters** to apply the filters, or **Clear** to reset.

## Project Structure

```
LinkedApiDoc/
├── public/
│   ├── index.html      # Main HTML file
│   ├── styles.css      # Styles
│   └── app.js          # Frontend JavaScript
├── server.js           # Express server
├── package.json        # Dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml # Docker Compose config
├── schema.sql         # Database schema
└── README.md          # This file
```

## License

Copyright © 2024 Linked Solutions. All rights reserved.