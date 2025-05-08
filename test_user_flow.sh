#!/bin/bash

# Test User Flow for Notes App
# This script tests the complete user flow including:
# - Registration
# - Login
# - Creating a note
# - Viewing notes
# - Updating a note
# - Translating a note
# - Deleting a note

# Set API base URL
API_URL="http://localhost:8000/api/v1"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}==== Notes App API User Flow Test ====${NC}"

# Clear database
echo -e "${YELLOW}\nStep 0: Clearing database...${NC}"
if [ -f notes_app.db ]; then
    rm notes_app.db
    echo -e "${GREEN}Database cleared successfully${NC}"
else
    echo -e "${YELLOW}Database file not found, creating fresh database${NC}"
fi

if [ -d data ]; then
    rm -f data/*.db
    echo -e "${GREEN}Data directory database files cleared${NC}"
fi

echo -e "${YELLOW}\nMake sure the backend API is running on http://localhost:8000${NC}"
read -p "Press enter to continue with tests..."

# Test user credentials
USERNAME="testuser2"
EMAIL="test@example2.com"
PASSWORD="Password123"
NEW_PASSWORD="NewPassword123"

# Step 1: Register a new user
echo -e "${YELLOW}\nStep 1: Registering a new user...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$USERNAME\",\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

echo "Registration Response:"
echo "$REGISTER_RESPONSE" | jq . 2>/dev/null || echo "$REGISTER_RESPONSE"

if echo "$REGISTER_RESPONSE" | grep -q "id"; then
    echo -e "${GREEN}Registration successful${NC}"
else
    echo -e "${RED}Registration failed${NC}"
    exit 1
fi

# Step 2: Login with the registered user
echo -e "${YELLOW}\nStep 2: Logging in...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

echo "Login Response:"
echo "$LOGIN_RESPONSE" | jq . 2>/dev/null || echo "$LOGIN_RESPONSE"

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')

if [ -z "$TOKEN" ]; then
    echo -e "${RED}Login failed, no token received${NC}"
    exit 1
else
    echo -e "${GREEN}Login successful, token received${NC}"
fi

# Step 3: Get current user information
echo -e "${YELLOW}\nStep 3: Getting user information...${NC}"
USER_RESPONSE=$(curl -s -X GET "$API_URL/auth/me" \
    -H "Authorization: Bearer $TOKEN")

echo "User Info Response:"
echo "$USER_RESPONSE" | jq . 2>/dev/null || echo "$USER_RESPONSE"

if echo "$USER_RESPONSE" | grep -q "username"; then
    echo -e "${GREEN}User information retrieved successfully${NC}"
else
    echo -e "${RED}Failed to get user information${NC}"
    exit 1
fi

# Step 4: Create a note
echo -e "${YELLOW}\nStep 4: Creating a note...${NC}"
CREATE_NOTE_RESPONSE=$(curl -s -X POST "$API_URL/notes" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"Test Note\",\"content\":\"This is a test note content.\"}")

echo "Create Note Response:"
echo "$CREATE_NOTE_RESPONSE" | jq . 2>/dev/null || echo "$CREATE_NOTE_RESPONSE"

# Extract note ID
NOTE_ID=$(echo "$CREATE_NOTE_RESPONSE" | grep -o '"id":[0-9]*' | sed 's/"id"://')

if [ -z "$NOTE_ID" ]; then
    echo -e "${RED}Failed to create note, no ID received${NC}"
    exit 1
else
    echo -e "${GREEN}Note created successfully with ID $NOTE_ID${NC}"
fi

# Step 5: Get all notes
echo -e "${YELLOW}\nStep 5: Getting all notes...${NC}"
NOTES_RESPONSE=$(curl -s -X GET "$API_URL/notes" \
    -H "Authorization: Bearer $TOKEN")

echo "Get Notes Response:"
echo "$NOTES_RESPONSE" | jq . 2>/dev/null || echo "$NOTES_RESPONSE"

if echo "$NOTES_RESPONSE" | grep -q "Test Note"; then
    echo -e "${GREEN}Notes retrieved successfully${NC}"
else
    echo -e "${RED}Failed to retrieve notes${NC}"
    exit 1
fi

# Step 6: Get a specific note
echo -e "${YELLOW}\nStep 6: Getting specific note (ID: $NOTE_ID)...${NC}"
NOTE_RESPONSE=$(curl -s -X GET "$API_URL/notes/$NOTE_ID" \
    -H "Authorization: Bearer $TOKEN")

echo "Get Specific Note Response:"
echo "$NOTE_RESPONSE" | jq . 2>/dev/null || echo "$NOTE_RESPONSE"

if echo "$NOTE_RESPONSE" | grep -q "Test Note"; then
    echo -e "${GREEN}Specific note retrieved successfully${NC}"
else
    echo -e "${RED}Failed to retrieve specific note${NC}"
    exit 1
fi

# Step 7: Update a note
echo -e "${YELLOW}\nStep 7: Updating note...${NC}"
UPDATE_NOTE_RESPONSE=$(curl -s -X PUT "$API_URL/notes/$NOTE_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"Updated Test Note\",\"content\":\"This note has been updated.\"}")

echo "Update Note Response:"
echo "$UPDATE_NOTE_RESPONSE" | jq . 2>/dev/null || echo "$UPDATE_NOTE_RESPONSE"

if echo "$UPDATE_NOTE_RESPONSE" | grep -q "Updated Test Note"; then
    echo -e "${GREEN}Note updated successfully${NC}"
else
    echo -e "${RED}Failed to update note${NC}"
    exit 1
fi

# Step 8: Create a note with Russian content for translation
echo -e "${YELLOW}\nStep 8: Creating a note with Russian content...${NC}"
CREATE_RUSSIAN_NOTE_RESPONSE=$(curl -s -X POST "$API_URL/notes" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"Русская заметка\",\"content\":\"Это тестовая заметка на русском языке.\"}")

echo "Create Russian Note Response:"
echo "$CREATE_RUSSIAN_NOTE_RESPONSE" | jq . 2>/dev/null || echo "$CREATE_RUSSIAN_NOTE_RESPONSE"

# Extract note ID
RUSSIAN_NOTE_ID=$(echo "$CREATE_RUSSIAN_NOTE_RESPONSE" | grep -o '"id":[0-9]*' | sed 's/"id"://')

if [ -z "$RUSSIAN_NOTE_ID" ]; then
    echo -e "${RED}Failed to create Russian note, no ID received${NC}"
    exit 1
else
    echo -e "${GREEN}Russian note created successfully with ID $RUSSIAN_NOTE_ID${NC}"
fi

# Step 9: Translate the note
echo -e "${YELLOW}\nStep 9: Translating note...${NC}"
TRANSLATE_RESPONSE=$(curl -s -X POST "$API_URL/notes/$RUSSIAN_NOTE_ID/translate" \
    -H "Authorization: Bearer $TOKEN")

echo "Translate Note Response:"
echo "$TRANSLATE_RESPONSE" | jq . 2>/dev/null || echo "$TRANSLATE_RESPONSE"

if echo "$TRANSLATE_RESPONSE" | grep -q "is_translated"; then
    echo -e "${GREEN}Note translated successfully${NC}"
else
    echo -e "${RED}Failed to translate note${NC}"
    exit 1
fi

# Step 10: Delete the first note
echo -e "${YELLOW}\nStep 10: Deleting first note...${NC}"
DELETE_RESPONSE=$(curl -s -X DELETE "$API_URL/notes/$NOTE_ID" \
    -H "Authorization: Bearer $TOKEN" -w "%{http_code}")

# Check HTTP status code
if [[ "$DELETE_RESPONSE" == *"204"* ]]; then
    echo -e "${GREEN}Note deleted successfully${NC}"
else
    echo -e "${RED}Failed to delete note. Response: $DELETE_RESPONSE${NC}"
    exit 1
fi

# Step 11: Delete the Russian note
echo -e "${YELLOW}\nStep 11: Deleting Russian note...${NC}"
DELETE_RUSSIAN_RESPONSE=$(curl -s -X DELETE "$API_URL/notes/$RUSSIAN_NOTE_ID" \
    -H "Authorization: Bearer $TOKEN" -w "%{http_code}")

# Check HTTP status code
if [[ "$DELETE_RUSSIAN_RESPONSE" == *"204"* ]]; then
    echo -e "${GREEN}Russian note deleted successfully${NC}"
else
    echo -e "${RED}Failed to delete Russian note. Response: $DELETE_RUSSIAN_RESPONSE${NC}"
    exit 1
fi

echo -e "${GREEN}\n==== All tests passed successfully! ====${NC}" 
