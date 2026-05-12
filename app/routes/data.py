from flask import Blueprint, request, jsonify
from app import db
from app.models import Sale, ImportLog
from app.services.etl import process_upload_sync
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

    user_id = get_jwt_identity()
    file_content = file.read()
    
    # Process synchronously for now
    success, log_id = process_upload_sync(file_content, file.filename, user_id)
    
    log = ImportLog.query.get(log_id)
    
    if success:
        return jsonify({
            "msg": f"Successfully processed {log.rows_processed} rows",
            "log_id": log.id
        }), 201
    else:
        return jsonify({
            "msg": "Data processing failed",
            "error": log.errors
        }), 500

@data_bp.route('/data', methods=['GET'])
@jwt_required()
def get_data():
    sales = Sale.query.order_by(Sale.date.desc()).limit(1000).all() # Limit to avoid huge payloads
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

@data_bp.route('/import-logs', methods=['GET'])
@jwt_required()
def get_import_logs():
    user_id = get_jwt_identity()
    logs = ImportLog.query.filter_by(user_id=user_id).order_by(ImportLog.created_at.desc()).limit(20).all()
    return jsonify([{
        "id": log.id,
        "filename": log.filename,
        "status": log.status,
        "rows_processed": log.rows_processed,
        "errors": log.errors,
        "created_at": log.created_at.isoformat()
    } for log in logs]), 200

