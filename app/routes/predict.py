from flask import Blueprint, request, jsonify
from app import db
from app.models import Sale, Prediction
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from datetime import timedelta
from flask_jwt_extended import jwt_required

predict_bp = Blueprint('predict', __name__)

@predict_bp.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    data = request.get_json()
    product = data.get('product')
    region = data.get('region')
    horizon = int(data.get('horizon', 6)) # Months

    # Get historical data
    query = Sale.query
    if product:
        query = query.filter_by(product=product)
    if region:
        query = query.filter_by(region=region)
    
    sales = query.all()
    if len(sales) < 2:
        return jsonify({"msg": "Not enough data for prediction"}), 400

    df = pd.DataFrame([{
        "date": s.date,
        "value": s.sales_value
    } for s in sales])

    df = df.sort_values('date')
    df['date_ordinal'] = df['date'].map(lambda x: x.toordinal())

    X = df[['date_ordinal']].values
    y = df['value'].values

    model = LinearRegression()
    model.fit(X, y)

    # Predict future dates
    last_date = df['date'].max()
    predictions = []
    
    for i in range(1, horizon + 1):
        future_date = last_date + pd.DateOffset(months=i)
        pred_value = model.predict([[future_date.toordinal()]])[0]
        
        # Save prediction
        prediction = Prediction(
            predicted_value=float(pred_value),
            date=future_date,
            model_type="Linear Regression",
            product=product,
            region=region
        )
        db.session.add(prediction)
        predictions.append({
            "date": future_date.strftime('%Y-%m-%d'),
            "predicted_value": round(float(pred_value), 2)
        })

    db.session.commit()
    return jsonify(predictions), 200
