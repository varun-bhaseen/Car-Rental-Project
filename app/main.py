import sqlite3
import time
import datetime
import random
import operator

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from collections import Counter
from math import sqrt, pow
# from flask.ext.login  import LoginManager


# Configuration
DATABASE = 'database/newdb.db'
DEBUG = True
SECRET_KEY = 'Development key'
USERNAME = 'admin'
PASSWORD = 'admin'


# create application
app = Flask(__name__)
app.config.from_object(__name__)


# Home Page
@app.route('/')
def index():
    session.pop('dealer_id', None)
    session.pop('user_id', None)
    session.pop('dealer_logged_in', None)
    session.pop('user_logged_in', None)
    session.pop('admin_logged_in', None)
    return render_template('home.html')

# Navigate to user signup or dealer Signup
@app.route('/signup')
def signup():
    return render_template('signup.html')

# display user sign up form
@app.route('/signup_user')
def signup_user():
    return render_template('signup_user.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/search_results', methods=['POST'])
def search_results():

    searchterm = request.form['search_term']
    searchstring = '%' + searchterm + '%'
    # vehicles available to be reservationed
    query = ''' 
            select ar.brand_name, d.vehicle_name, i.vehicle_id, i.vehicle_copy, i.dealer_id
            from inventory as i
            inner join vehicle as d
                on i.vehicle_id = d.vehicle_id
            inner join brand_makes as au 
                on i.vehicle_id = au.vehicle_id
            inner join brand as ar 
                on au.brand_id = ar.brand_id
            left join vehicle_keyword as k
                on i.vehicle_id = k.vehicle_id  
            where ( d.vehicle_name like (?) or k.keyword like (?) or ar.brand_name like (?))
            group by i.vehicle_id
            '''

    cur = g.db.execute(query, [searchstring, searchstring, searchstring])
    rows = [dict(brand_name=row[0], vehicle_name=row[1],
                 vehicle_id=row[2], keyword=row[3]) for row in cur.fetchall()]

    print(rows)

    return render_template('search_results.html', searchterm=searchterm, rows=rows)


@app.route('/add_user', methods=['POST'])
def add_user():
    if request.method == 'POST':
        try:
            g.db.execute('insert into user (user_id,user_name,password,driver_licence,is_member) values (?, ?, ?, ?,?)',
                         [request.form['user_id'], request.form['user_name'], request.form['password'], request.form['driver_license'],0])
            g.db.commit()

            g.db.execute('insert into membership (user_id, dealer_id) values (?, ?)',
                         [request.form['user_id'], 'dealer1'])
            g.db.commit()
    
            return redirect(url_for('login', username=request.form['user_id'], type="user"))
        except sqlite3.Error as e:
            print(e)
            flash("Please try again", 'danger')
            return redirect(url_for('signup_user'))
            print("could not commit to db")
    return redirect(url_for('signup_user'))


@app.route('/keywords')
@app.route('/keywords/<vehicle_id>/')
def keywords(vehicle_id=None):

    query = ''' select vehicle_name, vehicle_id from vehicle '''
    cur = g.db.execute(query)
    options = [dict(vehicle_id=row[1], vehicle_name=row[0])
               for row in cur.fetchall()]

    if vehicle_id == None:
        query = ''' 
                select dk.vehicle_id, dk.keyword, d.vehicle_name 
                from vehicle_keyword as dk 
                inner join vehicle as d
                    on dk.vehicle_id = d.vehicle_id
                order by d.vehicle_name 
                '''
        cur = g.db.execute(query)
        rows = [dict(vehicle_id=row[0], keyword=row[1], vehicle_name=row[2])
                for row in cur.fetchall()]
    else:
        query = ''' 
                select dk.vehicle_id, dk.keyword, d.vehicle_name 
                from vehicle_keyword as dk 
                inner join vehicle as d
                    on dk.vehicle_id = d.vehicle_id
                where d.vehicle_id = (?)
                order by d.vehicle_name 
                '''
        cur = g.db.execute(query, [vehicle_id])
        rows = [dict(vehicle_id=row[0], keyword=row[1], vehicle_name=row[2])
                for row in cur.fetchall()]

    return render_template('keywords.html', options=options, rows=rows)


@app.route('/add_keyword', methods=['post'])
def add_keyword():

    query = ''' insert into vehicle_keyword values (?, ?) '''
    cur = g.db.execute(
        query, [request.form['vehicle'], request.form['keyword']])
    g.db.commit()
    return redirect( url_for('keywords', vehicle_id=request.form['vehicle']) )

@app.route('/reservation_cancel/<reservation_id>')
def reservation_cancel(reservation_id=None):
    if reservation_id:
        get_reservation_date = g.db.execute('select reservation_date from reservation where reservation_id = (?)', [reservation_id])
        reservation_date = get_reservation_date.fetchone()[0]
        print('here')
        min_before_reservation = get_minutes_before_reservation(str(datetime.datetime.now()),(str(reservation_date)))
        late_cancel_fee = 0
        if min_before_reservation > 0 and min_before_reservation < 60:
            # get rental fee
            print('check')
            get_flat_fee = g.db.execute('select flat_rate from misc_info')
            late_cancel_fee = get_flat_fee.fetchone()[0]
            flash("Late cancellation. We charged you for 1 hr ($" + str(late_cancel_fee) + ")","success")
        else:
            print('hell')
            flash("Successful Cancellation!","success")
            
        
            print('hereeeee')
            g.db.execute('delete from reservation where reservation_id = (?)', [ reservation_id])
            g.db.commit()
            g.db.execute('update history set  late_cancel_fee = (?) where reservation_id = (?)', [late_cancel_fee, reservation_id])
            g.db.commit()
            return redirect( url_for('user_home') )


    return redirect( url_for('user_home') )

@app.route('/user_home')
@app.route('/user_home/<user_home>/')
def user_home(user_home = None):
    todays_date_long = datetime.datetime.now()
    
    # show a list of all books the user has checked out
    query = ''' select b.dealer_id, b.vehicle_id, b.vehicle_copy, b.reservation_date, b.exp_return, d.vehicle_name, b.reservation_id 
                from reservation as b
                inner join vehicle as d
                   on b.vehicle_id = d.vehicle_id
                where b.user_id = (?)
                  and not exists( select * 
                                  from return as r
                                    where r.return_id = b.reservation_id )
            '''

    cur = g.db.execute(query, [session['user_id']])
    # cur = g.db.execute('select dealer_id, vehicle_id, vehicle_copy, reservation_date, exp_return from reservation where user_id = (?)', [session['user_id']] )
    rows = [dict(dealer_id=row[0], vehicle_id=row[1], vehicle_copy=row[2], reservation_date=row[3], exp_return=row[4],
                 vehicle_name=row[5], reservation_id=row[6], exp_return_frmt=format_date(row[4])) for row in cur.fetchall()]

    for row in rows:

        if todate(row['exp_return']) < todate(str(todays_date_long)):
            row['vehicle_status'] = 'Overdue'
        else:
            row['vehicle_status'] = 'Good'

    # show a list of all cars the user has returned
    returnquery = ''' select r.dealer_id, r.vehicle_id, r.late_fee, r.actual_return, d.vehicle_name, r.return_id 
                from return as r
                inner join vehicle as d
                    on r.vehicle_id = d.vehicle_id
                where r.user_id = (?) 
            '''

    returncur = g.db.execute(returnquery, [session['user_id']])
    returnrows = [dict(dealer_id=row[0], vehicle_id=row[1], late_fee=row[2], actual_return=row[3], vehicle_name=row[4],
                       return_id=row[5], actual_return_frmt=format_date(row[3])) for row in returncur.fetchall()]

    # show a list of all cars the user is ordered
    orderquery = ''' select d.vehicle_name, l.vehicle_id, l.vehicle_copy, l.order_date, l.delivery_date, l.status
                    from lend as l 
                    inner join vehicle as d
                        on l.vehicle_id = d.vehicle_id
                    where l.for_user = (?)
                      and l.status = "processing"
                 '''

    ordercur = g.db.execute(orderquery, [session['user_id']])
    orderrows = [dict(vehicle_name=row[0], vehicle_id=row[1], vehicle_copy=row[2],
                      wait_date=row[3], delivery_date=row[4], status=row[5]) for row in ordercur.fetchall()]

    # Select all vehicles a user is wait for
    waitquery = '''
                    select w.vehicle_id, w.wait_date, d.vehicle_name 
                    from wait as w 
                    inner join vehicle as d 
                        on w.vehicle_id = d.vehicle_id
                    where user_id = (?)
                '''

    waitcur = g.db.execute(waitquery, [session['user_id']])
    waitrows = [dict(vehicle_id=row[0], wait_date=row[1],
                     vehicle_name=row[2]) for row in waitcur.fetchall()]

    # Search for dealerraries that may not have this vehicle in stock
    # If the users dealer has this vehicle in stock put an entry in the reservation relation
    for wait_vehicle in waitrows:
        print(wait_vehicle)
        query = '''
                    select d.vehicle_id, max( i.vehicle_copy ), i.dealer_id
                    from inventory as i
                    inner join vehicle as d 
                        on i.vehicle_id = d.vehicle_id
                    where i.curr_location = (?)
                        and i.vehicle_id = (?)
                    and not exists
                    (
                        select *
                        from reservation as b
                        where b.vehicle_id   = i.vehicle_id
                            and b.vehicle_copy = i.vehicle_copy
                    )and not exists
                    (
                        select *
                        from return as r
                        where r.vehicle_id   = i.vehicle_id
                            and r.vehicle_copy = i.vehicle_copy 
                            and r.actual_return = (?)
                    )
                    and not exists
                    (
                        select *
                        from lend as l
                        where l.vehicle_id = i.vehicle_id
                            and l.vehicle_copy = i.vehicle_copy
                            and l.status = 'processing'
                    )
                '''
        cur = g.db.execute(
            query, [session['dealer_id'], wait_vehicle['vehicle_id'], todays_date_long])
        availrows = [dict(vehicle_id=row[0], vehicle_copy=row[1])
                     for row in cur.fetchall()]

        # If available rows is <> to empty that means the users current dealer has the vehicle available
        print(availrows)
        if availrows[0]['vehicle_id'] is not None and availrows[0]['vehicle_copy'] is not None:
            print('reservation wait vehicle')
            reservation_vehicle(
                session['dealer_id'], availrows[0]['vehicle_id'], availrows[0]['vehicle_copy'])
            cur = g.db.execute('update inventory set curr_location = (?) where vehicle_id = (?) and vehicle_copy = (?)', [
                               session['dealer_id'], availrows[0]['vehicle_id'], availrows[0]['vehicle_copy']])
            g.db.commit()
            cur = g.db.execute('delete from wait where vehicle_id = (?) and user_id = (?)', [
                               availrows[0]['vehicle_id'], session['user_id']])
            g.db.commit()

    # If the vehicle is available at another dealer put an entry in the lend relation
    for wait_vehicle in waitrows:
        print(wait_vehicle)
        query = '''
                    select d.vehicle_id, max( i.vehicle_copy ), i.dealer_id
                    from inventory as i
                    inner join vehicle as d 
                        on i.vehicle_id = d.vehicle_id
                    where i.curr_location <> (?)
                        and i.vehicle_id = (?)
                    and not exists
                    (
                        select *
                        from reservation as b
                        where b.vehicle_id   = i.vehicle_id
                            and b.vehicle_copy = i.vehicle_copy
                    )and not exists
                    (
                        select *
                        from return as r
                        where r.vehicle_id   = i.vehicle_id
                            and r.vehicle_copy = i.vehicle_copy 
                            and r.actual_return = (?)
                    )
                    and not exists
                    (
                        select *
                        from lend as l
                        where l.vehicle_id = i.vehicle_id
                            and l.vehicle_copy = i.vehicle_copy
                            and l.status = 'processing'
                    )
                '''
        cur = g.db.execute(
            query, [session['dealer_id'], wait_vehicle['vehicle_id'], todays_date_long])
        vehicleOtherdealer = [
            dict(vehicle_id=row[0], vehicle_copy=row[1]) for row in cur.fetchall()]

        # If available rows is <> to empty that means the users current dealer has the vehicle available
        print(vehicleOtherdealer)
        if vehicleOtherdealer[0]['vehicle_id'] is not None and vehicleOtherdealer[0]['vehicle_copy'] is not None:
            print('Order wait vehicle')
            order(vehicleOtherdealer[0]['vehicle_id'])
            cur = g.db.execute('delete from wait where vehicle_id = (?) and user_id = (?)', [
                               vehicleOtherdealer[0]['vehicle_id'], session['user_id']])
            g.db.commit()

    return render_template('user_home.html', rows=rows, returnrows=returnrows, orderrows=orderrows, waitrows=waitrows)


@app.route('/vehicle_return/<reservation_id>')
def vehicle_return(reservation_id=None):
    if reservation_id:
        query = ''' select d.vehicle_name, b.dealer_id, b.vehicle_id, b.vehicle_copy, b.reservation_id, b.exp_return, b.reservation_date
            from reservation as b
            inner join vehicle as d 
            on b.vehicle_id = d.vehicle_id 
            where b.reservation_id = (?) 
            '''
        cur = g.db.execute(query, [reservation_id])
        rows = [dict(vehicle_name=row[0], dealer_id=row[1], vehicle_id=row[2], vehicle_copy=row[3],
                     reservation_id=row[4], exp_return=row[5], reservation_date=row[6]) for row in cur.fetchall()]
        query = ''' select dealer_id from dealer'''
        cur = g.db.execute(query)
        options = [dict(dealer_id=row[0]) for row in cur.fetchall()]

        query = ''' select late_fee_base from misc_info'''
        cur = g.db.execute(query)
        late_fee_base = [dict(late_fee_base=row[0]) for row in cur.fetchall()]

        get_late_fee = g.db.execute('select late_fee_base from misc_info')
        late_fee_base = get_late_fee.fetchone()[0]
        
        # get rental fee
        get_flat_fee = g.db.execute('select flat_rate from misc_info')
        flat_fee = get_flat_fee.fetchone()[0]
        rental_fee = get_rental_fee(str(rows[0]['reservation_date']), str(datetime.datetime.now()), flat_fee)
        if rental_fee <= 0:
            flash('You cannot return this car. You have not picked it up yet. ','error')
            return redirect( url_for('user_home') )

        # late fee calculation
        late_hrs = 0
        late_hrs = int(late_hours(
            str(rows[0]['exp_return']), str(datetime.datetime.now())))
        late_fee = 0
        if late_hrs > 0:
            late_fee = late_feee_calc(late_hrs, late_fee_base)
    else:
        pass

    return render_template('return.html', context=rows, options=options, late_fee=late_fee, rental_fee=rental_fee)


@app.route('/member')
def member():
    get_member_fee = g.db.execute('select membership_fee from misc_info')
    member_fee = get_member_fee.fetchone()[0]
    
    return render_template('member.html', member_fee = member_fee)

@app.route('/pay_member', methods=['POST'])
def pay_member():
    credit_card = request.form['credit_card']
    print('credot card = ', credit_card)
    g.db.execute('update user set is_member = 1, credit_card = (?) where user_id = (?)', [credit_card, session['user_id']])
    g.db.commit()
    name = session['user_id']
    price = g.db.execute(
        'select membership_fee from misc_info').fetchone()[0]
    flash(
        f"Please note, {name}! You are now a 6-month member. You have been charged {price}!", "info")
    return redirect( url_for('inventory') )

@app.route('/dreturn', methods=['POST'])
def dreturn():
    todays_date = datetime.datetime.now()
    rental_fee = request.form['rental_fee']
    try:
        late_fee = request.form['late_fee']
    except:
        late_fee = 0
    
    g.db.execute('insert into return (return_id, user_id, dealer_id, vehicle_id, vehicle_copy, actual_return, late_fee, return_condition, return_comments, paid_fee) values (?, ?, ?, ?, ?, ?,?,?,?,?)', 
                    [ request.form['reservation_id'], session['user_id'], request.form['return_to'], request.form['vehicle_id'], request.form['vehicle_copy'], todays_date, late_fee, request.form['return_condition'], request.form['return_comments'], rental_fee])
    g.db.commit()

    g.db.execute('delete from reservation where reservation_id = (?)', [
                 request.form['reservation_id']])
    g.db.commit()

    g.db.execute('update history set returned_to = (?), return_date = (?) where reservation_id = (?)', [
                 request.form['return_to'], todays_date, request.form['reservation_id']])
    g.db.commit()

    g.db.execute('update inventory set curr_location = (?) where vehicle_id = (?) and vehicle_copy = (?)', [
                 request.form['return_to'], request.form['vehicle_id'], request.form['vehicle_copy']])
    g.db.commit()

    return redirect(url_for('user_home'))

# display dealer sign up form
@app.route('/signup_dealer')
def signup_dealer():
    return render_template('signup_dealer.html')


@app.route('/add_dealer', methods=['POST'])
def add_dealer():

    if request.method == 'POST':
        try:

            g.db.execute('insert into dealer (dealer_id, dealer_name, zip_code, password) values (?, ?, ?, ?)',
                         [request.form['dealer_id'], request.form['dealer_name'], request.form['dealer_zip_code'], request.form['password']])
            g.db.execute('insert into location(state,city,zip_code) values (?,?,?)',[request.form['dealer_state'],request.form['dealer_city'],request.form['dealer_zip_code']])
            g.db.commit()
            name = request.form['dealer_name']
            flash(f"Hi {name}! Successfully signed up!", "success")

            return redirect(url_for('login', username=request.form['dealer_id'], type="dealer"))
        except sqlite3.Error as e:
            print(e)
            flash("Please try again", 'danger')
            print("could not commit to db")
    else:
        pass
    flash("Please try again", 'danger')
    return redirect(url_for('signup_dealer'))


@app.route('/add_to_inventory/<vehicle_id>/')
def add_to_inventory(vehicle_id=None):

    get_vehicle_copy = g.db.execute(
        'select max(vehicle_copy) from inventory where vehicle_id = (?)', [vehicle_id])
    vehicle_copy = get_vehicle_copy.fetchone()[0]
    print(vehicle_copy)

    get_max_copies = g.db.execute(
        'select number_copies from vehicle where vehicle_id = (?)', [vehicle_id])
    max_copy = get_max_copies.fetchone()[0]
    print(max_copy)

    if vehicle_copy == None:
        vehicle_copy = 0

    # Needs to be tested and fixed
    if int(max_copy) == int(vehicle_copy):
        flash('No more copies available', 'danger')
        return redirect(url_for('vehicle'))
    else:
        insert_as_copy = vehicle_copy + 1
        g.db.execute('insert into inventory (dealer_id, vehicle_id, vehicle_copy, curr_location) values (?, ?, ?, ? )',
                     [session['dealer_id'], vehicle_id, insert_as_copy, session['dealer_id']])
        g.db.commit()
        flash('vehicle added to inventory!', 'success')
        return redirect(url_for('vehicle'))


# display login form
@app.route('/login/')
@app.route('/login/<username>/')
@app.route('/login/<username>/<type>/')
def login(username=None, type=None):

    signout()

    context = {
        "username": username,
        "type": type
    }

    return render_template('login.html', context=context)


@app.route('/user_login', methods=['POST'])
def user_login():

    if request.method == 'POST':
        entries = ''

        if request.form['radios'] == 'user':
            try:
                cur = g.db.execute('select user_id, password from user where user_id = (?) and password = (?)',
                                   [request.form['username'], request.form['password']])
                # print([ request.form['username'], request.form['password']  ])
                entries = [dict(username=row[0], password=row[1])
                           for row in cur.fetchall()]
                if not entries:
                    flash('Please check the username and password', 'danger')
                    return redirect(url_for('login'))
                session['user_logged_in'] = True
                session['user_id'] = request.form['username']

                # Get users preferred dealer
                cur = g.db.execute('select dealer_id from membership where user_id = (?)',
                                   [request.form['username']])
                entries = [dict(dealer_id=row[0]) for row in cur.fetchall()]
                session['dealer_id'] = entries[0]['dealer_id']

                return redirect(url_for('user_home'))
            except sqlite3.Error as er:
                print(er)
                print("could not find user in DB")
        elif request.form['radios'] == 'dealer':
            try:
                cur = g.db.execute('select dealer_id, password from dealer where dealer_id = (?) and password = (?)',
                                   [request.form['username'], request.form['password']])
                entries = [dict(username=row[0], password=row[1])
                           for row in cur.fetchall()]
                if not entries:
                    flash('Please check the username and password', 'danger')
                    return redirect(url_for('login'))
                session['dealer_logged_in'] = True
                session['dealer_id'] = request.form['username']
                return redirect(url_for('dealer_home'))
            except:
                print("could not find dealer in DB")
        elif request.form['radios'] == 'admin':
            if [request.form['username'], request.form['password']] == ['admin', 'admin']:
                session['admin_logged_in'] = True
                session['admin_id'] = request.form['username']
                return redirect(url_for('admin_home'))
            else:
                flash('Wrong input', 'danger')
                return redirect('login')

        else:
            print("Request is not valid")

        print('User: ')
        print(entries)

        if entries:
            print("Login as :" + request.form['radios'])
        else:
            print("Invalid login")

    else:
        pass

    return redirect(url_for('login'))


@app.route('/admin_home')
def admin_home():
    return render_template('admin_home.html')

# @app.route('/admin_home')
@app.route('/dealer_home')
def dealer_home():
    # show a list of all books in inventory of this dealer and their status, location etc..
    query = ''' select i.dealer_id, i.vehicle_id, i.vehicle_copy, i.curr_location,  d.vehicle_name
                from inventory as i
                inner join vehicle as d 
                    on d.vehicle_id = i.vehicle_id
                where curr_location = (?)
                  and not exists(
                      select *
                      from reservation as b
                      where b.vehicle_id   = i.vehicle_id
                        and b.vehicle_copy = i.vehicle_copy  
                  );
            '''
    cur = g.db.execute(query, [session['dealer_id']])
    rows = [dict(dealer_id=row[0], vehicle_id=row[1], vehicle_copy=row[2],
                 curr_location=row[3], vehicle_name=row[4]) for row in cur.fetchall()]
    # vehicles at other dealerraries
    query = ''' select * 
                from inventory as i
                where dealer_id = (?) and curr_location != (?)
                  and not exists (
                      select * from reservation as b where b.vehicle_id = i.vehicle_id and b.vehicle_copy = i.vehicle_copy
                  )
            '''
    acur = g.db.execute(query, [session['dealer_id'], session['dealer_id']])
    arows = [dict(dealer_id=row[0], vehicle_id=row[1], vehicle_copy=row[2],
                  curr_location=row[3]) for row in acur.fetchall()]
    # vehicles being reservationed
    bcur = g.db.execute(
        'select * from reservation where dealer_id = (?)', [session['dealer_id']])
    brows = [dict(reservation_id=row[0], user_id=row[1], dealer_id=row[2], vehicle_id=row[3],
                  vehicle_copy=row[4], reservation_date=row[5], exp_return=row[6]) for row in bcur.fetchall()]

    todays_date = datetime.datetime.now()
    todays_date_long = datetime.datetime.now()

    for row in brows:
        if todate(row['exp_return']) < todays_date_long:
            row['vehicle_status'] = 'Overdue'
        else:
            row['vehicle_status'] = 'Good'

     # Orders Placed that are in process
    query = ''' select from_dealer, order_date, delivery_date, vehicle_id, vehicle_copy, status, lend_id
                from lend
                where to_dealer = (?)
                  and status <> 'complete'
            '''
    ocur = g.db.execute(query, [session['dealer_id']])
    orders = [dict(from_dealer=row[0], order_date=row[1], delivery_date=row[2], vehicle_id=row[3],
                   vehicle_copy=row[4], vehicle_status=row[5], lend_id=row[6]) for row in ocur.fetchall()]

    # Process Orders
    for row in orders:
        if todate(row['delivery_date']) <= todays_date_long:
            row['vehicle_status'] = 'recently completed'
            g.db.execute('update lend set status = ("complete") where lend_id = (?)', [
                         row['lend_id']])
            g.db.commit()
            # Once status is complete delivery to user in wait queue

    # Orders Placed and completed
    query = ''' select from_dealer, order_date, delivery_date, vehicle_id, vehicle_copy, status, lend_id
                from lend
                where to_dealer = (?)
                  and status = 'complete'
            '''
    ccur = g.db.execute(query, [session['dealer_id']])
    corders = [dict(from_dealer=row[0], order_date=row[1], delivery_date=row[2], vehicle_id=row[3],
                    vehicle_copy=row[4], vehicle_status=row[5], lend_id=row[6]) for row in ccur.fetchall()]

    return render_template('dealer_home.html', rows=rows, arows=arows, brows=brows, orders=orders, corders=corders)


@app.route('/retrieve/<vehicle_id>/<vehicle_copy>')
def retrieve(vehicle_id=None, vehicle_copy=None):
    g.db.execute('update inventory set curr_location = (?) where vehicle_id = (?) and vehicle_copy = (?)', [
                 session['dealer_id'], vehicle_id, vehicle_copy])
    g.db.commit()
    return redirect(url_for('dealer_home'))


@app.route('/inventory')
def inventory():
# add memeber validation
    
    get_member = g.db.execute('select is_member from user where user_id = ?', [session['user_id']])
    member = get_member.fetchone()[0]
    if member == None or member != 1:
        flash('You did not pay membership fee. Please pay now.', 'error')
        return redirect( url_for('member') )
        
    todays_date_long = datetime.datetime.now()
    # show a list of all cars in inventory of this dealer and their status, location etc..
    # vehicles should not show if they are in the process of being rent out
    query = ''' select d.vehicle_name, i.vehicle_copy, i.curr_location, i.vehicle_id
            from inventory as i
            inner join vehicle as d 
            on i.vehicle_id = d.vehicle_id
            where i.dealer_id = (?)
              and i.curr_location = (?)
            and not exists
            (
                select *
                from reservation as b
                where b.vehicle_id    = i.vehicle_id
                  and b.user_id = (?)
            )and not exists
            (
                select *
                from return as r
                where r.vehicle_id   = i.vehicle_id
                  and r.vehicle_copy = i.vehicle_copy 
                  and r.actual_return >= (?)
            )
            and not exists
            (
                select *
                from lend as l
                where l.vehicle_id = i.vehicle_id
                  and l.vehicle_copy = i.vehicle_copy
                  and l.status = 'processing'
            )
            group by i.vehicle_id 
            '''

    cur = g.db.execute(query, [
                       session['dealer_id'], session['dealer_id'], session['user_id'], todays_date_long])
    rows = [dict(vehicle_name=row[0], vehicle_copy=row[1],
                 curr_location=row[2], vehicle_id=row[3]) for row in cur.fetchall()]
    print(rows)
    # vehicles from other locations
    query = ''' 
            select d.vehicle_name, d.vehicle_id, i.curr_location
            from inventory i
            left outer join vehicle as d
            on i.vehicle_id = d.vehicle_id 
            where i.curr_location <> (?)
            and not exists
            (
                select *
                from reservation as b
                where b.user_id = (?)
                    and b.vehicle_id = d.vehicle_id
            )
            and not exists(
                select *
                from lend as l
                where l.for_user = (?)
                  and l.status = 'processing'
                  and l.vehicle_id = d.vehicle_id
            )
            group by d.vehicle_id ;
            '''

    cur = g.db.execute(query, [session['dealer_id'],
                               session['user_id'], session['user_id']])
    uarows = [dict(vehicle_name=row[0], vehicle_id=row[1],
                   curr_location=row[2]) for row in cur.fetchall()]

    query = '''
            select *
            from vehicle as d
            where not exists(
                select * 
                from reservation as b
                where b.vehicle_id = d.vehicle_id
                and b.user_id = (?)  
            )  
            and not exists(
                select *
                from inventory as i
                where i.vehicle_id = d.vehicle_id
                and not exists
                    (
                    select * 
                    from reservation as b
                    where b.vehicle_id = d.vehicle_id
                        and b.vehicle_copy = i.vehicle_copy     
                    )   
                and not exists 
                    (
                    select * 
                    from return as r
                    where r.vehicle_id = d.vehicle_id
                        and r.vehicle_copy = i.vehicle_copy
                        and r.actual_return = (?)
                    )         
            );
            '''
    cur = g.db.execute(query, [session['user_id'], todays_date_long])
    waitvehicles = [dict(vehicle_id=row[0], vehicle_name=row[1])
                    for row in cur.fetchall()]

    return render_template('inventory.html', rows=rows, uarows=uarows, waitvehicles=waitvehicles)


@app.route('/wait/<vehicle_id>/')
def wait(vehicle_id=None):
    todays_date_long = datetime.datetime.now()
    g.db.execute('insert into wait (user_id, vehicle_id, wait_date) values (?, ?, ?)', [
                 session['user_id'], vehicle_id, todays_date_long])
    g.db.commit()

    return redirect(url_for('user_home'))


@app.route('/order/<vehicle_id>/')
def order(vehicle_id=None):
  
    todays_date_long = datetime.datetime.now()
    date = datetime.datetime.now()
    delivery_date = date + datetime.timedelta(days=5)

    # Insert into wait queue
    # try:
    #     g.db.execute('insert into wait (user_id, vehicle_id, wait_date) values (?, ?, ?)', [ session['user_id'], vehicle_id, todays_date ])
    #     g.db.commit()
    # except:
    #     return redirect( url_for('user_home') )

    # Find a vehicle that is available
    # vehicles should not be in the lend table under the completed status
    query = '''
            select i.dealer_id, i.vehicle_id, max( i.vehicle_copy )
            from inventory as i
            where i.curr_location <> (?)
            and i.vehicle_id = (?)
            and not exists
            (
                select *
                from reservation as b
                where b.vehicle_id = i.vehicle_id
                    and b.vehicle_copy = i.vehicle_copy 
            )
            and not exists
            (
                select *
                from lend as l
                where l.vehicle_id = i.vehicle_id
                  and l.vehicle_copy = i.vehicle_copy
                  and l.status = 'processing'
            );
            '''
    cur = g.db.execute(query, [session['dealer_id'], vehicle_id])
    rows = [dict(dealer_id=row[0], vehicle_id=row[1], vehicle_copy=row[2])
            for row in cur.fetchall()]

    print("Waiting for ", rows)

    # Create lend entry using available vehicle
    g.db.execute('insert into lend (to_dealer, from_dealer, order_date, delivery_date, vehicle_id, vehicle_copy, status, for_user) values (?, ?, ?, ?, ?, ?, ?, ?)',
                 [session['dealer_id'], rows[0]['dealer_id'], todays_date_long, delivery_date, rows[0]['vehicle_id'], rows[0]['vehicle_copy'], "processing", session['user_id']])
    g.db.commit()

    # vehicle/Copy being delivered as unavailable until it is delivered
    # g.db.execute('update inventory set vehicle_status = ("unavailable") where vehicle_id = (?) and vehicle_copy = (?)', [ rows[0]['vehicle_id'], rows[0]['vehicle_copy'] ])
    # g.db.commit()

    return redirect(url_for('user_home'))


@app.route('/history')
def history():

    query = '''
        select h.user_id, h.reservationed_from, h.returned_to, h.vehicle_id, h.vehicle_copy, h.reservation_date, h.return_date, d.vehicle_name
        from history as h
        inner join vehicle as d
            on h.vehicle_id = d.vehicle_id 
        '''
    cur = g.db.execute(query)
    rows = [dict(user_id=row[0], reservationed_from=row[1], returned_to=row[2], vehicle_id=row[3], vehicle_copy=row[4],
                 reservation_date=row[5], return_date=row[6], vehicle_name=row[7]) for row in cur.fetchall()]

    return render_template('history.html', rows=rows)

@app.route('/modify_user/')
@app.route('/modify_user/<user_id>')
def modify_user(user_id=None):
    if user_id:
        g.db.execute("update user set is_member=0 where user_id = (?)",[user_id])
        g.db.commit()
    query = '''
        select user_id, user_name from user where is_member=1;
        '''
    cur = g.db.execute(query)
    rows = [dict(user_id=row[0],user_name=row[1]) for row in cur.fetchall()]

    return render_template('modify_user.html', rows=rows)


@app.route('/dealer_lend')
def dealer_lend():

    # show a list of all books in inventory of this dealer and their status, location etc..
    query = ''' select d.vehicle_name, i.vehicle_copy, i.curr_location, i.vehicle_id, i.dealer_id
            from inventory as i
            inner join vehicle as d 
            on i.vehicle_id = d.vehicle_id
            where i.dealer_id <> (?)
              and i.dealer_id = i.curr_location
              and not exists(
                select *
                from reservation as b
                where b.vehicle_id   = i.vehicle_id
                  and b.vehicle_copy = i.vehicle_copy
            ) 
            '''

    cur = g.db.execute(query, [session['dealer_id']])
    rows = [dict(vehicle_name=row[0], vehicle_copy=row[1], curr_location=row[2],
                 vehicle_id=row[3], dealer_id=row[4]) for row in cur.fetchall()]

    # Unavailble vehicles
    query = ''' select d.vehicle_name, i.vehicle_copy, i.curr_location, i.vehicle_id, i.dealer_id
        from inventory as i
        inner join vehicle as d 
        on i.vehicle_id = d.vehicle_id
        where i.dealer_id <> (?)
          and exists(
            select *
            from reservation as b
            where b.vehicle_id    = i.vehicle_id
              and b.vehicle_copy  = i.vehicle_copy
        ) or i.dealer_id <> i.curr_location
        '''

    cur = g.db.execute(query, [session['dealer_id']])
    uarows = [dict(vehicle_name=row[0], vehicle_copy=row[1], curr_location=row[2],
                   vehicle_id=row[3], dealer_id=row[4]) for row in cur.fetchall()]

    return render_template('dealer_lend.html', rows=rows, uarows=uarows)


@app.route('/lend/<vehicle_id>/<vehicle_copy>/')
def lend(vehicle_id=None, vehicle_copy=None):

    todays_date = time  # .strftime("%Y-%m-%d")
    todays_date_long = datetime.datetime.today().date()
    date = datetime.datetime.today().date()
    delivery_date = todays_date_long + datetime.timedelta(days=5)

    if vehicle_id and vehicle_copy:
        query = ''' select d.vehicle_name, i.vehicle_copy, d.vehicle_type, i.curr_location, i.vehicle_id, i.dealer_id
            from inventory as i
            inner join vehicle as d 
            on i.vehicle_id = d.vehicle_id 
            where i.vehicle_id   = (?) 
              and i.vehicle_copy = (?)
            '''
        cur = g.db.execute(query, [vehicle_id, vehicle_copy])
        rows = [dict(vehicle_name=row[0], vehicle_copy=row[1], vehicle_desc=row[2],
                     curr_location=row[3], vehicle_id=row[4], dealer_id=row[5]) for row in cur.fetchall()]
        rows[0]['deliver_to'] = session['dealer_id']
        rows[0]['order_date'] = todays_date_long
        rows[0]['delivery_date'] = delivery_date

    else:
        pass

    return render_template('confirm_lend.html', context=rows)


@app.route('/confirm_lend', methods=['POST'])
def confirm_lend():

    # Insert into lend
    print(request.form.items)
    g.db.execute('insert into lend (to_dealer, from_dealer, order_date, delivery_date, vehicle_id, vehicle_copy, status) values (?, ?, ?, ?, ?, ?, ?)',
                 [request.form['to_dealer'], request.form['from_dealer'], todate(request.form['order_date']), todate(request.form['delivery_date']), request.form['vehicle_id'], request.form['vehicle_copy'], "processing"])
    g.db.commit()

    return redirect(url_for('dealer_home'))


@app.route('/waitlist')
def waitlist():
    return redirect(url_for('user_home'))


@app.route('/vehicle_info/<vehicle_id>')
def vehicle_info(vehicle_id=None):

    if vehicle_id:
        query = 'select vehicle_id, vehicle_name, vehicle_type from vehicle where vehicle_id = (?)'
        cur = g.db.execute(query, [vehicle_id])
        rows = [dict(vehicle_id=row[0], vehicle_name=row[1],
                     vehicle_type=row[2]) for row in cur.fetchall()]

        # #Retrieve keywords
        query = 'select keyword from vehicle_keyword where vehicle_id = (?)'
        cur = g.db.execute(query, [vehicle_id])
        keywords = [dict(vehicle_keyword=row[0]) for row in cur.fetchall()]

        print(keywords)
        # Retrieve all vehicle keywords in a separate list
        count = vehicle_count()
        vehicle_list = []
        vehicle_similarity = []
        ordered_by_sim = []
        if keywords:

            # Create a list of lists, each list contains all the keywords for a given vehicle
            for vehicle in range(1, count + 1):
                query = 'select vehicle_id, keyword from vehicle_keyword where vehicle_id = (?)'
                cur = g.db.execute(query, [vehicle])
                vehicle_words = [
                    dict(vehicle_id=row[0], vehicle_keyword=row[1]) for row in cur.fetchall()]
                if vehicle_words:
                    vehicle_list.append(vehicle_words)

            print(vehicle_list)

            for item in vehicle_list:
                # print item
                vehicle_index = int(vehicle_id) - 1
                original_keywords = normalize_list(vehicle_list[vehicle_index])
                compare_keywords = normalize_list(item)

                # print 'List1', original_keywords
                # print 'List2', compare_keywords
                # Call cosine sim with each vehicle paired to the vehicle you are searching
                similarity = cosineSim(original_keywords, compare_keywords)

                # Get name of vehicle
                query = 'select vehicle_name from vehicle where vehicle_id = (?)'
                cur = g.db.execute(query, [item[0]['vehicle_id']])
                vehicle_name = cur.fetchone()[0]

                vehicle_object = {
                    'vehicle_id':  item[0]['vehicle_id'],
                    'vehicle_name': vehicle_name,
                    'similarity': similarity
                }

                vehicle_similarity.append(vehicle_object)

            # # #Exclude the original vehicle
            del vehicle_similarity[vehicle_index]
            # #print vehicle_similarity

            for vehicle_sim in sorted(vehicle_similarity, key=operator.itemgetter("similarity"), reverse=True):
                # print vehicle_sim
                ordered_by_sim.append(vehicle_sim)

    else:
        pass

    return render_template('vehicle_info.html', context=rows, keywords=keywords, ordered_by_sim=ordered_by_sim)


def cosineSim(oList, cList):

    vectorlist1, vectorlist2 = wordVector(oList, cList)

    dotProduct = 0
    for x in range(len(vectorlist1)):
        dotProduct += vectorlist1[x] * vectorlist2[x]

    # print dotProduct
    sigmaList1 = 0.0
    sigmaList2 = 0.0

    for x in range(len(vectorlist1)):
        sigmaList1 += pow(vectorlist1[x], 2)

    # print sigmaList1

    for x in range(len(vectorlist2)):
        sigmaList2 += pow(vectorlist2[x], 2)

    # print sigmaList2

    normalization1 = sqrt(sigmaList1)
    normalization2 = sqrt(sigmaList2)

    # print normalization1
    # print normalization2

    return (dotProduct / (normalization1 * normalization2))


def wordVector(keywordlist, keywordlist2):

    # print 'wordvector'
    # count the character or characters
    charCounter = Counter(keywordlist)

    charCounter2 = Counter(keywordlist2)

    # .keys() Returns a list of dictionary keys
    wholeList = set(charCounter.keys()).union(set(charCounter2.keys()))

    # print wholeList

    listVector = [charCounter[i] for i in wholeList]

    listVector2 = [charCounter2[i] for i in wholeList]

    return listVector, listVector2


def normalize_list(vehicle_list):
    vehicle_keywords = []
    vehicle_id = 0
    for vehicle in vehicle_list:
        vehicle_id = vehicle['vehicle_id']
        vehicle_keywords.append(vehicle['vehicle_keyword'])

    vehicle_object = {
        'vehicle_id':  vehicle_id,
        'keywords': vehicle_keywords
    }

    return vehicle_keywords


def vehicle_count():

    cur = g.db.execute('select count(vehicle_id) from vehicle')
    count = cur.fetchone()[0]
    return count


@app.route('/reservation/<vehicle_id>/')
@app.route('/reservation/<vehicle_id>/<curr_location>/')
def reservation(vehicle_id=None, curr_location=None):

    if vehicle_id:
        todays_date_long = datetime.datetime.now()

        buttons = {
            'reservation': False,
            'order': False,
            'wait': False,
            'unavailable': False
        }

        # Select the max available vehicle from the users main dealer
        query = ''' 
            select d.vehicle_name, max( i.vehicle_copy ), d.vehicle_type, i.curr_location, i.vehicle_id, i.dealer_id
            from inventory as i
            inner join vehicle as d 
                on i.vehicle_id = d.vehicle_id
            where i.curr_location = (?)
              and i.vehicle_id = (?)
            and not exists
            (
                select *
                from reservation as b
                where b.vehicle_id   = i.vehicle_id
                  and b.vehicle_copy = i.vehicle_copy
            )and not exists
            (
                select *
                from return as r
                where r.vehicle_id   = i.vehicle_id
                  and r.vehicle_copy = i.vehicle_copy 
                  and r.actual_return >= (?)
            )
            and not exists
            (
                select *
                from lend as l
                where l.vehicle_id = i.vehicle_id
                  and l.vehicle_copy = i.vehicle_copy
                  and l.status = 'processing'
            );
            '''
        cur = g.db.execute(
            query, [curr_location, vehicle_id, todays_date_long])
        rows = [dict(vehicle_name=row[0], vehicle_copy=row[1], vehicle_desc=row[2],
                     curr_location=row[3], vehicle_id=row[4], dealer_id=row[5]) for row in cur.fetchall()]

        # If rows is blank, then the users current dealer does not have any copies available
        if rows[0]['vehicle_id'] == None:
            print('NO vehicle AVAILABLE')
            buttons['unavailable'] = True
            vehicle_search = g.db.execute(
                'select vehicle_name, vehicle_type from vehicle where vehicle_id = (?)', [vehicle_id])
            na_vehicle = [dict(vehicle_name=row[0], vehicle_desc=row[1])
                          for row in vehicle_search.fetchall()]
            rows[0]['vehicle_name'] = na_vehicle[0]['vehicle_name']
            rows[0]['vehicle_copy'] = 'N/A'
            rows[0]['vehicle_desc'] = na_vehicle[0]['vehicle_desc']
            rows[0]['curr_location'] = 'N/A'
            rows[0]['vehicle_id'] = vehicle_id
            rows[0]['dealer_id'] = ''
        else:
            buttons['reservation'] = True

        # Check if the vehicle is available at another dealer and the user is not already wait for an order with this vehicle
        # Unavailble vehicles
        query = ''' 
                select d.vehicle_name, d.vehicle_id
                from vehicle as d
                where d.vehicle_id = (?)
                and not exists(
                    select i.vehicle_id
                    from inventory as i 
                    where i.dealer_id = (?)
                    and i.vehicle_id = d.vehicle_id 
                )
                and exists
                (
                    select i.vehicle_id
                    from inventory as i 
                    where i.dealer_id <> (?)
                    and i.vehicle_id = d.vehicle_id 
                )
                and not exists
                (
                    select *
                    from reservation as b
                    where b.user_id = (?)
                    and b.vehicle_id = d.vehicle_id
                )and not exists(
                    select *
                    from lend as l
                    where l.vehicle_id = d.vehicle_id
                      and l.for_user = (?)
                      and l.status = 'processing'
                )  
                '''

        cur = g.db.execute(query, [vehicle_id, session['dealer_id'],
                                   session['dealer_id'], session['user_id'], session['user_id']])
        ua_vehicles = [dict(vehicle_name=row[0], vehicle_id=row[1])
                       for row in cur.fetchall()]

        if ua_vehicles:
            buttons['order'] = True

        # print 'reservation -----------------------'
        # print reservation_vehicles
        # print 'Unavailable -----------------------'
        # print ua_vehicles

        # print buttons
        # print rows
        # print len( rows )

            # Check if vehicle is available to be reservationed
        # show a list of all cars in inventory of this dealer and their status, location etc..
        # vehicles should not show if they are in the process of being lent out
        # query = ''' select d.vehicle_name, i.vehicle_copy, i.curr_location, i.vehicle_id
        #     from inventory as i
        #     inner join vehicle as d
        #     on i.vehicle_id = d.vehicle_id
        #     where i.dealer_id = (?)
        #       and i.curr_location = (?)
        #       and i.vehicle_id = (?)
        #     and not exists
        #     (
        #         select *
        #         from reservation as b
        #         where b.vehicle_id    = i.vehicle_id
        #           and b.user_id = (?)
        #     )
        #     and not exists
        #     (
        #         select *
        #         from lend as l
        #         where l.vehicle_id = i.vehicle_id
        #           and l.vehicle_copy = i.vehicle_copy
        #           and l.status = 'processing'
        #     )
        #     group by i.vehicle_id
        #     '''

        # cur = g.db.execute( query, [ session['dealer_id'], session['dealer_id'], vehicle_id, session['user_id'] ] )
        # reservation_vehicles = [dict( vehicle_name=row[0], vehicle_copy=row[1], curr_location=row[2], vehicle_id=row[3]) for row in cur.fetchall()]

        # if reservation_vehicles:
        #     buttons['reservation'] = True

        # cur = g.db.execute( 'select vehicle_id from wait where vehicle_id = (?) and user_id = (?)', [vehicle_id, session['user_id']] )
        # wait_vehicles = [dict( vehicle_id=row[0] ) for row in cur.fetchall()]

        # print 'Waiting -----------------------'
        # print wait_vehicles

        # if rows[0]['vehicle_id'] is None:
        #     for wvehicle in wait_vehicles:
        #         if wvehicle['vehicle_id'] == vehicle_id:
        #             #You are already wait for this vehicle
        #             print 'something'
            # return redirect( url_for('user_home' ) )
            # return redirect( url_for('wait', vehicle_id=vehicle_id ) )
    else:
        pass

    return render_template('reservation.html', context=rows, buttons=buttons)


@app.route('/reservation_vehicle/<dealer_id>/<vehicle_id>/')
@app.route('/reservation_vehicle/<dealer_id>/<vehicle_id>/', methods=['POST'])
def reservation_vehicle(dealer_id=None, vehicle_id=None, vehicle_copy=None):
    days = request.form['days']
    hours = request.form['hours']
    pickup_date = request.form['pickup_date']
    pickup_time = request.form['pickup_time']
    # print('===============', request.form['days'])
    try:
        days = int(days) 
    except:
        days = 0

    try:
        rentHours = int(days) * 24
    except:
        rentHours = 0
    try:
        rentHours += int(hours)
    except:
        rentHours += 0
    
    if rentHours == 0 or rentHours > 72:
        flash('Rent Time is invalid. Please adjust.', 'error')
        return redirect( url_for('reservation', vehicle_id=vehicle_id, curr_location=dealer_id) )
   
    # print('hi')
    reservation_date = create_date(str(pickup_date), int(pickup_time))
    print('reservation_date = ', reservation_date)
    if todate(reservation_date) < datetime.datetime.now():
        flash('Please select a valid date.', 'error')
        # return redirect( url_for('reservation_vehicle', dealer_id = dealer_id, vehicle_id=vehicle_id, vehicle_copy=vehicle_copy) )
        # return
       
    expected_return = todate(reservation_date) + datetime.timedelta(hours=rentHours)

    #Check if vehicle is already being reservationed 
    cur = g.db.execute('select vehicle_id from reservation where user_id = (?) and vehicle_id = (?)', 
                    [ session['user_id'], vehicle_id])
    isreservationed = [dict( vehicle_id=row[0] ) for row in cur.fetchall()]
    
    #print('length: ', len( isreservationed ))
    #print(isreservationed)
    if isreservationed != []:
        flash('You are already reserved this kind of vehicle', 'error')
        return redirect( url_for('reservation', vehicle_id=vehicle_id, curr_location=dealer_id) )
       
    #Insert into reservation 
    g.db.execute('insert into reservation (user_id, dealer_id, vehicle_id, vehicle_copy, reservation_date, exp_return) values (?, ?, ?, ?, ?, ?)', 
                    [ session['user_id'], dealer_id, vehicle_id, vehicle_copy, reservation_date, expected_return ])
    g.db.commit()
    
    #Select current row to get reservation id
    query = ''' select reservation_id
            from reservation
            where vehicle_id    = (?) 
              and user_id = (?)
            '''
    cur = g.db.execute( query, [vehicle_id, session['user_id']] )
    rows = [dict( reservation_id=row[0] ) for row in cur.fetchall()]
    #print(rows)
    #Track reservation History  
    g.db.execute('insert into history (reservation_id, user_id, reservationed_from, vehicle_id, vehicle_copy, reservation_date) values (?, ?, ?, ?, ?, ?)', 
                    [ rows[0]['reservation_id'], session['user_id'], dealer_id, vehicle_id, vehicle_copy, reservation_date ])
    g.db.commit()
    
    return redirect(url_for('user_home'))


@app.route('/brand')
def brand():
    cur = g.db.execute('select * from brand')
    rows = [dict(brand_id=row[0], brand_name=row[1]) for row in cur.fetchall()]

    return render_template('brand.html', rows=rows)


@app.route('/add_brand', methods=['POST'])
def add_brand():
    g.db.execute('insert into brand (brand_name) values (?)',
                 [request.form['brand_name']])
    g.db.commit()

    return redirect(url_for('brand'))


@app.route('/vehicle')
@app.route('/vehicle/<brand_id>/')
def vehicle(brand_id=None):

    if brand_id == None:
        query = '''
                    select d.vehicle_id, d.vehicle_name, d.vehicle_type, d.number_copies, u.brand_name, max(i.vehicle_copy)
                    from vehicle as d
                    inner join brand_makes as a
                        on d.vehicle_id = a.vehicle_id
                    inner join brand as u
                        on a.brand_id = u.brand_id
                    left join inventory as i
                        on d.vehicle_id = i.vehicle_id
                    group by i.vehicle_id
                '''
        cur = g.db.execute(query)
        rows = [dict(vehicle_id=row[0], vehicle_name=row[1], vehicle_type=row[2],
                     number_copies=row[3], brand_name=row[4], copies_out=row[5]) for row in cur.fetchall()]
    else:
        query = '''
                    select d.vehicle_id, d.vehicle_name, d.vehicle_type, d.number_copies, u.brand_name, max(i.vehicle_copy)
                    from vehicle as d
                    inner join brand_makes as a
                        on d.vehicle_id = a.vehicle_id
                    inner join brand as u
                        on a.brand_id = u.brand_id
                    left join inventory as i
                        on d.vehicle_id = i.vehicle_id
                    where u.brand_id = (?)
                    group by i.vehicle_id
                '''
        cur = g.db.execute(query, [brand_id])
        rows = [dict(vehicle_id=row[0], vehicle_name=row[1], vehicle_type=row[2],
                     number_copies=row[3], brand_name=row[4], copies_out=row[5]) for row in cur.fetchall()]

    for row in rows:
        print(row)
        if row['copies_out'] is not None:
            row['copies_remaining'] = int(
                row['number_copies']) - int(row['copies_out'])
        else:
            row['copies_remaining'] = int(row['number_copies'])

    cur = g.db.execute('select * from brand')
    options = [dict(brand_id=row[0], brand_name=row[1])
               for row in cur.fetchall()]

    return render_template('vehicle.html', rows=rows, options=options)


@app.route('/add_vehicle', methods=['POST'])
def add_vehicle():
    g.db.execute('insert into vehicle (vehicle_name, vehicle_type, number_copies) values (?, ?, ?)',
                 [request.form['vehicle_name'], request.form['vehicle_type'], request.form['number_copies']])
    get_vehicle_id = g.db.execute('select last_insert_rowid()')
    vehicle_id = get_vehicle_id.fetchone()[0]
    g.db.commit()

    g.db.execute('insert into brand_makes (brand_id, vehicle_id) values (?, ?)',
                 [request.form['brands'], vehicle_id])
    g.db.commit()

    return redirect(url_for('vehicle', brand_id=request.form['brands']))


def todate(datestr, format="%Y-%m-%d %H:%M:%S.%f"):
    result = datetime.datetime.now()
    if not datestr:
        return result
    try:
        result = datetime.datetime.strptime(datestr, format)
    except:
        result = datetime.datetime.strptime(datestr, "%Y-%m-%d")
    return result

def create_date(s2, hrs):
    FMT = '%Y-%m-%d'
    return str(datetime.datetime.strptime(s2, FMT) + datetime.timedelta(hours=hrs, seconds=0, microseconds=0)) + ".865036"

def late_hours(s1, s2):
    from datetime import timedelta
    FMT = '%Y-%m-%d %H:%M:%S.%f'
    hours = 0
    days = 0
    sec = 0
    try:
        tdelta = datetime.datetime.strptime(
            s2, FMT) - datetime.datetime.strptime(s1, FMT)
    except:
        FMT = '%Y-%m-%d'
        s2 = str(datetime.datetime.now().date())
        tdelta = datetime.datetime.strptime(
            s2, FMT) - datetime.datetime.strptime(s1, FMT)

    days = tdelta.days
    sec = tdelta.seconds
    hours = days * 24 + sec / 3600
    return hours


def get_rental_fee(s1, s2, fee):
    from datetime import timedelta
    FMT = '%Y-%m-%d %H:%M:%S.%f'
    hours = 0
    days = 0
    sec = 0
    try:
        tdelta = datetime.datetime.strptime(
            s2, FMT) - datetime.datetime.strptime(s1, FMT)
    except:
        FMT = '%Y-%m-%d'
        s2 = str(datetime.datetime.now().date())
        tdelta = datetime.datetime.strptime(
            s2, FMT) - datetime.datetime.strptime(s1, FMT)

    days = tdelta.days
    sec = tdelta.seconds
    hours = days * 24 + sec / 3600
    # if hours < 0:
        # return 15
    return int(hours) * fee


def late_feee_calc(hours, fee):
    if hours == 1:
        return fee
    if hours > 1:
        return fee + (hours - 1) * fee * 0.05
    return 0

def get_minutes_before_reservation(s1, s2):
    from datetime import timedelta
    FMT = '%Y-%m-%d %H:%M:%S.%f'
    hours = 0
    days = 0 
    sec = 0
    try:
        tdelta = datetime.datetime.strptime(s2, FMT) - datetime.datetime.strptime(s1, FMT)
    except:
        FMT = '%Y-%m-%d'
        s2 = str(datetime.datetime.now().date())
        tdelta = datetime.datetime.strptime(s2, FMT) - datetime.datetime.strptime(s1, FMT)

    days = tdelta.days
    sec = tdelta.seconds
    min = days * 24 * 60 + sec / 60

    return int(min) 

def format_date(date):
    res_date = date
    try:
        FMT = '%Y-%m-%d'
        res_date = datetime.datetime.strptime(date, FMT).date()
    except:
        FMT = '%Y-%m-%d %H:%M:%S.%f'
        res_date = datetime.datetime.strptime(date, FMT).date()
    return res_date

# Sign out of session
@app.route('/signout')
def signout():
    session.pop('dealer_id', None)
    session.pop('user_id', None)
    session.pop('admin_id', None)
    session.pop('dealer_logged_in', None)
    session.pop('user_logged_in', None)
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 80, debug= True)
