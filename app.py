from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, Recipe
import google.generativeai as genai
import json
import io
from fpdf import FPDF

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, supports_credentials=True)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configure Gemini
if app.config['GEMINI_API_KEY']:
    genai.configure(api_key=app.config['GEMINI_API_KEY'])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def hello_world():
    return 'ChefAI Backend is Running!'

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({'message': 'Login successful', 'user_id': user.id, 'username': user.username})
    
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/check_session', methods=['GET'])
def check_session():
    if current_user.is_authenticated:
        return jsonify({'logged_in': True, 'user_id': current_user.id, 'username': current_user.username})
    return jsonify({'logged_in': False})

@app.route('/api/generate_recipe', methods=['POST'])
def generate_recipe():
    data = request.get_json()
    ingredients = data.get('ingredients')
    
    if not ingredients:
        return jsonify({'error': 'Please enter at least one ingredient.'}), 400
        
    if not app.config['GEMINI_API_KEY']:
        # Mock response for development without API Key
        mock_response = {
            "title": "Mock Chicken Stir Fry",
            "ingredients": ["chicken", "broccoli", "soy sauce"],
            "missing_ingredients": ["sesame oil", "garlic"],
            "steps": ["1. Cut chicken.", "2. Stir fry with veggies.", "3. Serve."],
            "nutrition": { "calories": 450, "protein": "35g", "fat": "12g", "carbs": "10g" },
            "time": "25 mins",
            "difficulty": "Easy",
            "servings": 2
        }
        return jsonify(mock_response)

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Create a recipe using these ingredients: {ingredients}.
        You can assume common pantry items (salt, pepper, oil, water) are available.
        Return ONLY a JSON object with the following structure (no markdown formatting):
        {{
            "title": "Recipe Name",
            "ingredients": ["list", "of", "ingredients", "used"],
            "missing_ingredients": ["list", "of", "missing", "essential", "ingredients"],
            "steps": ["step 1", "step 2"],
            "nutrition": {{ "calories": 500, "protein": "20g", "fat": "10g", "carbs": "50g" }},
            "time": "30 mins",
            "difficulty": "Easy/Medium/Hard",
            "servings": 2
        }}
        """
        response = model.generate_content(prompt)
        
        # Clean up response text to ensure valid JSON
        text = response.text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.endswith('```'):
            text = text[:-3]
            
        recipe_data = json.loads(text)
        
        # Save to DB if user is logged in
        if current_user.is_authenticated:
            recipe = Recipe(
                user_id=current_user.id,
                title=recipe_data['title'],
                ingredients=json.dumps(recipe_data['ingredients']),
                missing_ingredients=json.dumps(recipe_data.get('missing_ingredients', [])),
                steps=json.dumps(recipe_data['steps']),
                nutrition=json.dumps(recipe_data.get('nutrition', {})),
            )
            db.session.add(recipe)
            db.session.commit()
            
        return jsonify(recipe_data)
        
    except Exception as e:
        print(f"Error generating recipe: {e}")
        return jsonify({'error': 'Recipe generation failed. Try again later.'}), 500

@app.route('/api/history', methods=['GET'])
@login_required
def history():
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
    return jsonify(history_data)

@app.route('/api/export_pdf', methods=['POST'])
def export_pdf():
    data = request.get_json()
    title = data.get('title', 'Recipe')
    ingredients = data.get('ingredients', [])
    steps = data.get('steps', [])
    nutrition = data.get('nutrition', {})
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt=title, ln=1, align='C')
    pdf.ln(10)
    
    pdf.cell(200, 10, txt="Ingredients:", ln=1)
    for ing in ingredients:
        pdf.cell(200, 10, txt=f"- {ing}", ln=1)
    pdf.ln(5)
        
    pdf.cell(200, 10, txt="Steps:", ln=1)
    for step in steps:
        pdf.multi_cell(0, 10, txt=f"{step}")
    pdf.ln(5)
    
    if nutrition:
        pdf.cell(200, 10, txt="Nutrition:", ln=1)
        nutrition_text = ", ".join([f"{k}: {v}" for k, v in nutrition.items()])
        pdf.multi_cell(0, 10, txt=nutrition_text)
        
    # Output to memory
    pdf_output = io.BytesIO()
    try:
        pdf_string = pdf.output(dest='S')
        if isinstance(pdf_string, str):
             pdf_bytes = pdf_string.encode('latin-1')
        else:
             pdf_bytes = pdf_string
    except TypeError:
        # Newer FPDF versions might act differently or take no dest arg to return bytes directly?
        # If dest='S' fails, try output() without args if it returns bytes, 
        # but fpdf 1.7.2 (installed) uses dest='S' to return string.
        # Let's stick to the string encoding which is standard for fpdf 1.7.
        pdf_bytes = pdf.output(dest='S').encode('latin-1')

    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    
    return send_file(
        pdf_output,
        as_attachment=True,
        download_name='recipe.pdf',
        mimetype='application/pdf'
    )


@app.route('/recipe/generate', methods=['POST'])
def recipe_generate_alias():
    """Alias endpoint to match spec `/recipe/generate` - reuses existing logic."""
    return generate_recipe()


def estimate_nutrition(ingredients, servings=1):
    """
    Lightweight nutrition estimator for demo purposes.
    Accepts `ingredients` as a string (comma-separated) or list.
    Returns per-serving calories/protein/fat/carbs.
    """
    # Normalize to list of lowercase ingredient names
    if isinstance(ingredients, str):
        items = [i.strip().lower() for i in ingredients.split(',') if i.strip()]
    elif isinstance(ingredients, list):
        items = [str(i).strip().lower() for i in ingredients]
    else:
        items = []

    # Very small lookup table (per typical portion) for demo
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

    if servings and servings > 0:
        per_serving = {
            'calories': int(totals['calories'] / servings),
            'protein': f"{round(totals['protein'] / servings, 1)}g",
            'fat': f"{round(totals['fat'] / servings, 1)}g",
            'carbs': f"{round(totals['carbs'] / servings, 1)}g",
        }
    else:
        per_serving = {
            'calories': int(totals['calories']),
            'protein': f"{round(totals['protein'],1)}g",
            'fat': f"{round(totals['fat'],1)}g",
            'carbs': f"{round(totals['carbs'],1)}g",
        }

    return per_serving


@app.route('/nutrition/calculate', methods=['POST'])
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
        return jsonify({'error': 'No ingredients provided'}), 400

    try:
        nutrition = estimate_nutrition(ingredients, servings=servings)
        return jsonify({'nutrition': nutrition, 'servings': servings})
    except Exception as e:
        print(f"Nutrition calc error: {e}")
        return jsonify({'error': 'Nutrition calculation failed.'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
