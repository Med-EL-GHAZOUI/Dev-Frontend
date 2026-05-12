from flask import Blueprint, request, jsonify
from app import db
from app.models import Sale, Prediction
from app.services.ml_engine import ForecastingModel
import pandas as pd
from datetime import datetime
from flask_jwt_extended import jwt_required

predict_bp = Blueprint('predict', __name__)

@predict_bp.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    data = request.get_json()
    product = data.get('product')
    region = data.get('region')
    horizon = int(data.get('horizon', 6)) # Months
    model_choice = data.get('model', 'auto') # 'auto', 'Linear Regression', 'Random Forest', 'ARIMA'

    # Get historical data
    query = Sale.query
    if product:
        query = query.filter_by(product=product)
    if region:
        query = query.filter_by(region=region)
    
    sales = query.all()
    if len(sales) < 5:
        return jsonify({"msg": "Not enough data for advanced prediction (minimum 5 points required)"}), 400

    # Prepare data for ML engine
    df = pd.DataFrame([{
        "date": s.date,
        "sales_value": float(s.sales_value)
    } for s in sales])

    try:
        # Initialize ML Engine
        engine = ForecastingModel(df)
        
        if model_choice == 'auto':
            best_model_name, forecast_results, accuracy = engine.auto_forecast(horizon_months=horizon)
        elif model_choice == 'Random Forest':
            forecast_results, accuracy = engine.predict_random_forest(horizon_months=horizon)
            best_model_name = 'Random Forest'
        elif model_choice == 'ARIMA':
            forecast_results, accuracy = engine.predict_arima(horizon_months=horizon)
            best_model_name = 'ARIMA'
        else:
            forecast_results, accuracy = engine.predict_linear(horizon_months=horizon)
            best_model_name = 'Linear Regression'
            
        if not forecast_results:
             return jsonify({"msg": "Could not generate forecast. Check data quality."}), 500
        
        predictions_output = []
        for result in forecast_results:
            future_date = result['date']
            pred_value = result['predicted_value']
            lower = result['lower']
            upper = result['upper']
            
            # Save prediction to DB
            prediction = Prediction(
                predicted_value=float(pred_value),
                confidence_lower=float(lower),
                confidence_upper=float(upper),
                date=future_date,
                model_type=best_model_name,
                accuracy_score=float(accuracy),
                product=product,
                region=region
            )
            db.session.add(prediction)
            
            predictions_output.append({
                "date": future_date.strftime('%Y-%m-%d'),
                "predicted_value": round(float(pred_value), 2),
                "lower_bound": round(float(lower), 2),
                "upper_bound": round(float(upper), 2)
            })

        db.session.commit()
        return jsonify({
            "model_used": best_model_name,
            "accuracy_score": round(accuracy, 4),
            "predictions": predictions_output
        }), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"msg": f"Error during prediction: {str(e)}"}), 500
