"""
Employee Activity Tracking Application

This Flask application provides functionality for tracking employee activities,
including time spent on different projects, clients, and tasks. It supports
activity logging, reporting, and data export features.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from contextlib import contextmanager
import pandas as pd
from io import BytesIO
from models import User, Activity, Leave, Expense, user_to_dict, activity_to_dict, leave_to_dict, expense_to_dict
from database import engine, Base, SessionLocal
from dotenv import load_dotenv
from functools import wraps
from sqlalchemy.orm import Session
from sqlalchemy import func
import calendar
from datetime import timedelta

# Încarcă variabilele de mediu
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Decorator pentru a verifica dacă utilizatorul este autentificat
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vă rugăm să vă autentificați pentru a accesa această pagină.', 'error')
            return redirect(url_for('login'))
        try:
            db = SessionLocal()
            user = db.query(User).get(session['user_id'])
            if not user:
                session.clear()
                flash('Sesiune invalidă. Vă rugăm să vă autentificați din nou.', 'error')
                return redirect(url_for('login'))
        except Exception as e:
            print(f"Eroare la verificarea sesiunii: {str(e)}")
            session.clear()
            flash('A apărut o eroare. Vă rugăm să vă autentificați din nou.', 'error')
            return redirect(url_for('login'))
        finally:
            db.close()
        return f(*args, **kwargs)
    return decorated_function

def leave_to_dict(leave):
    return {
        'id': leave.id,
        'start_date': leave.start_date.strftime('%Y-%m-%d'),
        'end_date': leave.end_date.strftime('%Y-%m-%d'),
        'leave_type': leave.leave_type,
        'description': leave.description
    }

@contextmanager
def get_db_session():
    """Context manager pentru gestionarea sesiunilor de bază de date"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def check_session():
    """Verifică dacă sesiunea este validă"""
    if 'user_id' not in session:
        raise Exception('Sesiune expirată')
    return session['user_id']

@app.route('/')
@login_required
def index():
    try:
        db = SessionLocal()
        try:
            # Get user info
            user = db.query(User).get(session['user_id'])
            if not user:
                return redirect(url_for('logout'))
            
            # Calculăm data de început a săptămânii curente și trecute
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            start_of_last_week = start_of_week - timedelta(days=7)
            start_of_month = today.replace(day=1)
            
            # Activități pentru săptămâna curentă
            current_week_activities = db.query(Activity).filter(
                Activity.user_id == session['user_id'],
                Activity.date >= start_of_week,
                Activity.date <= today
            ).all()
            
            # Activități pentru săptămâna trecută
            last_week_activities = db.query(Activity).filter(
                Activity.user_id == session['user_id'],
                Activity.date >= start_of_last_week,
                Activity.date < start_of_week
            ).all()
            
            # Activități recente pentru tabel
            recent_activities = db.query(Activity).filter(
                Activity.user_id == session['user_id']
            ).order_by(Activity.date.desc()).limit(10).all()
            
            # Calculăm totalul orelor pentru săptămâna curentă și precedentă
            current_week_hours = sum(activity.hours for activity in current_week_activities)
            last_week_hours = sum(activity.hours for activity in last_week_activities)
            
            # Calculăm diferența procentuală
            if last_week_hours > 0:
                percentage_change = ((current_week_hours - last_week_hours) / last_week_hours) * 100
            else:
                percentage_change = 100 if current_week_hours > 0 else 0
            
            # Determinăm direcția schimbării (creștere sau scădere)
            trend_direction = 'up' if percentage_change >= 0 else 'down'
            
            # Calculăm zilele lucrate în săptămâna curentă
            working_days = len(set(activity.date for activity in current_week_activities))
            
            # Calculăm proiecte și clienți activi pentru luna curentă
            active_projects = db.query(Activity.project).filter(
                Activity.user_id == session['user_id'],
                Activity.date >= start_of_month
            ).distinct().count()
            
            active_clients = db.query(Activity.client).filter(
                Activity.user_id == session['user_id'],
                Activity.date >= start_of_month
            ).distinct().count()
            
            return render_template('index.html',
                                username=user.username,
                                current_week_activities=current_week_activities,
                                last_week_activities=last_week_activities,
                                current_week_hours=current_week_hours,
                                last_week_hours=last_week_hours,
                                percentage_change=abs(round(percentage_change, 1)),
                                trend_direction=trend_direction,
                                working_days=working_days,
                                active_projects=active_projects,
                                active_clients=active_clients,
                                recent_activities=recent_activities)
        except Exception as e:
            print(f"Eroare la încărcarea datelor: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
    except Exception as e:
        flash('A apărut o eroare la încărcarea datelor. Vă rugăm să încercați din nou.', 'error')
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.username == username).first()
                
                if user and check_password_hash(user.password, password):
                    session['user_id'] = user.id
                    return redirect(url_for('index'))
                else:
                    flash('Nume de utilizator sau parolă invalidă', 'error')
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        except Exception as e:
            print(f"Eroare la autentificare: {str(e)}")
            flash('A apărut o eroare la autentificare. Vă rugăm să încercați din nou.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = SessionLocal()
        if db.query(User).filter(User.username == username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        new_user = User(
            username=username,
            password=generate_password_hash(password)
        )
        db.add(new_user)
        db.commit()
        
        flash('Registration successful', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/add_activity', methods=['GET', 'POST'])
@login_required
def add_activity():
    if request.method == 'GET':
        try:
            db = SessionLocal()
            user = db.query(User).get(session['user_id'])
            return render_template('add_activity.html', 
                                current_user_id=session['user_id'],
                                current_username=user.username)
        except Exception as e:
            flash('Eroare la încărcarea paginii', 'error')
            return redirect(url_for('index'))
        finally:
            db.close()
    else:
        try:
            db = SessionLocal()
            try:
                user_id = session['user_id']
                data = request.form
                
                new_activity = Activity(
                    user_id=user_id,
                    date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
                    client=data['client'],
                    project=data['project'],
                    activity_type=data['activity_type'],
                    achievements=data['achievements'],
                    challenges=data['challenges'],
                    hours=float(data['hours'])
                )
                
                db.add(new_activity)
                db.commit()
                
                flash('Activitate adăugată cu succes!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        except Exception as e:
            print(f"Eroare la adăugarea activității: {str(e)}")
            flash('Eroare la adăugarea activității: ' + str(e), 'error')
            return redirect(url_for('add_activity'))

@app.route('/leaves')
@login_required
def leaves():
    try:
        db = SessionLocal()
        return render_template('leaves.html')
    except Exception as e:
        flash('Eroare la încărcarea paginii', 'error')
        return redirect(url_for('index'))
    finally:
        db.close()

@app.route('/api/leaves', methods=['GET'])
@login_required
def get_leaves():
    try:
        db = SessionLocal()
        user_id = session['user_id']
        leaves = db.query(Leave).filter(Leave.user_id == user_id).order_by(Leave.start_date.desc()).all()
        return jsonify([leave_to_dict(l) for l in leaves])
    except Exception as e:
        print(f"Error getting leaves: {str(e)}")
        return jsonify({'error': 'A apărut o eroare la încărcarea absențelor'}), 500
    finally:
        db.close()

@app.route('/api/leaves', methods=['POST'])
@login_required
def add_leave():
    try:
        db = SessionLocal()
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'Nu s-au primit date'}), 400

            user_id = session['user_id']
            
            # Validăm datele primite
            required_fields = ['start_date', 'end_date', 'leave_type']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Câmpul {field} este obligatoriu'}), 400
            
            # Convertim string-urile de dată în obiecte date
            try:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Format dată invalid'}), 400

            # Verificăm ca data de început să fie înainte de data de sfârșit
            if start_date > end_date:
                return jsonify({'error': 'Data de început trebuie să fie înainte de data de sfârșit'}), 400

            # Creăm noua absență
            new_leave = Leave(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                leave_type=data['leave_type'],
                description=data.get('description', '')  # câmp opțional
            )

            db.add(new_leave)
            db.commit()
            
            # Returnăm toate absențele actualizate
            leaves = db.query(Leave).filter(Leave.user_id == user_id).order_by(Leave.start_date.desc()).all()
            return jsonify([leave_to_dict(l) for l in leaves])
        
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    except Exception as e:
        print(f"Error adding leave: {str(e)}")
        return jsonify({'error': 'A apărut o eroare la salvarea absenței'}), 500

@app.route('/api/leaves/<int:leave_id>', methods=['DELETE'])
@login_required
def delete_leave(leave_id):
    try:
        db = SessionLocal()
        user_id = session['user_id']
        
        # Verificăm dacă absența există și aparține utilizatorului curent
        leave = db.query(Leave).filter(Leave.id == leave_id, Leave.user_id == user_id).first()
        if not leave:
            return jsonify({'error': 'Absența nu a fost găsită'}), 404
            
        db.delete(leave)
        db.commit()
        
        # Returnăm toate absențele actualizate
        leaves = db.query(Leave).filter(Leave.user_id == user_id).order_by(Leave.start_date.desc()).all()
        return jsonify([leave_to_dict(l) for l in leaves])
        
    except Exception as e:
        print(f"Error deleting leave: {str(e)}")
        return jsonify({'error': 'A apărut o eroare la ștergerea absenței'}), 500
    finally:
        db.close()

@app.route('/expenses')
@login_required
def expenses():
    try:
        db = SessionLocal()
        user_id = session['user_id']
        user_expenses = db.query(Expense).filter(Expense.user_id == user_id).all()
        return render_template('expenses.html', expenses=[expense_to_dict(e) for e in user_expenses])
    except Exception as e:
        flash('Eroare la încărcarea paginii', 'error')
        return redirect(url_for('index'))
    finally:
        db.close()

@app.route('/api/expenses/add', methods=['POST'])
@login_required
def add_expense():
    try:
        db = SessionLocal()
        user_id = session['user_id']
        data = request.form
        
        if not all([data.get('date'), data.get('project'), data.get('amount'),
                   data.get('description'), data.get('category')]):
            return jsonify({'success': False, 'error': 'Toate câmpurile sunt obligatorii'})
        
        new_expense = Expense(
            user_id=user_id,
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            project=data['project'],
            amount=float(data['amount']),
            description=data['description'],
            category=data['category']
        )
        
        db.add(new_expense)
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error adding expense: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        db.close()

@app.route('/api/expenses')
@login_required
def get_expenses():
    try:
        db = SessionLocal()
        user_id = session['user_id']
        expenses = db.query(Expense).filter(Expense.user_id == user_id).all()
        return jsonify([expense_to_dict(e) for e in expenses])
    except Exception as e:
        print(f"Error getting expenses: {str(e)}")
        return jsonify({'error': 'A apărut o eroare la încărcarea cheltuielilor'}), 500
    finally:
        db.close()

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    try:
        db = SessionLocal()
        try:
            expense = db.query(Expense).filter(
                Expense.id == expense_id,
                Expense.user_id == session['user_id']
            ).first()
            
            if not expense:
                return jsonify({'error': 'Cheltuiala nu a fost găsită'}), 404
            
            db.delete(expense)
            db.commit()
            
            return jsonify({'message': 'Cheltuiala a fost ștearsă cu succes'})
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export_data/<type>')
@login_required
def export_data(type):
    try:
        db = SessionLocal()
        user_id = session['user_id']
        
        # Get user info
        user = db.query(User).filter(User.id == user_id).first()
        user_name = user.username if user else "Necunoscut"
        
        if type == 'excel':
            # Get all activities for the current user
            activities = db.query(Activity).filter(Activity.user_id == user_id).all()
            data = []
            for activity in activities:
                data.append({
                    'Angajat': user_name,
                    'Data': activity.date,
                    'Client': activity.client,
                    'Proiect': activity.project,
                    'Tip Activitate': activity.activity_type,
                    'Ore': activity.hours,
                    'Realizări': activity.achievements,
                    'Provocări': activity.challenges
                })
            df = pd.DataFrame(data)
            
            # Create a BytesIO buffer for the Excel file
            buffer = BytesIO()
            df.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            
            return send_file(
                buffer,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'activitati_{user_name}_{datetime.now().strftime("%Y%m%d")}.xlsx'
            )
            
        elif type == 'csv':
            # Get all activities for the current user
            activities = db.query(Activity).filter(Activity.user_id == user_id).all()
            data = []
            for activity in activities:
                data.append({
                    'Angajat': user_name,
                    'Data': activity.date,
                    'Client': activity.client,
                    'Proiect': activity.project,
                    'Tip Activitate': activity.activity_type,
                    'Ore': activity.hours,
                    'Realizări': activity.achievements,
                    'Provocări': activity.challenges
                })
            df = pd.DataFrame(data)
            
            # Create a BytesIO buffer for the CSV file
            buffer = BytesIO()
            df.to_csv(buffer, index=False, encoding='utf-8')
            buffer.seek(0)
            
            return send_file(
                buffer,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'activitati_{user_name}_{datetime.now().strftime("%Y%m%d")}.csv'
            )
            
        else:
            return jsonify({'error': 'Format invalid'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/export_expenses/<type>')
@login_required
def export_expenses(type):
    try:
        db = SessionLocal()
        user_id = session['user_id']
        
        # Get user info
        user = db.query(User).filter(User.id == user_id).first()
        user_name = user.username if user else "Necunoscut"
        
        # Get all expenses for the current user
        expenses = db.query(Expense).filter(Expense.user_id == user_id).all()
        data = []
        for expense in expenses:
            data.append({
                'Angajat': user_name,
                'Data': expense.date,
                'Proiect': expense.project,
                'Categorie': expense.category,
                'Descriere': expense.description,
                'Sumă': expense.amount,
                'Status': expense.status
            })
        df = pd.DataFrame(data)
        
        buffer = BytesIO()
        
        if type == 'excel':
            df.to_excel(buffer, index=False, engine='openpyxl')
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            extension = 'xlsx'
        elif type == 'csv':
            df.to_csv(buffer, index=False, encoding='utf-8')
            mimetype = 'text/csv'
            extension = 'csv'
        else:
            return jsonify({'error': 'Format invalid'}), 400
            
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=f'cheltuieli_{user_name}_{datetime.now().strftime("%Y%m%d")}.{extension}'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/reports')
@login_required
def reports():
    try:
        db = SessionLocal()
        user_id = session['user_id']
        
        # Get unique clients and projects for dropdowns
        clients = db.query(Activity.client).filter(
            Activity.user_id == user_id,
            Activity.client != None,
            Activity.client != ''
        ).distinct().all()
        
        projects = db.query(Activity.project).filter(
            Activity.user_id == user_id,
            Activity.project != None,
            Activity.project != ''
        ).distinct().all()
        
        # Get current user info
        user = db.query(User).filter(User.id == user_id).first()
        employees = [{'user_id': user.id, 'username': user.username}]
        
        return render_template('reports.html',
                             employees=employees,
                             current_user_id=user_id,
                             clients=[c[0] for c in clients if c[0]],
                             projects=[p[0] for p in projects if p[0]])
    except Exception as e:
        flash('Eroare la încărcarea paginii', 'error')
        return redirect(url_for('index'))
    finally:
        db.close()

@app.route('/api/report/weekly', methods=['POST'])
@login_required
def generate_weekly_report():
    try:
        db = SessionLocal()
        user_id = check_session()
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = start_date + timedelta(days=6)
        
        activities = db.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.date >= start_date,
            Activity.date <= end_date
        ).order_by(Activity.date.desc()).all()
        
        if not activities:
            return jsonify({
                'total_hours': 0,
                'working_days': 0,
                'unique_projects': 0,
                'activities': [],
                'clients': {},
                'projects': {}
            })
        
        # Calculăm statisticile
        total_hours = sum(activity.hours for activity in activities)
        working_days = len(set(activity.date for activity in activities))
        unique_projects = len(set(activity.project for activity in activities))
        
        # Grupăm orele pe client și proiect
        clients = {}
        projects = {}
        for activity in activities:
            if activity.client:
                clients[activity.client] = clients.get(activity.client, 0) + activity.hours
            if activity.project:
                projects[activity.project] = projects.get(activity.project, 0) + activity.hours
        
        return jsonify({
            'total_hours': total_hours,
            'working_days': working_days,
            'unique_projects': unique_projects,
            'activities': [activity_to_dict(a) for a in activities],
            'clients': clients,
            'projects': projects
        })
    except Exception as e:
        print(f"Weekly report error: {str(e)}")
        return jsonify({'error': 'Eroare la generarea raportului săptămânal'}), 500
    finally:
        db.close()

@app.route('/api/report/monthly', methods=['POST'])
@login_required
def generate_monthly_report():
    try:
        db = SessionLocal()
        user_id = check_session()
        month_year = request.form['month']  # Format: "YYYY-MM"
        year, month = map(int, month_year.split('-'))
        
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        activities = db.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.date >= start_date,
            Activity.date <= end_date
        ).order_by(Activity.date.desc()).all()
        
        if not activities:
            return jsonify({
                'total_hours': 0,
                'working_days': 0,
                'unique_projects': 0,
                'activities': [],
                'clients': {},
                'projects': {}
            })
        
        # Calculăm statisticile
        total_hours = sum(activity.hours for activity in activities)
        working_days = len(set(activity.date for activity in activities))
        unique_projects = len(set(activity.project for activity in activities))
        
        # Grupăm orele pe client și proiect
        clients = {}
        projects = {}
        for activity in activities:
            if activity.client:
                clients[activity.client] = clients.get(activity.client, 0) + activity.hours
            if activity.project:
                projects[activity.project] = projects.get(activity.project, 0) + activity.hours
        
        return jsonify({
            'total_hours': total_hours,
            'working_days': working_days,
            'unique_projects': unique_projects,
            'activities': [activity_to_dict(a) for a in activities],
            'clients': clients,
            'projects': projects
        })
    except Exception as e:
        print(f"Monthly report error: {str(e)}")
        return jsonify({'error': 'Eroare la generarea raportului lunar'}), 500
    finally:
        db.close()

@app.route('/api/report/client', methods=['POST'])
@login_required
def generate_client_report():
    try:
        db = SessionLocal()
        user_id = check_session()
        client = request.form.get('client')
        if not client:
            return jsonify({'error': 'Clientul este obligatoriu'}), 400
        
        activities = db.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.client == client
        ).order_by(Activity.date.desc()).all()
        
        if not activities:
            return jsonify({
                'total_hours': 0,
                'working_days': 0,
                'unique_projects': 0,
                'activities': [],
                'clients': {client: 0},
                'projects': {}
            })
        
        # Calculăm statisticile
        total_hours = sum(activity.hours for activity in activities)
        working_days = len(set(activity.date for activity in activities))
        unique_projects = len(set(activity.project for activity in activities))
        
        # Grupăm orele pe proiect
        projects = {}
        for activity in activities:
            if activity.project:
                projects[activity.project] = projects.get(activity.project, 0) + activity.hours
        
        return jsonify({
            'total_hours': total_hours,
            'working_days': working_days,
            'unique_projects': unique_projects,
            'activities': [activity_to_dict(a) for a in activities],
            'clients': {client: total_hours},
            'projects': projects
        })
    except Exception as e:
        print(f"Client report error: {str(e)}")
        return jsonify({'error': 'Eroare la generarea raportului pe client'}), 500
    finally:
        db.close()

@app.route('/api/report/project', methods=['POST'])
@login_required
def generate_project_report():
    try:
        db = SessionLocal()
        user_id = check_session()
        project = request.form.get('project')
        if not project:
            return jsonify({'error': 'Proiectul este obligatoriu'}), 400
        
        activities = db.query(Activity).filter(
            Activity.user_id == user_id,
            Activity.project == project
        ).order_by(Activity.date.desc()).all()
        
        if not activities:
            return jsonify({
                'total_hours': 0,
                'working_days': 0,
                'unique_projects': 1,
                'activities': [],
                'clients': {},
                'projects': {project: 0}
            })
        
        # Calculăm statisticile
        total_hours = sum(activity.hours for activity in activities)
        working_days = len(set(activity.date for activity in activities))
        
        # Grupăm orele pe client
        clients = {}
        for activity in activities:
            if activity.client:
                clients[activity.client] = clients.get(activity.client, 0) + activity.hours
        
        return jsonify({
            'total_hours': total_hours,
            'working_days': working_days,
            'unique_projects': 1,
            'activities': [activity_to_dict(a) for a in activities],
            'clients': clients,
            'projects': {project: total_hours}
        })
    except Exception as e:
        print(f"Project report error: {str(e)}")
        return jsonify({'error': 'Eroare la generarea raportului pe proiect'}), 500
    finally:
        db.close()

@app.route('/api/activity/<int:activity_id>', methods=['GET'])
@login_required
def get_activity(activity_id):
    try:
        db = SessionLocal()
        try:
            activity = db.query(Activity).filter(
                Activity.id == activity_id,
                Activity.user_id == session['user_id']
            ).first()
            
            if not activity:
                return jsonify({'error': 'Activitatea nu a fost găsită'}), 404
                
            return jsonify({
                'id': activity.id,
                'date': activity.date.strftime('%Y-%m-%d'),
                'client': activity.client,
                'project': activity.project,
                'activity_type': activity.activity_type,
                'hours': activity.hours,
                'achievements': activity.achievements,
                'challenges': activity.challenges
            })
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/activity/<int:activity_id>', methods=['DELETE'])
@login_required
def delete_activity(activity_id):
    try:
        db = SessionLocal()
        try:
            activity = db.query(Activity).filter(
                Activity.id == activity_id,
                Activity.user_id == session['user_id']
            ).first()
            
            if not activity:
                return jsonify({'error': 'Activitatea nu a fost găsită'}), 404
            
            db.delete(activity)
            db.commit()
            
            return jsonify({'message': 'Activitatea a fost ștearsă cu succes'})
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/profile')
@login_required
def profile():
    try:
        db = SessionLocal()
        user = db.query(User).get(session['user_id'])
        if user is None:
            flash('Utilizator negăsit.', 'error')
            return redirect(url_for('logout'))
        return render_template('profile.html', current_user=user)
    except Exception as e:
        print(f"Eroare la încărcarea profilului: {str(e)}")
        flash('A apărut o eroare la încărcarea profilului.', 'error')
        return redirect(url_for('index'))
    finally:
        db.close()

@app.route('/update_password', methods=['POST'])
@login_required
def update_password():
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            flash('Toate câmpurile sunt obligatorii.', 'error')
            return redirect(url_for('profile'))
            
        if new_password != confirm_password:
            flash('Parolele noi nu se potrivesc.', 'error')
            return redirect(url_for('profile'))
            
        db = SessionLocal()
        try:
            user = db.query(User).get(session['user_id'])
            if not user:
                flash('Utilizator negăsit.', 'error')
                return redirect(url_for('logout'))
                
            if not check_password_hash(user.password, current_password):
                flash('Parola curentă este incorectă.', 'error')
                return redirect(url_for('profile'))
                
            user.password = generate_password_hash(new_password)
            db.commit()
            flash('Parola a fost actualizată cu succes!', 'success')
            return redirect(url_for('profile'))
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"Eroare la actualizarea parolei: {str(e)}")
        flash('A apărut o eroare la actualizarea parolei.', 'error')
        return redirect(url_for('profile'))

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    try:
        db = SessionLocal()
        try:
            user = db.query(User).get(session['user_id'])
            if user:
                db.delete(user)
                db.commit()
                session.clear()
                flash('Contul tău a fost șters cu succes.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Utilizator negăsit.', 'error')
                return redirect(url_for('profile'))
        finally:
            db.close()
    except Exception as e:
        print(f"Eroare la ștergerea contului: {str(e)}")
        flash('A apărut o eroare la ștergerea contului.', 'error')
        return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True)