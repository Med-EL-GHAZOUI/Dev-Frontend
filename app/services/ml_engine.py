import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

class ForecastingModel:
    def __init__(self, data):
        self.df = data
        self.df = self.df.sort_values('date')
        self.df['date_ordinal'] = self.df['date'].map(lambda x: x.toordinal())

    def get_metrics(self, y_true, y_pred):
        return {
            "MAE": mean_absolute_error(y_true, y_pred),
            "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
            "R2": r2_score(y_true, y_pred)
        }

    def predict_linear_regression(self, horizon_months=6):
        X = self.df[['date_ordinal']].values
        y = self.df['sales_value'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        last_date = self.df['date'].max()
        future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, horizon_months + 1)]
        X_future = np.array([[d.toordinal()] for d in future_dates])
        
        predictions = model.predict(X_future)
        return list(zip(future_dates, predictions))

    def predict_random_forest(self, horizon_months=6):
        X = self.df[['date_ordinal']].values
        y = self.df['sales_value'].values
        
        model = RandomForestRegressor(n_estimators=100)
        model.fit(X, y)
        
        last_date = self.df['date'].max()
        future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, horizon_months + 1)]
        X_future = np.array([[d.toordinal()] for d in future_dates])
        
        predictions = model.predict(X_future)
        return list(zip(future_dates, predictions))

    def predict_arima(self, horizon_months=6):
        # ARIMA requires a frequency, we'll assume monthly for this example
        series = self.df.set_index('date')['sales_value']
        model = ARIMA(series, order=(5,1,0))
        model_fit = model.fit()
        
        predictions = model_fit.forecast(steps=horizon_months)
        last_date = self.df['date'].max()
        future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, horizon_months + 1)]
        
        return list(zip(future_dates, predictions))
