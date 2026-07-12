import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import Category, Coupon, MenuItem, RestaurantSettings


class Command(BaseCommand):
    help = "Seeds database with 200+ unique Telugu food items, coupons, and restaurant settings"

    def handle(self, *args, **options):
        self.stdout.write("Clearing existing menu items and categories...")
        MenuItem.objects.all().delete()
        Category.objects.all().delete()
        Coupon.objects.all().delete()
        RestaurantSettings.objects.all().delete()

        # Create default superuser if none exists
        from django.contrib.auth.models import User

        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                "Creating default superuser (admin / admin123)..."
            )
            User.objects.create_superuser(
                "admin", "admin@example.com", "admin123"
            )

        self.stdout.write("Seeding Telugu categories...")

        # 1. Create target categories
        cats = {}
        category_data = [
            (
                "Breakfast",
                "bi-egg-fried",
                "Traditional breakfast crepes, idlis, and morning delicacies.",
            ),
            (
                "Veg",
                "bi-leaf-fill",
                "Pure vegetarian traditional curries and dry fries.",
            ),
            (
                "Non Veg",
                "bi-fire",
                "Spicy country chicken, mutton masalas, and local meat signature items.",
            ),
            (
                "Seafood",
                "bi-water",
                "Nellore style fish pulusu, spiced prawns, and marine foods.",
            ),
            (
                "Snacks",
                "bi-cookie",
                "Local street foods, deep fried bajjis, and evening bites.",
            ),
            (
                "Rice",
                "bi-list-ul",
                "Pulao, curd rice, lemon rice, and bagara rice options.",
            ),
            (
                "Biryani",
                "bi-award-fill",
                "Hyderabadi dum biryanis, pot biryanis, and special local masalas.",
            ),
            (
                "Desserts",
                "bi-cake2-fill",
                "Sweet local pootharekulu, bobbatlu, and traditional festival desserts.",
            ),
            (
                "Beverages",
                "bi-cup-hot",
                "Refreshing sharbaths, lassis, and hot spiced filter coffee.",
            ),
        ]

        for name, icon, desc in category_data:
            cat, _ = Category.objects.get_or_create(
                name=name, defaults={"icon": icon, "description": desc}
            )
            cats[name] = cat

        # Districts and origins mapping
        districts = [
            "Guntur",
            "Nellore",
            "Kurnool",
            "Kadapa",
            "Anantapur",
            "Chittoor",
            "Vizag",
            "Vijayawada",
            "East Godavari",
            "West Godavari",
            "Hyderabad",
            "Warangal",
            "Nalgonda",
            "Khammam",
            "Karimnagar",
        ]
        origins = [
            "Andhra Pradesh",
            "Telangana",
            "Rayalaseema",
            "Uttarandhra",
            "Coastal Andhra",
            "Nizam Heritage",
        ]

        # Dynamic image selection helper with distinct image pools, keyword matching, and parameter variation (view/color shifts)
        def get_image_url_for_item(category_name, item_name, index):
            name_lower = item_name.lower()

            # Sub-type keyword to Unsplash ID mapping with MULTIPLE photo options per keyword to avoid repetition
            keyword_mapping = {
                "dosa": [
                    "photo-1668236543090-82eba5ee5976",  # Dosa 1
                    "photo-1589301760014-d929f3979dbc",  # Dosa 2/South Indian Platter
                ],
                "idli": [
                    "photo-1589301760014-d929f3979dbc",
                    "photo-1621972750749-0fbb1abb7736",
                ],
                "wada": [
                    "photo-1626132647523-66f5bf380027",
                    "photo-1589301760014-d929f3979dbc",
                ],
                "vada": [
                    "photo-1626132647523-66f5bf380027",
                    "photo-1589301760014-d929f3979dbc",
                ],
                "pesarattu": [
                    "photo-1668236543090-82eba5ee5976",
                    "photo-1621972750749-0fbb1abb7736",
                ],
                "puri": ["photo-1627308595229-7830a5c91f9f"],
                "bonda": ["photo-1589301760014-d929f3979dbc"],
                "punugulu": ["photo-1589301760014-d929f3979dbc"],
                "vankaya": [
                    "photo-1626777552726-4a6b54c97e46",  # eggplant
                    "photo-1560684352-8497838a2229",  # rich curry
                ],
                "paneer": [
                    "photo-1631452180519-c014fe946bc7",
                    "photo-1606755962773-d324e0a13086",
                ],
                "dal": [
                    "photo-1610192244261-3f33de3f55e4",
                    "photo-1546833999-b9f581a1996d",
                ],
                "pappu": [
                    "photo-1610192244261-3f33de3f55e4",
                    "photo-1546833999-b9f581a1996d",
                ],
                "kodi": [
                    "photo-1603894584373-5ac82b2ae398",  # chicken
                    "photo-1624300629298-e9de39c13be5",
                    "photo-1567306226416-28f0efdc88ce",
                ],
                "chicken": [
                    "photo-1603894584373-5ac82b2ae398",
                    "photo-1624300629298-e9de39c13be5",
                    "photo-1567306226416-28f0efdc88ce",
                ],
                "mutton": [
                    "photo-1534422298391-e4f8c172dddb",
                    "photo-1608039829572-78524f79c4c7",
                    "photo-1555939594-58d7cb561ad1",
                ],
                "chepala": [
                    "photo-1535401991746-da3d9055713e",  # fish
                    "photo-1519708227418-c8fd9a32b7a2",
                ],
                "fish": [
                    "photo-1535401991746-da3d9055713e",
                    "photo-1519708227418-c8fd9a32b7a2",
                ],
                "royyala": [
                    "photo-1599084993091-1cb5c0721cc6",  # prawns
                    "photo-1555939594-58d7cb561ad1",
                ],
                "prawn": [
                    "photo-1599084993091-1cb5c0721cc6",
                    "photo-1555939594-58d7cb561ad1",
                ],
                "shrimp": ["photo-1599084993091-1cb5c0721cc6"],
                "peethala": ["photo-1599084993091-1cb5c0721cc6"],  # crab
                "crab": ["photo-1599084993091-1cb5c0721cc6"],
                "mirchi": [
                    "photo-1599487488170-d11ec9c172f0",
                    "photo-1476224203421-9ac39bcb3327",
                ],
                "bajji": [
                    "photo-1599487488170-d11ec9c172f0",
                    "photo-1476224203421-9ac39bcb3327",
                ],
                "samosa": [
                    "photo-1476224203421-9ac39bcb3327",  # Samosas / Fried snacks
                    "photo-1593560708920-61dd98c46a4e",  # Indian snacks
                ],
                "biryani": [
                    "photo-1633945274405-b6c8069047b0",  # Biryani 1
                    "photo-1563379091339-03b21ab4a4f8",  # Biryani 2/Pulao
                    "photo-1617196034183-421b4917c92d",  # Biryani 3
                ],
                "pulao": [
                    "photo-1563379091339-03b21ab4a4f8",
                    "photo-1596797038530-2c107229654b",
                ],
                "rice": [
                    "photo-1596797038530-2c107229654b",
                    "photo-1541832676-9b763b0239ab",
                    "photo-1621972750749-0fbb1abb7736",
                ],
                "bagara": ["photo-1596797038530-2c107229654b"],
                "laddu": [
                    "photo-1587314168485-3236d6710814",
                    "photo-1606313564200-e75d5e30476c",
                ],
                "halwa": [
                    "photo-1587314168485-3236d6710814",
                    "photo-1606313564200-e75d5e30476c",
                ],
                "pootharekulu": [
                    "photo-1606313564200-e75d5e30476c",
                    "photo-1617396900799-f4ec2b43c7ae",
                ],
                "bobbatlu": [
                    "photo-1606313564200-e75d5e30476c",
                    "photo-1617396900799-f4ec2b43c7ae",
                ],
                "meetha": [
                    "photo-1517433367423-c7e5b0f35086",
                    "photo-1617396900799-f4ec2b43c7ae",
                ],
                "sharbath": ["photo-1513558161293-cdaf765ed2fd"],
                "coffee": ["photo-1514432324607-a09d9b4aefdd"],
                "chai": ["photo-1576092768241-dec231879fc3"],
                "tea": ["photo-1576092768241-dec231879fc3"],
                "buttermilk": ["photo-1505576399279-565b52d4ac71"],
                "lassi": ["photo-1513558161293-cdaf765ed2fd"],
            }

            photo_id = None
            for kw, pids in keyword_mapping.items():
                if kw in name_lower:
                    # Select from options list based on index to avoid identical matches
                    photo_id = pids[index % len(pids)]
                    break

            # Diverse image pools per category if no keyword matches (using verified active IDs)
            if not photo_id:
                category_pools = {
                    "Breakfast": [
                        "photo-1668236543090-82eba5ee5976",  # Dosa
                        "photo-1589301760014-d929f3979dbc",  # Idli
                        "photo-1626132647523-66f5bf380027",  # Vada
                        "photo-1627308595229-7830a5c91f9f",  # Puri
                        "photo-1610192244261-3f33de3f55e4",  # Healthy crepe
                        "photo-1621972750749-0fbb1abb7736",  # Upma thali
                        "photo-1505253716362-afaea1d3d1af",  # Roti
                        "photo-1506084868230-bb9d95c24759",  # Oats/grain breakfast
                        "photo-1498837167922-ddd27525d352",  # Breakfast table
                    ],
                    "Veg": [
                        "photo-1626777552726-4a6b54c97e46",  # Eggplant curry
                        "photo-1546833999-b9f581a1996d",  # Yellow Dal
                        "photo-1610192244261-3f33de3f55e4",  # Dal Tadka
                        "photo-1628294895950-9805252327bc",  # Chana Masala
                        "photo-1631452180519-c014fe946bc7",  # Paneer
                        "photo-1512621776951-a57141f2eefd",  # Salad bowl veg
                        "photo-1606755962773-d324e0a13086",  # Aloo Gobhi
                        "photo-1560684352-8497838a2229",  # Creamy Curry
                        "photo-1490645935967-10de6ba17061",  # Healthy green bowl
                    ],
                    "Non Veg": [
                        "photo-1603894584373-5ac82b2ae398",  # Chicken curry
                        "photo-1534422298391-e4f8c172dddb",  # Mutton dry roast
                        "photo-1624300629298-e9de39c13be5",  # Dry chicken fry
                        "photo-1565557623262-b51c2513a641",  # Tandoori kebabs
                        "photo-1608039829572-78524f79c4c7",  # Lamb Rogan Josh
                        "photo-1567306226416-28f0efdc88ce",  # Chicken tikka curry
                        "photo-1555939594-58d7cb561ad1",  # Tandoori seekh skewers
                    ],
                    "Seafood": [
                        "photo-1535401991746-da3d9055713e",  # Fish curry
                        "photo-1519708227418-c8fd9a32b7a2",  # Fish shallow fry
                        "photo-1455619452474-d2be8b1e70cd",  # Prawns/Seafood curry
                        "photo-1599084993091-1cb5c0721cc6",  # Crab curry
                        "photo-1565557623262-b51c2513a641",  # Tandoori prawns
                    ],
                    "Snacks": [
                        "photo-1599487488170-d11ec9c172f0",  # Mirchi bajji
                        "photo-1476224203421-9ac39bcb3327",  # Samosas / Fried snacks
                        "photo-1617196034183-421b4917c92d",  # Indian street snacks
                    ],
                    "Rice": [
                        "photo-1596797038530-2c107229654b",  # Bagara rice
                        "photo-1541832676-9b763b0239ab",  # Steamed rice bowl
                        "photo-1621972750749-0fbb1abb7736",  # South Indian rice meal
                        "photo-1563379091339-03b21ab4a4f8",  # Lemon yellow rice
                    ],
                    "Biryani": [
                        "photo-1633945274405-b6c8069047b0",  # Chicken Biryani
                        "photo-1563379091339-03b21ab4a4f8",  # Mutton Biryani
                        "photo-1626777552726-4a6b54c97e46",  # Prawn/Veg Biryani
                        "photo-1631452180519-c014fe946bc7",  # Paneer Biryani
                        "photo-1555939594-58d7cb561ad1",  # Meat Biryani
                    ],
                    "Desserts": [
                        "photo-1587314168485-3236d6710814",  # Gulab jamun
                        "photo-1517433367423-c7e5b0f35086",  # Kheer/Payasam
                        "photo-1606313564200-e75d5e30476c",  # Double Ka Meetha
                        "photo-1625398407796-82650a8c135f",  # Qubani Ka Meetha
                        "photo-1588195538326-c5b1e9f80a1b",  # Cake slice
                        "photo-1617396900799-f4ec2b43c7ae",  # Chocolate Sweet
                        "photo-1484723091739-30a097e8f929",  # French toast/honey
                    ],
                    "Beverages": [
                        "photo-1576092768241-dec231879fc3",  # Irani Chai
                        "photo-1514432324607-a09d9b4aefdd",  # Filter Coffee
                        "photo-1513558161293-cdaf765ed2fd",  # Sharbath/Lassi
                        "photo-1505576399279-565b52d4ac71",  # Spiced buttermilk
                    ],
                }
                pool = category_pools.get(
                    category_name, ["photo-1546069901-ba9599a7e63c"]
                )
                photo_id = pool[index % len(pool)]

            # Mirroring: Horizontal flip is safe and keeps food right side up
            flip_param = "&flip=h" if (index % 2 == 1) else ""

            # Cache buster and unique resource identifier
            sig_param = f"&sig={index}"

            return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w=600&q=80{flip_param}{sig_param}"

        # 2. Add signature items (around 45 specific items to ensure high quality)
        signature_items = [
            # Breakfast
            (
                "Nellore Ghee Karam Dosa",
                "Breakfast",
                90,
                "Nellore",
                "Rayalaseema",
                "Crisp thin crepe smeared with local spicy red chili-garlic paste, topped with pure cow ghee.",
            ),
            (
                "Pesarattu Upma",
                "Breakfast",
                110,
                "Vijayawada",
                "Coastal Andhra",
                "Spiced green gram batter crepe stuffed with traditional hot ginger semolina upma.",
            ),
            (
                "Kurnool Uggani Bajji",
                "Breakfast",
                80,
                "Kurnool",
                "Rayalaseema",
                "Puffed rice seasoned with roasted chickpea powder and onions, served with hot Mirchi Bajji.",
            ),
            (
                "Madugula Halwa Dosa",
                "Breakfast",
                120,
                "Vizag",
                "Uttarandhra",
                "Sweet, unique crepe variation served with cardamoms and traditional sweet halwa smear.",
            ),
            (
                "Guntur Onion Rava Dosa",
                "Breakfast",
                95,
                "Guntur",
                "Coastal Andhra",
                "Semolina batter crepe topped with minced red onions, green chilies, and cumin seeds.",
            ),
            # Veg
            (
                "Gutti Vankaya Curry",
                "Veg",
                240,
                "East Godavari",
                "Coastal Andhra",
                "Tender baby eggplants stuffed with a rich roasted peanut, sesame, and coconut masala paste.",
            ),
            (
                "Gongura Pappu",
                "Veg",
                180,
                "Guntur",
                "Coastal Andhra",
                "Creamy pigeon pea lentils boiled with tangy sorrel leaves (Gongura), garlic, and red chilies.",
            ),
            (
                "Nellore Bendakaya Pulusu",
                "Veg",
                210,
                "Nellore",
                "Coastal Andhra",
                "Tender lady fingers simmered in a tangy sweet tamarind sauce with onions and curry leaves.",
            ),
            (
                "Anantapur Tomato Pappu",
                "Veg",
                160,
                "Anantapur",
                "Rayalaseema",
                "Yellow split lentils cooked with juicy country tomatoes and tempered with mustard and garlic.",
            ),
            (
                "Kandhi Podi Ghee Rice Combo",
                "Veg",
                190,
                "Kadapa",
                "Rayalaseema",
                "Authentic roasted split-pea lentil powder served with steamed rice and hot melted ghee.",
            ),
            # Non Veg
            (
                "Gongura Chicken Curry",
                "Non Veg",
                320,
                "Guntur",
                "Andhra Pradesh",
                "Tangy country style chicken cooked in sorrel leaves paste and traditional spices.",
            ),
            (
                "Natu Kodi Pulusu",
                "Non Veg",
                360,
                "Chittoor",
                "Rayalaseema",
                "Fiery country chicken slow-cooked in a spicy rustic gravy, best paired with Ragi Sankati.",
            ),
            (
                "Kurnool Mutton Fry",
                "Non Veg",
                420,
                "Kurnool",
                "Rayalaseema",
                "Tender mutton chunks dry-roasted with fresh crushed black pepper, garlic, and coriander leaves.",
            ),
            (
                "Warangal Kodi Vepudu",
                "Non Veg",
                310,
                "Warangal",
                "Telangana",
                "Dry chicken fry marinated in local red chili paste and pan-roasted with curry leaves.",
            ),
            (
                "Telangana Mutton Curry",
                "Non Veg",
                390,
                "Karimnagar",
                "Telangana",
                "Rich, spicy mutton gravy flavored with stone flower, cinnamon, and dry coconut powder.",
            ),
            # Seafood
            (
                "Nellore Chepala Pulusu",
                "Seafood",
                380,
                "Nellore",
                "Coastal Andhra",
                "Fish cutlets slow-cooked in a spicy, extremely tangy tamarind gravy with raw green mango.",
            ),
            (
                "Bhimavaram Royyala Vepudu",
                "Seafood",
                350,
                "West Godavari",
                "Coastal Andhra",
                "Juicy fresh-water prawns fried with ground green chilies, cashew nuts, and garam masala.",
            ),
            (
                "Vizag Chepala Vepudu",
                "Seafood",
                340,
                "Vizag",
                "Uttarandhra",
                "Fish steaks marinated in ginger-garlic paste and shallow-fried with local spices.",
            ),
            (
                "Konaseema Peethala Pulusu",
                "Seafood",
                450,
                "East Godavari",
                "Coastal Andhra",
                "Spiced mud crab curry simmered in tamarind sauce and seasoned with fresh coriander.",
            ),
            (
                "Godavari Royyala Iguru",
                "Seafood",
                360,
                "West Godavari",
                "Coastal Andhra",
                "Semi-dry prawn masala cooked with red onions, curry leaves, and local masala paste.",
            ),
            # Snacks
            (
                "Mirchi Bajji",
                "Snacks",
                60,
                "Guntur",
                "Andhra Pradesh",
                "Long green chilies stuffed with tangy ajwain and lemon juice, batter-fried until crisp.",
            ),
            (
                "Mysore Bonda",
                "Snacks",
                70,
                "Hyderabad",
                "Nizam Heritage",
                "Fluffy deep-fried fritters made of fermented flour and yogurt, served with coconut chutney.",
            ),
            (
                "Vijayawada Punugulu",
                "Snacks",
                50,
                "Vijayawada",
                "Coastal Andhra",
                "Bite-sized fritters made from fermented idli batter, fried golden brown.",
            ),
            (
                "Guntur Karampodi Bajji",
                "Snacks",
                80,
                "Guntur",
                "Coastal Andhra",
                "Cut mirchi bajjis sprinkled with roasted lentil chili powder and chopped onions.",
            ),
            (
                "Hyderabad Samosa",
                "Snacks",
                60,
                "Hyderabad",
                "Nizam Heritage",
                "Crispy pockets filled with spiced minced onions and green peas.",
            ),
            # Rice
            (
                "Bagara Rice",
                "Rice",
                160,
                "Hyderabad",
                "Telangana",
                "Basmati rice flavored with mint leaves, coriander, whole spices, and cooked in ghee.",
            ),
            (
                "Nellore Curd Rice",
                "Rice",
                120,
                "Nellore",
                "Andhra Pradesh",
                "Steamed rice mashed with fresh yogurt, tempered with mustard seeds, curry leaves, and ginger.",
            ),
            (
                "Chittoor Lemon Rice",
                "Rice",
                140,
                "Chittoor",
                "Andhra Pradesh",
                "Zesty yellow rice tossed with lemon juice, roasted peanuts, green chilies, and curry leaves.",
            ),
            (
                "Godavari Coconut Rice",
                "Rice",
                170,
                "East Godavari",
                "Coastal Andhra",
                "Rice cooked in fresh coconut milk and tempered with cashews and mustard seeds.",
            ),
            (
                "Rayalaseema Ragi Sankati",
                "Rice",
                130,
                "Kadapa",
                "Rayalaseema",
                "Healthy cooked balls made of finger millet and rice, traditionally eaten with chicken pulusu.",
            ),
            # Biryani
            (
                "Hyderabadi Chicken Dum Biryani",
                "Biryani",
                290,
                "Hyderabad",
                "Nizam Heritage",
                "Fragrant Basmati rice and marinated chicken slow-cooked on dum with saffron and herbs.",
            ),
            (
                "Ulavacharu Chicken Biryani",
                "Biryani",
                320,
                "Vijayawada",
                "Coastal Andhra",
                "Fragrant rice cooked with thick brown horsegram soup and tender chicken pieces.",
            ),
            (
                "Gongura Mutton Biryani",
                "Biryani",
                380,
                "Guntur",
                "Andhra Pradesh",
                "Basmati biryani layered with tangy sorrel leaf mutton masala.",
            ),
            (
                "Bhimavaram Prawns Biryani",
                "Biryani",
                340,
                "West Godavari",
                "Coastal Andhra",
                "Fragrant rice layered with spiced pan-roasted Godavari prawns.",
            ),
            (
                "Kaju Paneer Biryani",
                "Biryani",
                260,
                "Kurnool",
                "Rayalaseema",
                "Vegetarian basmati rice layered with fried cashews, paneer cubes, and aromatic masalas.",
            ),
            # Desserts
            (
                "Atreyapuram Pootharekulu",
                "Desserts",
                120,
                "East Godavari",
                "Coastal Andhra",
                "Paper-thin sugar sheets made of rice starch, rolled with sugar dust, cardamoms, and ghee.",
            ),
            (
                "Nellore Bobbatlu",
                "Desserts",
                100,
                "Nellore",
                "Andhra Pradesh",
                "Sweet flatbreads stuffed with sweet chana dal and cardamom paste, roasted with ghee.",
            ),
            (
                "Double Ka Meetha",
                "Desserts",
                90,
                "Hyderabad",
                "Nizam Heritage",
                "Crispy fried bread slices soaked in sweet saffron milk syrup and garnished with pistachios.",
            ),
            (
                "Qubani Ka Meetha",
                "Desserts",
                110,
                "Hyderabad",
                "Nizam Heritage",
                "Traditional dry apricot compote topped with fresh cream or vanilla ice cream.",
            ),
            (
                "Bandar Laddu",
                "Desserts",
                80,
                "Vijayawada",
                "Coastal Andhra",
                "Smooth melt-in-mouth sweet balls made of roasted chickpea flour, ghee, and jaggery.",
            ),
            # Beverages
            (
                "Nannari Sharbath",
                "Beverages",
                50,
                "Kadapa",
                "Rayalaseema",
                "Cooling summer drink made of sarsaparilla root syrup, lemon juice, and basil seeds.",
            ),
            (
                "Ragi Malt Drink",
                "Beverages",
                40,
                "Anantapur",
                "Rayalaseema",
                "Nutritious morning beverage made of finger millet flour, buttermilk, and chopped onions.",
            ),
            (
                "Spiced Buttermilk",
                "Beverages",
                30,
                "Guntur",
                "Andhra Pradesh",
                "Chilled churned curd diluted with water, ginger, green chilies, cilantro, and curry leaves.",
            ),
            (
                "Hyderabad Irani Chai",
                "Beverages",
                35,
                "Hyderabad",
                "Nizam Heritage",
                "Thick, creamy milk tea slow-brewed on dam, served with salt biscuits.",
            ),
            (
                "Nellore Filter Coffee",
                "Beverages",
                40,
                "Nellore",
                "Andhra Pradesh",
                "Strong chicory-mixed coffee dripped from brass filter, frothed with hot milk.",
            ),
        ]

        self.stdout.write("Registering signature dishes...")
        for idx, (name, cat_name, price, dist, orig, desc) in enumerate(
            signature_items
        ):
            cat = cats[cat_name]
            MenuItem.objects.create(
                name=name,
                category=cat,
                price=price,
                is_veg=(
                    cat_name
                    in [
                        "Breakfast",
                        "Veg",
                        "Snacks",
                        "Rice",
                        "Desserts",
                        "Beverages",
                    ]
                    and "Chicken" not in name
                    and "Mutton" not in name
                    and "Kodi" not in name
                    and "Prawns" not in name
                ),
                is_spicy=(
                    "Spicy" in name
                    or "Chili" in name
                    or "Karam" in name
                    or "Fiery" in name
                    or cat_name in ["Non Veg", "Seafood"]
                ),
                is_available=True,
                rating=round(random.uniform(4.5, 5.0), 1),
                is_chef_special=(
                    "Special" in name
                    or "Signature" in name
                    or "Nellore" in name
                ),
                is_today_offer=(random.choice([True, False, False])),
                is_popular=True,
                is_recommended=True,
                origin=orig,
                district=dist,
                state="Andhra Pradesh" if orig != "Telangana" else "Telangana",
                image_url=get_image_url_for_item(cat_name, name, idx),
            )

        # 3. Generate remaining items to reach 200+ unique entries
        self.stdout.write(
            "Generating remaining unique variations to reach 200+ items..."
        )

        # We will dynamically construct combinations
        # We need approximately 160 more items
        items_needed = 160
        created_count = len(signature_items)

        prefixes = [
            "Ghee",
            "Butter",
            "Onion",
            "Spicy",
            "Special",
            "Masala",
            "Karam",
            "Chettinad",
            "Kaju",
            "Paneer",
            "Egg",
            "Jeera",
            "Methi",
            "Mirchi",
            "Andhra",
            "Rayalaseema",
            "Telangana",
        ]
        bases = {
            "Breakfast": [
                "Idli",
                "Dosa",
                "Wada",
                "Puri",
                "Uthappam",
                "Pesarattu",
                "Upma",
            ],
            "Veg": [
                "Pappu",
                "Vepudu",
                "Iguru",
                "Kura",
                "Pulusu",
                "Charu",
                "Gongura Curry",
            ],
            "Non Veg": [
                "Kodi Kura",
                "Mutton Curry",
                "Keema Fry",
                "Natu Kodi Roast",
                "Wings",
                "Dry Fry",
            ],
            "Seafood": [
                "Chepala Pulusu",
                "Royyala Fry",
                "Fish Tikka",
                "Peethala Iguru",
                "Prawn Masala",
            ],
            "Snacks": [
                "Bajji",
                "Pakodi",
                "Punugulu",
                "Bonda",
                "Samosa",
                "Cutlet",
            ],
            "Rice": ["Rice", "Biryani Rice", "Pulao", "Khichdi", "Sankati"],
            "Biryani": [
                "Biryani",
                "Dum Biryani",
                "Pot Biryani",
                "Fry Piece Biryani",
            ],
            "Desserts": [
                "Laddu",
                "Halwa",
                "Payasam",
                "Kheer",
                "Kaja",
                "Ariselu",
            ],
            "Beverages": [
                "Tea",
                "Coffee",
                "Sharbath",
                "Lassi",
                "Milkshake",
                "Buttermilk",
            ],
        }

        while created_count < 210:
            cat_name = random.choice(list(cats.keys()))
            prefix = random.choice(prefixes)
            base = random.choice(bases[cat_name])

            # Avoid redundant classifications
            is_non_veg_cat = cat_name in ["Non Veg", "Seafood"]
            is_non_veg_name = (
                "Kodi" in prefix
                or "Mutton" in prefix
                or "Egg" in prefix
                or "Fish" in prefix
            )

            name = f"{prefix} {base}"

            # Ensure uniqueness
            if MenuItem.objects.filter(name=name).exists():
                continue

            cat = cats[cat_name]
            dist = random.choice(districts)
            orig = random.choice(origins)

            price = random.choice(range(50, 450, 10))
            rating = round(random.uniform(4.0, 5.0), 1)

            desc = f"A signature gourmet preparation of {name.lower()}, sourced traditionally and prepared with authentic local spices in {dist} style."

            MenuItem.objects.create(
                name=name,
                category=cat,
                price=price,
                is_veg=not (is_non_veg_cat or is_non_veg_name),
                is_spicy=(random.choice([True, False])),
                is_available=True,
                rating=rating,
                is_chef_special=(random.choice([True, False, False])),
                is_today_offer=(random.choice([True, False, False, False])),
                is_popular=(random.choice([True, False])),
                is_recommended=(random.choice([True, False])),
                origin=orig,
                district=dist,
                state="Andhra Pradesh" if orig != "Telangana" else "Telangana",
                image_url=get_image_url_for_item(
                    cat_name, name, created_count
                ),
                preparation_time=random.choice([10, 15, 20, 25, 30]),
                calories=random.choice([150, 220, 310, 420, 560, 680]),
                spice_level=random.choice(
                    ["MILD", "MEDIUM", "HOT", "EXTRA_HOT"]
                ),
                is_today_special=random.choice([True, False, False, False]),
                is_new_arrival=random.choice(
                    [True, False, False, False, False]
                ),
                is_trending=random.choice([True, False, False, False]),
            )
            created_count += 1

        self.stdout.write("Seeding coupons...")
        Coupon.objects.create(
            code="WELCOME15",
            discount_percent=15,
            active=True,
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_to=timezone.now() + timezone.timedelta(days=30),
        )
        Coupon.objects.create(
            code="GOURMET20",
            discount_percent=20,
            active=True,
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_to=timezone.now() + timezone.timedelta(days=30),
        )

        self.stdout.write("Seeding restaurant settings...")
        RestaurantSettings.objects.create(
            restaurant_name="V Restaurant",
            opening_hours="Mon - Fri: 11:00 AM - 11:00 PM, Sat - Sun: 10:00 AM - Midnight",
            happy_hours="04:00 PM - 07:00 PM",
            contact_phone="+91 7601098423",
            contact_email="vrestaurant@gmail.com",
            address="Tiruvuru, NTR District, Andhra Pradesh, India",
            whatsapp_number="+917601098423",
            google_maps_url="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3801.378945618195!2d80.6095033!3d17.1171896!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3a35ab5bcf41d2f7%3A0xe21262eb127c59!2sTiruvuru%2C%20Andhra%20Pradesh!5e0!3m2!1sen!2sin!4v1700000000000",
            delivery_charges=50.00,
            gst_percentage=5.00,
        )

        self.stdout.write("Seeding culinary blogs...")
        from apps.core.models import BlogPost
        BlogPost.objects.all().delete()

        BlogPost.objects.create(
            title="Secrets of Traditional Gongura Pickle",
            author="Chef V",
            content="Gongura (Roselle leaves) is a centerpiece of Andhra cuisine. In this article, Chef V shares the traditional process of harvesting and curing the leaves, selecting the local dried red chillies, and grinding the mixture using mortar and pestle to achieve the optimal rustic flavor profile that pairs beautifully with warm rice and ghee.",
            summary="An inside look at how V Restaurant prepares its signature Andhra Gongura pickle using traditional methods.",
            image_url="https://images.unsplash.com/photo-1546833999-b9f581a1996d",
        )
        BlogPost.objects.create(
            title="The Art of Perfect Hyderabadi Dum Biryani",
            author="Chef V",
            content="Dum cooking is an ancient technique where the pot is sealed with wheat dough, trapping steam inside. This allows the meat and basmati rice to cook slowly in their own juices, absorbing the rich cardamom, saffron, and mint spices. Explore our step-by-step cooking process that has been passed down for generations.",
            summary="Chef V outlines the slow-cooking principles and premium spices required to master the Hyderabadi Dum Biryani.",
            image_url="https://images.unsplash.com/photo-1633945274405-b6c8069047b0",
        )
        BlogPost.objects.create(
            title="Nellore Chepala Pulusu: A Tangy Masterpiece",
            author="Chef V",
            content="Nellore fish curry is widely celebrated for its rich tamarind base and raw mango chunks. In this guide, we detail how we source local fresh catch and simmer it in a clay pot, resulting in a tangy, hot broth that tastes even better when enjoyed the next day.",
            summary="A deep dive into Nellore style clay-pot fish curry seasoned with sour mangoes.",
            image_url="https://images.unsplash.com/photo-1535401991746-da3d9055713e",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded {created_count} Telugu food items and configurations!"
            )
        )
