from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Farm
from app import db

farms_bp = Blueprint('farms', __name__, url_prefix='/farms')


@farms_bp.route('/')
@login_required
def index():
    q = request.args.get('q', '').strip()
    query = Farm.query
    if q:
        query = query.filter(
            Farm.name.ilike(f'%{q}%') |
            Farm.village.ilike(f'%{q}%') |
            Farm.district.ilike(f'%{q}%')
        )
    farms = query.order_by(Farm.created_at.desc()).all()
    return render_template('farms/index.html', farms=farms, q=q)


@farms_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        farm = Farm(
            name=request.form.get('name', '').strip(),
            village=request.form.get('village', '').strip(),
            district=request.form.get('district', '').strip(),
            phone=request.form.get('phone', '').strip(),
            user_id=current_user.id
        )
        db.session.add(farm)
        db.session.commit()
        flash('Farm added successfully', 'success')
        return redirect(url_for('farms.index'))
    return render_template('farms/form.html', farm=None)


@farms_bp.route('/edit/<int:fid>', methods=['GET', 'POST'])
@login_required
def edit(fid):
    farm = Farm.query.filter_by(id=fid).first_or_404()
    if request.method == 'POST':
        farm.name = request.form.get('name', '').strip()
        farm.village = request.form.get('village', '').strip()
        farm.district = request.form.get('district', '').strip()
        farm.phone = request.form.get('phone', '').strip()
        db.session.commit()
        flash('Farm updated successfully', 'success')
        return redirect(url_for('farms.index'))
    return render_template('farms/form.html', farm=farm)


@farms_bp.route('/delete/<int:fid>', methods=['POST'])
@login_required
def delete(fid):
    farm = Farm.query.filter_by(id=fid).first_or_404()
    db.session.delete(farm)
    db.session.commit()
    flash('Farm deleted', 'success')
    return redirect(url_for('farms.index'))


@farms_bp.route('/api/list')
@login_required
def api_list():
    farms = Farm.query.all()
    return jsonify([{'id': f.id, 'name': f.name} for f in farms])
