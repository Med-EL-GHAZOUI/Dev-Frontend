import pandas as pd
import io
from app.models import Sale, ImportLog
from app import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def process_upload_sync(file_content, filename, user_id):
    """
    Synchronous processing of the uploaded file.
    In a fully productionized setup, this should be a Celery task.
    """
    log = ImportLog(user_id=user_id, filename=filename, status='processing')
    db.session.add(log)
    db.session.commit()
    
    try:
        if filename.endswith('.csv'):
            # Detect encoding
            encodings = ['utf-8', 'iso-8859-1', 'cp1252']
            content_decoded = None
            for enc in encodings:
                try:
                    content_decoded = file_content.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            
            if not content_decoded:
                raise ValueError("Could not decode CSV file.")
            
            df = pd.read_csv(io.StringIO(content_decoded))
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise ValueError("Unsupported file format.")
            
        # Clean column names
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        # Mapping mapping logic
        mapping = {
            'product': ['product', 'product name', 'article', 'item', 'produit', 'nom du produit'],
            'region': ['region', 'région', 'zone', 'location', 'country', 'pays', 'ville'],
            'date': ['date', 'order date', 'date de commande', 'timestamp', 'period', 'mois'],
            'sales': ['sales', 'ventes', 'sales_value', 'revenue', 'amount', 'montant', 'chiffre d\'affaire']
        }

        found_mapping = {}
        for target, variations in mapping.items():
            for var in variations:
                if var in df.columns:
                    found_mapping[target] = var
                    break
                    
        required_targets = ['product', 'region', 'date', 'sales']
        missing = [t for t in required_targets if t not in found_mapping]
        
        if missing:
            raise ValueError(f"Missing logical columns: {missing}. Found headers: {df.columns.tolist()}")
            
        # Drop duplicates
        df = df.drop_duplicates()
        
        # Drop rows where required columns are NaN
        df = df.dropna(subset=[found_mapping[t] for t in required_targets])
        
        # Clean sales float
        def clean_float(val):
            if pd.isna(val): return 0.0
            s = str(val).replace('$', '').replace('€', '').replace(',', '').replace(' ', '').strip()
            try:
                return float(s)
            except:
                return 0.0
                
        df['clean_sales'] = df[found_mapping['sales']].apply(clean_float)
        
        # Parse dates
        df['parsed_date'] = pd.to_datetime(df[found_mapping['date']], errors='coerce')
        df = df.dropna(subset=['parsed_date'])
        
        # Save to DB
        sales_to_insert = []
        for _, row in df.iterrows():
            sale = Sale(
                product=str(row[found_mapping['product']]),
                region=str(row[found_mapping['region']]),
                date=row['parsed_date'],
                sales_value=row['clean_sales'],
                user_id=user_id
            )
            sales_to_insert.append(sale)
            
        db.session.bulk_save_objects(sales_to_insert)
        
        log.status = 'completed'
        log.rows_processed = len(sales_to_insert)
        db.session.commit()
        return True, log.id
        
    except Exception as e:
        logger.error(f"ETL Error: {e}")
        log.status = 'failed'
        log.errors = str(e)
        db.session.commit()
        return False, log.id
