from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Farm, Sale, SaleEntry
from app import db
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if getattr(current_user, 'role', 'user') != 'admin':
        flash('Only admins can access the dashboard', 'danger')
        return redirect(url_for('farms.index'))

    # All farms comparison
    farms = Farm.query.all()
    
    # 1. Total KG of chicken per farm (sum of net weight in completed sales)
    # net_weight = load_weight - empty_weight
    farm_data = []
    for farm in farms:
        # Sum of (load_weight - empty_weight) for completed sales of this farm
        total_kg = db.session.query(
            func.sum(SaleEntry.load_weight - SaleEntry.empty_weight)
        ).join(Sale).filter(
            Sale.farm_id == farm.id,
            Sale.status == 'completed'
        ).scalar() or 0.0
        
        farm_data.append({
            'name': farm.name,
            'kg': round(total_kg, 2)
        })

    # 2. Total Chickens per farm
    farm_chickens = []
    for farm in farms:
        total_chickens = db.session.query(
            func.sum(SaleEntry.empty_boxes * SaleEntry.chickens_per_box)
        ).join(Sale).filter(
            Sale.farm_id == farm.id,
            Sale.status == 'completed'
        ).scalar() or 0
        
        farm_chickens.append({
            'name': farm.name,
            'count': total_chickens
        })

    return render_template('admin/dashboard.html', 
                          farm_data=farm_data, 
                          farm_chickens=farm_chickens)
