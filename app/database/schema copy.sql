PRAGMA foreign_keys = ON;
.headers on
.mode column

drop table if exists dealer;
drop table if exists location;
drop table if exists inventory;
drop table if exists vehicle;
drop table if exists vehicle_keyword;
drop table if exists brand;
drop table if exists brandmakes;
drop table if exists user;
drop table if exists reservation;
drop table if exists return;
drop table if exists wait;
drop table if exists lend;
drop table if exists membership;
drop table if exists history;


create table dealer(
	dealer_id varchar,
	dealer_name varchar,
    zip_code int,
    password varchar,
	primary key(dealer_id)
);

create table location(
    state varchar,
    city varchar,
    zip_code int,
    primary key(zip_code)
);

create table inventory(
	dealer_id varchar,
	vehicle_id int,
	vehicle_copy int,
    curr_location int,
	primary key(vehicle_id, vehicle_copy)
    -- foreign key(dealer_id) references dealer(dealer_id),
    -- foreign key(vehicle_id) references vehicle(vehicle_id)
);

create table vehicle(
	vehicle_id integer primary key autoincrement,
	vehicle_name varchar,
	vehicle_type varchar,
	number_copies varchar
);

create table vehicle_keyword(
    vehicle_id int,
    keyword varchar
    -- foreign key(vehicle_id) references vehicle(vehicle_id)
);

create table brand(
    brand_id integer primary key autoincrement,
    brand_name varchar
);

create table brand_makes(
    brand_id integer,
    vehicle_id integer,
    primary key(brand_id, vehicle_id)
    -- foreign key(brand_id) references brand(brand_id),
    -- foreign key(vehicle_id) references vehicle(vehicle_id)
);

create table user(
    user_id varchar,
    user_name varchar,
    user_type varchar,
    password varchar,
    primary key(user_id)
    -- foreign key(dealer_id) references dealer(dealer_id)
);

create table reservation(
    reservation_id integer primary key autoincrement,
    user_id varchar,
    dealer_id varchar,
    vehicle_id int,
    vehicle_copy int,
    reservation_date date,
    exp_return date
    -- foreign key(user_id) references user(user_id),
    -- foreign key(dealer_id) references inventory(dealer_id),
    -- foreign key(vehicle_id) references inventory(vehicle_id)
);

create table history(
    reservation_id integer,
    user_id varchar,
    reservationed_from varchar,
    returned_to varchar,
    vehicle_id int,
    vehicle_copy int,
    reservation_date date,
    return_date date
);

create table return(
    return_id integer,
    user_id varchar,
    dealer_id varchar,
    vehicle_id int,
    vehicle_copy int,
    actual_return date
    -- foreign key(user_id) references user(user_id),
    -- foreign key(dealer_id) references inventory(dealer_id),
    -- foreign key(vehicle_id) references inventory(vehicle_id)
);

create table wait(
    user_id int,
    vehicle_id int,
    wait_date date,
    primary key(user_id, vehicle_id, wait_date)
);

create table lend(
    lend_id integer primary key autoincrement,
    to_dealer int,
    from_dealer int,
    order_date date,
    delivery_date date,
    vehicle_id int,
    vehicle_copy int,
    status varchar,
    for_user varchar
);

create table membership(
    user_id varchar,
    dealer_id varchar,
    primary key(user_id, dealer_id)
    -- foreign key(user_id) references user(user_id),
    -- foreign key(dealer_id) references dealer(dealer_id)
);