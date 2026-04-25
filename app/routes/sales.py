from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Farm, Sale, SaleEntry, Customer
from app import db
from datetime import date

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')


def generate_sale_code():
    last = Sale.query.order_by(Sale.id.desc()).first()
    num = (last.id + 1) if last else 1
    return f'SALE_{num:03d}'


@sales_bp.route('/<int:farm_id>')
@login_required
def index(farm_id):
    farm = Farm.query.filter_by(id=farm_id).first_or_404()
    q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '')

    query = Sale.query.filter_by(farm_id=farm_id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if q:
        query = query.join(Customer).filter(Customer.name.ilike(f'%{q}%'))

    sales = query.order_by(Sale.created_at.desc()).all()
    return render_template('sales/index.html', farm=farm, sales=sales, q=q, status_filter=status_filter)


@sales_bp.route('/<int:farm_id>/new', methods=['GET', 'POST'])
@login_required
def new_sale(farm_id):
    farm = Farm.query.filter_by(id=farm_id).first_or_404()
    if request.method == 'POST':
        sale = Sale(
            sale_code=generate_sale_code(),
            farm_id=farm_id,
            status='draft',
            sale_date=date.today()
        )
        db.session.add(sale)
        db.session.commit()
        return redirect(url_for('sales.edit_sale', sale_id=sale.id))
    return render_template('sales/new.html', farm=farm)


@sales_bp.route('/edit/<int:sale_id>', methods=['GET', 'POST'])
@login_required
def edit_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    farm = Farm.query.filter_by(id=sale.farm_id).first_or_404()
    return render_template('sales/edit.html', sale=sale, farm=farm)


@sales_bp.route('/api/save-draft/<int:sale_id>', methods=['POST'])
@login_required
def save_draft(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    Farm.query.filter_by(id=sale.farm_id).first_or_404()

    if sale.status == 'completed':
        return jsonify({'status': 'error', 'message': 'Sale is already completed'})

    data = request.get_json()
    entries_data = data.get('entries', [])
    customer_data = data.get('customer', {})

    # Clear existing entries
    SaleEntry.query.filter_by(sale_id=sale_id).delete()

    for i, e in enumerate(entries_data, 1):
        entry = SaleEntry(
            sale_id=sale_id,
            entry_number=i,
            empty_boxes=int(e.get('empty_boxes', 0)),
            empty_weight=float(e.get('empty_weight', 0)),
            chickens_per_box=int(e.get('chickens_per_box', 0)),
            load_weight=float(e.get('load_weight', 0))
        )
        db.session.add(entry)

    if customer_data and customer_data.get('name'):
        Customer.query.filter_by(sale_id=sale_id).delete()
        customer = Customer(
            sale_id=sale_id,
            name=customer_data.get('name', ''),
            phone=customer_data.get('phone', ''),
            vehicle_number=customer_data.get('vehicle_number', ''),
            price_per_kg=float(customer_data.get('price_per_kg', 0) or 0)
        )
        db.session.add(customer)

    db.session.commit()
    return jsonify({'status': 'ok', 'sale_code': sale.sale_code, 'message': 'Draft saved'})


@sales_bp.route('/api/complete/<int:sale_id>', methods=['POST'])
@login_required
def complete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    Farm.query.filter_by(id=sale.farm_id).first_or_404()

    data = request.get_json()
    entries_data = data.get('entries', [])
    customer_data = data.get('customer', {})

    # Save entries
    SaleEntry.query.filter_by(sale_id=sale_id).delete()
    for i, e in enumerate(entries_data, 1):
        entry = SaleEntry(
            sale_id=sale_id,
            entry_number=i,
            empty_boxes=int(e.get('empty_boxes', 0)),
            empty_weight=float(e.get('empty_weight', 0)),
            chickens_per_box=int(e.get('chickens_per_box', 0)),
            load_weight=float(e.get('load_weight', 0))
        )
        db.session.add(entry)

    # Save customer
    Customer.query.filter_by(sale_id=sale_id).delete()
    customer = Customer(
        sale_id=sale_id,
        name=customer_data.get('name', ''),
        phone=customer_data.get('phone', ''),
        vehicle_number=customer_data.get('vehicle_number', ''),
        price_per_kg=float(customer_data.get('price_per_kg', 0))
    )
    db.session.add(customer)

    sale.status = 'completed'
    from datetime import date as d
    sale_date = d.today()
    sale.sale_date = sale_date
    
    # Update ChickenDaily records to subtract sold chickens
    total_sold = sum(int(e.get('empty_boxes', 0)) * int(e.get('chickens_per_box', 0)) for e in entries_data)
    
    from app.models import ChickenBatch, ChickenDaily
    # Find active batch for this farm (one that covers today)
    batch = ChickenBatch.query.filter(
        ChickenBatch.farm_id == sale.farm_id,
        ChickenBatch.start_date <= sale_date
    ).order_by(ChickenBatch.start_date.desc()).first()
    
    if batch:
        # Find the record for today or the sale date
        daily_record = ChickenDaily.query.filter_by(batch_id=batch.id, entry_date=sale_date).first()
        if daily_record:
            daily_record.sold_count = (daily_record.sold_count or 0) + total_sold
            
            # Recalculate all subsequent days' remaining count
            all_records = ChickenDaily.query.filter_by(batch_id=batch.id).order_by(ChickenDaily.day_number).all()
            prev_rem = batch.initial_count
            for r in all_records:
                r.remaining = prev_rem - (r.deaths or 0) - (r.sold_count or 0)
                prev_rem = r.remaining

    db.session.commit()

    return jsonify({'status': 'ok', 'message': 'Sale completed'})


@sales_bp.route('/api/get/<int:sale_id>')
@login_required
def get_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    Farm.query.filter_by(id=sale.farm_id).first_or_404()

    entries = [{'empty_boxes': e.empty_boxes, 'empty_weight': e.empty_weight,
                'chickens_per_box': e.chickens_per_box, 'load_weight': e.load_weight}
               for e in sale.entries]

    customer = {}
    if sale.customer:
        customer = {'name': sale.customer.name, 'phone': sale.customer.phone,
                    'vehicle_number': sale.customer.vehicle_number, 'price_per_kg': sale.customer.price_per_kg}

    return jsonify({'entries': entries, 'customer': customer, 'status': sale.status, 'sale_code': sale.sale_code})


@sales_bp.route('/delete/<int:sale_id>', methods=['POST'])
@login_required
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    farm = Farm.query.filter_by(id=sale.farm_id).first_or_404()
    db.session.delete(sale)
    db.session.commit()
    flash('Sale deleted', 'success')
    return redirect(url_for('sales.index', farm_id=farm.id))
