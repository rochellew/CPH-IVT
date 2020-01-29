# custom URL path component converters, for converting parts of URLs into view parameters
# https://docs.djangoproject.com/en/2.1/topics/http/urls/#registering-custom-path-converters


class StateUSPSConverter():
    """
    Matches USPS 2-letter state codes; exactly two alphabetic characters a-zA-Z

    """
    # Matches either 2 lower case letters or 2 upper-case letters,
    # but does *not* match mixed case
    regex = '[a-z]{2}|[A-Z]{2}'

    # convert the URL path string to a python value
    def to_python(self, value):
        """

        :param value: 

        """
        # state codes should be uppercase for matching against our model
        return value.upper()

    # convert a python value to a URL path string
    def to_url(self, value):
        """

        :param value: 

        """
        # state codes should be lowercase for URLs
        return value.lower()


class FIPS3Converter():
    """
    Matches 3-digit FIPS codes - exactly 3 digits 0-9, as a string
    """
    regex = '[0-9]{3}'

    def to_python(self, value):
        """

        :param value: 

        """
        # presumably the RegEx will ensure we receieved only digits; we don't
        # have to convert the type so there is nothing else to do here
        return value

    def to_url(self, value):
        """

        :param value: 

        """
        return value
