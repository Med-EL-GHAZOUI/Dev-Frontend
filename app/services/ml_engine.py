import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings

try:
    from statsmodels.tsa.arima.model import ARIMA
    has_arima = True
except ImportError:
    has_arima = False

try:
    from prophet import Prophet
    has_prophet = True
except ImportError:
    has_prophet = False

class ForecastingModel:
    def __init__(self, data):
        """
        data: pandas DataFrame with 'date' and 'sales_value' columns
        """
        self.df = data.copy()
        self.df = self.df.sort_values('date')
        
        # Aggregate by month for smoother time series forecasting if daily
        self.df['month'] = self.df['date'].dt.to_period('M')
        monthly = self.df.groupby('month')['sales_value'].sum().reset_index()
        monthly['date'] = monthly['month'].dt.to_timestamp()
        
        self.ts_data = monthly.sort_values('date').copy()
        self.ts_data['date_ordinal'] = self.ts_data['date'].map(lambda x: x.toordinal())

    def get_metrics(self, y_true, y_pred):
        if len(y_true) < 2:
            return {"MAE": 0, "RMSE": 0, "R2": 0}
        return {
            "MAE": mean_absolute_error(y_true, y_pred),
            "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
            "R2": r2_score(y_true, y_pred)
        }

    def _generate_future_dates(self, horizon_months):
        if len(self.ts_data) == 0:
            return []
        last_date = self.ts_data['date'].max()
        return [last_date + pd.DateOffset(months=i) for i in range(1, horizon_months + 1)]

    def predict_linear(self, horizon_months=6):
        if len(self.ts_data) < 3:
            return None, 0
            
        X = self.ts_data[['date_ordinal']].values
        y = self.ts_data['sales_value'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        train_preds = model.predict(X)
        metrics = self.get_metrics(y, train_preds)
        
        future_dates = self._generate_future_dates(horizon_months)
        X_future = np.array([[d.toordinal()] for d in future_dates])
        
        predictions = model.predict(X_future)
        predictions = [max(0, float(p)) for p in predictions]
        
        # Simple confidence interval based on RMSE
        rmse = metrics['RMSE']
        results = []
        for d, p in zip(future_dates, predictions):
            results.append({
                'date': d, 'predicted_value': p, 
                'lower': max(0, p - 1.96 * rmse), 'upper': p + 1.96 * rmse
            })
            
        return results, metrics['R2']

    def predict_random_forest(self, horizon_months=6):
        if len(self.ts_data) < 5:
            return None, 0
            
        # Feature engineering for RF (month, year)
        df_rf = self.ts_data.copy()
        df_rf['year'] = df_rf['date'].dt.year
        df_rf['month_num'] = df_rf['date'].dt.month
        
        X = df_rf[['year', 'month_num']].values
        y = df_rf['sales_value'].values
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        train_preds = model.predict(X)
        metrics = self.get_metrics(y, train_preds)
        
        future_dates = self._generate_future_dates(horizon_months)
        X_future = np.array([[d.year, d.month] for d in future_dates])
        
        predictions = model.predict(X_future)
        predictions = [max(0, float(p)) for p in predictions]
        
        rmse = metrics['RMSE']
        results = []
        for d, p in zip(future_dates, predictions):
            results.append({
                'date': d, 'predicted_value': p, 
                'lower': max(0, p - 1.96 * rmse), 'upper': p + 1.96 * rmse
            })
            
        return results, metrics['R2']

    def predict_arima(self, horizon_months=6):
        if not has_arima or len(self.ts_data) < 10:
            return None, 0
            
        y = self.ts_data['sales_value'].values
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # Auto ARIMA simplified
                model = ARIMA(y, order=(1, 1, 1))
                fit_model = model.fit()
                
                # In-sample for pseudo-R2
                train_preds = fit_model.predict(start=1, end=len(y)-1)
                metrics = self.get_metrics(y[1:], train_preds)
                
                forecast = fit_model.get_forecast(steps=horizon_months)
                mean_forecast = forecast.predicted_mean
                conf_int = forecast.conf_int(alpha=0.05)
                
                future_dates = self._generate_future_dates(horizon_months)
                
                results = []
                for i, d in enumerate(future_dates):
                    p = max(0, mean_forecast[i])
                    results.append({
                        'date': d, 'predicted_value': p,
                        'lower': max(0, conf_int[i][0]), 'upper': max(0, conf_int[i][1])
                    })
                return results, metrics.get('R2', 0)
        except Exception as e:
             return None, 0

    def auto_forecast(self, horizon_months=6):
        """
        Runs available models and selects the best one based on R2 score.
        """
        models = {}
        
        lin_res, lin_r2 = self.predict_linear(horizon_months)
        if lin_res:
            models['Linear Regression'] = {'results': lin_res, 'score': lin_r2}
            
        rf_res, rf_r2 = self.predict_random_forest(horizon_months)
        if rf_res:
             models['Random Forest'] = {'results': rf_res, 'score': rf_r2}
             
        arima_res, arima_r2 = self.predict_arima(horizon_months)
        if arima_res:
             models['ARIMA'] = {'results': arima_res, 'score': arima_r2}
             
        if not models:
            return "Linear Regression", [], 0
            
        # Select best model
        best_model_name = max(models.items(), key=lambda x: x[1]['score'])[0]
        best_model_data = models[best_model_name]
        
        return best_model_name, best_model_data['results'], best_model_data['score']
