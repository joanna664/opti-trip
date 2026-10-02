from src.geocoding import GeocodingService

geo_service = GeocodingService()

query = "White Tower Thessaloniki"
print(f"Αναζήτηση για: {query}...")

loc = geo_service.resolve_location(query)

if loc:
    print(f"Βρέθηκε: {loc.name}")
    print(f"Συντεταγμένες: Lat {loc.lat}, Lon {loc.lon}")
else:
    print("Η τοποθεσία δεν βρέθηκε.")