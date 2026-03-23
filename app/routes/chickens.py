from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Farm, ChickenBatch, ChickenDaily
from app import db
from datetime import date, timedelta

chickens_bp = Blueprint('chickens', __name__, url_prefix='/chickens')


@chickens_bp.route('/<int:farm_id>')
@login_required
def index(farm_id):
    farm = Farm.query.filter_by(id=farm_id).first_or_404()
    batches = ChickenBatch.query.filter_by(farm_id=farm_id).order_by(ChickenBatch.created_at.desc()).all()
    return render_template('chickens/index.html', farm=farm, batches=batches)


@chickens_bp.route('/<int:farm_id>/new-batch', methods=['GET', 'POST'])
@login_required
def new_batch(farm_id):
    farm = Farm.query.filter_by(id=farm_id).first_or_404()
    if request.method == 'POST':
        initial = int(request.form.get('initial_count', 0))
        start = request.form.get('start_date')
        total_days = int(request.form.get('total_days', 50))
        from datetime import datetime
        batch = ChickenBatch(
            farm_id=farm_id,
            initial_count=initial,
            start_date=datetime.strptime(start, '%Y-%m-%d').date(),
            total_days=total_days
        )
        db.session.add(batch)
        db.session.flush()

        # Pre-create daily records
        for day in range(1, total_days + 1):
            entry_date = batch.start_date + timedelta(days=day - 1)
            daily = ChickenDaily(
                batch_id=batch.id,
                day_number=day,
                deaths=0,
                remaining=initial,
                entry_date=entry_date
            )
            db.session.add(daily)

        db.session.commit()
        flash('Batch created successfully', 'success')
        return redirect(url_for('chickens.view_batch', batch_id=batch.id))
    return render_template('chickens/new_batch.html', farm=farm)


@chickens_bp.route('/batch/<int:batch_id>')
@login_required
def view_batch(batch_id):
    batch = ChickenBatch.query.get_or_404(batch_id)
    farm = Farm.query.filter_by(id=batch.farm_id).first_or_404()
    records = ChickenDaily.query.filter_by(batch_id=batch_id).order_by(ChickenDaily.day_number).all()
    return render_template('chickens/batch.html', farm=farm, batch=batch, records=records)


@chickens_bp.route('/batch/<int:batch_id>/update', methods=['POST'])
@login_required
def update_batch(batch_id):
    batch = ChickenBatch.query.get_or_404(batch_id)
    Farm.query.filter_by(id=batch.farm_id).first_or_404()

    data = request.get_json()
    records = ChickenDaily.query.filter_by(batch_id=batch_id).order_by(ChickenDaily.day_number).all()

    prev_remaining = batch.initial_count
    for record in records:
        key = str(record.day_number)
        deaths = int(data.get(key, {}).get('deaths', 0))
        record.deaths = deaths
        record.remaining = prev_remaining - deaths
        prev_remaining = record.remaining

    db.session.commit()
    return jsonify({'status': 'ok', 'message': 'Saved successfully'})
