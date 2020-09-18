PRAGMA foreign_keys = ON;
.headers on
.mode column


-- Add Location
insert into location values ('New Jersey', 'Bloomfield', 07003);
insert into location values ('New York', 'Dale', 09009);
insert into location values ('New York', 'Newark', 02039);
insert into location values ('Delaware', 'Denton', 97093);

-- Add dealers
insert into dealer values ('dealer1', 'Bloomfield dealer', 07003, 'admin');
insert into dealer values ('dealer2', 'New York dealer', 09009, 'admin');
insert into dealer values ('dealer3', 'New York-Newark dealer', 02039, 'admin');
insert into dealer values ('dealer4', 'Denton dealer', 97093, 'admin');

-- Add vehicles
insert into vehicle values (1, 'BMW X5', 'SUV', 9);
insert into vehicle values (2, 'Camaro ', 'Sports', 5);
insert into vehicle values (3, 'Infiti Q50', 'Sedan', 5);
insert into vehicle values (4, 'Ford F150', 'Truck', 6);
insert into vehicle values (5, 'Range Rover Discovery', 'SUV', 6);
insert into vehicle values (6, 'Tesla Model S', 'Sedan', 5);
insert into vehicle values (7, 'Ford Figo', 'Hatchback', 5);
insert into vehicle values (8, 'Volkswagon Polo', 'Hatchback', 5);
insert into vehicle values (9, 'Ford Mustang', 'Sports', 5);
insert into vehicle values (10, 'Jeep Wrangler', 'SUV', 2);
insert into vehicle values (11, 'Dodge RAM', 'Truck', 1);
insert into vehicle values (12, 'Toyota Corolla', 'Sedan', 1);
-- Add vehicle Keyword
insert into vehicle_keyword values (1, 'Offroad');
insert into vehicle_keyword values (1, 'dirt');
insert into vehicle_keyword values (1, 'Heighted');
insert into vehicle_keyword values (1, 'Heavy');
insert into vehicle_keyword values (1, 'luxury');
insert into vehicle_keyword values (2, 'fast');
insert into vehicle_keyword values (2, 'sporty');
insert into vehicle_keyword values (2, 'speed');
insert into vehicle_keyword values (2, 'racer');
insert into vehicle_keyword values (2, 'quick');
insert into vehicle_keyword values (3, 'luxury');
insert into vehicle_keyword values (3, 'comfort');
insert into vehicle_keyword values (3, 'long');
insert into vehicle_keyword values (3, 'fast');
insert into vehicle_keyword values (3, 'quick');
insert into vehicle_keyword values (4, 'vehiclerier');
insert into vehicle_keyword values (4, 'storage');
insert into vehicle_keyword values (4, 'offroad');
insert into vehicle_keyword values (4, 'big');
insert into vehicle_keyword values (5, 'Offroad');
insert into vehicle_keyword values (5, 'luxury');
insert into vehicle_keyword values (5, 'fast');
insert into vehicle_keyword values (5, '4WD');
insert into vehicle_keyword values (6, 'luxury');
insert into vehicle_keyword values (6, 'electric');
insert into vehicle_keyword values (6, 'automatic');
insert into vehicle_keyword values (6, 'auto pilot');
insert into vehicle_keyword values (6, 'media center');
insert into vehicle_keyword values (7, 'small');
insert into vehicle_keyword values (7, 'compact');
insert into vehicle_keyword values (7, 'great');
insert into vehicle_keyword values (7, 'clean');
insert into vehicle_keyword values (7, 'automatic');
insert into vehicle_keyword values (8, 'good');
insert into vehicle_keyword values (8, 'compact');
insert into vehicle_keyword values (8, 'mileage');
insert into vehicle_keyword values (8, 'fast');
insert into vehicle_keyword values (9, 'go');
insert into vehicle_keyword values (9, 'fast');
insert into vehicle_keyword values (9, 'sports');
insert into vehicle_keyword values (9, 'quick');
insert into vehicle_keyword values (9, 'race');
insert into vehicle_keyword values (9, 'manual');
insert into vehicle_keyword values (10, 'space');
insert into vehicle_keyword values (10, 'Offroad');
insert into vehicle_keyword values (10, 'Big');
insert into vehicle_keyword values (10, 'slow');
insert into vehicle_keyword values (10, 'comfort');
insert into vehicle_keyword values (11, 'Big');
insert into vehicle_keyword values (11, 'heavy');
insert into vehicle_keyword values (12, 'quick');
insert into vehicle_keyword values (12, 'comfort');



-- Add users
insert into user values ('user1','Michael','researcher','admin');
insert into user values ('user2','Richard','researcher','admin');
insert into user values ('user3','James','student','admin');
insert into user values ('user4','Paul','Hobby','admin');
insert into user values ('user5','Jazmine','student','admin');
insert into user values ('user6','Amanda','Hobby','admin');

-- Add membership
insert into membership values ('user1','dealer1');
insert into membership values ('user2','dealer1');
insert into membership values ('user3','dealer2');
insert into membership values ('user4','dealer2');
insert into membership values ('user5','dealer3');
insert into membership values ('user6','dealer4');

-- Add Inventory
insert into inventory values ('dealer1', 1, 1, 'dealer1');
insert into inventory values ('dealer1', 11, 1, 'dealer1');
insert into inventory values ('dealer1', 1, 2, 'dealer1');
insert into inventory values ('dealer1', 1, 3, 'dealer1');
insert into inventory values ('dealer1', 1, 4, 'dealer1');
insert into inventory values ('dealer1', 9, 1, 'dealer1');
insert into inventory values ('dealer1', 9, 2, 'dealer1');
insert into inventory values ('dealer1', 9, 3, 'dealer1');
insert into inventory values ('dealer1', 9, 4, 'dealer1');
insert into inventory values ('dealer1', 10, 1, 'dealer1');
insert into inventory values ('dealer1', 10, 2, 'dealer1');
insert into inventory values ('dealer4', 1, 5, 'dealer4');
insert into inventory values ('dealer4', 1, 6, 'dealer4');
insert into inventory values ('dealer4', 1, 7, 'dealer4');
insert into inventory values ('dealer2', 2, 1, 'dealer2');
insert into inventory values ('dealer2', 2, 2, 'dealer2');
insert into inventory values ('dealer3', 2, 3, 'dealer3');
insert into inventory values ('dealer3', 2, 4, 'dealer3');
insert into inventory values ('dealer1', 3, 1, 'dealer1');
insert into inventory values ('dealer2', 3, 2, 'dealer2');
insert into inventory values ('dealer4', 3, 3, 'dealer4');
insert into inventory values ('dealer4', 3, 4, 'dealer4');
insert into inventory values ('dealer4', 3, 5, 'dealer4');
insert into inventory values ('dealer2', 4, 1, 'dealer2');
insert into inventory values ('dealer2', 4, 2, 'dealer2');
insert into inventory values ('dealer3', 4, 3, 'dealer3');
insert into inventory values ('dealer1', 5, 1, 'dealer1');
insert into inventory values ('dealer2', 5, 2, 'dealer2');
insert into inventory values ('dealer2', 5, 3, 'dealer2');
insert into inventory values ('dealer4', 5, 4, 'dealer4');
insert into inventory values ('dealer4', 5, 5, 'dealer4');
insert into inventory values ('dealer2', 6, 1, 'dealer2');
insert into inventory values ('dealer3', 6, 2, 'dealer3');
insert into inventory values ('dealer3', 6, 3, 'dealer3');
insert into inventory values ('dealer4', 6, 4, 'dealer4');
insert into inventory values ('dealer4', 6, 5, 'dealer4');
insert into inventory values ('dealer2', 7, 1, 'dealer2');
insert into inventory values ('dealer3', 7, 2, 'dealer3');
insert into inventory values ('dealer3', 7, 3, 'dealer3');
insert into inventory values ('dealer4', 8, 1, 'dealer4');
insert into inventory values ('dealer4', 8, 2, 'dealer4');
insert into inventory values ('dealer4', 8, 3, 'dealer4');
-- Add brands
insert into brand values (1,'BMW');
insert into brand values (2,'Chevrolet');
insert into brand values (3,'Nissan');
insert into brand values (4,'Ford');
insert into brand values (5,'Range Rover');
insert into brand values (6,'Tesla');
insert into brand values (7,'Volkswagon');
insert into brand values (8,'Jeep');
insert into brand values (9,'Dodge');
insert into brand values (10,'Toyota');
-- Add brand_makes
insert into brand_makes values (1, 1);
insert into brand_makes values (1, 2);
insert into brand_makes values (2, 3);
insert into brand_makes values (2, 4);
insert into brand_makes values (3, 5);
insert into brand_makes values (3, 6);
insert into brand_makes values (4, 7);
insert into brand_makes values (4, 8);
insert into brand_makes values (1, 9);
insert into brand_makes values (1, 10);
insert into brand_makes values (2, 11);
insert into brand_makes values (2, 12);
-- Add wait 
-- insert into wait values ('user1', 1, '2016-04-16');
-- insert into wait values ('user2', 1, '2016-04-16');
-- insert into wait values ('user3', 1, '2016-04-16');
-- insert into wait values ('user1', 2, '2016-04-16');
-- insert into wait values ('user2', 2, '2016-04-16');
-- insert into wait values ('user3', 2, '2016-04-16');
-- Add reservation

-- Add Return

-- Add Lend


--Print Data to console
--  select * from dealer;
--  select * from location;
--  select * from vehicle;
--  select * from vehicle_keyword;