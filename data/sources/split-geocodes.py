import os
import csv

INPUT_FILENAME = "all-geocodes-v2017.csv"
STATE_OUTPUT_FILENAME = "states.csv"
COUNTY_OUTPUT_FILENAME = "counties.csv"

LEVELS = {
    "STATE": "040",
    "COUNTY": "050",
}

INDICES = {
    "level": 0,
    "state_fips": 1,
    "county_fips": 2,
    "name": 6
}

state_list = []
county_list = []

with open(INPUT_FILENAME, newline='') as inputfile:
    reader = csv.reader(inputfile)

    for row in reader:
        level = row[INDICES["level"]]
        state_fips = row[INDICES["state_fips"]]
        county_fips = row[INDICES["county_fips"]]
        name = row[INDICES["name"]]

        if level == LEVELS["STATE"]:
            state_list.append((state_fips, name))
        elif level == LEVELS["COUNTY"]:
            county_list.append((state_fips, county_fips, name))

print(len(state_list))
print(len(county_list))

def write_csv(filename, headers, rows):
    with open(filename, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)
        writer.writerows(rows)

write_csv(STATE_OUTPUT_FILENAME, ("state_fips", "name"), state_list)
write_csv(COUNTY_OUTPUT_FILENAME, ("state_fips", "county_fips", "name"), county_list)

print("done")
