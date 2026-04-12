# Linkr — Backend API

A REST API backend for **Linkr**, an Android app that lets friends share their real-time location and ping each other to meet up. Built with Flask, backed by Supabase (PostgreSQL), and deployed on Vercel.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Flask |
| Database | PostgreSQL via Supabase |
| ORM | SQLAlchemy + psycopg2 |
| Auth | JWT (Flask-JWT-Extended) |
| Password Hashing | Flask-Bcrypt |
| Push Notifications | Firebase Cloud Messaging (FCM) |
| Deployment | Vercel |

---

## Features

- User registration and login with JWT authentication
- Friend system — send, accept, reject, and remove friends
- Real-time location sharing — update and fetch friend locations
- Ping system — send a meetup ping with a location to a friend, accept or reject it
- Firebase push notifications on new pings
- User search by name or email
- FCM token registration per device

---

## Project Structure

```
linkr-backend/
└── app.py      # All routes, models, and configuration
```

---

## Environment Variables

Before running locally or deploying, set the following environment variables:

| Variable | Description |
|---|---|
| `FIREBASE_CRED_JSON` | Base64-encoded Firebase service account JSON |
| `DB_PASSWORD` | PostgreSQL database password (Supabase) |
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens |

> ⚠️ Do not hardcode credentials in the source code. Use `.env` locally and environment variable settings on Vercel.

---

## Local Setup

### Prerequisites

- Python 3.9+
- A Supabase project with the required tables (see Database Schema)
- Firebase project with a service account JSON

### Install dependencies

```bash
pip install flask flask_sqlalchemy flask_bcrypt flask_jwt_extended psycopg2-binary firebase-admin aiohttp
```

### Run locally

```bash
export FIREBASE_CRED_JSON=<your_base64_encoded_firebase_json>
python app.py
```

The server will start at `http://localhost:5000`.

---

## Database Schema

The following tables are required in your Supabase PostgreSQL database:

### `users`
| Column | Type |
|---|---|
| id | UUID (PK) |
| name | VARCHAR |
| email | VARCHAR (unique) |
| password_hash | TEXT |
| profile_picture | VARCHAR (nullable) |

### `friend_requests`
| Column | Type |
|---|---|
| id | SERIAL (PK) |
| requester_id | UUID (FK → users) |
| receiver_id | UUID (FK → users) |
| status | VARCHAR (`pending`, `accepted`, `rejected`) |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

### `friends`
| Column | Type |
|---|---|
| id | SERIAL (PK) |
| user1_id | UUID (FK → users) |
| user2_id | UUID (FK → users) |
| created_at | TIMESTAMP |

### `locations`
| Column | Type |
|---|---|
| user_id | UUID (PK, FK → users) |
| latitude | FLOAT |
| longitude | FLOAT |
| updated_at | TIMESTAMP |

### `pings`
| Column | Type |
|---|---|
| id | SERIAL (PK) |
| sender_id | UUID (FK → users) |
| receiver_id | UUID (FK → users) |
| status | VARCHAR (`pending`, `accepted`, `rejected`) |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

### `ping_locations`
| Column | Type |
|---|---|
| id | SERIAL (PK) |
| ping_id | INTEGER (FK → pings, unique) |
| name | VARCHAR |
| address | TEXT (nullable) |
| latitude | FLOAT |
| longitude | FLOAT |
| created_at | TIMESTAMP |

### `user_fcm_tokens`
| Column | Type |
|---|---|
| id | SERIAL (PK) |
| user_id | UUID (FK → users) |
| fcm_token | TEXT |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

---

## API Reference

All protected routes require the header:
```
Authorization: Bearer <jwt_token>
```

---

### Auth

#### `POST /auth/register`
Register a new user.

**Request body:**
```json
{
  "name": "Shubham",
  "email": "shubham@example.com",
  "password": "yourpassword"
}
```

**Response `201`:**
```json
{
  "message": "User registered successfully",
  "user": { "id": "...", "name": "Shubham", "email": "shubham@example.com", "profile_picture": null }
}
```

---

#### `POST /auth/login`
Login and receive a JWT token.

**Request body:**
```json
{
  "email": "shubham@example.com",
  "password": "yourpassword"
}
```

**Response `200`:**
```json
{
  "token": "<jwt_token>",
  "user": { "id": "...", "name": "Shubham", "email": "shubham@example.com", "profile_picture": null }
}
```

---

#### `GET /users/<id>` 🔒
Get a user's profile by ID.

---

#### `GET /users/search?q=<query>` 🔒
Search users by name or email. Returns all matching users except the current user.

---

### Friends

#### `GET /friends` 🔒
Get the current user's full friend list.

#### `POST /friends/request` 🔒
Send a friend request.

**Request body:**
```json
{ "receiver_id": "<user_id>" }
```

#### `GET /friends/requests` 🔒
Get all pending incoming friend requests.

#### `POST /friends/request/<request_id>/accept` 🔒
Accept a friend request by its ID.

#### `POST /friends/request/<req_id>/reject` 🔒
Reject a friend request by its ID.

#### `DELETE /friends/<id>` 🔒
Remove a friend by their user ID.

---

### Location

#### `POST /location` 🔒
Update the current user's location.

**Request body:**
```json
{
  "latitude": 19.0760,
  "longitude": 72.8777
}
```

#### `GET /location/friends` 🔒
Get the latest locations of all friends.

#### `GET /location/<friend_id>` 🔒
Get the latest location of a specific friend by their UUID.

---

### Ping

#### `POST /ping` 🔒
Send a meetup ping to a friend with a suggested location.

**Request body:**
```json
{
  "receiver_id": "<user_id>",
  "location_name": "Starbucks, Andheri",
  "location_address": "Andheri West, Mumbai",
  "latitude": 19.1197,
  "longitude": 72.8468
}
```

Triggers an FCM push notification to the receiver's registered device(s).

#### `GET /ping/incoming` 🔒
Get all pending incoming pings for the current user, including location details.

#### `POST /ping/<ping_id>/respond` 🔒
Accept or reject a ping.

**Request body:**
```json
{ "status": "accepted" }
```
Status must be `accepted` or `rejected`.

---

### Firebase / FCM

#### `POST /fcm/register` 🔒
Register or update the FCM device token for the current user. The Android app should call this on login or when the FCM token refreshes.

**Request body:**
```json
{ "token": "<fcm_device_token>" }
```

---

## Deployment (Vercel)

1. Add a `vercel.json` in the project root:

```json
{
  "builds": [{ "src": "app.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "app.py" }]
}
```

2. Set all environment variables in the Vercel project dashboard under **Settings → Environment Variables**.

3. Deploy:

```bash
vercel --prod
```

---

*Linkr Backend — Flask + Supabase + Firebase*
