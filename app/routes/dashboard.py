from flask import Blueprint, jsonify
from app import db
from app.models import Sale, Prediction
from sqlalchemy import func
from flask_jwt_extended import jwt_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    # Total Revenue
    total_revenue = db.session.query(func.sum(Sale.sales_value)).scalar() or 0
    
    # Sales by Region
    region_stats = db.session.query(
        Sale.region, func.sum(Sale.sales_value)
    ).group_by(Sale.region).all()
    
    # Sales by Product
    product_stats = db.session.query(
        Sale.product, func.sum(Sale.sales_value)
    ).group_by(Sale.product).all()

    return jsonify({
        "total_revenue": round(total_revenue, 2),
        "regions": [{"name": r[0], "value": round(r[1], 2)} for r in region_stats],
        "products": [{"name": p[0], "value": round(p[1], 2)} for p in product_stats]
    }), 200
