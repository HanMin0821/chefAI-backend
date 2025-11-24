from flask import Flask, request, send_file
from flask_cors import CORS
from config import Config
from models import db, User, Recipe
from utils import ApiResponse, generate_token, token_required
import google.generativeai as genai
import json
import io
from fpdf import FPDF

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, supports_credentials=True)

db.init_app(app)

# Configure Gemini
if app.config['GEMINI_API_KEY']:
    genai.configure(api_key=app.config['GEMINI_API_KEY'])


@app.route("/")
def index():
    print("Loaded GEMINI_API_KEY =", app.config["GEMINI_API_KEY"])
    return ApiResponse.success(message="ChefAI Backend is Running")


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return ApiResponse.error("Missing required fields")

    if User.query.filter_by(username=username).first():
        return ApiResponse.error("Username already exists")

    if User.query.filter_by(email=email).first():
        return ApiResponse.error("Email already exists")

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = generate_token(user.id)

    return ApiResponse.success(
        data={"token": token, "user": {"id": user.id, "username": user.username}},
        message="User created successfully"
    )

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return ApiResponse.error("Invalid username or password", status_code=401)

    token = generate_token(user.id)

    return ApiResponse.success(
        data={"token": token, "user": {"id": user.id, "username": user.username}},
        message="Login successful"
    )


@app.route('/api/generate_recipe', methods=['POST'])
@token_required
def generate_recipe(current_user):
    data = request.get_json()
    ingredients = data.get('ingredients')
    
    if not ingredients:
        return ApiResponse.error("Please enter at least one ingredient")

    if not app.config.get("GEMINI_API_KEY"):
        result = {
            "title": "Mock Chicken Stir Fry",
            "ingredients": ["chicken", "broccoli", "soy sauce"],
            "missing_ingredients": ["sesame oil", "garlic"],
            "steps": ["1. Cut chicken.", "2. Stir fry with veggies.", "3. Serve."],
            "nutrition": { "calories": 450, "protein": "35g", "fat": "12g", "carbs": "10g" },
            "time": "25 mins",
            "difficulty": "Easy",
            "servings": 2
        }

        recipe = Recipe(
            user_id=current_user.id,
            title=result["title"],
            ingredients=json.dumps(result["ingredients"]),
            missing_ingredients=json.dumps(result["missing_ingredients"]),
            steps=json.dumps(result["steps"]),
            nutrition=json.dumps(result["nutrition"])
        )
        db.session.add(recipe)
        db.session.commit()

        return ApiResponse.success(result, "Recipe generated")

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"Create a recipe JSON using ingredients: {ingredients}"
        resp = model.generate_content(prompt)

        text = resp.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]

        result = json.loads(text)

        recipe = Recipe(
            user_id=current_user.id,
            title=result["title"],
            ingredients=json.dumps(result["ingredients"]),
            missing_ingredients=json.dumps(result.get("missing_ingredients", [])),
            steps=json.dumps(result["steps"]),
            nutrition=json.dumps(result.get("nutrition", {}))
        )
        db.session.add(recipe)
        db.session.commit()

        return ApiResponse.success(result, "Recipe generated")

    except Exception as e:
        return ApiResponse.error("Recipe generation failed", errors=str(e), status_code=500)


@app.route("/api/history", methods=["GET"])
@token_required
def history(current_user):
    recipes = Recipe.query.filter_by(user_id=current_user.id).order_by(Recipe.created_at.desc()).all()
    history_data = []
    for r in recipes:
        history_data.append({
            'id': r.id,
            'title': r.title,
            'ingredients': json.loads(r.ingredients),
            'nutrition': json.loads(r.nutrition) if r.nutrition else {},
            'created_at': r.created_at.isoformat()
        })

    return ApiResponse.success(data=data, message="History loaded")


@app.route('/api/export_pdf', methods=['POST'])
def export_pdf():
    data = request.get_json()
    title = data.get("title", "Recipe")
    ingredients = data.get("ingredients", [])
    steps = data.get("steps", [])
    nutrition = data.get("nutrition", {})

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=title, ln=1, align="C")
    pdf.ln(10)

    pdf.cell(200, 10, txt="Ingredients:", ln=1)
    for item in ingredients:
        pdf.cell(200, 10, txt=f"- {item}", ln=1)

    pdf.ln(5)
    pdf.cell(200, 10, txt="Steps:", ln=1)
    for step in steps:
        pdf.multi_cell(0, 10, txt=step)

    if nutrition:
        pdf.ln(5)
        pdf.cell(200, 10, txt="Nutrition:", ln=1)
        pdf.multi_cell(0, 10, txt=str(nutrition))

    buf = io.BytesIO()
    output = pdf.output(dest="S")
    output_bytes = output.encode("latin-1") if isinstance(output, str) else output
    buf.write(output_bytes)
    buf.seek(0)

    return send_file(buf, as_attachment=True, download_name="recipe.pdf", mimetype="application/pdf")

def estimate_nutrition(ingredients, servings=1):
    if isinstance(ingredients, str):
        items = [i.strip().lower() for i in ingredients.split(",") if i.strip()]
    elif isinstance(ingredients, list):
        items = [str(i).strip().lower() for i in ingredients]
    else:
        items = []

    lookup = {
        'chicken': {'calories': 250, 'protein': 30, 'fat': 8, 'carbs': 0},
        'chicken breast': {'calories': 220, 'protein': 32, 'fat': 6, 'carbs': 0},
        'broccoli': {'calories': 55, 'protein': 3.7, 'fat': 0.6, 'carbs': 11},
        'rice': {'calories': 200, 'protein': 4.5, 'fat': 0.4, 'carbs': 44},
        'garlic': {'calories': 5, 'protein': 0.2, 'fat': 0, 'carbs': 1},
        'olive oil': {'calories': 120, 'protein': 0, 'fat': 14, 'carbs': 0},
        'soy sauce': {'calories': 10, 'protein': 1, 'fat': 0, 'carbs': 1},
        'default': {'calories': 50, 'protein': 1, 'fat': 1, 'carbs': 5}
    }

    totals = {'calories': 0, 'protein': 0, 'fat': 0, 'carbs': 0}
    for item in items:
        matched = False
        for key, v in lookup.items():
            if key != 'default' and key in item:
                totals['calories'] += v['calories']
                totals['protein'] += v['protein']
                totals['fat'] += v['fat']
                totals['carbs'] += v['carbs']
                matched = True
                break
        if not matched:
            v = lookup['default']
            totals['calories'] += v['calories']
            totals['protein'] += v['protein']
            totals['fat'] += v['fat']
            totals['carbs'] += v['carbs']

    return {
        "calories": int(totals["calories"] / servings),
        "protein": f"{round(totals['protein'] / servings, 1)}g",
        "fat": f"{round(totals['fat'] / servings, 1)}g",
        "carbs": f"{round(totals['carbs'] / servings, 1)}g",
    }

@app.route("/api/calculate_nutrition", methods=["POST"])
def nutrition_calculate():
    data = request.get_json() or {}
    ingredients = data.get('ingredients')
    servings = data.get('servings') or 1

    # Accept a whole recipe object too
    if not ingredients and data.get('recipe'):
        recipe = data.get('recipe')
        ingredients = recipe.get('ingredients', [])
        servings = recipe.get('servings', servings)

    if not ingredients:
        return ApiResponse.error("No ingredients provided")

    try:
        nutrition = estimate_nutrition(ingredients, servings)
        return ApiResponse.success(
            data={"nutrition": nutrition, "servings": servings},
            message="Nutrition calculated"
        )
    except Exception as e:
        return ApiResponse.error("Nutrition calculation failed", errors=str(e), status_code=500)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="127.0.0.1", port=5000, debug=True)