from app import create_app, db
from app.models import Sale, Farm

app = create_app()
with app.app_context():
    farms = Farm.query.all()
    for farm in farms:
        sales = Sale.query.filter_by(farm_id=farm.id).order_by(Sale.id).all()
        for i, sale in enumerate(sales, 1):
            sale.sale_code = f'SALE_{i:03d}'
    
    db.session.commit()
    print('Sales renumbered successfully per farm')
