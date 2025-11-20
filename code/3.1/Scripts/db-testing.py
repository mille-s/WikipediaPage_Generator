import csv
import re
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime

DATA_TYPE = "dbo"      # Can be "dbo" or "dbp" → selects ontology namespace
SECTION = "Eile"       # Used to filter rows in input CSV
PARAMETER = ""         # Optional: filter pages by incoming property

FOLDER = "code/3.1"    # Base folder path for I/O files


# ------------------------------------------------------------
# BASIC DATA VALIDATION HELPERS
# ------------------------------------------------------------

def is_yyyy_mm_dd(text: str) -> bool:
    """
    Validates date literal format YYYY-MM-DD.
    Handles negative years and pads them to 4 digits.
    """
    try:
        if text.startswith('-'):
            temp_text = text[1:]
            parts = temp_text.split("-")

            # Pad negative-year if needed (e.g., -57 → -0057)
            if len(parts[0]) < 4:
                parts[0] = parts[0].zfill(4)

            padded_text = "-".join(parts)
            datetime.strptime(padded_text, "%Y-%m-%d")
        else:
            datetime.strptime(text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_double(text: str) -> bool:
    """Validates if string can be parsed as float."""
    try:
        float(text)
        return True
    except ValueError:
        return False


def is_year(text: str) -> bool:
    """Validates pure integer year format (positive or negative)."""
    return re.fullmatch(r"-?\d+", text) is not None


def is_non_negative_integer(text: str) -> bool:
    """Validates integer ≥ 0."""
    if not text:
        return False
    return text.strip().isdigit()


def is_positive_integer(text: str) -> bool:
    """Validates integer > 0."""
    return text.isdigit() and int(text) > 0


def is_integer(text: str) -> bool:
    """Validates integer literal."""
    return text.isdigit()


# ------------------------------------------------------------
# DBPEDIA VALIDATION CLASS
# ------------------------------------------------------------

class DBpediaValidator:
    """
    Validates DBpedia resources based on:
    - outgoing dbo properties
    - incoming dbo properties
    - correctness of object type vs expected rdfs:range
    """
    def __init__(self, data_type):
        self.sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        self.sparql.setReturnFormat(JSON)
        self.invalid_instances = []   # Logged invalid type checks
        self.data_type = data_type    # "dbo" or "dbp"


    def clean_name(self, name):
        """
        Normalizes DBpedia resource names:
        - replaces spaces with underscores
        - escapes quotes
        """
        new_name = name.replace(" ", "_").replace("'", r"\'")
        return new_name


    # ------------------------------------------------------------
    # PROPERTY RANGE FETCHERS
    # ------------------------------------------------------------

    def get_dbo_property_ranges(self, prop):
        """Fetches rdfs:range for dbo:property."""
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        SELECT DISTINCT ?range WHERE {{ dbo:{prop} rdfs:range ?range . }}
        """
        return [r["range"]["value"] for r in self.query(query)]
        

    def get_dbp_property_ranges(self, prop):
        """
        Fetches rdfs:range for dbp:property.
        Attempts:
        1. Look for owl:equivalentProperty mapping
        2. Fallback: try dbo:property with same name
        """
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX dbp: <http://dbpedia.org/property/>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>

        SELECT DISTINCT ?range WHERE {{
            {{
                dbp:{prop} owl:equivalentProperty ?dboProp .
                ?dboProp rdfs:range ?range .
            }}
            UNION
            {{
                dbo:{prop} rdfs:range ?range .
            }}
        }}
        """
        results = self.query(query)
        ranges = [r["range"]["value"] for r in results if "range" in r]
        return ranges or []


    def get_resource_types(self, resource_name):
        """
        Returns all rdf:type values under dbo: namespace for a resource.
        """
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT DISTINCT ?type WHERE {{
            <http://dbpedia.org/resource/{resource_name}> rdf:type ?type .
            FILTER(STRSTARTS(STR(?type), "http://dbpedia.org/ontology/"))
        }}
        """
        return [r["type"]["value"] for r in self.query(query)]


    def get_superclasses(self, resource_url):
        """
        Returns all superclasses via rdfs:subClassOf*.
        """
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?superclass WHERE {{
            <{resource_url}> rdfs:subClassOf* ?superclass .
            FILTER(?superclass != <{resource_url}>)
            FILTER(STRSTARTS(STR(?superclass), "http://dbpedia.org/ontology/"))
        }}
        """
        return [r["superclass"]["value"] for r in self.query(query)]


    # ------------------------------------------------------------
    # PROPERTY FETCHERS (OUTGOING / INCOMING)
    # ------------------------------------------------------------

    def get_all_outgoing_properties(self, page_name):
        """
        Returns all dbo:* outgoing properties for a resource.
        Filters out irrelevant or string-descriptive properties.
        """
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        SELECT ?property ?value WHERE {{
            <http://dbpedia.org/resource/{page_name}> ?property ?value .
            FILTER(STRSTARTS(STR(?property), "http://dbpedia.org/ontology/"))
            FILTER(!CONTAINS(STR(?property), "wikiPage"))
            FILTER(?property NOT IN (
                dbo:abstract, dbo:bicycleInformation, dbo:boilerPressure, dbo:carNumber, dbo:careerStation, dbo:collection,
                dbo:damage, dbo:depictionDescription, dbo:description, dbo:event, dbo:imageSize, dbo:impactFactorAsOf,
                dbo:isHandicappedAccessible, dbo:leaderFunction, dbo:lengthReference, dbo:liberationDate, dbo:logo,
                dbo:mapCaption, dbo:militaryService, dbo:minister, dbo:name, dbo:note, dbo:notes,
                dbo:numberOfVisitorsAsOf, dbo:orderInOffice, dbo:other, dbo:parkingInformation,
                dbo:personFunction, dbo:picture, dbo:politicalLeader, dbo:projectKeyword, dbo:pronunciation,
                dbo:quote, dbo:reference, dbo:restingPlacePosition, dbo:restriction, dbo:sales, dbo:selection,
                dbo:signature, dbo:soundRecording, dbo:speaker, dbo:statisticLabel, dbo:strength,
                dbo:termPeriod, dbo:thumbnail, dbo:title, dbo:tournamentRecord,
                dbo:visitorStatisticsAsOf, dbo:winsAtAsia, dbo:winsAtAus, dbo:winsAtChallenges,
                dbo:winsAtChampionships, dbo:winsAtJapan, dbo:winsAtLET, dbo:winsAtNWIDE,
                dbo:winsAtOtherTournaments, dbo:winsAtPGA, dbo:winsAtSenEuro, dbo:winsInEurope
            ))
        }}
        ORDER BY ?property ?value
        """

        results = []
        for r in self.query(query):
            prop = r["property"]["value"].split("/")[-1]

            # If URI resource, extract name; else literal
            value = r["value"]["value"]
            if value.startswith("http://"):
                resource = value.split("/")[-1]
            else:
                resource = value

            results.append((prop, resource))

        return results


    def get_all_incoming_properties(self, page_name):
        """
        Returns all dbo:* properties where OTHER resource points to THIS resource.
        """
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        SELECT ?subject ?property WHERE {{
            ?subject ?property <http://dbpedia.org/resource/{page_name}> .
            FILTER(STRSTARTS(STR(?property), "http://dbpedia.org/ontology/"))
            FILTER(!CONTAINS(STR(?property), "wikiPage"))
        }}
        ORDER BY ?property ?subject
        """
        results = []
        for r in self.query(query):
            subject = r["subject"]["value"]
            if subject.startswith("http://"):
                subject = subject.split("/")[-1]

            prop = r["property"]["value"].split("/")[-1]
            results.append((subject, prop))

        return results


    def get_just_incoming_properties(self, page_name):
        """
        Returns only incoming property names as a simple list.
        Used for filtering mode.
        """
        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        SELECT ?subject ?property WHERE {{
            ?subject ?property <http://dbpedia.org/resource/{page_name}> .
            FILTER(STRSTARTS(STR(?property), "http://dbpedia.org/ontology/"))
            FILTER(!CONTAINS(STR(?property), "wikiPage"))
        }}
        ORDER BY ?property ?subject
        """
        results = []
        for r in self.query(query):
            prop = r["property"]["value"].split("/")[-1]
            results.append(prop)
        return results


    # ------------------------------------------------------------
    # VALIDATION LOGIC
    # ------------------------------------------------------------

    def is_valid_type(self, resource_types, expected_ranges, target_resource, page_name=None, property_name=None, direction=None):
        """
        Validates that:
        - the target resource type matches expected range
        - OR superclass matches
        - OR literal value satisfies XSD type rules
        """
        if not expected_ranges:
            return 0.5   # Unknown → partial credit

        # Direct type match
        if set(resource_types) & set(expected_ranges):
            return 1.0

        # Check superclass inheritance
        for rtype in resource_types:
            superclasses = self.get_superclasses(rtype)
            if set(superclasses) & set(expected_ranges):
                return 1.0

        # Literal validators for xsd:* datatypes
        checks = {
            "http://www.w3.org/2001/XMLSchema#date": is_yyyy_mm_dd,
            "http://www.w3.org/2001/XMLSchema#double": is_double,
            "http://www.w3.org/2001/XMLSchema#float": is_double,
            "http://www.w3.org/2001/XMLSchema#gYear": is_year,
            "http://www.w3.org/2001/XMLSchema#nonNegativeInteger": is_non_negative_integer,
            "http://www.w3.org/2001/XMLSchema#positiveInteger": is_positive_integer,
            "http://www.w3.org/2001/XMLSchema#integer": is_integer,
        }

        # Validate literal types
        for dtype, validator in checks.items():
            if dtype in expected_ranges and validator(target_resource):
                return 1.0

        # Accept string literals
        if (
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#langString" in expected_ranges
            or "http://www.w3.org/2001/XMLSchema#string" in expected_ranges
        ):
            if target_resource is not None:
                return 1.0

        # If reached here: invalid → record it
        self.invalid_instances.append({
            'page_name': page_name or '',
            'property': property_name or '',
            'target_resource': target_resource or '',
            'direction': direction or '',
            'expected_ranges': '; '.join(expected_ranges) if expected_ranges else '',
            'actual_types': '; '.join(resource_types) if resource_types else ''
        })

        return 0.0


    def query(self, query_string):
        """
        Executes SPARQL query with safe fallback.
        Returns JSON results list.
        """
        try:
            self.sparql.setQuery(query_string)
            return self.sparql.query().convert()["results"]["bindings"]
        except:
            return []


    # ------------------------------------------------------------
    # CSV INPUT / OUTPUT
    # ------------------------------------------------------------

    def read_names(self, input):
        """
        Reads CSV file with format:
        name, category
        Filters by SECTION.
        """
        with open(input, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)

            pages = [
                row[0].strip()
                for row in reader
                if row and row[0].strip() and not row[0].startswith("#") and row[1] == SECTION
            ]

        return pages


    def save_invalid_instances(self, filename):
        """
        Writes invalid instances to CSV for debugging.
        """
        if not self.invalid_instances:
            print("No invalid instances to save.")
            return

        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'page_name', 'property', 'target_resource', 'direction',
                'expected_ranges', 'actual_types'
            ])
            writer.writeheader()
            writer.writerows(self.invalid_instances)

        print(f"Saved {len(self.invalid_instances)} invalid instances to {filename}")


    # ------------------------------------------------------------
    # MAIN VALIDATOR FOR ONE RESOURCE
    # ------------------------------------------------------------

    def validate_resource(self, page_name):
        """
        Validates:
        - outgoing dbo:* property values
        - incoming dbo:* property references
        Computes scores and prints detailed report.
        """
        clean_page = self.clean_name(page_name)
        score = total = 0
        out_score = out_total = 0
        in_score = in_total = 0

        print(f"\nValidating: {page_name}")
        print("=" * 50)

        outgoing = self.get_all_outgoing_properties(clean_page)
        incoming = self.get_all_incoming_properties(clean_page)
        page_types = self.get_resource_types(clean_page)

        if outgoing == [] and incoming == []:
            return "N/A", "", "", "", "", ""

        print("\n--- Outgoing Properties ---")
        property_ranges_cache = {}

        for prop, target_resource in outgoing:

            # Cache property ranges
            if prop not in property_ranges_cache:
                if self.data_type == "dbo":
                    property_ranges_cache[prop] = self.get_dbo_property_ranges(prop)
                else:
                    property_ranges_cache[prop] = self.get_dbp_property_ranges(prop)

            ranges = property_ranges_cache[prop]
            target_types = self.get_resource_types(target_resource)

            validity = self.is_valid_type(target_types, ranges, target_resource, page_name, prop, 'outgoing')
            score += validity
            total += 1
            out_score += validity
            out_total += 1

            status = "✅" if validity == 1 else "❓" if validity == 0.5 else "❌"
            print(f"{prop} → {target_resource} {status}")

        print("\n--- Incoming Properties ---")

        for subject, prop in incoming:

            if prop not in property_ranges_cache:
                if self.data_type == "dbo":
                    property_ranges_cache[prop] = self.get_dbo_property_ranges(prop)
                else:
                    property_ranges_cache[prop] = self.get_dbp_property_ranges(prop)

            ranges = property_ranges_cache[prop]

            validity = self.is_valid_type(page_types, ranges, page_name, page_name, prop, 'incoming')
            score += validity
            total += 1
            in_score += validity
            in_total += 1

            status = "✅" if validity == 1 else "❓" if validity == 0.5 else "❌"
            print(f"{subject} ({prop}) → {page_name} {status}")

        # Compute percentages
        percentage = round(score / total * 100) if total > 0 else 0
        out_percentage = round(out_score / out_total * 100) if out_total > 0 else 0
        in_percentage = round(in_score / in_total * 100) if in_total > 0 else 0

        print(f"\nScore: {percentage}% ({score}/{total})")
        print(f"Outgoing: {out_percentage}% ({out_score}/{out_total})")
        print(f"Incoming: {in_percentage}% ({in_score}/{in_total})")

        return percentage, total, out_percentage, out_total, in_percentage, in_total


    # ------------------------------------------------------------
    # MAIN CSV WRITER
    # ------------------------------------------------------------

    def write_to_file(self, output, invalid, pages):
        """
        Validates all pages and writes:
        - main score CSV
        - invalid instances CSV
        """
        with open(output, 'w', encoding='utf-8', newline='') as out_f, \
             open(invalid, 'w', encoding='utf-8', newline='') as fail_f:

            valid_writer = csv.writer(out_f)
            invalid_writer = csv.DictWriter(fail_f, fieldnames=[
                'page_name', 'property', 'target_resource', 'direction',
                'expected_ranges', 'actual_types'
            ])

            valid_writer.writerow([
                "Page Name", "Score", "Datapoints",
                "Properties Score", "Properties Checked",
                "Incoming Score", "Incoming Checked"
            ])
            invalid_writer.writeheader()

            for page in pages:
                score, datapoints, propscore, proptotal, isofscore, isoftotal = self.validate_resource(page)

                # Write scores
                valid_writer.writerow([page, score, datapoints, propscore, proptotal, isofscore, isoftotal])
                out_f.flush()

                # Write invalid instances
                if self.invalid_instances:
                    invalid_writer.writerows(self.invalid_instances)
                    fail_f.flush()
                    print(f"  → {len(self.invalid_instances)} invalid instances written for {page}")
                    self.invalid_instances.clear()

                print(f"Written {page} to CSV")
                print("=" * 100)


# ------------------------------------------------------------
# MAIN ENTRY POINT
# ------------------------------------------------------------

def main():
    validator = DBpediaValidator(DATA_TYPE)

    input_file = f'{FOLDER}/Input/files-sorted.csv'
    output_file = f'{FOLDER}/Output/Scores/{SECTION}_{DATA_TYPE}_scores.csv'
    invalid_file = f'{FOLDER}/Output/Fails/{SECTION}_{DATA_TYPE}_invalid_instances.csv'

    filtered_pages = []

    # CSV mode
    if input_file.__contains__(".csv"):
        pages = validator.read_names(input_file)
        filtered_pages = pages

    # Filtering mode (not used here)
    else:
        pages = validator.get_values_from_list(input_file)

        if PARAMETER != "":
            print(f"Checking pages for {PARAMETER} property...")
            for i, page in enumerate(pages):
                print(f"\t{round(i / len(pages) * 100)}% completed ({page})", end="\r")
                just_incoming_props = set(validator.get_just_incoming_properties(validator.clean_name(page)))
                if PARAMETER in just_incoming_props:
                    filtered_pages.append(page)
        else:
            filtered_pages = pages

    validator.write_to_file(output_file, invalid_file, filtered_pages)


if __name__ == "__main__":
    main()
