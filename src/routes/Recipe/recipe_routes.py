from flask import Blueprint, request, jsonify
from models.Recipe.recipe_model import Receta
from models.RecipeFavorite.recipe_favorite_model import RecetaFavorita
from models import db
from sqlalchemy import func
from flask_jwt_extended import get_jwt_identity, jwt_required

recipe_bp = Blueprint('recipe_bp', __name__)

@recipe_bp.route('/save', methods=['POST'])
@jwt_required()
def save_recipe():    
    data = request.get_json()
    print("Datos recibidos:", data) 
    user_id = get_jwt_identity()
    print(user_id)
    try:
        if not all(key in data for key in ['titulo', 'descripcion', 'pasos', 'calorias', 'nutrientes', 'tiempo_elaboracion']):
            return jsonify({"error": "Faltan datos obligatorios"}), 400

        receta = Receta(
            usuario_id=user_id,
            titulo=data['titulo'],
            descripcion=data['descripcion'],
            ingredients=data['ingredients'],
            pasos=data['pasos'],
            calorias=data['calorias'],
            nutrientes=data['nutrientes'],
            tiempo_elaboracion=data['tiempo_elaboracion'],
            origen='ia',  
        )

        # Agregar la receta a la base de datos
        db.session.add(receta)
        db.session.commit()

        return jsonify({"message": "Receta guardada con éxito", "receta": receta.serialize()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# 📌 Obtener las recetas más populares
@recipe_bp.route('/popular', methods=['GET'])
def get_popular_recipes():
    popular_recipes = db.session.query(
        Receta.id,
        Receta.titulo,
        func.count(RecetaFavorita.id).label('favorites_count')
    ).join(RecetaFavorita, Receta.id == RecetaFavorita.receta_id)\
     .group_by(Receta.id)\
     .order_by(func.count(RecetaFavorita.id).desc())\
     .limit(10).all()
    
    response = [
        {"id": r.id, "titulo": r.titulo, "favorites_count": r.favorites_count}
        for r in popular_recipes
    ]
    return jsonify(response), 200


# 📌 Cambiar visibilidad de una receta (pública/privada)
@recipe_bp.route('/<int:id>/visibility', methods=['PUT'])
def update_recipe_visibility(id):
    data = request.json
    receta = Receta.query.get(id)
    if not receta:
        return jsonify({"error": "Receta no encontrada"}), 404
    
    receta.visibilidad = data.get('visibilidad', 'privada')
    db.session.commit()
    return jsonify({"message": "Visibilidad de la receta actualizada"}), 200


