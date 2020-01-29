import csv
import os.path

SOURCE_DIR = os.path.join(".", "data", "sources")

OLD_COUNTIES_FILE = os.path.join(SOURCE_DIR, "counties_and_equivalents_2010.csv")
NEW_COUNTIES_FILE = os.path.join(SOURCE_DIR, "counties_and_equivalents_2017.csv")

OLD_STATES_FILE = os.path.join(SOURCE_DIR, "states_territories_2010.csv")
NEW_STATES_FILE = os.path.join(SOURCE_DIR, "states_territories_2017.csv")

COUNTY_OUTPUT_FILE = os.path.join(".", "data", "counties.csv")
STATE_OUTPUT_FILE = os.path.join(".", "data", "states.csv")


def load_csv(filename, proc):
    with open(filename) as file:
        return [proc(row) for row in csv.DictReader(file)]


def parse_old_state(row):
    # FIPS,USPS,NAME
    return {
        "Name": row["NAME"],
        "FIPS": row["FIPS"],
        "USPS": row["USPS"],
    }


def parse_old_county(row):
    # STATE_USPS,STATE_FIPS,FIPS,NAME
    return {
        "Name": row["NAME"],
        "FIPS": row["FIPS"],
        "State": {
            "FIPS": row["STATE_FIPS"],
            "USPS": row["STATE_USPS"],
        },
    }


def make_usps_table(old_states):
    return {state["FIPS"]: state["USPS"] for state in old_states}


def parse_new_state(usps_table):
    def parse(row):
        # state_fips,name
        return {
            "Name": row["name"],
            "FIPS": row["state_fips"],
            "USPS": usps_table[row["state_fips"]],
        }
    return parse


def parse_new_county(usps_table):
    def parse(row):
        # state_fips,county_fips,name
        return {
            "Name": row["name"],
            "FIPS": row["county_fips"],
            "State": {
                "FIPS": row["state_fips"],
                "USPS": usps_table[row["state_fips"]]
            }
        }
    return parse


def write_csv(filename, headers, rows):
    with open(filename, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)
        writer.writerows(rows)


def main():
    # load our old data up first...
    old_states = load_csv(OLD_STATES_FILE, parse_old_state)
    old_counties = load_csv(OLD_COUNTIES_FILE, parse_old_county)

    # this gives us a map from State FIPS -> State USPS
    usps_table = make_usps_table(old_states)

    # now load up our newer data...
    new_states = load_csv(NEW_STATES_FILE, parse_new_state(usps_table))
    new_counties = load_csv(NEW_COUNTIES_FILE, parse_new_county(usps_table))

    # now that all the data is in memory, figure out that territories existed in the old
    # file that do not exist in the new file:
    old_state_codes = set([state["FIPS"] for state in old_states])
    new_state_codes = set([state["FIPS"] for state in new_states])
    missing_states = old_state_codes - new_state_codes

    # now create a master list of counties start with the newer list, then add counties from
    # the older list if they are from a state that wasn't originally included in the newer list
    master_county_list = new_counties + \
        [county for county in old_counties if county["State"]["FIPS"] in missing_states]

    # change list of dicts into list of tuples so we can pass them to a csv writer as rows
    # (could maybe skip this with a DictWriter?)
    county_rows = [(c["State"]["FIPS"], c["FIPS"], c["State"]["USPS"], c["Name"])
                   for c in master_county_list]
    county_headers = ("STATE_FIPS", "FIPS", "STATE_USPS", "NAME")
    write_csv(COUNTY_OUTPUT_FILE, county_headers, county_rows)

    # write the list of states, similar to above
    # (later maybe we do more processing on the states; for now this list is equivalent
    # to the one in OLD_STATES_FILE)
    state_rows = [(s["FIPS"], s["USPS"], s["Name"]) for s in old_states]
    state_headers = ("FIPS", "USPS", "NAME")
    write_csv(STATE_OUTPUT_FILE, state_headers, state_rows)


if __name__ == "__main__":
    main()
