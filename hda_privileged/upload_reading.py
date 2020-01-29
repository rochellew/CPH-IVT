# Logic for reading data points out of a CSV file.
# We have three possible column formats; this uses a different function
# to retrieve counties from the database depending on the the format
# choice that is passed in at runtime

import csv

from hda_privileged.models import US_State, US_County, Data_Point

# constants

CHOICE_NAME = "NAME"
CHOICE_1FIPS = "1FIPS"
CHOICE_2FIPS = "2FIPS"

UPLOAD_FORMAT_CHOICES = [
    (CHOICE_NAME, "Use state name ('State') and county name ('County')"),
    (CHOICE_1FIPS, "Use single 5-digit FIPS code ('FIPS')"),
    (CHOICE_2FIPS, "Use 2-digit state ('State') and 3-digit county ('County') FIPS codes"),
]


# Regardless of whether the file was using 5-digit FIPS codes or split ones,
# the heavy lifting of FIPS code matching is done here: both get_county_2fips
# and get_county_1fips call this method after extracting the appropriate codes
# from the CSV rows.
def get_county_with_fips(state_fips, county_fips):
    """

    :param state_fips: eg: '01'
    :param county_fips: eg: '001'

    """
    try:
        state = US_State.objects.get(fips=state_fips)
        county = state.counties.get(fips=county_fips)
        return (county, None)
    except US_State.DoesNotExist:
        msg = {county_fips:state_fips}
        return (None, msg)
    except US_County.DoesNotExist:
        msg = {county_fips: state_fips}
        return (None, msg)

# Defines functions that can translate a DictReader row into a county model object
# based on the selected column format. e.g. if 'choice' is 'NAME', we want a
# function that takes in a DictReader row and uses the state name and county name
# to query and return a unique US_County instance.
# These functions have the signature:
#     func(row: dict<str, str>): (US_County, None) | (None, String)
# i.e. they return a tuple where either the first member is a county instance,
# OR the second member is an error message.


def get_county_with_2fips(row):
    """

    :param row: breaks the combination of state_fips and county_fips into state_fips and county_fips respectively

    """
    state_fips = row['State']
    county_fips = row['County']
    return get_county_with_fips(state_fips, county_fips)


def get_county_with_1fips(row):
    """

    :param row: combination of state_fips and county_fips

    """
    fips = row['FIPS']
    state_fips = fips[0:2]
    county_fips = fips[2:5]
    return get_county_with_fips(state_fips, county_fips)


def get_county_with_name(row):
    """

    :param row: reads the state and county name

    """
    state_name = row['State']
    county_name = row['County']
    try:
        state = US_State.objects.get(full=state_name)
    except US_State.DoesNotExist:
        msg = {county_name: state_name}
        return (None, msg)
    # can't use get with startswith for counties, because of situations like:
    # Clay County, GA and Clayton County, GA
    # trying to use startswith=Clay will match both of these
    # county = state.counties.get(name__startswith=county_name)
    possible_counties = state.counties.filter(name__startswith=county_name)
    # how do we narrow this down?
    if possible_counties.count() == 1:
        return (possible_counties.first(), None)
    elif possible_counties.count() > 1:
        # if we matched a substring of multiple  county names, prefer the shortest as being
        # the most exact; first evaluate the query
        county_iter = possible_counties.iterator()
        # sort in ascending order of name length, returning a list
        shortest_first = sorted(county_iter, key=lambda c: len(c.name))
        # return the first county (shortest name)
        return (shortest_first[0], None)
    else:
        msg = {county_name: state_name}
        return (None, msg)

# map choice options to the appropriate function for parsing counties
UPLOAD_FORMAT_FUNCTIONS = {
    CHOICE_1FIPS: get_county_with_1fips,
    CHOICE_2FIPS: get_county_with_2fips,
    CHOICE_NAME: get_county_with_name,
}


def read_data_points_from_file(file, choice, data_set):
    """Reads all the data points from a CSV file, adding them to the given data set.

    :param file: user's selected csv file
    :param choice: one of the choice codes from UPLOAD_FORMAT_CHOICES
    :param CHOICE_NAME: assume the State and County columns contain full names in each row
    :param CHOICE_1FIPS: assume there is one column to uniquely identify the county
    :param CHOICE_2FIPS: assume the State and County columns contain 2 FIPS: codes
    :param data_set: a Data_Set model instance
    :returns: A list of Data_Point model objects, one per row in the CSV file, all pointing to
        the indicated Data_Set instance.

    """
    county_getter = UPLOAD_FORMAT_FUNCTIONS.get(choice, None)
    if not county_getter:
        raise TypeError(f"Choice {choice} did not match to a county parsing function")

    unsuccessful_counties_datapoints = {}
    successful_counties_datapoints = []

    count = 0
    for row in csv.DictReader(file):
        # read a row
        (county, error) = county_getter(row)
        # handle the results
        if county is not None:
            # if there is no value, do not specify a default here:
            # leave it blank/None when creating the Data Point and let
            # the model implementation handle defaults.
            value_str = row.get('Value', None)
            value = float(value_str) if value_str else None
            # create and collect (but do not save!) the data point
            data_point = Data_Point(county=county, data_set=data_set, value=value)
            successful_counties_datapoints.append(data_point)
        elif error is not None:
            unsuccessful_counties_datapoints.update(error)
        # increment a row counter
        count += 1

    return successful_counties_datapoints, unsuccessful_counties_datapoints
