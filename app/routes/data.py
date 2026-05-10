from flask import Blueprint, request, jsonify
from app import db
from app.models import Sale
import pandas as pd
import io
from flask_jwt_extended import jwt_required, get_jwt_identity

data_bp = Blueprint('data', __name__)

@data_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_data():
    if 'file' not in request.files:
        return jsonify({"msg": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"msg": "No selected file"}), 400

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(file.stream.read().decode("UTF8")))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file.stream)
        else:
            return jsonify({"msg": "Unsupported file format"}), 400

        # Required columns check (case-insensitive for convenience)
        required_cols = ['product', 'region', 'date', 'sales']
        df.columns = [c.lower() for c in df.columns]
        
        if not all(col in df.columns for col in required_cols):
            return jsonify({"msg": f"Missing columns. Required: {required_cols}"}), 400

        # Basic cleaning
        df = df.dropna(subset=required_cols)
        df['date'] = pd.to_datetime(df['date'])
        
        user_id = get_jwt_identity()

        for _, row in df.iterrows():
            sale = Sale(
                product=row['product'],
                region=row['region'],
                date=row['date'],
                sales_value=row['sales'],
                user_id=user_id
            )
            db.session.add(sale)
        
        db.session.commit()
        return jsonify({"msg": f"Successfully uploaded {len(df)} rows"}), 201

    except Exception as e:
        return jsonify({"msg": str(e)}), 500

@data_bp.route('/data', methods=['GET'])
@jwt_required()
def get_data():
    sales = Sale.query.all()
    output = []
    for sale in sales:
        output.append({
            "id": sale.id,
            "product": sale.product,
            "region": sale.region,
            "date": sale.date.strftime('%Y-%m-%d'),
            "sales_value": sale.sales_value
        })
    return jsonify(output), 200
