import os
import psycopg2
import psycopg2.extras
import redis
import uuid
import functools
from psycopg2 import pool
from flask import Flask
from flask import g
from flask import request
from flask import render_template
from flask import json
from flask import make_response
from flask import redirect
from markupsafe import escape

app = Flask(__name__)
#create connection pool to DB and keep in it app config
app.config['postgreSQL_pool'] = psycopg2.pool.SimpleConnectionPool(4, 20,
                                host=os.environ['POSTGRES_HOST'],
                                port=os.environ['POSTGRES_PORT'],
                                database=os.environ['POSTGRES_DB'],
                                user=os.environ['POSTGRES_USER'],
                                password=os.environ['POSTGRES_PASSWORD'])
app.config['redis_pool'] = redis.ConnectionPool(host=os.environ['REDIS_HOST'], port=os.environ['REDIS_PORT'], db=os.environ['REDIS_DB'])

def get_db_connection():
    '''
    Get DB connection from pool and put it to g
    '''
    if 'db' not in g:
        g.db = app.config['postgreSQL_pool'].getconn()
    return g.db

@app.teardown_appcontext
def close_conn(e):
    '''
    Return DB connection to pool before exit from app context
    '''
    db = g.pop('db', None)
    if db is not None:
        app.config['postgreSQL_pool'].putconn(db)

def login_required(view):
    '''
    Check if user session exists in Redis
    '''
    @functools.wraps(view) #keeps wrapped function metadata
    def wrapped_view(**kwargs):
        login_ok = True
        r = redis.Redis(connection_pool=app.config['redis_pool'])
        session_id = request.cookies.get('SessionId')
        if not session_id:
            login_ok = False
        else:
            user_id = r.hget('session:'+session_id, 'user_id')
            if user_id:
                result = handle_session(action='start', session_id=session_id, user_id=user_id) 
            else:
                login_ok = False

        #if session exists - return view
        if login_ok:
            resp = view(**kwargs)
        #if session does not exist - return redirect for GET and "success False" for POST
        else:
            if request.method == 'GET':
                resp = make_response(redirect('/static/login.html'))
            elif request.method == 'POST':
                resp = make_response(json.dumps({'success': False, 'error_code': 2}))
        return resp

    return wrapped_view

@app.route('/search', methods=['POST'])
@login_required
def search():
    '''
    Search users request in DB, returns result in json format
    '''
    sreq = escape(request.json['sreq'])

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT ts_rank(v.value, plainto_tsquery(%s)),
                          c.support_ticket_number,
                          pn.value product_name,
                          c.subject
                   FROM cases c
                   LEFT JOIN cases_tsvector_sum v ON c.id = v.id
                   LEFT JOIN cases_product_name pn ON pn.id = c.product_name
                   WHERE v.value @@ plainto_tsquery(%s)
                   ORDER BY  ts_rank(v.value, plainto_tsquery(%s)) DESC;''',
                [sreq, sreq, sreq])
    db_res = cur.fetchall()
    cur.close()

    if db_res != []:
        return json.dumps({'success': True, 'result': db_res})
    else:
        return json.dumps({'success': False, 'error_code': 1})


@app.route('/case', methods=['GET'])
@app.route('/case/', methods=['GET'])
@app.route('/case/<sf_ticket_number>', methods=['GET'])
@login_required
def return_case_info(sf_ticket_number=None):
    '''
    Returns all case data. Case is identified by number
    '''
    sf_ticket_number = escape(sf_ticket_number)

    #Check if case number is correct
    if sf_ticket_number.isnumeric():
        sf_ticket_number = int(sf_ticket_number)
    else:
        return render_template('incorrect_result.html.jinja', db_res={'success': False, 'result': 'Incorrect case number :-('})

    #Search for case number
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute('''SELECT c.id,
                          c.support_ticket_number,
                          s.value severity,
                          ao.value assessed_outage,
                          ss.value status,
                          an.value account_name,
                          oc.value operational_customer_name,
                          pn.value product_name,
                          pr.value product_release,
                          c.subject,
                          c.description,
                          c.technical_analysis,
                          c.temporary_solution,
                          c.solution_details,
                          st.value support_ticket_owner,
                          cn.value contact_name,
                          cw.value current_workgroup,
                          c.legacy_case_number,
                          c.problem,
                          c.recovery_actions,
                          c.summary_of_analysis,
                          c.root_cause_description,
                          c.r_d_reference,
                          c.target_release
                   FROM cases c
                   LEFT JOIN cases_severity s ON c.severity = s.id
                   LEFT JOIN cases_assessed_outage ao ON c.assessed_outage = ao.id
                   LEFT JOIN cases_status ss ON c.status = ss.id
                   LEFT JOIN cases_account_name an ON c.account_name = an.id
                   LEFT JOIN cases_operational_customer_name oc ON c.operational_customer_name = oc.id
                   LEFT JOIN cases_product_name pn ON c.product_name = pn.id
                   LEFT JOIN cases_product_release pr ON c.product_release = pr.id
                   LEFT JOIN cases_support_ticket_owner st ON c.support_ticket_owner = st.id
                   LEFT JOIN cases_contact_name cn ON c.contact_name = cn.id
                   LEFT JOIN cases_current_workgroup cw ON c.current_workgroup = cw.id
                   WHERE c.support_ticket_number = %s;''',
                [sf_ticket_number])
    db_res = cur.fetchall()
    cur.close()

    #return result. if there is no result - return error
    if db_res == []:
        return_template = 'incorrect_result.html.jinja'
        db_res = {'success': False, 'result': 'Incorrect case number :-('}
    else:
        return_template = 'case_data.html.jinja'
    return render_template(return_template, db_res=db_res)


@app.route('/login', methods = ['POST'])
def login():
    '''
    Perform login to system
    '''
    #search for user data
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute('''SELECT id FROM cases_engineers WHERE
                          login = %s and
                          password= %s;''',
                   [escape(request.form['login']), escape(request.form['password'])])
    db_res = cur.fetchall()
    cur.close()
    #if user found - start session, set cookie, return redirect to index
    if db_res:
       session = handle_session(action='start', user_id=db_res[0]['id'])
       if session['success'] == True:
           resp = make_response(redirect('/static/index.html'))
           resp.set_cookie('SessionId', session['session_id'])
    #if no user found - return error
    else:
       resp = make_response(render_template('login_incorrect.html.jinja'))

    return resp

@app.route('/exit', methods=['POST'])
def exit():
    '''
    Logout from system
    '''
    session_id = request.cookies.get('SessionId')
    #if no session_id in request - no need to delete session
    if not session_id:
        pass
    #delete session if session_id in request
    else:
        session = handle_session(action='stop', session_id=session_id, user_id=None)
    
    #delete cookie, return redirect to login
    resp = make_response(redirect('/static/login.html'))
    resp.set_cookie('SessionId', '')

    return resp

@app.route('/check_session', methods=['POST'])
@login_required
def check_session():
    '''
    Check session after direct access to index page.
    Function returns "success True", actual checking performed by decorator login_required
    '''
    resp = make_response(json.dumps({'success': True}))
    return resp

def handle_session(action, session_id=None, user_id=None):
    '''
    Starts and stops user session
    '''
    r = redis.Redis(connection_pool=app.config['redis_pool'])
    #start session
    if action == 'start':
        #generate session_id
        if not session_id:
            session_id = uuid.uuid4().hex
        #write session_id to redis and set expire via pipe
        pipe = r.pipeline()
        pipe.hset('session:'+session_id, 'user_id', user_id)
        pipe.expire('session:'+session_id, 900)
        pipe.execute()
        result = {'success': True, 'session_id': session_id}

    #stop session - delete key from redis
    elif action == 'stop':
        r.delete('session:'+session_id)
        result = {'success': True}

    else:
        result = {'success': False}

    return result
