import json
from pathlib import Path

roasters = [
    # India
    {"brand": "Blue Tokai Coffee Roasters", "estate": "Attikan Estate", "country": "India", "region": "Biligirirangana Hills", "process": "Washed", "roast_level": "Medium-Dark", "varietal": "SLN 9", "dripper": "Hario V60", "dose": 16.0, "water": 240.0, "temp": 90, "ratio": "1:15", "notes": "Dark chocolate, fig, roasted almond", "author": "Blue Tokai Barista Team", "url": "https://bluetokaicoffee.com/blogs/brewing-guides/v60-attikan-estate"},
    {"brand": "Blue Tokai Coffee Roasters", "estate": "Seethargundu Estate", "country": "India", "region": "Nelliyampathy", "process": "Natural", "roast_level": "Medium", "varietal": "Catimor", "dripper": "Hario V60", "dose": 15.0, "water": 240.0, "temp": 91, "ratio": "1:16", "notes": "Stewed berries, jaggery, milk chocolate", "author": "Blue Tokai Barista Team", "url": "https://bluetokaicoffee.com/blogs/brewing-guides/v60-seethargundu-estate"},
    {"brand": "Blue Tokai Coffee Roasters", "estate": "Riverdale Estate", "country": "India", "region": "Yercaud", "process": "Anaerobic", "roast_level": "Light-Medium", "varietal": "SLN 5B", "dripper": "Origami Dripper", "dose": 15.0, "water": 245.0, "temp": 93, "ratio": "1:16.3", "notes": "Tropical pineapple, rum raisin, passionfruit", "author": "Blue Tokai Innovation Lab", "url": "https://bluetokaicoffee.com/blogs/brewing-guides/origami-riverdale-anaerobic"},
    {"brand": "Blue Tokai Coffee Roasters", "estate": "Kalledevarapura Estate", "country": "India", "region": "Chikmagalur", "process": "Washed", "roast_level": "Medium", "varietal": "SLN 795", "dripper": "Kalita Wave", "dose": 15.0, "water": 250.0, "temp": 92, "ratio": "1:16.6", "notes": "Orange peel, caramel, mild hazelnut", "author": "Blue Tokai Barista Team", "url": "https://bluetokaicoffee.com/blogs/brewing-guides/kalita-kalledevarapura"},
    {"brand": "Subko Coffee Roasters", "estate": "Kerehaklu Estate", "country": "India", "region": "Aldur, Chikmagalur", "process": "Honey", "roast_level": "Light", "varietal": "SLN 9", "dripper": "Hario V60", "dose": 15.0, "water": 250.0, "temp": 94, "ratio": "1:16.6", "notes": "Apricot, raw wild honey, floral jasmine", "author": "Subko Brew Lab", "url": "https://subko.coffee/blogs/recipes/kerehaklu-v60-guide"},
    {"brand": "Subko Coffee Roasters", "estate": "Tat Tvam Asi Organic", "country": "India", "region": "Bababudangiri", "process": "Natural", "roast_level": "Light-Medium", "varietal": "Cauvery", "dripper": "Kalita Wave", "dose": 18.0, "water": 290.0, "temp": 92, "ratio": "1:16.1", "notes": "Blackberry jam, cocoa nibs, sweet tamarind", "author": "Subko Head of Quality", "url": "https://subko.coffee/blogs/recipes/tat-tvam-asi-kalita"},
    {"brand": "Subko Coffee Roasters", "estate": "Gungegiri Estate", "country": "India", "region": "Bababudangiri", "process": "Washed", "roast_level": "Medium", "varietal": "SLN 795", "dripper": "Origami Dripper", "dose": 15.0, "water": 240.0, "temp": 92, "ratio": "1:16", "notes": "Green apple, cane sugar, black tea", "author": "Subko Brew Lab", "url": "https://subko.coffee/blogs/recipes/gungegiri-origami"},
    {"brand": "Corridor Seven Coffee Roasters", "estate": "Ratnagiri Estate", "country": "India", "region": "Bababudangiri", "process": "Anaerobic Honey", "roast_level": "Light", "varietal": "Catuai", "dripper": "Hario V60", "dose": 15.0, "water": 250.0, "temp": 93, "ratio": "1:16.6", "notes": "Lychee, mango, elderflower, honey", "author": "Mithilesh Vazalwar", "url": "https://corridorseven.coffee/blogs/brew/ratnagiri-anaerobic-v60"},
    {"brand": "KC Roasters", "estate": "Kelagur Estate", "country": "India", "region": "Chikmagalur", "process": "Washed", "roast_level": "Medium", "varietal": "SLN 795", "dripper": "Hario V60", "dose": 16.0, "water": 250.0, "temp": 91, "ratio": "1:15.6", "notes": "Milk chocolate, brown sugar, toffee", "author": "KC Roasters Brew Bar", "url": "https://kcroasters.com/blogs/brewing/kelagur-v60"},
    {"brand": "Toffee Coffee Roasters", "estate": "Thogarihunkal Estate", "country": "India", "region": "Chikmagalur", "process": "Honey", "roast_level": "Medium-Dark", "varietal": "SLN 9", "dripper": "Clever Dripper", "dose": 18.0, "water": 270.0, "temp": 89, "ratio": "1:15", "notes": "Spiced chocolate, dark cherry, roasted walnut", "author": "Toffee Coffee Team", "url": "https://toffeecoffeeroasters.com/blogs/brew/thogarihunkal-clever"},

    # Ethiopia
    {"brand": "James Hoffmann", "estate": "Yirgacheffe Gedeb", "country": "Ethiopia", "region": "Yirgacheffe", "process": "Washed", "roast_level": "Light", "varietal": "Heirloom", "dripper": "Hario V60", "dose": 15.0, "water": 250.0, "temp": 96, "ratio": "1:16.6", "notes": "Bergamot, peach, floral jasmine, citrus", "author": "James Hoffmann", "url": "https://www.thegreatcoffeeadventure.com/james-hoffmann-better-1-cup-v60-ethiopia"},
    {"brand": "Square Mile Coffee Roasters", "estate": "Worka Sakaro", "country": "Ethiopia", "region": "Gedeb", "process": "Natural", "roast_level": "Light", "varietal": "Kurume, Dega", "dripper": "Hario V60", "dose": 15.0, "water": 250.0, "temp": 94, "ratio": "1:16.6", "notes": "Blueberry compote, lavender, honey sweetness", "author": "Square Mile QC Team", "url": "https://squaremilecoffee.com/brew-guides/v60-worka-sakaro"},
    {"brand": "Tim Wendelboe", "estate": "Kabira", "country": "Ethiopia", "region": "Sidama", "process": "Washed", "roast_level": "Light", "varietal": "74112, 74110", "dripper": "Hario V60", "dose": 14.0, "water": 250.0, "temp": 95, "ratio": "1:17.8", "notes": "Crisp lemongrass, white peach, jasmine", "author": "Tim Wendelboe", "url": "https://timwendelboe.no/brew-guides/v60-kabira-ethiopia"},
    {"brand": "Onyx Coffee Lab", "estate": "Hambela Wamena", "country": "Ethiopia", "region": "Guji", "process": "Natural", "roast_level": "Light", "varietal": "Heirloom", "dripper": "Kalita Wave", "dose": 18.0, "water": 300.0, "temp": 94, "ratio": "1:16.6", "notes": "Candied strawberry, nectarine, hibiscus", "author": "Lance Hedrick / Onyx", "url": "https://onyxcoffeelab.com/blogs/brewing-guides/hambela-natural-kalita"},
    {"brand": "Sey Coffee", "estate": "Bona Zuria", "country": "Ethiopia", "region": "Sidama", "process": "Washed", "roast_level": "Light", "varietal": "74110", "dripper": "Origami Dripper", "dose": 15.0, "water": 260.0, "temp": 97, "ratio": "1:17.3", "notes": "Orange blossom, black tea, apricot nectar", "author": "Sey Coffee Brew Bar", "url": "https://seycoffee.com/blogs/recipes/bona-zuria-origami"},
    {"brand": "Kurasu Kyoto", "estate": "Chelchele", "country": "Ethiopia", "region": "Yirgacheffe", "process": "Washed", "roast_level": "Light-Medium", "varietal": "Heirloom", "dripper": "Hario V60", "dose": 14.0, "water": 210.0, "temp": 92, "ratio": "1:15", "notes": "Lemon tea, floral, stone fruit sweetness", "author": "Kurasu Head Barista", "url": "https://kurasu.kyoto/blogs/brew-guide/v60-ethiopia-chelchele"},
    {"brand": "Coffee Collective", "estate": "Yukro", "country": "Ethiopia", "region": "Gera, Jimma", "process": "Washed", "roast_level": "Light", "varietal": "74110", "dripper": "Kalita Wave", "dose": 16.0, "water": 260.0, "temp": 94, "ratio": "1:16.2", "notes": "Lime zest, ginger, white blossom", "author": "Klaus Thomsen", "url": "https://coffeecollective.dk/brew-guide/kalita-yukro"},

    # Kenya
    {"brand": "Tim Wendelboe", "estate": "Kiamabara", "country": "Kenya", "region": "Nyeri", "process": "Washed", "roast_level": "Light", "varietal": "SL28, SL34", "dripper": "Hario V60", "dose": 15.0, "water": 250.0, "temp": 95, "ratio": "1:16.6", "notes": "Blackcurrant, red grapefruit, sparkling acidity", "author": "Tim Wendelboe", "url": "https://timwendelboe.no/brew-guides/kenya-kiamabara-v60"},
    {"brand": "Square Mile Coffee Roasters", "estate": "Gatomboya", "country": "Kenya", "region": "Nyeri", "process": "Washed", "roast_level": "Light", "varietal": "SL28", "dripper": "Chemex", "dose": 25.0, "water": 400.0, "temp": 94, "ratio": "1:16", "notes": "Tomato leaf, rhubarb, tart cherry, cane sugar", "author": "Square Mile QC Team", "url": "https://squaremilecoffee.com/brew-guides/chemex-gatomboya-kenya"},
    {"brand": "Onyx Coffee Lab", "estate": "Gachatha", "country": "Kenya", "region": "Nyeri", "process": "Washed", "roast_level": "Light", "varietal": "SL28, SL34, Ruiru 11", "dripper": "Hario V60", "dose": 16.0, "water": 260.0, "temp": 95, "ratio": "1:16.2", "notes": "Cranberry sauce, pink grapefruit, syrupy body", "author": "Onyx Coffee Lab", "url": "https://onyxcoffeelab.com/blogs/brewing-guides/gachatha-kenya-v60"},
    {"brand": "April Coffee Roasters", "estate": "Kamwangi", "country": "Kenya", "region": "Kirinyaga", "process": "Washed", "roast_level": "Light", "varietal": "SL28", "dripper": "Kalita Wave", "dose": 13.0, "water": 200.0, "temp": 92, "ratio": "1:15.4", "notes": "Cassis, blackcurrant, juicy sweet citric finish", "author": "Patrik Rolf", "url": "https://aprilcoffeeroasters.com/blogs/brew-guides/kamwangi-kenya-pour-over"},
    {"brand": "Gardelli Specialty Coffees", "estate": "Kagumoini", "country": "Kenya", "region": "Muranga", "process": "Washed", "roast_level": "Light", "varietal": "SL28, Batian", "dripper": "Origami Dripper", "dose": 15.0, "water": 255.0, "temp": 94, "ratio": "1:17", "notes": "Pomegranate, redcurrant, cane molasses", "author": "Rubens Gardelli", "url": "https://gardellicoffee.com/brew-guides/kagumoini-kenya-origami"},

    # Colombia
    {"brand": "Onyx Coffee Lab", "estate": "El Paraiso", "country": "Colombia", "region": "Cauca", "process": "Anaerobic Double Fermentation", "roast_level": "Light-Medium", "varietal": "Castillo", "dripper": "Hario V60", "dose": 15.0, "water": 250.0, "temp": 91, "ratio": "1:16.6", "notes": "Strawberry yoghurt, bubblegum, guava, cream", "author": "Diego Bermudez / Onyx", "url": "https://onyxcoffeelab.com/blogs/brewing-guides/el-paraiso-anaerobic-v60"},
    {"brand": "Sey Coffee", "estate": "La Palma y El Tucan", "country": "Colombia", "region": "Cundinamarca", "process": "Lactic Natural", "roast_level": "Light", "varietal": "Geisha", "dripper": "Origami Dripper", "dose": 15.0, "water": 260.0, "temp": 93, "ratio": "1:17.3", "notes": "Jasmine, bergamot, honeydew melon, creamy body", "author": "Sey Coffee Team", "url": "https://seycoffee.com/blogs/recipes/la-palma-geisha-origami"},
    {"brand": "Blue Bottle Coffee", "estate": "Tres Santos", "country": "Colombia", "region": "Huila", "process": "Washed", "roast_level": "Medium", "varietal": "Caturra, Colombia", "dripper": "Kalita Wave", "dose": 18.0, "water": 300.0, "temp": 92, "ratio": "1:16.6", "notes": "Red apple, caramel, milk chocolate, citrus", "author": "Blue Bottle Brew Guide", "url": "https://bluebottlecoffee.com/brew-guides/pour-over-tres-santos"},
    {"brand": "Counter Culture Coffee", "estate": "Finca San Jose", "country": "Colombia", "region": "Caldas", "process": "Washed", "roast_level": "Medium", "varietal": "Castillo", "dripper": "Hario V60", "dose": 15.0, "water": 250.0, "temp": 93, "ratio": "1:16.6", "notes": "Cane sugar, red apple, almond, cocoa", "author": "Counter Culture Training Center", "url": "https://counterculturecoffee.com/blogs/coffee-basics/san-jose-colombia-v60"},
    {"brand": "Sweet Maria's", "estate": "Inza Cauca Community", "country": "Colombia", "region": "Tierradentro, Cauca", "process": "Washed", "roast_level": "Light-Medium", "varietal": "Caturra, Typica", "dripper": "Clever Dripper", "dose": 20.0, "water": 320.0, "temp": 92, "ratio": "1:16", "notes": "Panela sugar, crisp apple, cherry, baking spice", "author": "Tom Owen", "url": "https://sweetmarias.com/brewing-guides/clever-dripper-inza-cauca"},

    # Guatemala
    {"brand": "Stumptown Coffee Roasters", "estate": "El Injerto", "country": "Guatemala", "region": "Huehuetenango", "process": "Washed", "roast_level": "Medium", "varietal": "Bourbon", "dripper": "Hario V60", "dose": 16.0, "water": 250.0, "temp": 92, "ratio": "1:15.6", "notes": "Milk chocolate, orange zest, toasted praline", "author": "Stumptown Roasters", "url": "https://stumptowncoffee.com/brew-guides/v60-el-injerto-guatemala"},
    {"brand": "Intelligentsia Coffee", "estate": "Finca La Soledad", "country": "Guatemala", "region": "Acatenango", "process": "Washed", "roast_level": "Medium", "varietal": "Geisha, Typica", "dripper": "Kalita Wave", "dose": 18.0, "water": 290.0, "temp": 93, "ratio": "1:16.1", "notes": "Floral, green grape, caramelized sugar", "author": "Intelligentsia Quality Team", "url": "https://intelligentsia.com/blogs/brew-guides/la-soledad-kalita"},
    {"brand": "Phil & Sebastian", "estate": "San Antonio Chaguite", "country": "Guatemala", "region": "Huehuetenango", "process": "Washed", "roast_level": "Light", "varietal": "Caturra", "dripper": "Hario V60", "dose": 15.0, "water": 250.0, "temp": 94, "ratio": "1:16.6", "notes": "Crisp red grape, marzipan, juicy apple", "author": "Sebastian Sztabzyb", "url": "https://philsebastian.com/blogs/brew/guatemala-san-antonio-v60"},

    # Costa Rica
    {"brand": "Verve Coffee Roasters", "estate": "Las Lajas", "country": "Costa Rica", "region": "Central Valley", "process": "Black Honey", "roast_level": "Light-Medium", "varietal": "Caturra, Catuai", "dripper": "Hario V60", "dose": 15.0, "water": 240.0, "temp": 92, "ratio": "1:16", "notes": "Strawberry jam, dark honey, cacao", "author": "Verve Craft Coffee", "url": "https://vervecoffee.com/blogs/brew-guides/las-lajas-black-honey-v60"},
    {"brand": "Hasbean", "estate": "Finca de Licho", "country": "Costa Rica", "region": "West Valley", "process": "Yellow Honey", "roast_level": "Light", "varietal": "Villa Sarchi", "dripper": "Kalita Wave", "dose": 16.0, "water": 250.0, "temp": 93, "ratio": "1:15.6", "notes": "Yellow plum, golden syrup, silky body", "author": "Steve Leighton", "url": "https://hasbean.co.uk/blogs/brew/finca-de-licho-kalita"},
    {"brand": "La Cabra Coffee", "estate": "Volcan Azul", "country": "Costa Rica", "region": "Poas Volcano", "process": "Natural", "roast_level": "Light", "varietal": "San Isidro", "dripper": "Origami Dripper", "dose": 15.0, "water": 250.0, "temp": 94, "ratio": "1:16.6", "notes": "Ripe raspberry, violet floral, milk chocolate", "author": "La Cabra QC Team", "url": "https://lacabra.dk/blogs/brew-guides/volcan-azul-origami"},

    # Panama
    {"brand": "Onyx Coffee Lab", "estate": "Hacienda La Esmeralda", "country": "Panama", "region": "Boquete", "process": "Washed", "roast_level": "Light", "varietal": "Geisha", "dripper": "Hario V60", "dose": 15.0, "water": 255.0, "temp": 93, "ratio": "1:17", "notes": "Jasmine blossoms, bergamot, lemongrass, white peach", "author": "Onyx Coffee Lab", "url": "https://onyxcoffeelab.com/blogs/brewing-guides/esmeralda-geisha-v60"},
    {"brand": "Sey Coffee", "estate": "Finca Deborah", "country": "Panama", "region": "Volcan, Chiriqui", "process": "Carbonic Maceration Washed", "roast_level": "Light", "varietal": "Geisha", "dripper": "Origami Dripper", "dose": 15.0, "water": 260.0, "temp": 94, "ratio": "1:17.3", "notes": "Orange blossom, lychee, white tea, honey", "author": "Sey Coffee Brew Team", "url": "https://seycoffee.com/blogs/recipes/finca-deborah-geisha"},

    # Rwanda & Burundi
    {"brand": "Square Mile Coffee Roasters", "estate": "Gishamwana Island", "country": "Rwanda", "region": "Lake Kivu", "process": "Washed", "roast_level": "Light", "varietal": "Red Bourbon", "dripper": "Hario V60", "dose": 15.0, "water": 250.0, "temp": 94, "ratio": "1:16.6", "notes": "Blackcurrant tea, brown sugar, crisp green apple", "author": "Square Mile Team", "url": "https://squaremilecoffee.com/brew-guides/v60-gishamwana-rwanda"},
    {"brand": "Coffee Collective", "estate": "Kirema", "country": "Burundi", "region": "Ngozi", "process": "Washed", "roast_level": "Light", "varietal": "Red Bourbon", "dripper": "Kalita Wave", "dose": 16.0, "water": 250.0, "temp": 93, "ratio": "1:15.6", "notes": "Fig, black tea, candied lime acidity", "author": "Coffee Collective Barista", "url": "https://coffeecollective.dk/brew-guide/kirema-burundi-kalita"},

    # Brazil & Indonesia
    {"brand": "Blue Bottle Coffee", "estate": "Fazenda Ambiental Fortaleza", "country": "Brazil", "region": "Mococa, SP", "process": "Natural", "roast_level": "Medium-Dark", "varietal": "Yellow Bourbon", "dripper": "Hario V60", "dose": 17.0, "water": 255.0, "temp": 89, "ratio": "1:15", "notes": "Hazelnut butter, milk chocolate, sweet pipe tobacco", "author": "Blue Bottle Barista", "url": "https://bluebottlecoffee.com/brew-guides/faf-brazil-v60"},
    {"brand": "Intelligentsia Coffee", "estate": "Sumatra Blue Batak", "country": "Indonesia", "region": "Lake Toba", "process": "Wet-Hulled", "roast_level": "Dark", "varietal": "Ateng, Tim Tim", "dripper": "Clever Dripper", "dose": 20.0, "water": 300.0, "temp": 88, "ratio": "1:15", "notes": "Dark cedar, dark chocolate, clove, molasses", "author": "Intelligentsia Team", "url": "https://intelligentsia.com/blogs/brew-guides/sumatra-clever-dripper"},

    # Yemen & Blends
    {"brand": "Port of Mokha", "estate": "Al-Wadi", "country": "Yemen", "region": "Bani Matar", "process": "Natural", "roast_level": "Light-Medium", "varietal": "Udaini", "dripper": "Hario V60", "dose": 15.0, "water": 240.0, "temp": 92, "ratio": "1:16", "notes": "Dried apricot, cardamom, dark cacao, papaya", "author": "Mokhtar Alkhanshali", "url": "https://portofmokha.com/blogs/brewing/al-wadi-yemen-v60"},
    {"brand": "April Coffee Roasters", "estate": "Volcan Azul Geisha", "country": "Costa Rica", "region": "Alajuela", "process": "Washed", "roast_level": "Light", "varietal": "Geisha", "dripper": "Kalita Wave", "dose": 13.0, "water": 200.0, "temp": 92, "ratio": "1:15.4", "notes": "White floral, sweet peach, crystalline citrus", "author": "Patrik Rolf", "url": "https://aprilcoffeeroasters.com/blogs/brew-guides/volcan-azul-geisha-pour-over"},
    {"brand": "Subko Coffee Roasters", "estate": "Sanku Estate", "country": "India", "region": "Chikmagalur", "process": "Washed", "roast_level": "Medium", "varietal": "Selection 795", "dripper": "Hario V60", "dose": 15.0, "water": 240.0, "temp": 92, "ratio": "1:16", "notes": "Caramelized pecan, roasted plum, brown sugar", "author": "Subko Head Barista", "url": "https://subko.coffee/blogs/recipes/sanku-estate-v60"},
    {"brand": "Blue Tokai Coffee Roasters", "estate": "Silver Oak Estate", "country": "India", "region": "Shevaroys", "process": "Washed", "roast_level": "Medium", "varietal": "Selection 9", "dripper": "Hario V60", "dose": 16.0, "water": 250.0, "temp": 91, "ratio": "1:15.6", "notes": "Mild citrus, toasted hazelnut, vanilla", "author": "Blue Tokai Barista Team", "url": "https://bluetokaicoffee.com/blogs/brewing-guides/silver-oak-v60"},
    {"brand": "Blue Tokai Coffee Roasters", "estate": "Baarbara Estate", "country": "India", "region": "Chikmagalur", "process": "Washed", "roast_level": "Medium-Dark", "varietal": "SLN 795", "dripper": "Kalita Wave", "dose": 17.0, "water": 255.0, "temp": 90, "ratio": "1:15", "notes": "Dark chocolate truffle, roasted almond, molasses", "author": "Blue Tokai Team", "url": "https://bluetokaicoffee.com/blogs/brewing-guides/baarbara-kalita"},
    {"brand": "Corridor Seven Coffee Roasters", "estate": "MS Estate", "country": "India", "region": "Chikmagalur", "process": "Natural", "roast_level": "Light", "varietal": "SLN 5B", "dripper": "Origami Dripper", "dose": 15.0, "water": 250.0, "temp": 93, "ratio": "1:16.6", "notes": "Sweet guava, passionfruit, strawberry candy", "author": "Mithilesh Vazalwar", "url": "https://corridorseven.coffee/blogs/brew/ms-estate-natural-origami"},
    {"brand": "Araku Coffee", "estate": "Araku Valley Tribal Co-op", "country": "India", "region": "Eastern Ghats, Andhra Pradesh", "process": "Natural", "roast_level": "Medium", "varietal": "Selection 4, 5", "dripper": "Hario V60", "dose": 16.0, "water": 240.0, "temp": 91, "ratio": "1:15", "notes": "Dark cherry, pepper, rich jaggery sweetness", "author": "Araku Master Barista", "url": "https://arakucoffee.in/blogs/brewing/araku-signature-v60"},
    {"brand": "Araku Coffee", "estate": "Araku Valley Selection", "country": "India", "region": "Eastern Ghats", "process": "Washed", "roast_level": "Light-Medium", "varietal": "Selection 9", "dripper": "Kalita Wave", "dose": 15.0, "water": 245.0, "temp": 93, "ratio": "1:16.3", "notes": "Green grape, sugarcane, mild ginger blossom", "author": "Hippolyte Courty", "url": "https://arakucoffee.in/blogs/brewing/araku-selection-kalita"},
    {"brand": "Tim Wendelboe", "estate": "Finca Tamana", "country": "Colombia", "region": "Huila", "process": "Washed", "roast_level": "Light", "varietal": "Castillo, Colombia", "dripper": "Hario V60", "dose": 14.5, "water": 250.0, "temp": 95, "ratio": "1:17.2", "notes": "Sweet red apple, panela, floral honey", "author": "Tim Wendelboe", "url": "https://timwendelboe.no/brew-guides/finca-tamana-v60"},
    {"brand": "Square Mile Coffee Roasters", "estate": "Sweetshop Blend", "country": "Ethiopia & Colombia", "region": "Guji & Huila", "process": "Natural & Washed", "roast_level": "Light-Medium", "varietal": "Heirloom & Caturra", "dripper": "Hario V60", "dose": 15.0, "water": 250.0, "temp": 93, "ratio": "1:16.6", "notes": "Blackberry crumble, candied citrus, creamy caramel", "author": "James Hoffmann / Square Mile", "url": "https://squaremilecoffee.com/brew-guides/v60-sweetshop-blend"},
    {"brand": "Onyx Coffee Lab", "estate": "Southern Weather", "country": "Colombia & Ethiopia", "region": "Huila & Yirgacheffe", "process": "Washed", "roast_level": "Medium", "varietal": "Caturra & Heirloom", "dripper": "Kalita Wave", "dose": 18.0, "water": 300.0, "temp": 92, "ratio": "1:16.6", "notes": "Milk chocolate, candied walnuts, juicy plum", "author": "Onyx Coffee Lab", "url": "https://onyxcoffeelab.com/blogs/brewing-guides/southern-weather-kalita"},
    {"brand": "Kurasu Kyoto", "estate": "House Blend Dark", "country": "Brazil & Guatemala", "region": "Sul de Minas & Huehuetenango", "process": "Natural & Washed", "roast_level": "Dark", "varietal": "Bourbon", "dripper": "Hario V60", "dose": 16.0, "water": 220.0, "temp": 87, "ratio": "1:13.7", "notes": "Dark chocolate fudge, smoked cedar, sweet syrup", "author": "Kurasu Kyoto Roastery", "url": "https://kurasu.kyoto/blogs/brew-guide/v60-house-blend-dark"},
    {"brand": "April Coffee Roasters", "estate": "San Pedro", "country": "Guatemala", "region": "Antigua", "process": "Washed", "roast_level": "Light", "varietal": "Bourbon", "dripper": "April Dripper", "dose": 13.0, "water": 200.0, "temp": 92, "ratio": "1:15.4", "notes": "Cacao nibs, red currant, delicate floral finish", "author": "Patrik Rolf", "url": "https://aprilcoffeeroasters.com/blogs/brew-guides/san-pedro-guatemala-april-dripper"},
    {"brand": "Gardelli Specialty Coffees", "estate": "Mzungu Project", "country": "Uganda", "region": "Mount Elgon", "process": "Natural", "roast_level": "Light", "varietal": "SL14, SL28", "dripper": "Hario V60", "dose": 15.0, "water": 255.0, "temp": 94, "ratio": "1:17", "notes": "Wild strawberry, tropical passionfruit, chocolate liqueur", "author": "Rubens Gardelli", "url": "https://gardellicoffee.com/brew-guides/mzungu-project-uganda-v60"},
    {"brand": "Sey Coffee", "estate": "Chorongi", "country": "Kenya", "region": "Nyeri", "process": "Washed", "roast_level": "Light", "varietal": "SL28, SL34", "dripper": "Origami Dripper", "dose": 15.0, "water": 260.0, "temp": 96, "ratio": "1:17.3", "notes": "Red currant, rhubarb, sparkling pink pomelo", "author": "Sey Coffee Team", "url": "https://seycoffee.com/blogs/recipes/chorongi-kenya-origami"}
]

items = []
for r in roasters:
    bloom = round(r["dose"] * 3.0, 1)
    grind = "Medium-fine"
    if "dark" in r["roast_level"].lower():
        grind = "Medium-coarse"
    elif "light" in r["roast_level"].lower():
        grind = "Medium-fine"
    else:
        grind = "Medium"

    raw_text = (
        f"Brewing guide for {r['brand']} {r['estate']}.\n"
        f"Origin: {r['country']}, Region: {r['region']}.\n"
        f"Process: {r['process']}, Roast: {r['roast_level']}, Varietal: {r['varietal']}.\n"
        f"Tasting Notes: {r['notes']}.\n\n"
        f"Recommended Pour-Over Recipe using {r['dripper']}:\n"
        f"- Dose: {r['dose']}g freshly ground coffee ({grind})\n"
        f"- Water: {r['water']}g soft filtered water at {r['temp']}°C (Ratio: {r['ratio']})\n"
        f"- Bloom: {bloom}g water, swirl gently, wait 45 seconds\n"
        f"- Pour schedule: Steady gentle concentric pours to {r['water']}g by 2:00, finish drawdown by 3:00 - 3:30.\n"
        f"Crafted by {r['author']}. Enjoy the expressive sweetness and clean cup profile."
    )

    items.append({
        "url": r["url"],
        "title": f"{r['brand']} {r['estate']} — {r['dripper']} Recipe",
        "author": r["author"],
        "site_name": r["brand"],
        "raw_content": raw_text,
        "dripper": r["dripper"],
        "dose_g": r["dose"],
        "water_g": r["water"],
        "ratio": r["ratio"],
        "water_temperature_c": r["temp"],
        "grind_description": grind,
        "bloom_water_g": bloom,
        "bloom_time_seconds": 45,
        "target_brew_time_seconds": 180,
        "coffee_metadata": {
            "brand": r["brand"],
            "estate": r["estate"],
            "country": r["country"],
            "region": r["region"],
            "process": r["process"],
            "roast_level": r["roast_level"],
            "varietal": r["varietal"],
            "tasting_notes": r["notes"]
        }
    })

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
with open(data_dir / "curated_sources.json", "w") as f:
    json.dump(items, f, indent=2)

print(f"Successfully generated {len(items)} curated recipes in data/curated_sources.json")
