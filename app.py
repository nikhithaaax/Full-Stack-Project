from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from datetime import datetime
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pets.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---------- Models ----------
class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    species = db.Column(db.String(50), nullable=False)   # Dog, Cat, Rabbit, etc.
    breed = db.Column(db.String(120), nullable=True)
    age = db.Column(db.String(50), nullable=False)       # Baby, Young, Adult, Senior
    size = db.Column(db.String(50), nullable=False)      # Small, Medium, Large, X-Large
    gender = db.Column(db.String(20), nullable=False)    # Male, Female
    city = db.Column(db.String(120), nullable=True)
    state = db.Column(db.String(120), nullable=True)
    good_with_kids = db.Column(db.Boolean, default=False)
    vaccinated = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdoptionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---------- Seed data ----------
def seed_data():
    if Pet.query.count() > 0:
        return
    demo_pets = [
        Pet(name="Buddy", species="Dog", breed="Labrador Mix", age="Young", size="Large",
            gender="Male", city="Bengaluru", state="Karnataka", good_with_kids=True,
            vaccinated=True, description="Playful and loves fetch!",
            photo_url="https://picsum.photos/seed/dog1/600/400"),
        Pet(name="Luna", species="Cat", breed="Siamese", age="Adult", size="Small",
            gender="Female", city="Pune", state="Maharashtra", good_with_kids=True,
            vaccinated=True, description="Calm, cuddly, and curious.",
            photo_url="https://picsum.photos/seed/cat1/600/400"),
        Pet(name="Coco", species="Rabbit", breed="Holland Lop", age="Baby", size="Small",
            gender="Female", city="Delhi", state="Delhi", good_with_kids=True,
            vaccinated=False, description="Tiny hopper, very gentle.",
            photo_url="https://picsum.photos/seed/rabbit1/600/400"),
        Pet(name="Max", species="Dog", breed="Beagle", age="Adult", size="Medium",
            gender="Male", city="Mumbai", state="Maharashtra", good_with_kids=False,
            vaccinated=True, description="Sniffer pro. Needs active family.",
            photo_url="https://picsum.photos/seed/dog2/600/400"),
        Pet(name="Misty", species="Cat", breed="Persian", age="Senior", size="Small",
            gender="Female", city="Hyderabad", state="Telangana", good_with_kids=False,
            vaccinated=True, description="Regal, relaxed, and low-maintenance.",
            photo_url="https://picsum.photos/seed/cat2/600/400"),
    ]
    db.session.add_all(demo_pets)
    db.session.commit()

# ---------- Pages ----------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/pets/<int:pet_id>")
def pet_detail_page(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    return render_template("pet_detail.html", pet=pet)

@app.route("/admin")
def admin_page():
    return render_template("admin.html")

# ---------- API: Pets with filters, sort, pagination ----------
@app.route("/api/pets")
def api_pets():
    q = request.args.get("q", "", type=str).strip()
    species = request.args.get("species", "", type=str)
    age = request.args.get("age", "", type=str)
    size = request.args.get("size", "", type=str)
    gender = request.args.get("gender", "", type=str)
    city = request.args.get("city", "", type=str)
    state = request.args.get("state", "", type=str)
    kids = request.args.get("kids", "", type=str)       # 'true' or ''
    vacc = request.args.get("vaccinated", "", type=str) # 'true' or ''
    sort = request.args.get("sort", "newest", type=str) # newest|name|age
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 8, type=int)

    query = Pet.query

    if q:
        ilike = f"%{q}%"
        query = query.filter(or_(Pet.name.ilike(ilike), Pet.breed.ilike(ilike), Pet.description.ilike(ilike), Pet.city.ilike(ilike), Pet.state.ilike(ilike)))
    if species:
        query = query.filter(Pet.species == species)
    if age:
        query = query.filter(Pet.age == age)
    if size:
        query = query.filter(Pet.size == size)
    if gender:
        query = query.filter(Pet.gender == gender)
    if city:
        query = query.filter(Pet.city.ilike(f"%{city}%"))
    if state:
        query = query.filter(Pet.state.ilike(f"%{state}%"))
    if kids == "true":
        query = query.filter(Pet.good_with_kids.is_(True))
    if vacc == "true":
        query = query.filter(Pet.vaccinated.is_(True))

    if sort == "name":
        query = query.order_by(Pet.name.asc())
    elif sort == "age":
        # crude ordering: Baby < Young < Adult < Senior
        case = db.case(
            (Pet.age == "Baby", 1),
            (Pet.age == "Young", 2),
            (Pet.age == "Adult", 3),
            (Pet.age == "Senior", 4),
            else_=5
        )
        query = query.order_by(case.asc(), Pet.created_at.desc())
    else:
        query = query.order_by(Pet.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    items = [{
        "id": p.id,
        "name": p.name,
        "species": p.species,
        "breed": p.breed,
        "age": p.age,
        "size": p.size,
        "gender": p.gender,
        "city": p.city,
        "state": p.state,
        "good_with_kids": p.good_with_kids,
        "vaccinated": p.vaccinated,
        "photo_url": p.photo_url,
        "created_at": p.created_at.isoformat()
    } for p in pagination.items]

    return jsonify({
        "items": items,
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total
    })

@app.route("/api/pets/<int:pet_id>")
def api_pet_detail(pet_id):
    p = Pet.query.get_or_404(pet_id)
    return jsonify({
        "id": p.id,
        "name": p.name,
        "species": p.species,
        "breed": p.breed,
        "age": p.age,
        "size": p.size,
        "gender": p.gender,
        "city": p.city,
        "state": p.state,
        "good_with_kids": p.good_with_kids,
        "vaccinated": p.vaccinated,
        "description": p.description,
        "photo_url": p.photo_url,
        "created_at": p.created_at.isoformat()
    })

# ---------- API: Create adoption request ----------
@app.route("/api/adopt", methods=["POST"])
def api_adopt():
    data = request.get_json(force=True)
    pet_id = data.get("pet_id")
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    message = data.get("message", "").strip()

    if not (pet_id and full_name and email):
        return jsonify({"ok": False, "error": "Missing required fields."}), 400

    req = AdoptionRequest(
        pet_id=pet_id, full_name=full_name, email=email,
        phone=phone, message=message
    )
    db.session.add(req)
    db.session.commit()
    return jsonify({"ok": True, "id": req.id})

# ---------- API: Admin add a pet (simple, no auth) ----------
@app.route("/api/admin/pets", methods=["POST"])
def api_admin_add_pet():
    data = request.get_json(force=True)
    required = ["name", "species", "age", "size", "gender"]
    if any(not data.get(k) for k in required):
        return jsonify({"ok": False, "error": "Missing required fields."}), 400

    pet = Pet(
        name=data["name"].strip(),
        species=data["species"].strip(),
        breed=(data.get("breed") or "").strip(),
        age=data["age"].strip(),
        size=data["size"].strip(),
        gender=data["gender"].strip(),
        city=(data.get("city") or "").strip(),
        state=(data.get("state") or "").strip(),
        good_with_kids=bool(data.get("good_with_kids")),
        vaccinated=bool(data.get("vaccinated")),
        description=(data.get("description") or "").strip(),
        photo_url=(data.get("photo_url") or "").strip() or "/static/img/placeholder.png"
    )
    db.session.add(pet)
    db.session.commit()
    return jsonify({"ok": True, "id": pet.id})

# ---------- App bootstrap ----------
if __name__ == "__main__":
    if not os.path.exists("pets.db"):
        with app.app_context():
            db.create_all()
            seed_data()
    else:
        with app.app_context():
            db.create_all()
            # no reseed on existing db
    app.run(debug=True)
