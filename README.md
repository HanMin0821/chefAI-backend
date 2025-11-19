# ChefAI – The Smart Recipe Generator

ChefAI is a lightweight web application to help users decide what to cook based on the ingredients they already have. By entering a list of ingredients, the system will generate a complete recipe by AI, including cooking steps, difficulty, a list of missing ingredients (shopping list), and estimated nutrition information.

## Project Overview

**Project Name:** ChefAI – The Smart Recipe Generator
**Goal:** Generate a complete recipe from a list of available ingredients without requiring users to browse through large recipe databases.

### Core Features

1.  **Generate Recipe from Ingredients**
    *   User enters ingredients (e.g., "chicken breast, broccoli, rice").
    *   System validates input and calls the AI engine (Gemini API).
    *   System returns a recipe with steps, time, difficulty, servings, missing ingredients, and nutrition info.

2.  **Handle Empty Input**
    *   Prevents requests with no data.
    *   Displays error messages for invalid input.

3.  **Generate Shopping List**
    *   Identifies missing ingredients required for the generated recipe.
    *   Displays them as a checklist.

4.  **Estimate Nutrition Information**
    *   Provides estimated calories, protein, fat, and carbs per serving.

5.  **Export Recipe to PDF**
    *   Allows users to download the recipe, shopping list, and nutrition info as a PDF file.

6.  **View Recent Recipe History**
    *   Logged-in users can see their previously generated recipes.

7.  **User Authentication**
    *   Signup, Login, and Logout functionality.
    *   Secure password hashing.

## API Documentation

### Authentication

*   **POST /api/signup**
    *   Body: `{ "username": "...", "email": "...", "password": "..." }`
    *   Response: `{ "message": "User created successfully" }` or error.

*   **POST /api/login**
    *   Body: `{ "username": "...", "password": "..." }`
    *   Response: `{ "message": "Login successful", "user_id": 1 }` or error.

*   **POST /api/logout**
    *   Response: `{ "message": "Logged out successfully" }`

### Recipes

*   **POST /api/generate_recipe**
    *   Headers: `Authorization` (if token-based) or Cookie (if session-based)
    *   Body: `{ "ingredients": "chicken, rice" }`
    *   Response:
        ```json
        {
          "title": "Chicken Stir Fry",
          "ingredients": ["chicken", "rice", "soy sauce"],
          "missing_ingredients": ["soy sauce"],
          "steps": ["1. Cook chicken...", "2. Add rice..."],
          "nutrition": { "calories": 500, "protein": "30g" },
          "time": "30 mins",
          "difficulty": "Easy",
          "servings": 2
        }
        ```

*   **GET /api/history**
    *   Response: List of past recipes.

*   **POST /api/export_pdf**
    *   Body: `{ "recipe_data": { ... } }` (or ID if stored)
    *   Response: PDF file download.

## Tech Stack

*   **Backend:** Flask (Python)
*   **Database:** MySQL
*   **AI Engine:** Google Gemini API
*   **PDF Generation:** FPDF
*   **Authentication:** Werkzeug Security & Flask Sessions

