from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Farm, FeedStock, FeedUsage, ChickenDaily
from app import db
from datetime import datetime
from sqlalchemy import func

feed_bp = Blueprint('feed', __name__, url_prefix='/feed')


@feed_bp.route('/<int:farm_id>')
@login_required
def index(farm_id):
    farm = Farm.query.filter_by(id=farm_id).first_or_404()
    stocks = FeedStock.query.filter_by(farm_id=farm_id).order_by(FeedStock.date.desc()).all()
    usages = FeedUsage.query.filter_by(farm_id=farm_id).order_by(FeedUsage.day_number).all()

    total_added = float(db.session.query(func.sum(FeedStock.bags_added)).filter_by(farm_id=farm_id).scalar() or 0)
    total_used = float(db.session.query(func.sum(FeedUsage.bags_used)).filter_by(farm_id=farm_id).scalar() or 0)
    remaining = total_added - total_used

    active_batch = farm.active_batch
    remaining_chickens = active_batch.initial_count if active_batch else 0
    if active_batch and active_batch.daily_records:
        # Get the latest record's remaining count
        latest = db.session.query(ChickenDaily).filter_by(batch_id=active_batch.id).order_by(ChickenDaily.day_number.desc()).first()
        if latest:
            remaining_chickens = latest.remaining

    return render_template('feed/index.html',
                           farm=farm, stocks=stocks, usages=usages,
                           total_added=total_added, total_used=total_used, remaining=remaining,
                           active_batch=active_batch,
                           remaining_chickens=remaining_chickens)


@feed_bp.route('/<int:farm_id>/add-stock', methods=['POST'])
@login_required
def add_stock(farm_id):
    Farm.query.filter_by(id=farm_id).first_or_404()
    bags = int(request.form.get('bags_added', 0))
    date_str = request.form.get('date')
    note = request.form.get('note', '').strip()

    stock = FeedStock(
        farm_id=farm_id,
        bags_added=bags,
        date=datetime.strptime(date_str, '%Y-%m-%d').date(),
        note=note
    )
    db.session.add(stock)
    db.session.commit()
    flash('Feed stock added', 'success')
    return redirect(url_for('feed.index', farm_id=farm_id))


@feed_bp.route('/<int:farm_id>/delete-stock/<int:sid>', methods=['POST'])
@login_required
def delete_stock(farm_id, sid):
    stock = FeedStock.query.filter_by(id=sid, farm_id=farm_id).first_or_404()
    db.session.delete(stock)
    db.session.commit()
    flash('Stock entry deleted', 'success')
    return redirect(url_for('feed.index', farm_id=farm_id))


@feed_bp.route('/<int:farm_id>/save-usage', methods=['POST'])
@login_required
def save_usage(farm_id):
    farm = Farm.query.filter_by(id=farm_id).first_or_404()
    data = request.get_json()

    total_added = float(db.session.query(func.sum(FeedStock.bags_added)).filter_by(farm_id=farm_id).scalar() or 0)
    new_total_used = sum(float(v.get('bags_used', 0)) for v in data.values())

    if new_total_used > total_added:
        return jsonify({'status': 'error', 'message': 'Usage exceeds stock!'})

    # Clear existing usage for this farm
    FeedUsage.query.filter_by(farm_id=farm_id).delete()

    for day_str, vals in data.items():
        bags = float(vals.get('bags_used', 0))
        if bags > 0:
            usage = FeedUsage(
                farm_id=farm_id,
                day_number=int(day_str),
                bags_used=bags,
                entry_date=datetime.strptime(vals.get('date', ''), '%Y-%m-%d').date() if vals.get('date') else None
            )
            db.session.add(usage)

    db.session.commit()
    return jsonify({'status': 'ok', 'message': 'Feed usage saved'})
