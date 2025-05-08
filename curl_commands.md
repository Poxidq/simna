# Notes App API - User Flow Curl Commands

This document contains curl commands that demonstrate the complete user flow through the Notes App API. You can run these commands one by one to test the backend.

Before running these tests, you may want to clear the database:

```bash
# Remove the main database file
rm /home/nvy/other/SQRS/notes_app/notes_app.db

# Remove any database files in the data directory
rm -f /home/nvy/other/SQRS/notes_app/data/*.db
```

## Basic User Flow

### 1. Register a New User

This command creates a new user account with the username "testuser", email "test@example.com", and password "Password123".

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"Password123"}'
```

### 2. Login

After registering, use this command to login with the created credentials. This will return an access token that you'll need for all authenticated requests.

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Password123"}'
```

In the response, look for the `access_token` value. You'll need to use this token in the Authorization header for all subsequent requests. For example:

```json
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...","token_type":"bearer"}
```

### 3. Get User Information

Retrieve information about the currently logged-in user. Replace `YOUR_TOKEN` with the token you received from the login response.

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Create a Note

Create a new note. Replace `YOUR_TOKEN` with your access token.

```bash
curl -X POST "http://localhost:8000/api/v1/notes" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Note","content":"This is a test note content."}'
```

### 5. Get All Notes

Retrieve all notes for the current user. Replace `YOUR_TOKEN` with your access token.

```bash
curl -X GET "http://localhost:8000/api/v1/notes" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. Get a Specific Note

Retrieve a specific note by its ID. Replace `YOUR_TOKEN` with your access token and `NOTE_ID` with the ID of the note you want to retrieve.

```bash
curl -X GET "http://localhost:8000/api/v1/notes/NOTE_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 7. Update a Note

Update an existing note. Replace `YOUR_TOKEN` with your access token and `NOTE_ID` with the ID of the note you want to update.

```bash
curl -X PUT "http://localhost:8000/api/v1/notes/NOTE_ID" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated Test Note","content":"This note has been updated."}'
```

### 8. Create a Note with Russian Content

Create a note with Russian content for translation testing. Replace `YOUR_TOKEN` with your access token.

```bash
curl -X POST "http://localhost:8000/api/v1/notes" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Русская заметка","content":"Это тестовая заметка на русском языке."}'
```

### 9. Translate a Note

Translate a note from Russian to English. Replace `YOUR_TOKEN` with your access token and `NOTE_ID` with the ID of the Russian note.

```bash
curl -X POST "http://localhost:8000/api/v1/notes/NOTE_ID/translate" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 10. Delete a Note

Delete a note. Replace `YOUR_TOKEN` with your access token and `NOTE_ID` with the ID of the note you want to delete.

```bash
curl -X DELETE "http://localhost:8000/api/v1/notes/NOTE_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Tips for Running These Commands

1. After each successful request, check the response for important values like `id` and `access_token` that you'll need for subsequent requests.

2. You can use tools like `jq` to format the JSON responses for better readability, e.g.:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/notes" -H "Authorization: Bearer YOUR_TOKEN" | jq .
   ```

3. For debugging, you can add the `-v` flag to see more details about the request and response:
   ```bash
   curl -v -X POST "http://localhost:8000/api/v1/auth/login" -H "Content-Type: application/json" -d '{"username":"testuser","password":"Password123"}'
   ```

4. If you need to test with a new user, change the username and email values in the registration request to avoid conflicts with existing users. 