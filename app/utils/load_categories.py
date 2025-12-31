from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import CollectionInvalid

# Global counter for sub-category numb_ids
sub_cat_numb_id_counter = 1

# Original CATEGORIES_DATA with sub-categories as strings
_ORIGINAL_CATEGORIES_DATA = [
    {
        "numb_id": 1,
        "name": "Mobiles",
        "int_date": 30,
        "sub_categories": [
            "iPhone", "Mi", "Samsung", "Vivo", "Realme", "Oppo", "One Plus", "Other Mobiles",
            "Motorola", "Infinix", "Nokia", "Google Pixel", "Tecno", "ASUS", "Honor", "Lenovo",
            "Sony", "Huawei", "Micromax", "Lava", "Gionee", "BlackBerry", "HTC", "Intex", "Karbonn"
        ]
    },
    {
        "numb_id": 2,
        "name": "Mobile Accessories",
        "int_date": 30,
        "sub_categories": ["Mobile", "Tablets"]
    },
    {
        "numb_id": 3,
        "name": "Tablets",
        "int_date": 30,
        "sub_categories": ["iPads", "Other Tablets", "Samsung"]
    },
    {
        "numb_id": 4,
        "name": "Electronics & Appliances",
        "int_date": 60,
        "sub_categories": [
            "TVs, Video - Audio", "Computers & Laptops", "Kitchen & Other Appliances", "Fridges",
            "Cameras & Lenses", "Washing Machines", "Computer Accessories", "Games & Entertainment",
            "ACs", "Hard Disks, Printers & Monitors"
        ]
    },
    {
        "numb_id": 5,
        "name": "Properties",
        "int_date": 80,
        "sub_categories": [
            "House & Villa", "Flats / Apartments", "Independent / Builder Floors", "Farm House",
            "Lands & Plots - For Sale", "Lands & Plots - For Rent",
            "Shops & Offices - For Rent", "PG & Guest Houses", "Shops & Offices - For Sale"
        ]
    },
    {
        "numb_id": 6,
        "name": "Cars",
        "int_date": 70,
        "sub_categories": [
            "Maruti Suzuki", "Hyundai", "Mahindra", "Honda", "Tata", "Toyota", "Ford", "Volkswagen",
            "Renault", "Chevrolet", "Skoda", "Mercedes-Benz", "BMW", "Nissan", "Kia", "Datsun", "Fiat",
            "Audi", "Jeep", "MG", "Land Rover", "Mitsubishi", "Volvo", "Jaguar", "Force Motors", "Ashok Leyland",
            "Mini", "Porsche", "Isuzu", "Eicher Polaris", "Ambassador", "Mahindra Renault", "Ssangyong",
            "Lexus", "BYD", "DC", "Opel", "Rolls-Royce", "Premier", "Mazda", "Lamborghini", "Daewoo", "Maserati", "Bentley"
        ]
    },
    {
        "numb_id": 7,
        "name": "Furniture",
        "int_date": 40,
        "sub_categories": [
            "Sofa & Dining", "Other Household Items", "Beds & Wardrobes",
            "Home Decor & Garden", "Kids Furniture"
        ]
    },
    {
        "numb_id": 8,
        "name": "Bikes",
        "int_date": 50,
        "sub_categories": [
            "Bajaj", "Royal Enfield", "Hero", "Yamaha", "Honda", "TVS", "Hero Honda",
            "Other Brands", "KTM", "Suzuki", "Scooters - Honda", "Scooters - TVS",
            "Scooters - Hero", "Scooters - Other Brands", "Scooters - Suzuki", "Scooters - Bajaj",
            "Scooters - Mahindra", "Bicycles - Other Brands", "Bicycles - Hero", "Bicycles - Hercules",
            "Spare Parts"
        ]
    },
    {
        "numb_id": 9,
        "name": "Jobs",
        "int_date": 50,
        "sub_categories": [
            "Other Jobs", "Sales & Marketing", "Delivery & Collection", "Data entry & Back office",
            "BPO & Telecaller", "Cook", "Driver", "Office Assistant", "Receptionist & Front office",
            "Teacher", "Operator & Technician", "Accountant", "Hotel & Travel Executive",
            "IT Engineer & Developer", "Designer"
        ]
    },
    {
        "numb_id": 10,
        "name": "Commercial Vehicles & Spares",
        "int_date": 80,
        "sub_categories": [
            "Others", "Trucks", "Modified Jeeps", "Pick-up vans / Pick-up trucks", "Tractors",
            "Taxi Cabs", "Auto-rickshaws & E-rickshaws", "Heavy Machinery", "Buses", "Scrap Cars",
            "Spare Parts", "Wheels & Tyres", "Audio & Other Accessories"
        ]
    },
    {
        "numb_id": 11,
        "name": "Books, Sports & Hobbies",
        "int_date": 30,
        "sub_categories": [
            "Gym & Fitness", "Books", "Other Hobbies", "Sports Equipment", "Musical Instruments"
        ]
    },
    {
        "numb_id": 12,
        "name": "Fashion",
        "int_date": 30,
        "sub_categories": ["Men", "Women", "Kids"]
    },
    {
        "numb_id": 13,
        "name": "Services",
        "int_date": 40,
        "sub_categories": [
            "Other Services", "Electronics Repair & Services", "Education & Classes",
            "Health & Beauty", "Tours & Travel"
        ]
    },
    {
        "numb_id": 14,
        "name": "Pets",
        "int_date": 30,
        "sub_categories": ["Pet Food & Accessories"]
    }
]

# Processed CATEGORIES_DATA with sub-categories including numb_id
CATEGORIES_DATA = []
for category in _ORIGINAL_CATEGORIES_DATA:
    # Add numb_id to each sub-category
    sub_categories_with_ids = []
    
    for sub_cat in category["sub_categories"]:
        sub_categories_with_ids.append({
            "name": sub_cat,
            "numb_id": sub_cat_numb_id_counter
        })
        sub_cat_numb_id_counter += 1
    
    # Add the modified category to CATEGORIES_DATA
    CATEGORIES_DATA.append({
        "numb_id": category["numb_id"],
        "name": category["name"],
        "int_date": category["int_date"],
        "sub_categories": sub_categories_with_ids
    })

async def initialize_categories_collection(db: AsyncIOMotorDatabase):
    # Insert into categories collection
    existing_cats = await db.categories.count_documents({})
    if existing_cats == 0:
        categories_only = [
            {
                "numb_id": cat["numb_id"],
                "name": cat["name"],
                "int_date": cat["int_date"]
            }
            for cat in CATEGORIES_DATA
        ]
        await db.categories.insert_many(categories_only)
        print("[INIT] Inserted categories.")
    else:
        print("[INIT] Categories collection already initialized.")

    # Insert into sub_categories collection in new format
    existing_subs = await db.sub_categories.count_documents({})
    if existing_subs == 0:
        individual_docs = []
        for cat in CATEGORIES_DATA:
            for sub_cat in cat["sub_categories"]:
                category = await db.categories.find_one({"numb_id": cat["numb_id"]})
                individual_docs.append({
                    "parent_id": cat["numb_id"],
                    "name": sub_cat["name"],
                    "category_id": category["_id"],
                    "numb_id": sub_cat["numb_id"]
                })
        await db.sub_categories.insert_many(individual_docs)
        print("[INIT] Inserted individual sub-categories.")
    else:
        print("[INIT] Sub-categories collection already initialized.")